#!/usr/bin/env python3
"""Test mutation functionality for ddn_evo package"""
import numpy as np
import torch
import torch.nn as nn
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ddn_evo import DiscreteDistributionOutput, mutate_node
    print("✓ ddn_evo import successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

def test_mutate_node_basic():
    """Test basic mutate_node functionality"""
    print("\n" + "="*60)
    print("Test 1: Basic mutate_node functionality")
    print("="*60)
    
    # Test with torch.Tensor
    weight = torch.randn(3, 4) * 0.5
    original = weight.clone()
    
    # Test with mutation_type='none' (should return unchanged)
    result = mutate_node(weight.clone(), mutation_type='none')
    assert torch.allclose(result, original), "mutation_type='none' should not change data"
    print("✓ mutation_type='none' works correctly")
    
    # Test with mutation_rate=0.0 (should return unchanged)
    result = mutate_node(weight.clone(), mutation_rate=0.0)
    assert torch.allclose(result, original), "mutation_rate=0.0 should not change data"
    print("✓ mutation_rate=0.0 works correctly")
    
    # Test with gaussian mutation
    mutated = mutate_node(weight.clone(), mutation_type='gaussian', 
                         mutation_strength=0.01, mutation_rate=1.0)
    # Should be different (with high probability)
    assert not torch.allclose(mutated, original, atol=1e-6), "Mutation should change values"
    print("✓ Gaussian mutation changes values")
    
    # Test relative scaling - mutation should scale with std
    weight_small = torch.randn(3, 4) * 0.1  # Small std
    weight_large = torch.randn(3, 4) * 2.0   # Large std
    
    mutated_small = mutate_node(weight_small.clone(), mutation_type='gaussian',
                                mutation_strength=0.01, mutation_rate=1.0)
    mutated_large = mutate_node(weight_large.clone(), mutation_type='gaussian',
                                mutation_strength=0.01, mutation_rate=1.0)
    
    diff_small = (mutated_small - weight_small).abs().mean()
    diff_large = (mutated_large - weight_large).abs().mean()
    
    # Large weights should have larger absolute mutations
    assert diff_large > diff_small, "Mutation should scale with weight std"
    print(f"✓ Relative scaling works: small std diff={diff_small:.6f}, large std diff={diff_large:.6f}")
    
    # Test with numpy array
    arr = np.random.randn(3, 4) * 0.5
    arr_original = arr.copy()
    arr_mutated = mutate_node(arr, mutation_type='gaussian', 
                             mutation_strength=0.01, mutation_rate=1.0)
    assert not np.allclose(arr_mutated, arr_original, atol=1e-6), "Numpy mutation should change values"
    print("✓ Numpy array mutation works")
    
    print("✓ Test 1 passed!")


def test_mutation_with_ddn():
    """Test mutation integrated with DiscreteDistributionOutput"""
    print("\n" + "="*60)
    print("Test 2: Mutation with DiscreteDistributionOutput")
    print("="*60)
    
    # Create a simple DDN layer
    last_c = 16
    predict_c = 3
    k = 10
    
    ddn = DiscreteDistributionOutput(last_c, predict_c, k)
    optimizer = torch.optim.Adam(ddn.parameters(), lr=0.001)
    
    # Test that mutation parameters are accepted
    print("Testing mutation parameters are accepted...")
    
    # Manually trigger a split by manipulating the SDD
    # Add some loss to make split likely
    # Use the actual k from the SDD
    actual_k = ddn.sdd.k
    for _ in range(20):
        loss_matrix = np.random.rand(5, actual_k) * 0.3
        ddn.sdd.add_loss_matrix(loss_matrix)
    
    # Try split with mutation parameters
    try:
        ddn.try_split(
            optimizers=optimizer,
            mutation_type='gaussian',
            mutation_strength=0.01,
            mutation_rate=1.0,
            mutation_probability=0.5
        )
        print("✓ Mutation parameters accepted in try_split")
    except Exception as e:
        print(f"✗ Error with mutation parameters: {e}")
        raise
    
    # Test backward compatibility: no mutation by default
    print("\nTesting backward compatibility (no mutation)...")
    ddn2 = DiscreteDistributionOutput(last_c, predict_c, k)
    optimizer2 = torch.optim.Adam(ddn2.parameters(), lr=0.001)
    
    # Add some loss
    # Use the actual k from the SDD
    actual_k2 = ddn2.sdd.k
    for _ in range(15):
        loss_matrix = np.random.rand(5, actual_k2) * 0.3
        ddn2.sdd.add_loss_matrix(loss_matrix)
    
    # Try split without mutation parameters (should work - backward compatible)
    try:
        ddn2.try_split(optimizers=optimizer2)
        print("✓ Backward compatibility: try_split works without mutation params")
    except Exception as e:
        print(f"✗ Backward compatibility broken: {e}")
        raise
    
    print("✓ Test 2 passed!")


def test_mutation_probability():
    """Test that mutation_probability controls mutation frequency"""
    print("\n" + "="*60)
    print("Test 3: Mutation probability control")
    print("="*60)
    
    weight = torch.randn(5, 5) * 0.5
    original = weight.clone()
    
    # Test with mutation_probability=0.0 (via mutation_type='none')
    # This simulates what happens when mutation_probability=0.0 in split
    result = mutate_node(weight.clone(), mutation_type='none')
    assert torch.allclose(result, original), "No mutation should occur"
    print("✓ mutation_probability=0.0 (via 'none') works")
    
    # Test with mutation_probability=1.0 (always mutate)
    # We'll test this by calling mutate_node directly with rate=1.0
    mutated = mutate_node(weight.clone(), mutation_type='gaussian',
                         mutation_strength=0.01, mutation_rate=1.0)
    assert not torch.allclose(mutated, original, atol=1e-6), "Should mutate with rate=1.0"
    print("✓ mutation_rate=1.0 always mutates")
    
    # Test with mutation_rate < 1.0 (probabilistic)
    mutations_occurred = 0
    num_trials = 100
    for _ in range(num_trials):
        result = mutate_node(weight.clone(), mutation_type='gaussian',
                            mutation_strength=0.01, mutation_rate=0.5)
        if not torch.allclose(result, original, atol=1e-6):
            mutations_occurred += 1
    
    # Should be approximately 50% (with some variance)
    mutation_fraction = mutations_occurred / num_trials
    print(f"✓ mutation_rate=0.5: {mutations_occurred}/{num_trials} mutations ({mutation_fraction:.2%})")
    assert 0.3 < mutation_fraction < 0.7, f"Mutation rate should be ~0.5, got {mutation_fraction}"
    
    print("✓ Test 3 passed!")


def test_mutation_types():
    """Test different mutation types"""
    print("\n" + "="*60)
    print("Test 4: Different mutation types")
    print("="*60)
    
    weight = torch.randn(4, 4) * 0.5
    original = weight.clone()
    
    # Test gaussian
    gaussian = mutate_node(weight.clone(), mutation_type='gaussian',
                          mutation_strength=0.01, mutation_rate=1.0)
    assert not torch.allclose(gaussian, original, atol=1e-6)
    print("✓ Gaussian mutation works")
    
    # Test uniform
    uniform = mutate_node(weight.clone(), mutation_type='uniform',
                         mutation_strength=0.01, mutation_rate=1.0)
    assert not torch.allclose(uniform, original, atol=1e-6)
    print("✓ Uniform mutation works")
    
    # Test scale
    scale = mutate_node(weight.clone(), mutation_type='scale',
                       mutation_strength=0.01, mutation_rate=1.0)
    assert not torch.allclose(scale, original, atol=1e-6)
    print("✓ Scale mutation works")
    
    # Test invalid type
    try:
        mutate_node(weight.clone(), mutation_type='invalid')
        assert False, "Should raise ValueError for invalid mutation_type"
    except ValueError as e:
        assert 'invalid' in str(e).lower()
        print("✓ Invalid mutation_type raises ValueError")
    
    print("✓ Test 4 passed!")


if __name__ == "__main__":
    print("="*60)
    print("Testing Mutation Functionality")
    print("="*60)
    
    try:
        test_mutate_node_basic()
        test_mutation_with_ddn()
        test_mutation_probability()
        test_mutation_types()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

