"""
Unit tests for SpeedLM model
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile

from sixfinger.transformers import SpeedLM


class TestSpeedLM:
    """Test SpeedLM model"""
    
    @pytest.fixture
    def model(self):
        """Create small test model"""
        return SpeedLM(
            n_buckets=1000,
            n_features=64,
            context_sizes=[1, 2, 3],
            verbose=False
        )
    
    @pytest.fixture
    def sample_data(self):
        """Sample training data"""
        return b"The quick brown fox jumps over the lazy dog. " * 100
    
    def test_initialization(self, model):
        """Test model initialization"""
        assert model.n_buckets == 1000
        assert model.n_features == 64
        assert model.W_in.shape == (1000, 64)
        assert model.W_out.shape == (64, 256)
        assert model.W_in.dtype == np.int8
        assert model.W_out.dtype == np.int8
    
    def test_hashing(self, model):
        """Test hash function"""
        data = b"test data"
        
        # Hash should be consistent
        h1 = model._hash_ngram(data, 5, 3)
        h2 = model._hash_ngram(data, 5, 3)
        assert h1 == h2
        
        # Should be in range
        assert 0 <= h1 < model.n_buckets
        
        # Different positions should give different hashes
        h3 = model._hash_ngram(data, 6, 3)
        assert h1 != h3
    
    def test_forward(self, model):
        """Test forward pass"""
        data = b"test"
        hashes = model._get_hashes(data, 3)
        
        logits, hidden = model._forward(hashes)
        
        assert logits.shape == (256,)
        assert hidden.shape == (64,)
        assert not np.any(np.isnan(logits))
        assert not np.any(np.isnan(hidden))
    
    def test_train_data(self, model, sample_data):
        """Test training on data"""
        stats = model.train_data(sample_data)
        
        assert 'loss' in stats
        assert 'tokens' in stats
        assert stats['tokens'] > 0
        assert stats['loss'] > 0
    
    def test_generate(self, model):
        """Test text generation"""
        prompt = b"The"
        output = model.generate(prompt, length=20, verbose=False)
        
        assert isinstance(output, bytes)
        assert len(output) >= len(prompt)
        assert output.startswith(prompt)
    
    def test_save_load(self, model, sample_data):
        """Test model save/load"""
        # Train a bit
        model.train_data(sample_data[:1000])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'test_model.npz'
            
            # Save
            model.save(path)
            assert path.exists()
            
            # Load
            model2 = SpeedLM.from_pretrained(path, verbose=False)
            
            # Check weights match
            assert np.array_equal(model.W_in, model2.W_in)
            assert np.array_equal(model.W_out, model2.W_out)
            assert np.array_equal(model.bias_h, model2.bias_h)
            assert np.array_equal(model.bias_o, model2.bias_o)
            
            # Check generation matches
            prompt = b"Test"
            np.random.seed(42)
            out1 = model.generate(prompt, length=20, verbose=False)
            np.random.seed(42)
            out2 = model2.generate(prompt, length=20, verbose=False)
            assert out1 == out2
    
    def test_train_file(self, model):
        """Test training from file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            data_path = Path(tmpdir) / 'test_data.txt'
            with open(data_path, 'wb') as f:
                f.write(b"Test training data. " * 100)
            
            # Train
            stats = model.train_file(data_path, chunk_size=500)
            
            assert stats['tokens'] > 0
            assert stats['loss'] > 0
            assert stats['time'] > 0
    
    def test_temperature(self, model, sample_data):
        """Test temperature sampling"""
        model.train_data(sample_data)
        prompt = b"The"
        
        # Low temperature should be more deterministic
        np.random.seed(42)
        out1 = model.generate(prompt, length=50, temperature=0.1, verbose=False)
        np.random.seed(42)
        out2 = model.generate(prompt, length=50, temperature=0.1, verbose=False)
        
        # Should be very similar (not always identical due to floating point)
        similarity = sum(a == b for a, b in zip(out1, out2)) / len(out1)
        assert similarity > 0.8
        
        # High temperature should be more random
        np.random.seed(42)
        out3 = model.generate(prompt, length=50, temperature=1.5, verbose=False)
        
        similarity = sum(a == b for a, b in zip(out1, out3)) / len(out1)
        assert similarity < 0.9  # Should differ more
    
    def test_ternary_weights(self, model):
        """Test that weights stay ternary"""
        data = b"test data" * 100
        model.train_data(data)
        
        # Check all weights are -1, 0, or 1
        assert np.all(np.isin(model.W_in, [-1, 0, 1]))
        assert np.all(np.isin(model.W_out, [-1, 0, 1]))


class TestSampling:
    """Test sampling strategies"""
    
    def test_greedy_sample(self):
        """Test greedy sampling"""
        from sixfinger.transformers.generation.sampling import greedy_sample
        
        logits = np.array([0.1, 0.5, 0.2, 0.9, 0.3])
        token = greedy_sample(logits)
        assert token == 3  # Index of max
    
    def test_sample_token_temperature(self):
        """Test temperature sampling"""
        from sixfinger.transformers.generation.sampling import sample_token
        
        logits = np.array([1.0, 2.0, 3.0, 4.0])
        
        # Temperature = 0 should be greedy
        token = sample_token(logits, temperature=0.0)
        assert token == 3
        
        # Temperature > 0 should sample
        np.random.seed(42)
        samples = [sample_token(logits, temperature=1.0) for _ in range(100)]
        # Should have some variety
        assert len(set(samples)) > 1
    
    def test_top_k_filtering(self):
        """Test top-k filtering"""
        from sixfinger.transformers.generation.sampling import sample_token
        
        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Top-k=2 should only sample from top 2
        np.random.seed(42)
        samples = [sample_token(logits, temperature=1.0, top_k=2) for _ in range(100)]
        assert all(s in [3, 4] for s in samples)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])