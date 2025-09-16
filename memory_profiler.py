#!/usr/bin/env python3
"""
Memory Profiling Script for Bark TTS Integration
Measures and analyzes memory usage patterns for the Subway Surfers TTS system
"""
import os
import sys
import time
import psutil
import gc
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("📊 matplotlib not available - plots will be skipped")

try:
    import numpy as np
except ImportError:
    print("⚠️ numpy not available - using basic statistics")
    # Define minimal numpy replacements
    class np:
        @staticmethod
        def mean(data):
            return sum(data) / len(data) if data else 0

        @staticmethod
        def median(data):
            sorted_data = sorted(data)
            n = len(sorted_data)
            return sorted_data[n//2] if n % 2 == 1 else (sorted_data[n//2-1] + sorted_data[n//2]) / 2

        @staticmethod
        def std(data):
            if not data:
                return 0
            mean_val = np.mean(data)
            variance = sum((x - mean_val) ** 2 for x in data) / len(data)
            return variance ** 0.5

        @staticmethod
        def diff(data):
            return [data[i] - data[i-1] for i in range(1, len(data))]

# Memory profiling utilities
class MemoryProfiler:
    """Memory profiling and analysis utility"""

    def __init__(self, output_dir: str = "./memory_analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.process = psutil.Process()
        self.measurements = []
        self.monitoring = False
        self.monitor_thread = None

        # Memory tracking state
        self.baseline_memory = 0
        self.peak_memory = 0
        self.current_phase = "initialization"

    def get_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive memory information"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        # System memory info
        system_memory = psutil.virtual_memory()

        # GPU memory if available
        gpu_memory = self._get_gpu_memory()

        return {
            "timestamp": time.time(),
            "phase": self.current_phase,
            "process_memory": {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": memory_percent
            },
            "system_memory": {
                "total_mb": system_memory.total / 1024 / 1024,
                "available_mb": system_memory.available / 1024 / 1024,
                "used_mb": system_memory.used / 1024 / 1024,
                "percent": system_memory.percent
            },
            "gpu_memory": gpu_memory
        }

    def _get_gpu_memory(self) -> Optional[Dict[str, Any]]:
        """Get GPU memory information if available"""
        try:
            import torch
            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                total_memory = torch.cuda.get_device_properties(device).total_memory
                allocated = torch.cuda.memory_allocated(device)
                cached = torch.cuda.memory_reserved(device)

                return {
                    "device": device,
                    "total_mb": total_memory / 1024 / 1024,
                    "allocated_mb": allocated / 1024 / 1024,
                    "cached_mb": cached / 1024 / 1024,
                    "free_mb": (total_memory - allocated) / 1024 / 1024,
                    "utilization_percent": (allocated / total_memory) * 100
                }
        except ImportError:
            pass

        return None

    def set_phase(self, phase: str):
        """Set current profiling phase"""
        self.current_phase = phase
        print(f"📊 Memory profiling phase: {phase}")

    def take_snapshot(self, label: str = None) -> Dict[str, Any]:
        """Take a memory snapshot"""
        gc.collect()  # Force garbage collection
        memory_info = self.get_memory_info()

        if label:
            memory_info["label"] = label
            print(f"   Memory snapshot '{label}': {memory_info['process_memory']['rss_mb']:.1f} MB RSS")

        self.measurements.append(memory_info)

        # Update peak memory
        current_rss = memory_info['process_memory']['rss']
        if current_rss > self.peak_memory:
            self.peak_memory = current_rss

        return memory_info

    def start_monitoring(self, interval: float = 0.5):
        """Start continuous memory monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"🔍 Started memory monitoring (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop continuous memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("⏹️ Stopped memory monitoring")

    def _monitor_loop(self, interval: float):
        """Continuous monitoring loop"""
        while self.monitoring:
            self.take_snapshot()
            time.sleep(interval)

    def set_baseline(self):
        """Set baseline memory measurement"""
        baseline_info = self.take_snapshot("baseline")
        self.baseline_memory = baseline_info['process_memory']['rss']
        print(f"📏 Baseline memory: {self.baseline_memory / 1024 / 1024:.1f} MB")

    def get_memory_growth(self) -> float:
        """Get memory growth since baseline (MB)"""
        current_info = self.get_memory_info()
        current_rss = current_info['process_memory']['rss']
        return (current_rss - self.baseline_memory) / 1024 / 1024

    def save_measurements(self, filename: str = None):
        """Save measurements to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory_measurements_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.measurements, f, indent=2)

        print(f"💾 Saved {len(self.measurements)} measurements to {filepath}")
        return filepath

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory analysis report"""
        if not self.measurements:
            return {"error": "No measurements available"}

        # Extract RSS memory values
        rss_values = [m['process_memory']['rss_mb'] for m in self.measurements]
        phases = list(set(m['phase'] for m in self.measurements))

        # Calculate statistics
        stats = {
            "baseline_mb": self.baseline_memory / 1024 / 1024 if self.baseline_memory else 0,
            "peak_mb": max(rss_values),
            "current_mb": rss_values[-1],
            "average_mb": np.mean(rss_values),
            "median_mb": np.median(rss_values),
            "std_mb": np.std(rss_values),
            "growth_from_baseline_mb": max(rss_values) - (self.baseline_memory / 1024 / 1024 if self.baseline_memory else 0),
            "total_measurements": len(self.measurements),
            "phases_tested": phases
        }

        # Phase-specific analysis
        phase_stats = {}
        for phase in phases:
            phase_measurements = [m for m in self.measurements if m['phase'] == phase]
            phase_rss = [m['process_memory']['rss_mb'] for m in phase_measurements]

            if phase_rss:
                phase_stats[phase] = {
                    "count": len(phase_rss),
                    "avg_mb": np.mean(phase_rss),
                    "peak_mb": max(phase_rss),
                    "min_mb": min(phase_rss),
                    "std_mb": np.std(phase_rss)
                }

        # GPU analysis if available
        gpu_stats = None
        gpu_measurements = [m for m in self.measurements if m.get('gpu_memory')]
        if gpu_measurements:
            gpu_allocated = [m['gpu_memory']['allocated_mb'] for m in gpu_measurements]
            gpu_stats = {
                "peak_allocated_mb": max(gpu_allocated),
                "avg_allocated_mb": np.mean(gpu_allocated),
                "peak_utilization_percent": max(m['gpu_memory']['utilization_percent'] for m in gpu_measurements)
            }

        return {
            "summary": stats,
            "phase_analysis": phase_stats,
            "gpu_analysis": gpu_stats,
            "measurement_count": len(self.measurements),
            "analysis_timestamp": datetime.now().isoformat()
        }

    def plot_memory_usage(self, save_plot: bool = True):
        """Generate memory usage visualization"""
        if not MATPLOTLIB_AVAILABLE:
            print("📊 Plotting skipped - matplotlib not available")
            return

        if not self.measurements:
            print("❌ No measurements to plot")
            return

        # Prepare data
        timestamps = [m['timestamp'] for m in self.measurements]
        start_time = timestamps[0]
        relative_times = [(t - start_time) / 60 for t in timestamps]  # Minutes

        rss_values = [m['process_memory']['rss_mb'] for m in self.measurements]
        phases = [m['phase'] for m in self.measurements]

        # Create plot
        plt.figure(figsize=(12, 8))

        # Plot memory usage
        plt.subplot(2, 1, 1)
        plt.plot(relative_times, rss_values, 'b-', linewidth=2, label='RSS Memory')

        # Mark phase changes
        phase_changes = []
        current_phase = phases[0]
        for i, phase in enumerate(phases):
            if phase != current_phase:
                phase_changes.append((relative_times[i], phase))
                plt.axvline(x=relative_times[i], color='red', linestyle='--', alpha=0.7)
                current_phase = phase

        plt.xlabel('Time (minutes)')
        plt.ylabel('Memory Usage (MB)')
        plt.title('Memory Usage Over Time')
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Memory growth rate
        plt.subplot(2, 1, 2)
        if len(rss_values) > 1:
            growth_rates = np.diff(rss_values)
            plt.plot(relative_times[1:], growth_rates, 'g-', linewidth=1, alpha=0.7)
            plt.xlabel('Time (minutes)')
            plt.ylabel('Memory Growth Rate (MB/sample)')
            plt.title('Memory Growth Rate')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        plt.tight_layout()

        if save_plot:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = self.output_dir / f"memory_usage_{timestamp}.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"📈 Memory usage plot saved to {plot_path}")

        plt.show()


def test_baseline_memory():
    """Test baseline memory usage without any models"""
    print("🔬 Testing baseline memory usage...")

    profiler = MemoryProfiler()
    profiler.set_phase("baseline")
    profiler.set_baseline()

    # Test basic Python overhead
    profiler.take_snapshot("python_startup")

    # Import basic libraries
    profiler.set_phase("basic_imports")
    import numpy as np
    import requests
    profiler.take_snapshot("numpy_requests_imported")

    # Import audio libraries
    try:
        import soundfile as sf
        profiler.take_snapshot("soundfile_imported")
    except ImportError:
        print("⚠️ soundfile not available")

    # Import FastAPI
    try:
        from fastapi import FastAPI
        profiler.take_snapshot("fastapi_imported")
    except ImportError:
        print("⚠️ FastAPI not available")

    return profiler


def test_mock_server_memory():
    """Test memory usage with mock server"""
    print("🔬 Testing mock server memory usage...")

    profiler = MemoryProfiler()
    profiler.set_phase("mock_server")
    profiler.set_baseline()

    # Simulate mock server operations
    profiler.take_snapshot("before_mock_operations")

    # Simulate multiple voice generations
    for i in range(5):
        profiler.set_phase(f"mock_generation_{i}")

        # Simulate memory allocation for audio generation
        sample_rate = 22050
        duration = 3.0  # 3 seconds
        samples = int(duration * sample_rate)

        # Generate mock audio data (using basic Python if numpy not available)
        try:
            audio_data = np.random.normal(0, 0.1, samples).astype('float32')
        except:
            # Fallback without numpy
            import random
            audio_data = [random.gauss(0, 0.1) for _ in range(samples)]

        profiler.take_snapshot(f"mock_audio_{i}_generated")

        # Simulate encoding/processing
        if hasattr(audio_data, 'tobytes'):
            audio_bytes = audio_data.tobytes()
        else:
            # Fallback for list
            audio_bytes = bytes(int(x * 32767) & 0xFFFF for x in audio_data[:1000])  # Simulate first 1000 samples
        profiler.take_snapshot(f"mock_audio_{i}_encoded")

        # Clean up
        del audio_data, audio_bytes
        gc.collect()
        profiler.take_snapshot(f"mock_audio_{i}_cleaned")

    return profiler


def estimate_real_bark_memory():
    """Estimate memory usage for real Bark models"""
    print("🔬 Estimating real Bark model memory usage...")

    # Bark model size estimates (based on Hugging Face model cards)
    bark_models = {
        "suno/bark": {
            "model_size_gb": 5.1,
            "description": "Full Bark model with all components",
            "components": {
                "text_encoder": 0.5,
                "coarse_acoustics": 1.8,
                "fine_acoustics": 2.3,
                "codec": 0.5
            }
        },
        "suno/bark-small": {
            "model_size_gb": 2.8,
            "description": "Smaller Bark variant",
            "components": {
                "text_encoder": 0.3,
                "coarse_acoustics": 1.0,
                "fine_acoustics": 1.2,
                "codec": 0.3
            }
        }
    }

    estimates = {}

    for model_name, info in bark_models.items():
        # Base model memory (assuming float32)
        model_memory_mb = info["model_size_gb"] * 1024

        # Add overhead estimates
        loading_overhead = model_memory_mb * 0.3  # 30% overhead during loading
        inference_overhead = model_memory_mb * 0.2  # 20% overhead during inference

        # GPU vs CPU estimates
        gpu_memory_mb = model_memory_mb + inference_overhead
        cpu_memory_mb = model_memory_mb + inference_overhead + (model_memory_mb * 0.5)  # Extra CPU overhead

        estimates[model_name] = {
            "model_size_mb": model_memory_mb,
            "loading_overhead_mb": loading_overhead,
            "inference_overhead_mb": inference_overhead,
            "estimated_gpu_usage_mb": gpu_memory_mb,
            "estimated_cpu_usage_mb": cpu_memory_mb,
            "recommended_system_ram_gb": max(8, cpu_memory_mb / 1024 * 1.5),  # 1.5x for safety
            "recommended_gpu_ram_gb": max(6, gpu_memory_mb / 1024 * 1.3),  # 1.3x for safety
            "components": info["components"]
        }

    return estimates


def test_with_pytorch_server():
    """Test memory usage with actual PyTorch TTS server"""
    print("🔬 Testing with PyTorch TTS server...")

    profiler = MemoryProfiler()
    profiler.set_phase("pytorch_server_test")
    profiler.set_baseline()

    # Test server connectivity
    import requests
    server_url = "http://localhost:8000"

    try:
        # Check health
        profiler.take_snapshot("before_server_test")
        response = requests.get(f"{server_url}/health", timeout=5)
        profiler.take_snapshot("after_health_check")

        if response.status_code != 200:
            print(f"⚠️ Server not healthy: {response.status_code}")
            return profiler

        # Test voice synthesis
        test_requests = [
            {"text": "Short test", "voice": "narrator"},
            {"text": "This is a medium length test to see how memory usage scales with text length.", "voice": "announcer"},
            {"text": "This is a much longer test sentence that should help us understand how the Bark model handles longer text inputs and whether there are any memory scaling issues we need to be concerned about when processing longer content for the Subway Surfers video generation system.", "voice": "excited"}
        ]

        for i, req_data in enumerate(test_requests):
            profiler.set_phase(f"synthesis_request_{i}")
            profiler.take_snapshot(f"before_request_{i}")

            try:
                response = requests.post(
                    f"{server_url}/synthesize",
                    json=req_data,
                    timeout=120
                )
                profiler.take_snapshot(f"after_request_{i}")

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        audio_size = len(data.get("audio_data", "")) * 3 // 4  # Approximate decoded size
                        print(f"   ✅ Request {i}: {audio_size} bytes audio, {data.get('duration', 0):.1f}s")
                    else:
                        print(f"   ❌ Request {i}: {data.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ Request {i}: HTTP {response.status_code}")

            except requests.RequestException as e:
                print(f"   ❌ Request {i}: {e}")
                profiler.take_snapshot(f"error_request_{i}")

    except requests.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")

    return profiler


def analyze_memory_patterns(profiler: MemoryProfiler) -> Dict[str, Any]:
    """Analyze memory usage patterns and identify optimization opportunities"""
    report = profiler.generate_report()

    analysis = {
        "memory_efficiency": {},
        "optimization_opportunities": [],
        "deployment_recommendations": {},
        "scaling_analysis": {}
    }

    # Memory efficiency analysis
    if report.get("summary"):
        stats = report["summary"]

        # Calculate efficiency metrics
        peak_mb = stats.get("peak_mb", 0)
        baseline_mb = stats.get("baseline_mb", 0)
        growth_mb = stats.get("growth_from_baseline_mb", 0)

        analysis["memory_efficiency"] = {
            "baseline_overhead_mb": baseline_mb,
            "peak_usage_mb": peak_mb,
            "memory_growth_mb": growth_mb,
            "efficiency_ratio": (growth_mb / peak_mb * 100) if peak_mb > 0 else 0,
            "memory_stability": stats.get("std_mb", 0) / stats.get("average_mb", 1) * 100
        }

        # Identify optimization opportunities
        if growth_mb > 1000:  # > 1GB growth
            analysis["optimization_opportunities"].append({
                "type": "high_memory_growth",
                "impact": "high",
                "description": f"Memory growth of {growth_mb:.0f}MB indicates potential memory leaks or inefficient allocation",
                "recommendations": [
                    "Implement model caching with memory limits",
                    "Use CPU offloading for large models",
                    "Add garbage collection after each inference"
                ]
            })

        if baseline_mb > 500:  # > 500MB baseline
            analysis["optimization_opportunities"].append({
                "type": "high_baseline_memory",
                "impact": "medium",
                "description": f"High baseline memory usage of {baseline_mb:.0f}MB",
                "recommendations": [
                    "Use lazy importing for heavy libraries",
                    "Consider lighter alternative libraries",
                    "Optimize import structure"
                ]
            })

        # Deployment recommendations
        analysis["deployment_recommendations"] = {
            "minimum_ram_gb": max(4, (peak_mb / 1024) * 1.5),
            "recommended_ram_gb": max(8, (peak_mb / 1024) * 2),
            "docker_memory_limit_mb": int(peak_mb * 1.3),
            "scaling_strategy": "vertical" if peak_mb > 2000 else "horizontal"
        }

        # Scaling analysis
        phase_stats = report.get("phase_analysis", {})
        if phase_stats:
            memory_per_request = []
            for phase, stats in phase_stats.items():
                if "request" in phase or "synthesis" in phase:
                    memory_per_request.append(stats.get("avg_mb", 0))

            if memory_per_request:
                avg_memory_per_request = np.mean(memory_per_request)
                analysis["scaling_analysis"] = {
                    "memory_per_request_mb": avg_memory_per_request,
                    "estimated_concurrent_requests": int(8192 / avg_memory_per_request) if avg_memory_per_request > 0 else 0,
                    "memory_scaling_pattern": "linear" if len(set(memory_per_request)) <= 2 else "variable"
                }

    return analysis


def main():
    """Main memory profiling and analysis"""
    print("🎮 Bark TTS Memory Profiling for Subway Surfers")
    print("=" * 60)

    # Create output directory
    output_dir = Path("./memory_analysis")
    output_dir.mkdir(exist_ok=True)

    all_results = {}

    # 1. Test baseline memory
    print("\n1️⃣ Baseline Memory Test")
    baseline_profiler = test_baseline_memory()
    baseline_profiler.save_measurements("baseline_memory.json")
    all_results["baseline"] = baseline_profiler.generate_report()

    # 2. Test mock server memory
    print("\n2️⃣ Mock Server Memory Test")
    mock_profiler = test_mock_server_memory()
    mock_profiler.save_measurements("mock_server_memory.json")
    all_results["mock_server"] = mock_profiler.generate_report()

    # 3. Estimate real Bark memory
    print("\n3️⃣ Real Bark Model Estimates")
    bark_estimates = estimate_real_bark_memory()
    all_results["bark_estimates"] = bark_estimates

    # 4. Test with actual PyTorch server (if available)
    print("\n4️⃣ PyTorch Server Test")
    pytorch_profiler = test_with_pytorch_server()
    pytorch_profiler.save_measurements("pytorch_server_memory.json")
    all_results["pytorch_server"] = pytorch_profiler.generate_report()

    # 5. Analyze patterns and generate recommendations
    print("\n5️⃣ Memory Analysis and Recommendations")
    analysis = analyze_memory_patterns(pytorch_profiler)
    all_results["analysis"] = analysis

    # Save comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"memory_analysis_report_{timestamp}.json"

    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n📊 Comprehensive Report Generated")
    print(f"   Report saved to: {report_path}")

    # Print key findings
    print(f"\n🔍 Key Findings:")

    if all_results.get("baseline", {}).get("summary"):
        baseline_peak = all_results["baseline"]["summary"].get("peak_mb", 0)
        print(f"   • Baseline peak memory: {baseline_peak:.1f} MB")

    if all_results.get("mock_server", {}).get("summary"):
        mock_peak = all_results["mock_server"]["summary"].get("peak_mb", 0)
        print(f"   • Mock server peak memory: {mock_peak:.1f} MB")

    if all_results.get("pytorch_server", {}).get("summary"):
        pytorch_peak = all_results["pytorch_server"]["summary"].get("peak_mb", 0)
        print(f"   • PyTorch server peak memory: {pytorch_peak:.1f} MB")

    print(f"\n💡 Recommendations:")
    if analysis.get("deployment_recommendations"):
        rec = analysis["deployment_recommendations"]
        print(f"   • Minimum RAM: {rec.get('minimum_ram_gb', 0):.1f} GB")
        print(f"   • Recommended RAM: {rec.get('recommended_ram_gb', 0):.1f} GB")
        print(f"   • Docker memory limit: {rec.get('docker_memory_limit_mb', 0):.0f} MB")

    # Generate plots
    print(f"\n📈 Generating visualizations...")
    try:
        pytorch_profiler.plot_memory_usage()
    except Exception as e:
        print(f"   ⚠️ Could not generate plots: {e}")

    print(f"\n✅ Memory profiling complete!")
    print(f"   Results directory: {output_dir.absolute()}")


if __name__ == "__main__":
    main()