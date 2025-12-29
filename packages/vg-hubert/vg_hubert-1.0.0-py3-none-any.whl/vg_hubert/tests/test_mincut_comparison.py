"""
Compare current MinCut implementation with the new SyllableLM version.

Tests:
1. Results similarity - do they produce nearly identical boundaries?
2. Speed comparison - is the new one significantly faster?
"""

import numpy as np
import time
from typing import List

# Current implementation
def min_cut_current(ssm: np.ndarray, K: int) -> List[int]:
    """Current VG-HuBERT implementation"""
    N = ssm.shape[0]
    
    C = np.ones((N, K), dtype=np.float64) * np.inf
    B = np.zeros((N, K), dtype=np.int32)
    C[0, 0] = 0.0
    
    for i in range(1, N):
        temp = []
        for j in range(i):
            intra_sim = ssm[j:i, j:i].sum() / 2.0
            inter_sim = ssm[j:i, :j].sum() + ssm[j:i, i:].sum()
            temp.append((intra_sim, inter_sim))
        
        for k in range(1, K):
            obj = []
            for j, (intra_sim, inter_sim) in enumerate(temp):
                total_sim = intra_sim + inter_sim
                if total_sim > 0:
                    cut_cost = inter_sim / total_sim
                else:
                    cut_cost = 0.0
                obj.append(C[j, k - 1] + cut_cost)
            
            ind = np.argmin(obj)
            B[i, k] = ind
            C[i, k] = obj[ind]
    
    boundary = []
    prev_b = N - 1
    boundary.append(prev_b)
    
    for k in range(K - 1, 0, -1):
        prev_b = B[prev_b, k]
        boundary.append(prev_b)
    
    boundary = boundary[::-1]
    return boundary


# New SyllableLM implementation (from Experiments.ipynb Cell 41)
def min_cut_efficient(dp, K, min_hop=3, max_hop=50):
    """New efficient implementation from SyllableLM"""
    N = dp.shape[0] - 1

    C = np.ones((N+1, K), dtype=np.float32, order="C") * 100000
    B = np.ones((N+1, K), dtype=np.int32)
    C[0,0] = 0.
    
    for i in range(min_hop, N+1):
        temp = []
        for j in range(max(0, i-max_hop+1), i-min_hop+1):
            item = (
                (dp[i,i]-dp[j,i]-dp[i,j]+dp[j,j]),  # interior
                (dp[i,j]-dp[j,j]),  # left
                (dp[j,i]-dp[j,j]),  # top
                (dp[N,i]-dp[i,i]-dp[N,j]+dp[i,j]),  # bottom
                (dp[i,N]-dp[i,i]-dp[j,N]+dp[j,i]),  # right
            )
            temp.append((j, (item[1]+item[2]+item[3]+item[4])/(item[1]+item[2]+item[3]+item[4]+item[0]+1e-5)))
        for k in range(1,K):
            obj = [C[j, k-1] + item for (j, item) in temp]
            ind = np.argmin(obj)
            B[i,k] = temp[ind][0]
            C[i,k] = obj[ind]

    
    boundary = []
    prev_b = N
    loop = list(range(K))[::-1][:-1]
    boundary.append(prev_b)
    for k in loop:
        prev_b = B[prev_b,k]
        boundary.append(prev_b)
    boundary = boundary[::-1]
        
    return boundary


def test_similarity(ssm, K=11, tolerance_frames=2):
    """Test if both implementations produce similar boundaries"""
    print("=" * 70)
    print("TEST 1: Results Similarity")
    print("=" * 70)
    
    # Current method
    boundaries_current = min_cut_current(ssm, K)
    print(f"\nCurrent implementation boundaries: {boundaries_current}")
    
    # New method (needs cumsum preprocessing)
    dp = np.zeros((ssm.shape[0] + 1, ssm.shape[1] + 1))
    dp[1:,1:] = ssm.cumsum(axis=0).cumsum(axis=1)
    boundaries_new = min_cut_efficient(dp, K, min_hop=1, max_hop=ssm.shape[0])
    print(f"New implementation boundaries:     {boundaries_new}")
    
    # Compare
    print(f"\nComparison:")
    differences = []
    for i, (curr, new) in enumerate(zip(boundaries_current, boundaries_new)):
        diff = abs(curr - new)
        differences.append(diff)
        status = "✓" if diff <= tolerance_frames else "✗"
        print(f"  Boundary {i}: {curr} vs {new} (diff={diff}) {status}")
    
    max_diff = max(differences)
    mean_diff = np.mean(differences)
    
    print(f"\nMax difference: {max_diff} frames")
    print(f"Mean difference: {mean_diff:.2f} frames")
    
    similar = max_diff <= tolerance_frames
    print(f"\n{'✅' if similar else '❌'} Results are {'SIMILAR' if similar else 'DIFFERENT'} (tolerance={tolerance_frames} frames)")
    
    return similar, boundaries_current, boundaries_new


