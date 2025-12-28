"""Performance benchmark for wavelet batch optimization.

This script measures the actual speedup achieved by pre-computing
wavelet objects for batch processing.
"""

import time
import numpy as np
from driada.experiment.neuron import Neuron
from ssqueezepy.wavelets import Wavelet, time_resolution
from driada.experiment.wavelet_event_detection import get_adaptive_wavelet_scales


def generate_synthetic_traces(n_neurons=50, n_frames=1000, fps=20):
    """Generate synthetic calcium traces with realistic transients."""
    traces = []
    for i in range(n_neurons):
        trace = np.random.randn(n_frames) * 0.05  # Baseline noise

        # Add 3-5 calcium transients per neuron
        n_events = np.random.randint(3, 6)
        for _ in range(n_events):
            start = np.random.randint(0, n_frames - 100)
            duration = np.random.randint(20, 60)
            amplitude = 0.3 + np.random.rand() * 0.4

            # Exponential decay transient
            decay = np.exp(-np.arange(duration) / 15)
            trace[start:start+duration] += amplitude * decay

        # Normalize to [0, 1]
        trace = np.clip(trace, 0, None)
        trace = trace / (trace.max() + 1e-6)
        traces.append(trace)

    return traces


def benchmark_without_optimization(traces, fps=20):
    """Benchmark: Each neuron creates its own wavelet objects."""
    print("\n[Baseline] Without optimization (creates wavelet N times)...")
    neurons = []

    start_time = time.time()

    for i, trace in enumerate(traces):
        neuron = Neuron(cell_id=f"neuron_{i}", ca=trace, sp=None, fps=fps)
        neuron.reconstruct_spikes(
            method='wavelet',
            fps=fps,
            iterative=False,  # Single-pass for faster benchmark
            show_progress=False
        )
        neurons.append(neuron)

    elapsed = time.time() - start_time

    print(f"  [OK] Processed {len(traces)} neurons")
    print(f"  [OK] Total time: {elapsed:.2f}s")
    print(f"  [OK] Time per neuron: {elapsed/len(traces)*1000:.1f}ms")

    return elapsed, neurons


def benchmark_with_optimization(traces, fps=20):
    """Benchmark: Pre-compute wavelet objects once, reuse for all neurons."""
    print("\n[Optimized] With pre-computed wavelet objects...")

    # Pre-compute wavelet objects ONCE
    precompute_start = time.time()
    wavelet_shared = Wavelet(
        ("gmw", {"gamma": 3, "beta": 2, "centered_scale": True}), N=8196
    )
    manual_scales = get_adaptive_wavelet_scales(fps)
    rel_wvt_times_shared = [
        time_resolution(wavelet_shared, scale=sc, nondim=False, min_decay=200)
        for sc in manual_scales
    ]
    precompute_time = time.time() - precompute_start
    print(f"  [OK] Pre-computation time: {precompute_time:.3f}s")

    # Process all neurons with shared objects
    neurons = []
    process_start = time.time()

    for i, trace in enumerate(traces):
        neuron = Neuron(cell_id=f"neuron_{i}", ca=trace, sp=None, fps=fps)
        neuron.reconstruct_spikes(
            method='wavelet',
            fps=fps,
            iterative=False,
            show_progress=False,
            wavelet=wavelet_shared,           # Reuse!
            rel_wvt_times=rel_wvt_times_shared  # Reuse!
        )
        neurons.append(neuron)

    process_time = time.time() - process_start
    total_time = precompute_time + process_time

    print(f"  [OK] Processing time: {process_time:.2f}s")
    print(f"  [OK] Total time (precompute + process): {total_time:.2f}s")
    print(f"  [OK] Time per neuron: {process_time/len(traces)*1000:.1f}ms")

    return total_time, neurons


def verify_identical_results(neurons_baseline, neurons_optimized):
    """Verify that both methods produce identical results."""
    print("\n[Verification] Checking that results are identical...")

    for i, (n1, n2) in enumerate(zip(neurons_baseline, neurons_optimized)):
        # Compare amplitude spike arrays
        asp1 = n1.asp.data
        asp2 = n2.asp.data

        if not np.allclose(asp1, asp2, rtol=1e-6, atol=1e-6):
            max_diff = np.max(np.abs(asp1 - asp2))
            print(f"  [X] Neuron {i}: Results differ (max diff: {max_diff:.2e})!")
            return False

    print(f"  [OK] All {len(neurons_baseline)} neurons: Results identical")
    return True


def main():
    print("=" * 70)
    print("DRIADA Wavelet Batch Optimization - Performance Benchmark")
    print("=" * 70)

    # Test with different neuron counts
    test_configs = [
        (20, "Small batch"),
        (50, "Medium batch"),
        (100, "Large batch"),
    ]

    fps = 20
    n_frames = 1000

    for n_neurons, description in test_configs:
        print(f"\n{'=' * 70}")
        print(f"{description}: {n_neurons} neurons x {n_frames} frames @ {fps} Hz")
        print(f"{'=' * 70}")

        # Generate synthetic data
        print(f"\nGenerating {n_neurons} synthetic calcium traces...")
        traces = generate_synthetic_traces(n_neurons, n_frames, fps)
        print(f"  [OK] Generated {n_neurons} traces")

        # Benchmark without optimization
        time_baseline, neurons_baseline = benchmark_without_optimization(traces, fps)

        # Benchmark with optimization
        time_optimized, neurons_optimized = benchmark_with_optimization(traces, fps)

        # Verify results are identical
        identical = verify_identical_results(neurons_baseline, neurons_optimized)

        # Calculate speedup
        speedup = time_baseline / time_optimized
        time_saved = time_baseline - time_optimized
        overhead_per_neuron = time_saved / n_neurons

        print(f"\n{'=' * 70}")
        print(f"RESULTS for {n_neurons} neurons:")
        print(f"{'=' * 70}")
        print(f"  Baseline time:    {time_baseline:.2f}s")
        print(f"  Optimized time:   {time_optimized:.2f}s")
        print(f"  Time saved:       {time_saved:.2f}s ({time_saved/time_baseline*100:.1f}%)")
        print(f"  Speedup:          {speedup:.2f}x")
        print(f"  Overhead/neuron:  {overhead_per_neuron*1000:.1f}ms")
        print(f"  Results identical: {'[OK] YES' if identical else '[X] NO'}")

        # Estimate for 300 neurons
        if n_neurons >= 50:
            estimated_300_baseline = time_baseline * (300 / n_neurons)
            estimated_300_optimized = time_optimized * (300 / n_neurons)
            estimated_300_saved = estimated_300_baseline - estimated_300_optimized
            print(f"\n  Estimated for 300 neurons:")
            print(f"    Baseline:  {estimated_300_baseline:.1f}s")
            print(f"    Optimized: {estimated_300_optimized:.1f}s")
            print(f"    Saved:     {estimated_300_saved:.1f}s")

    print(f"\n{'=' * 70}")
    print("Benchmark complete!")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
