"""
Custom training example

Shows advanced training configuration and monitoring.
"""

from sixfinger.transformers import SpeedLM
from pathlib import Path
import time


def create_training_data():
    """Create larger synthetic dataset"""
    
    print("📝 Creating synthetic training data...")
    
    # Various text patterns
    sentences = [
        "The artificial intelligence model learns from data.",
        "Machine learning algorithms improve with experience.",
        "Neural networks consist of interconnected layers.",
        "Deep learning enables complex pattern recognition.",
        "Natural language processing analyzes human language.",
        "Computer vision interprets visual information.",
        "Reinforcement learning optimizes decision making.",
        "Data science extracts insights from information.",
    ]
    
    # Generate large corpus
    corpus = []
    for i in range(1000):  # ~500KB
        for sent in sentences:
            corpus.append(f"{sent}\n")
        corpus.append("\n")
    
    text = "".join(corpus)
    
    # Save
    path = Path('custom_training_data.txt')
    with open(path, 'w') as f:
        f.write(text)
    
    print(f"   Created {path} ({len(text) / 1024:.1f} KB)")
    return path


def train_with_monitoring():
    """Train with custom monitoring"""
    
    print("\n" + "=" * 60)
    print("Custom Training with Monitoring")
    print("=" * 60)
    
    # Create data
    data_path = create_training_data()
    
    # Model config
    config = {
        'n_buckets': 100_000,
        'n_features': 512,
        'context_sizes': [1, 2, 3, 4, 5, 8, 12],
        'lr': 0.01,
        'verbose': True
    }
    
    print("\n🚀 Initializing model...")
    print(f"   Config: {config}")
    
    model = SpeedLM(**config)
    
    # Train with multiple epochs
    print("\n📚 Training for 3 epochs...")
    
    epoch_stats = []
    start_time = time.time()
    
    for epoch in range(3):
        print(f"\n{'─'*60}")
        print(f"Epoch {epoch + 1}/3")
        print('─'*60)
        
        stats = model.train_file(
            data_path,
            chunk_size=50_000,
            num_epochs=1
        )
        
        epoch_stats.append(stats)
        
        # Show progress
        elapsed = time.time() - start_time
        print(f"\n📊 Epoch {epoch + 1} Summary:")
        print(f"   Loss: {stats['loss']:.4f}")
        print(f"   Speed: {stats['speed_kb_s']:.1f} KB/s")
        print(f"   Elapsed: {elapsed:.1f}s")
        
        # Save checkpoint
        checkpoint_path = f'checkpoint_epoch_{epoch + 1}.npz'
        model.save(checkpoint_path)
        print(f"   Saved: {checkpoint_path}")
    
    total_time = time.time() - start_time
    
    # Final summary
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    
    print("\n📊 Overall Statistics:")
    print(f"   Total time: {total_time / 60:.2f} minutes")
    print(f"   Epochs: 3")
    print(f"   Final loss: {epoch_stats[-1]['loss']:.4f}")
    print(f"   Loss improvement: {epoch_stats[0]['loss'] - epoch_stats[-1]['loss']:.4f}")
    
    # Save final model
    model.save('final_model.npz')
    print("\n💾 Final model saved: final_model.npz")
    
    # Test generation
    print("\n✍️  Test Generation:")
    test_prompts = [
        "The artificial",
        "Machine learning",
        "Deep learning"
    ]
    
    for prompt in test_prompts:
        output = model.generate(
            prompt.encode('utf-8'),
            length=100,
            temperature=0.7,
            verbose=False
        )
        print(f"\nPrompt: {prompt}")
        print(f"Output: {output.decode('utf-8', errors='ignore')[:200]}...")
    
    return model


if __name__ == '__main__':
    model = train_with_monitoring()
    
    print("\n" + "=" * 60)
    print("✅ Training pipeline complete!")
    print("=" * 60)