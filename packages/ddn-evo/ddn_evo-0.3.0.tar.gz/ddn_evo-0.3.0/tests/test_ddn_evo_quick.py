#!/usr/bin/env python3
"""Quick test of ddn_evo package with minimal dependencies"""
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ddn_evo import SplitableDiscreteDistribution
    print("✓ ddn_evo import successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Quick test: Create SDD and test split functionality
print("\nTesting SplitableDiscreteDistribution...")
k = 20  # Small number for quick test
sdd = SplitableDiscreteDistribution(k)
print(f"Created SDD with k={k}")

# Simulate some training iterations
batch_size = 5
num_iterations = 10
splits_occurred = 0

print(f"\nRunning {num_iterations} iterations with batch_size={batch_size}...")
for i in range(num_iterations):
    # Generate random loss matrix
    loss_matrix = np.random.rand(batch_size, k) * 0.5
    
    # Add loss matrix
    result = sdd.add_loss_matrix(loss_matrix)
    
    # Try split
    split_result = sdd.try_split()
    if split_result:
        splits_occurred += 1
        print(f"  Iter {i+1}: Split occurred! i_split={split_result['i_split']}, i_disapear={split_result['i_disapear']}")

print(f"\n✓ Test completed successfully!")
print(f"  Total iterations: {sdd.iter}")
print(f"  Splits occurred: {splits_occurred}")
print(f"  Final k: {sdd.k}")
print(f"  Count sum: {sdd.count.sum():.1f}")

