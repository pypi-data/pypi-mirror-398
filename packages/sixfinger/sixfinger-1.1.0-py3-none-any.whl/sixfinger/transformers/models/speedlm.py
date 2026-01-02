"""
SpeedLM - Ultra-Fast CPU Language Model
========================================

Hash-based ternary weights for maximum speed on CPU.
"""

import numpy as np
import time
import os
from typing import List, Optional, Union, Tuple
from pathlib import Path

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class SpeedLM:
    """
    Hash-Based Ternary Language Model
    
    Optimized for CPU training/inference with minimal memory.
    
    Args:
        n_buckets: Hash table size (higher = more capacity)
        n_features: Hidden dimension
        context_sizes: N-gram sizes for context (e.g., [1,2,3,4,5,8])
        vocab: Vocabulary size (256 for byte-level)
        lr: Learning rate
        update_threshold: Threshold for ternary weight updates
        verbose: Print progress information
        
    Example:
        >>> model = SpeedLM(n_buckets=100_000, n_features=256)
        >>> model.train_file('data.txt')
        >>> output = model.generate(b'Hello', length=100)
        >>> print(output.decode('utf-8', errors='ignore'))
    """
    
    def __init__(
        self,
        n_buckets: int = 500_000,
        n_features: int = 1024,
        context_sizes: List[int] = None,
        vocab: int = 256,
        lr: float = 0.01,
        update_threshold: float = 0.5,
        verbose: bool = True
    ):
        if context_sizes is None:
            context_sizes = [1, 2, 3, 4, 5, 8, 12]
            
        self.n_buckets = n_buckets
        self.n_features = n_features
        self.context_sizes = context_sizes
        self.vocab = vocab
        self.lr = lr
        self.update_threshold = update_threshold
        self.verbose = verbose
        
        self._initialize_weights()
        
        # Stats
        self.global_step = 0
        self.epoch = 0
    
    def _initialize_weights(self):
        """Initialize ternary weights"""
        if self.verbose:
            print(f"\n{'='*50}")
            print("🚀 Initializing SpeedLM")
            print(f"{'='*50}")
            print(f"  Buckets: {self.n_buckets:,}")
            print(f"  Features: {self.n_features:,}")
            print(f"  Context: {self.context_sizes}")
        
        # Ternary weights: -1, 0, +1
        self.W_in = np.random.choice(
            [-1, 0, 0, 0, 1],  # 60% sparse
            size=(self.n_buckets, self.n_features)
        ).astype(np.int8)
        
        self.W_out = np.random.choice(
            [-1, 0, 0, 0, 1],
            size=(self.n_features, self.vocab)
        ).astype(np.int8)
        
        self.bias_h = np.zeros(self.n_features, dtype=np.float32)
        self.bias_o = np.zeros(self.vocab, dtype=np.float32)
        
        # Gradient accumulators
        self.grad_acc_in = np.zeros((self.n_buckets, self.n_features), dtype=np.float32)
        self.grad_acc_out = np.zeros((self.n_features, self.vocab), dtype=np.float32)
        
        if self.verbose:
            mem_mb = self._memory_mb()
            total_params = self.n_buckets * self.n_features + self.n_features * self.vocab
            print(f"  Total params: {total_params:,}")
            print(f"  Memory: ~{mem_mb:.1f} MB")
            print(f"{'='*50}\n")
    
    def _memory_mb(self) -> float:
        """Estimate memory usage in MB"""
        w_size = (self.n_buckets * self.n_features + self.n_features * self.vocab) * 1  # int8
        grad_size = (self.n_buckets * self.n_features + self.n_features * self.vocab) * 4  # float32
        return (w_size + grad_size) / 1024 / 1024
    
    def _hash_ngram(self, data: bytes, pos: int, n: int) -> Optional[int]:
        """FNV-1a hash"""
        if pos < n - 1:
            return None
        h = 2166136261
        for i in range(n):
            h ^= data[pos - n + 1 + i]
            h = (h * 16777619) & 0xFFFFFFFF
        return h % self.n_buckets
    
    def _get_hashes(self, data: bytes, pos: int) -> List[int]:
        """Get context hashes"""
        hashes = []
        for n in self.context_sizes:
            h = self._hash_ngram(data, pos, n)
            if h is not None:
                hashes.append(h)
        return hashes
    
    def _forward(self, hashes: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """Forward pass (no matmul)"""
        # Sum ternary weights
        hidden = np.zeros(self.n_features, dtype=np.int32)
        for h in hashes:
            hidden += self.W_in[h]
        
        hidden_f = hidden.astype(np.float32) + self.bias_h
        hidden_act = np.maximum(hidden_f, 0)  # ReLU
        
        # Sparse output
        logits = np.zeros(self.vocab, dtype=np.float32)
        active = np.where(hidden_act > 0.1)[0]
        for idx in active:
            logits += hidden_act[idx] * self.W_out[idx].astype(np.float32)
        logits += self.bias_o
        
        return logits, hidden_act
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Stable softmax"""
        e = np.exp(x - x.max())
        return e / (e.sum() + 1e-10)
    
    def _train_step(self, data: bytes, pos: int, target: int) -> float:
        """Single training step"""
        hashes = self._get_hashes(data, pos)
        if not hashes:
            return 0.0
        
        logits, hidden = self._forward(hashes)
        probs = self._softmax(logits)
        loss = -np.log(probs[target] + 1e-10)
        
        # Backward
        grad = probs.copy()
        grad[target] -= 1.0
        self.bias_o -= self.lr * grad
        
        active = np.where(hidden > 0.1)[0]
        for idx in active:
            self.grad_acc_out[idx] += hidden[idx] * grad
        
        grad_h = np.zeros(self.n_features, dtype=np.float32)
        for idx in active:
            grad_h[idx] = np.sum(grad * self.W_out[idx])
        
        self.bias_h -= self.lr * grad_h
        
        for h in hashes:
            self.grad_acc_in[h] += grad_h
        
        self.global_step += 1
        return loss
    
    def _update_weights(self):
        """Update ternary weights"""
        # Input
        mask = np.abs(self.grad_acc_in) > self.update_threshold
        self.W_in = np.clip(
            self.W_in.astype(np.int16) - np.sign(self.grad_acc_in).astype(np.int16) * mask,
            -1, 1
        ).astype(np.int8)
        self.grad_acc_in[mask] = 0
        
        # Output
        mask = np.abs(self.grad_acc_out) > self.update_threshold
        self.W_out = np.clip(
            self.W_out.astype(np.int16) - np.sign(self.grad_acc_out).astype(np.int16) * mask,
            -1, 1
        ).astype(np.int8)
        self.grad_acc_out[mask] = 0
    
    def train_data(self, data: Union[bytes, str]) -> dict:
        """Train on data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        max_ctx = max(self.context_sizes)
        total_loss = 0.0
        n_tokens = 0
        
        start = time.time()
        
        for i in range(max_ctx, len(data)):
            loss = self._train_step(data, i-1, data[i])
            total_loss += loss
            n_tokens += 1
            
            if n_tokens % 1000 == 0:
                self._update_weights()
        
        self._update_weights()
        elapsed = time.time() - start
        
        return {
            'loss': total_loss / max(n_tokens, 1),
            'tokens': n_tokens,
            'time': elapsed,
            'speed': n_tokens / elapsed
        }
    
    def train_file(
        self,
        filepath: Union[str, Path],
        chunk_size: int = 100_000,
        num_epochs: int = 1
    ) -> dict:
        """Train from file (streaming)"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_size = filepath.stat().st_size
        
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"📂 Training: {filepath.name}")
            print(f"{'='*50}")
            print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
            print(f"  Epochs: {num_epochs}")
            print(f"  Chunk: {chunk_size / 1024:.1f} KB")
            print(f"{'='*50}\n")
        
        total_tokens = 0
        total_loss = 0.0
        start_time = time.time()
        
        for epoch in range(num_epochs):
            if self.verbose:
                print(f"📖 Epoch {epoch + 1}/{num_epochs}")
            
            with open(filepath, 'rb') as f:
                prev_tail = b''
                
                # Progress bar
                iterator = range(0, file_size, chunk_size)
                if HAS_TQDM and self.verbose:
                    iterator = tqdm(iterator, desc="Progress", unit="chunk")
                
                for _ in iterator:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    data = prev_tail + chunk
                    prev_tail = chunk[-max(self.context_sizes):]
                    
                    stats = self.train_data(data)
                    total_tokens += stats['tokens']
                    total_loss += stats['loss'] * stats['tokens']
                    
                    if HAS_TQDM and self.verbose:
                        elapsed = time.time() - start_time
                        speed = total_tokens / elapsed / 1000
                        iterator.set_postfix({
                            'loss': f"{total_loss / total_tokens:.3f}",
                            'speed': f"{speed:.1f}K tok/s"
                        })
            
            self.epoch += 1
        
        total_time = time.time() - start_time
        avg_loss = total_loss / max(total_tokens, 1)
        
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"✅ Training complete!")
            print(f"  Tokens: {total_tokens:,}")
            print(f"  Loss: {avg_loss:.4f}")
            print(f"  Time: {total_time / 60:.1f} min")
            print(f"  Speed: {total_tokens / total_time / 1000:.1f}K tok/s")
            
            # 1GB estimate
            speed_mb_s = (file_size * num_epochs) / total_time / 1024 / 1024
            est_1gb = 1024 / speed_mb_s / 60
            print(f"  1GB estimate: {est_1gb:.1f} min")
            print(f"{'='*50}\n")
        
        return {
            'loss': avg_loss,
            'tokens': total_tokens,
            'time': total_time,
            'speed_kb_s': (file_size * num_epochs) / total_time / 1024
        }
    
    def generate(
        self,
        prompt: Union[bytes, str],
        length: int = 100,
        temperature: float = 0.8,
        top_k: int = 0,
        top_p: float = 1.0
    ) -> bytes:
        """Generate text"""
        if isinstance(prompt, str):
            prompt = prompt.encode('utf-8')
        
        result = bytearray(prompt)
        
        for _ in range(length):
            hashes = self._get_hashes(bytes(result), len(result) - 1)
            if not hashes:
                result.append(np.random.randint(32, 127))
                continue
            
            logits, _ = self._forward(hashes)
            
            # Temperature
            logits = logits / temperature
            
            # Top-k
            if top_k > 0:
                indices = np.argpartition(logits, -top_k)[-top_k:]
                mask = np.ones_like(logits, dtype=bool)
                mask[indices] = False
                logits[mask] = -float('inf')
            
            # Top-p
            if top_p < 1.0:
                sorted_idx = np.argsort(logits)[::-1]
                sorted_logits = logits[sorted_idx]
                probs = self._softmax(sorted_logits)
                cumsum = np.cumsum(probs)
                mask = cumsum > top_p
                mask[0] = False
                logits[sorted_idx[mask]] = -float('inf')
            
            probs = self._softmax(logits)
            next_token = np.random.choice(self.vocab, p=probs)
            result.append(next_token)
        
        return bytes(result)
    
    def save(self, path: Union[str, Path]):
        """Save model"""
        path = Path(path)
        np.savez_compressed(
            path,
            W_in=self.W_in,
            W_out=self.W_out,
            bias_h=self.bias_h,
            bias_o=self.bias_o,
            config=np.array([{
                'n_buckets': self.n_buckets,
                'n_features': self.n_features,
                'context_sizes': self.context_sizes,
                'vocab': self.vocab,
                'lr': self.lr,
                'update_threshold': self.update_threshold,
                'global_step': self.global_step,
                'epoch': self.epoch,
            }], dtype=object)
        )
        
        if self.verbose:
            size = path.stat().st_size / 1024 / 1024
            print(f"💾 Model saved: {path} ({size:.1f} MB)")
    
    def load(self, path: Union[str, Path]):
        """Load model"""
        path = Path(path)
        data = np.load(path, allow_pickle=True)
        
        self.W_in = data['W_in']
        self.W_out = data['W_out']
        self.bias_h = data['bias_h']
        self.bias_o = data['bias_o']
        
        config = data['config'].item()
        self.n_buckets = config['n_buckets']
        self.n_features = config['n_features']
        self.context_sizes = config['context_sizes']
        self.vocab = config['vocab']
        self.lr = config['lr']
        self.update_threshold = config['update_threshold']
        self.global_step = config.get('global_step', 0)
        self.epoch = config.get('epoch', 0)
        
        # Reinit gradients
        self.grad_acc_in = np.zeros((self.n_buckets, self.n_features), dtype=np.float32)
        self.grad_acc_out = np.zeros((self.n_features, self.vocab), dtype=np.float32)
        
        if self.verbose:
            print(f"📥 Model loaded: {path}")
    
    @classmethod
    def from_pretrained(cls, path: Union[str, Path], **kwargs):
        """Load pretrained model"""
        model = cls(n_buckets=1, n_features=1, **kwargs)  # Dummy init
        model.load(path)
        return model