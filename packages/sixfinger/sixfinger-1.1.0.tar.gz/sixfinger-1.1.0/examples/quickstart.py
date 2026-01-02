"""
Quick start example for SixFinger transformers

Shows basic training and generation workflow.
"""

from sixfinger.transformers import SpeedLM


def main():
    print("=" * 60)
    print("SixFinger SpeedLM - Quick Start")
    print("=" * 60)
    
    # ===== 1. Create sample data =====
    print("\n📝 Creating sample training data...")
    
    sample_text = """
    The quick brown fox jumps over the lazy dog.
    Machine learning is a subset of artificial intelligence.
    Python is a powerful programming language for data science.
    Deep learning models require large amounts of training data.
    Natural language processing enables computers to understand text.
    Transformers have revolutionized the field of NLP.
    """ * 100  # Repeat for more data
    
    # Save to file
    with open('sample_data.txt', 'w') as f:
        f.write(sample_text)
    
    print(f"   Created sample_data.txt ({len(sample_text)} bytes)")
    
    # ===== 2. Initialize model =====
    print("\n🚀 Initializing SpeedLM model...")
    
    model = SpeedLM(
        n_buckets=50_000,      # Small model for demo
        n_features=256,
        context_sizes=[1, 2, 3, 4, 5],
        verbose=True
    )
    
    # ===== 3. Train =====
    print("\n📚 Training on sample data...")
    
    stats = model.train_file('sample_data.txt', chunk_size=10_000)
    
    print("\n📊 Training Results:")
    print(f"   Loss: {stats['loss']:.3f}")
    print(f"   Tokens: {stats['tokens']:,}")
    print(f"   Speed: {stats['speed_kb_s']:.1f} KB/s")
    
    # ===== 4. Save model =====
    print("\n💾 Saving model...")
    model.save('quickstart_model.npz')
    
    # ===== 5. Generate text =====
    print("\n✍️  Generating text...")
    
    prompts = [
        b"The quick",
        b"Machine learning",
        b"Python is"
    ]
    
    for prompt in prompts:
        print(f"\n  Prompt: {prompt.decode()}")
        output = model.generate(prompt, length=50, temperature=0.7, verbose=False)
        print(f"  Output: {output.decode('utf-8', errors='ignore')}")
    
    # ===== 6. Load and test =====
    print("\n📥 Testing model load...")
    
    model2 = SpeedLM.from_pretrained('quickstart_model.npz')
    output = model2.generate(b"Deep learning", length=50, verbose=False)
    print(f"  Loaded model output: {output.decode('utf-8', errors='ignore')}")
    
    print("\n" + "=" * 60)
    print("✅ Quick start complete!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("  1. Train on your own data: model.train_file('your_data.txt')")
    print("  2. Adjust model size: n_buckets=500_000, n_features=1024")
    print("  3. Experiment with generation: temperature, top_k, top_p")


if __name__ == '__main__':
    main()