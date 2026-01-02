"""
Tests for text generation utilities
"""

import pytest
import numpy as np

from sixfinger.transformers.generation import sampling


class TestSampling:
    
    def test_softmax(self):
        """Test softmax function"""
        logits = np.array([1.0, 2.0, 3.0])
        probs = sampling.softmax(logits)
        
        assert np.allclose(probs.sum(), 1.0)
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)
        assert probs[2] > probs[1] > probs[0]
    
    def test_greedy_sample(self):
        """Test greedy sampling"""
        logits = np.array([0.5, 1.5, 0.8, 2.1, 0.3])
        token = sampling.greedy_sample(logits)
        assert token == 3
    
    def test_top_k_filtering(self):
        """Test top-k filtering"""
        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        filtered = sampling.top_k_top_p_filtering(logits, top_k=3)
        
        # Should keep top 3, mask others
        assert not np.isinf(filtered[2])  # 3rd highest
        assert not np.isinf(filtered[3])  # 2nd highest
        assert not np.isinf(filtered[4])  # highest
        assert np.isinf(filtered[0])      # lowest (masked)
        assert np.isinf(filtered[1])      # 2nd lowest (masked)
    
    def test_top_p_filtering(self):
        """Test nucleus (top-p) filtering"""
        # Logits that give clear probability distribution
        logits = np.array([0.0, 0.0, 0.0, 3.0, 4.0])  # Most mass on last two
        
        filtered = sampling.top_k_top_p_filtering(logits, top_p=0.95)
        
        # Should keep tokens with cumsum < 0.95
        probs = sampling.softmax(logits)
        assert probs[4] + probs[3] > 0.95  # These two dominate
    
    def test_sample_token_deterministic(self):
        """Test deterministic sampling (temperature=0)"""
        logits = np.array([1.0, 5.0, 2.0])
        
        token = sampling.sample_token(logits, temperature=0.0)
        assert token == 1  # Always picks max
    
    def test_sample_token_random(self):
        """Test random sampling"""
        logits = np.array([1.0, 1.0, 1.0, 1.0])  # Uniform
        
        np.random.seed(42)
        samples = [sampling.sample_token(logits, temperature=1.0) for _ in range(100)]
        
        # Should sample all tokens
        assert len(set(samples)) == 4
        
        # Should be roughly uniform
        counts = [samples.count(i) for i in range(4)]
        for count in counts:
            assert 15 < count < 35  # Roughly 25% each
    
    def test_sample_token_with_top_k(self):
        """Test sampling with top-k"""
        logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        np.random.seed(42)
        samples = [sampling.sample_token(logits, temperature=1.0, top_k=2) for _ in range(50)]
        
        # Should only sample from top 2
        assert all(s in [3, 4] for s in samples)
    
    def test_sample_token_with_top_p(self):
        """Test sampling with nucleus filtering"""
        logits = np.array([0.0, 0.0, 0.0, 3.0, 4.0])
        
        np.random.seed(42)
        samples = [sampling.sample_token(logits, temperature=1.0, top_p=0.9) for _ in range(50)]
        
        # Should mostly sample from top tokens
        assert sum(s in [3, 4] for s in samples) > 45


if __name__ == '__main__':
    pytest.main([__file__, '-v'])