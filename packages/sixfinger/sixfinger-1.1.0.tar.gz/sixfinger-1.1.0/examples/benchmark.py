"""
Benchmark SpeedLM performance

Compare different configurations and measure speed.
"""

from sixfinger.transformers import SpeedLM
import time
import numpy as np


def benchmark_config(config: dict, data_size: int = 50_000):
    """Benchmark a specific configuration"""
    
    # Generate random data
    data = bytes(np.random.randint(0, 256, data_size).tolist())
    
    # Create model
    model = SpeedLM(**config, verbose=False)
    
    # Warmup
    model.train_data(data[:1000])
    
    # Benchmark training
    start = time.time()
    stats = model.train_data(data)
    train_time = time.time() - start
    
    # Benchmark generation
    prompt = b"The quick brown"
    start = time.time()
    for _ in range(10):
        model.generate(prompt, length=100, verbose=False)
    gen_time = (time.time() - start) / 10
    
    return {
        'config': config,
        'train_speed_kb_s': data_size / train_time / 1024,
        'train_time': train_time,
        'loss': stats['loss'],
        'gen_time_100tok': gen_time,
        'gen_speed_tok_s': 100 / gen_time,
        'memory_mb': model._memory_mb()
    }


def main():
    print("=" * 70)
    print("SixFinger SpeedLM - Performance Benchmark")
    print("=" * 70)
    
    # Configurations to test
    configs = [
        {
            'name': 'Tiny',
            'n_buckets': 10_000,
            'n_features': 128,
            'context_sizes': [1, 2, 3, 4],
        },
        {
            'name': 'Small',
            'n_buckets': 50_000,
            'n_features': 256,
            'context_sizes': [1, 2, 3, 4, 5],
        },
        {
            'name': 'Medium',
            'n_buckets': 100_000,
            'n_features': 512,
            'context_sizes': [1, 2, 3, 4, 5, 8],
        },
        {
            'name': 'Large',
            'n_buckets': 500_000,
            'n_features': 1024,
            'context_sizes': [1, 2, 3, 4, 5, 8, 12],
        },
    ]
    
    results = []
    
    for cfg in configs:
        name = cfg.pop('name')
        print(f"\n🧪 Benchmarking {name} model...")
        print(f"   Config: {cfg}")
        
        result = benchmark_config(cfg)
        result['name'] = name
        results.append(result)
        
        print(f"   ✓ Train: {result['train_speed_kb_s']:.1f} KB/s")
        print(f"   ✓ Generate: {result['gen_speed_tok_s']:.1f} tok/s")
        print(f"   ✓ Memory: {result['memory_mb']:.1f} MB")
    
    # Summary table
    print("\n" + "=" * 70)
    print("Benchmark Results")
    print("=" * 70)
    print(f"\n{'Model':<10} {'Memory':<12} {'Train Speed':<15} {'Gen Speed':<15} {'Loss':<8}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['name']:<10} "
              f"{r['memory_mb']:>6.1f} MB    "
              f"{r['train_speed_kb_s']:>8.1f} KB/s    "
              f"{r['gen_speed_tok_s']:>8.1f} tok/s   "
              f"{r['loss']:>6.3f}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("Recommendations")
    print("=" * 70)
    print("\n📱 Mobile/Phone:")
    print("   → Use 'Small' or 'Medium' (fast, low memory)")
    print("\n💻 Desktop/Laptop:")
    print("   → Use 'Large' (best quality)")
    print("\n🚀 Production:")
    print("   → Start with 'Medium', scale to 'Large' if needed")
    
    # 1GB estimate
    print("\n" + "=" * 70)
    print("1GB Training Time Estimates")
    print("=" * 70)
    
    for r in results:
        gb_time = (1024 * 1024) / r['train_speed_kb_s'] / 60
        print(f"   {r['name']:<10}: {gb_time:.1f} minutes")


if __name__ == '__main__':
    main()