def test_speed(ssm, K=11, num_runs=10):
    """Test speed comparison"""
    print("\n" + "=" * 70)
    print("TEST 2: Speed Comparison")
    print("=" * 70)
    
    # Warm up
    _ = min_cut_current(ssm, K)
    
    # Current method
    times_current = []
    for _ in range(num_runs):
        start = time.time()
        _ = min_cut_current(ssm, K)
        times_current.append(time.time() - start)
    
    time_current = np.mean(times_current)
    std_current = np.std(times_current)
    
    # New method
    dp = np.zeros((ssm.shape[0] + 1, ssm.shape[1] + 1))
    dp[1:,1:] = ssm.cumsum(axis=0).cumsum(axis=1)
    
    times_new = []
    for _ in range(num_runs):
        # Include preprocessing time
        start = time.time()
        dp_local = np.zeros((ssm.shape[0] + 1, ssm.shape[1] + 1))
        dp_local[1:,1:] = ssm.cumsum(axis=0).cumsum(axis=1)
        _ = min_cut_efficient(dp_local, K, min_hop=1, max_hop=ssm.shape[0])
        times_new.append(time.time() - start)
    
    time_new = np.mean(times_new)
    std_new = np.std(times_new)
    
    print(f"\nCurrent implementation: {time_current*1000:.2f} ± {std_current*1000:.2f} ms")
    print(f"New implementation:     {time_new*1000:.2f} ± {std_new*1000:.2f} ms")
    
    speedup = time_current / time_new
    print(f"\nSpeedup: {speedup:.2f}x")
    
    faster = speedup > 1.2  # At least 20% faster
    print(f"\n{'✅' if faster else '❌'} New implementation is {'SIGNIFICANTLY FASTER' if faster else 'NOT SIGNIFICANTLY FASTER'}")
    
    return faster, speedup


def run_comprehensive_test():
    """Run comprehensive comparison"""
    print("\n" + "=" * 70)
    print("MINCUT IMPLEMENTATION COMPARISON")
    print("VG-HuBERT vs SyllableLM (Baade, Peng, Harwath 2024)")
    print("=" * 70)
    
    # Test with different sizes
    test_sizes = [100, 150, 200]
    results = []
    
    for N in test_sizes:
        print(f"\n\n{'#' * 70}")
        print(f"# Test with N={N} frames")
        print('#' * 70)
        
        # Create synthetic self-similarity matrix
        np.random.seed(42)
        features = np.random.randn(N, 768)
        ssm = features @ features.T
        ssm = ssm - np.min(ssm) + 1e-7  # Make non-negative
        
        # Determine K based on typical syllable rate (~5 syllables/second, 50 fps)
        K = max(5, N // 10)  # Roughly 10 frames per segment
        print(f"Using K={K} boundaries")
        
        # Test similarity
        similar, bound_curr, bound_new = test_similarity(ssm, K)
        
        # Test speed
        faster, speedup = test_speed(ssm, K)
        
        results.append({
            'N': N,
            'K': K,
            'similar': similar,
            'faster': faster,
            'speedup': speedup,
            'boundaries_current': bound_curr,
            'boundaries_new': bound_new
        })
    
    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_similar = all(r['similar'] for r in results)
    all_faster = all(r['faster'] for r in results)
    avg_speedup = np.mean([r['speedup'] for r in results])
    
    print(f"\nResults across {len(results)} test sizes:")
    print(f"  Similarity: {'✅ ALL TESTS SIMILAR' if all_similar else '❌ SOME DIFFERENCES'}")
    print(f"  Speed: {'✅ CONSISTENTLY FASTER' if all_faster else '❌ NOT CONSISTENTLY FASTER'}")
    print(f"  Average speedup: {avg_speedup:.2f}x")
    
    if all_similar and all_faster:
        print("\n" + "🎯" * 35)
        print("✅ RECOMMENDATION: SWITCH TO NEW IMPLEMENTATION")
        print("   - Produces nearly identical results")
        print(f"   - {avg_speedup:.1f}x faster on average")
        print("   - From SyllableLM paper (Baade, Peng, Harwath 2024)")
        print("🎯" * 35)
        return True
    else:
        print("\n" + "⚠️" * 35)
        print("❌ RECOMMENDATION: KEEP CURRENT IMPLEMENTATION")
        if not all_similar:
            print("   - Results differ too much")
        if not all_faster:
            print("   - Speed improvement not consistent")
        print("⚠️" * 35)
        return False


if __name__ == "__main__":
    should_switch = run_comprehensive_test()
    exit(0 if should_switch else 1)
