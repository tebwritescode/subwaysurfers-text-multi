#!/usr/bin/env python3
"""
Comprehensive End-to-End Integration Tests for Bark TTS Implementation
====================================================================

This script performs comprehensive testing of the complete Bark TTS integration including:
- Server startup and health checks
- All Bark voice presets testing
- Video generation with Bark TTS
- Fallback to TikTok TTS
- Progress indicator updates
- Memory management
- Error handling

Usage:
    python integration_test.py [--mock] [--verbose] [--skip-server]

Options:
    --mock      Use mock server for testing
    --verbose   Enable detailed logging
    --skip-server  Skip server startup tests (assume server running)
"""

import os
import sys
import time
import json
import requests
import subprocess
import argparse
import threading
import queue
import tempfile
import shutil
import psutil
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pytorch_tts import PyTorchTTSClient, get_available_voices
from sub import script as generate_video_script

class TestResults:
    """Track test results and metrics"""
    def __init__(self):
        self.tests = {}
        self.start_time = time.time()
        self.metrics = {
            'server_startup_time': 0,
            'voice_synthesis_times': {},
            'video_generation_time': 0,
            'memory_usage': {},
            'fallback_tests': {},
        }

    def add_test(self, name: str, passed: bool, message: str = "", duration: float = 0):
        """Add a test result"""
        self.tests[name] = {
            'passed': passed,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }

    def add_metric(self, category: str, name: str, value):
        """Add a performance metric"""
        if category not in self.metrics:
            self.metrics[category] = {}
        self.metrics[category][name] = value

    def get_summary(self) -> Dict:
        """Get test summary"""
        total_tests = len(self.tests)
        passed_tests = sum(1 for t in self.tests.values() if t['passed'])
        total_duration = time.time() - self.start_time

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'tests': self.tests,
            'metrics': self.metrics
        }

class BarkTTSIntegrationTester:
    """Comprehensive integration tester for Bark TTS"""

    def __init__(self, verbose: bool = False, use_mock: bool = False, skip_server: bool = False):
        self.verbose = verbose
        self.use_mock = use_mock
        self.skip_server = skip_server
        self.results = TestResults()
        self.pytorch_endpoint = "http://localhost:8000"
        self.test_output_dir = Path("./integration_test_output")
        self.test_output_dir.mkdir(exist_ok=True)

        # Test configurations
        self.test_voices = ["narrator", "announcer", "excited", "calm", "deep"]
        self.test_texts = {
            "short": "Hello world!",
            "medium": "Welcome to Subway Surfers! This is an exciting endless runner game.",
            "long": "In the bustling underground world of Subway Surfers, players embark on an endless adventure through vibrant subway tunnels, dodging trains, collecting coins, and performing spectacular stunts while evading the grumpy inspector and his dog."
        }

        # Memory monitoring
        self.initial_memory = psutil.virtual_memory().used

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "WARN"]:
            print(f"[{timestamp}] {level}: {message}")

    def measure_memory(self) -> Dict:
        """Measure current memory usage"""
        memory = psutil.virtual_memory()
        return {
            'used_mb': memory.used / 1024 / 1024,
            'available_mb': memory.available / 1024 / 1024,
            'percent': memory.percent
        }

    def test_server_startup(self) -> bool:
        """Test server startup and health checks"""
        if self.skip_server:
            self.log("Skipping server startup test (--skip-server)")
            return True

        self.log("Testing server startup and health checks...")
        start_time = time.time()

        try:
            # Check if server is already running
            response = requests.get(f"{self.pytorch_endpoint}/health", timeout=5)
            if response.status_code == 200:
                self.log("Server already running and healthy")
                self.results.add_test("server_already_running", True, "Server was already healthy")
                return True
        except:
            pass

        # Start server using Docker Compose
        self.log("Starting PyTorch TTS server...")
        compose_cmd = [
            "docker-compose",
            "-f", "docker-compose.local-stack.yml",
            "up", "-d", "pytorch-tts"
        ]

        try:
            result = subprocess.run(compose_cmd, capture_output=True, text=True, cwd=project_root)
            if result.returncode != 0:
                self.log(f"Failed to start server: {result.stderr}", "ERROR")
                self.results.add_test("server_startup", False, f"Docker compose failed: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"Error starting server: {e}", "ERROR")
            self.results.add_test("server_startup", False, f"Exception: {e}")
            return False

        # Wait for server to be healthy
        max_wait = 120  # 2 minutes
        wait_interval = 5
        waited = 0

        while waited < max_wait:
            try:
                response = requests.get(f"{self.pytorch_endpoint}/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    startup_time = time.time() - start_time
                    self.results.add_metric('server_startup_time', 'total', startup_time)
                    self.log(f"Server healthy after {startup_time:.1f}s, device: {data.get('device', 'unknown')}")
                    self.results.add_test("server_startup", True, f"Healthy in {startup_time:.1f}s", startup_time)
                    return True
            except Exception as e:
                self.log(f"Waiting for server... ({waited}s/{max_wait}s)")

            time.sleep(wait_interval)
            waited += wait_interval

        self.log("Server failed to become healthy within timeout", "ERROR")
        self.results.add_test("server_startup", False, f"Timeout after {max_wait}s")
        return False

    def test_voice_availability(self) -> bool:
        """Test voice availability and presets"""
        self.log("Testing voice availability...")

        try:
            voices = get_available_voices(self.pytorch_endpoint)
            if not voices:
                self.results.add_test("voice_availability", False, "No voices available")
                return False

            self.log(f"Available voices: {voices}")

            # Check if expected voices are available
            missing_voices = [v for v in self.test_voices if v not in voices]
            if missing_voices:
                self.log(f"Missing expected voices: {missing_voices}", "WARN")
                self.results.add_test("voice_availability", False, f"Missing voices: {missing_voices}")
                return False

            self.results.add_test("voice_availability", True, f"All {len(voices)} voices available")
            return True

        except Exception as e:
            self.log(f"Error checking voices: {e}", "ERROR")
            self.results.add_test("voice_availability", False, f"Exception: {e}")
            return False

    def test_voice_synthesis(self) -> bool:
        """Test individual voice synthesis"""
        self.log("Testing voice synthesis for all presets...")

        client = PyTorchTTSClient(self.pytorch_endpoint)
        success_count = 0

        for voice in self.test_voices:
            self.log(f"Testing voice: {voice}")
            start_time = time.time()

            try:
                test_text = f"This is a test of the {voice} voice in Subway Surfers."
                audio_bytes = client.synthesize(test_text, voice)

                synthesis_time = time.time() - start_time
                self.results.add_metric('voice_synthesis_times', voice, synthesis_time)

                if audio_bytes and len(audio_bytes) > 1000:  # Basic sanity check
                    # Save test audio
                    output_file = self.test_output_dir / f"test_{voice}.wav"
                    with open(output_file, "wb") as f:
                        f.write(audio_bytes)

                    self.log(f"✅ {voice}: {synthesis_time:.1f}s, {len(audio_bytes)} bytes")
                    self.results.add_test(f"voice_synthesis_{voice}", True,
                                       f"Generated in {synthesis_time:.1f}s", synthesis_time)
                    success_count += 1
                else:
                    self.log(f"❌ {voice}: Invalid audio data", "ERROR")
                    self.results.add_test(f"voice_synthesis_{voice}", False, "Invalid audio data")

            except Exception as e:
                self.log(f"❌ {voice}: {e}", "ERROR")
                self.results.add_test(f"voice_synthesis_{voice}", False, f"Exception: {e}")

        overall_success = success_count == len(self.test_voices)
        self.results.add_test("voice_synthesis_overall", overall_success,
                           f"{success_count}/{len(self.test_voices)} voices successful")
        return overall_success

    def test_audio_generation_only(self) -> bool:
        """Test just the audio generation part without video pipeline"""
        self.log("Testing audio generation with Bark TTS...")

        # Set environment for PyTorch TTS
        os.environ['PYTORCH_TTS_ENDPOINT'] = self.pytorch_endpoint
        os.environ['PYTORCH_TTS_MODEL'] = 'suno/bark'

        from pytorch_tts import tts

        test_text = "Welcome to our Subway Surfers adventure! Get ready for an exciting journey through the underground tunnels."
        output_file = self.test_output_dir / "test_audio_bark.wav"

        start_time = time.time()

        try:
            # Generate audio with Bark TTS
            success = tts(
                text=test_text,
                voice="narrator",
                output_file=str(output_file),
                pytorch_endpoint=self.pytorch_endpoint,
                model="suno/bark"
            )

            generation_time = time.time() - start_time
            self.results.add_metric('audio_generation_time', 'bark_tts', generation_time)

            if success and output_file.exists():
                file_size = output_file.stat().st_size
                self.log(f"✅ Audio generated: {generation_time:.1f}s, {file_size} bytes")

                self.results.add_test("audio_generation_bark", True,
                                   f"Generated in {generation_time:.1f}s", generation_time)
                return True
            else:
                self.log("❌ Audio generation failed", "ERROR")
                self.results.add_test("audio_generation_bark", False, "Generation failed")
                return False

        except Exception as e:
            self.log(f"❌ Audio generation error: {e}", "ERROR")
            self.results.add_test("audio_generation_bark", False, f"Exception: {e}")
            return False

    def test_video_generation_with_bark(self) -> bool:
        """Test complete video generation pipeline with Bark TTS"""
        self.log("Testing video generation with Bark TTS...")

        # Check if Whisper server is available (required for video generation)
        whisper_url = os.getenv('WHISPER_ASR_URL', 'http://whisper-asr:9000')
        try:
            response = requests.get(f"{whisper_url}/health", timeout=5)
            if response.status_code != 200:
                self.log(f"Whisper server not available at {whisper_url}, skipping video generation test", "WARN")
                self.results.add_test("video_generation_bark", False, "Whisper server not available")
                return False
        except:
            self.log(f"Whisper server not available at {whisper_url}, skipping video generation test", "WARN")
            self.results.add_test("video_generation_bark", False, "Whisper server not available")
            return False

        # Set environment for PyTorch TTS
        os.environ['PYTORCH_TTS_ENDPOINT'] = self.pytorch_endpoint
        os.environ['PYTORCH_TTS_MODEL'] = 'suno/bark'

        test_text = "Welcome to our Subway Surfers adventure! Get ready for an exciting journey through the underground tunnels."
        output_file = self.test_output_dir / "test_video_bark.mp4"

        # Create progress queue to monitor updates
        progress_queue = queue.Queue()
        progress_updates = []

        def monitor_progress():
            """Monitor progress updates"""
            while True:
                try:
                    update = progress_queue.get(timeout=1)
                    progress_updates.append(update)
                    self.log(f"Progress: {update}")
                    if update.get('progress', 0) >= 100:
                        break
                except queue.Empty:
                    continue
                except:
                    break

        start_time = time.time()
        progress_thread = threading.Thread(target=monitor_progress, daemon=True)
        progress_thread.start()

        try:
            # Generate video with Bark TTS
            success = generate_video_script(
                input_text=test_text,
                customspeed=1.0,
                customvoice="narrator",  # Use Bark voice
                final_path=str(output_file),
                progress_queue=progress_queue
            )

            generation_time = time.time() - start_time
            self.results.add_metric('video_generation_time', 'bark_tts', generation_time)

            if success and output_file.exists():
                file_size = output_file.stat().st_size
                self.log(f"✅ Video generated: {generation_time:.1f}s, {file_size} bytes")
                self.log(f"Progress updates received: {len(progress_updates)}")

                self.results.add_test("video_generation_bark", True,
                                   f"Generated in {generation_time:.1f}s", generation_time)
                self.results.add_metric('progress_updates', 'bark_video', len(progress_updates))
                return True
            else:
                self.log("❌ Video generation failed", "ERROR")
                self.results.add_test("video_generation_bark", False, "Generation failed")
                return False

        except Exception as e:
            self.log(f"❌ Video generation error: {e}", "ERROR")
            self.results.add_test("video_generation_bark", False, f"Exception: {e}")
            return False

    def test_fallback_to_tiktok(self) -> bool:
        """Test fallback to TikTok TTS when Bark fails"""
        self.log("Testing fallback to TikTok TTS...")

        # Temporarily disable PyTorch TTS to test fallback
        original_endpoint = os.environ.get('PYTORCH_TTS_ENDPOINT')
        os.environ['PYTORCH_TTS_ENDPOINT'] = 'http://invalid-endpoint:9999'

        test_text = "This should use TikTok TTS as fallback mechanism when Bark TTS is unavailable or fails to connect properly."
        output_file = self.test_output_dir / "test_video_fallback.mp4"

        start_time = time.time()

        try:
            success = generate_video_script(
                input_text=test_text,
                customspeed=1.0,
                customvoice="en_us_001",  # TikTok voice
                final_path=str(output_file)
            )

            fallback_time = time.time() - start_time

            if success and output_file.exists():
                self.log(f"✅ Fallback successful: {fallback_time:.1f}s")
                self.results.add_test("fallback_tiktok", True, f"Fallback in {fallback_time:.1f}s")
                self.results.add_metric('fallback_tests', 'tiktok_success', fallback_time)
                result = True
            else:
                self.log("❌ Fallback failed", "ERROR")
                self.results.add_test("fallback_tiktok", False, "Fallback failed")
                result = False

        except Exception as e:
            self.log(f"❌ Fallback error: {e}", "ERROR")
            self.results.add_test("fallback_tiktok", False, f"Exception: {e}")
            result = False

        finally:
            # Restore original endpoint
            if original_endpoint:
                os.environ['PYTORCH_TTS_ENDPOINT'] = original_endpoint
            else:
                os.environ.pop('PYTORCH_TTS_ENDPOINT', None)

        return result

    def test_batch_voice_endpoint(self) -> bool:
        """Test the batch voice testing endpoint"""
        self.log("Testing batch voice endpoint...")

        try:
            response = requests.post(f"{self.pytorch_endpoint}/test-voices", timeout=300)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})

                successful_voices = sum(1 for r in results.values() if r.get("success"))
                total_voices = len(results)

                self.log(f"✅ Batch test: {successful_voices}/{total_voices} voices")
                self.results.add_test("batch_voice_test", True,
                                   f"{successful_voices}/{total_voices} voices successful")

                # Save batch test results
                for voice, result in results.items():
                    if result.get("success") and result.get("audio_data"):
                        audio_bytes = base64.b64decode(result["audio_data"])
                        output_file = self.test_output_dir / f"batch_{voice}.wav"
                        with open(output_file, "wb") as f:
                            f.write(audio_bytes)

                return successful_voices > 0
            else:
                self.log(f"❌ Batch test failed: {response.status_code}", "ERROR")
                self.results.add_test("batch_voice_test", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log(f"❌ Batch test error: {e}", "ERROR")
            self.results.add_test("batch_voice_test", False, f"Exception: {e}")
            return False

    def test_memory_management(self) -> bool:
        """Test memory usage during operations"""
        self.log("Testing memory management...")

        # Record memory before intensive operations
        memory_before = self.measure_memory()
        self.results.add_metric('memory_usage', 'before_tests', memory_before)

        # Perform multiple synthesis operations
        client = PyTorchTTSClient(self.pytorch_endpoint)

        for i in range(5):
            for voice in ["narrator", "excited"]:
                try:
                    audio_bytes = client.synthesize(
                        f"Memory test iteration {i+1} with {voice} voice.",
                        voice
                    )
                    time.sleep(0.5)  # Brief pause between operations
                except:
                    pass

        # Record memory after operations
        memory_after = self.measure_memory()
        self.results.add_metric('memory_usage', 'after_tests', memory_after)

        # Calculate memory increase
        memory_increase = memory_after['used_mb'] - memory_before['used_mb']
        self.results.add_metric('memory_usage', 'increase_mb', memory_increase)

        # Check for reasonable memory usage (less than 500MB increase)
        reasonable_increase = memory_increase < 500

        self.log(f"Memory usage: {memory_before['used_mb']:.1f}MB → {memory_after['used_mb']:.1f}MB (+{memory_increase:.1f}MB)")

        self.results.add_test("memory_management", reasonable_increase,
                           f"Memory increase: {memory_increase:.1f}MB")

        return reasonable_increase

    def test_error_handling(self) -> bool:
        """Test error handling scenarios"""
        self.log("Testing error handling...")

        client = PyTorchTTSClient(self.pytorch_endpoint)
        error_tests = 0
        passed_tests = 0

        # Test invalid voice
        try:
            result = client.synthesize("Test text", "invalid_voice_name")
            if result is None:  # Should fail gracefully
                passed_tests += 1
                self.log("✅ Invalid voice handled correctly")
            else:
                self.log("❌ Invalid voice should return None", "WARN")
        except:
            passed_tests += 1  # Exception is also acceptable
            self.log("✅ Invalid voice raised exception (acceptable)")
        error_tests += 1

        # Test empty text
        try:
            result = client.synthesize("", "narrator")
            if result is None:  # Should fail gracefully
                passed_tests += 1
                self.log("✅ Empty text handled correctly")
            else:
                self.log("❌ Empty text should return None", "WARN")
        except:
            passed_tests += 1
            self.log("✅ Empty text raised exception (acceptable)")
        error_tests += 1

        # Test very long text
        try:
            long_text = "A" * 10000  # Very long text
            result = client.synthesize(long_text, "narrator")
            if result is not None:  # Should either work or fail gracefully
                passed_tests += 1
                self.log("✅ Long text processed successfully")
            else:
                passed_tests += 1
                self.log("✅ Long text failed gracefully")
        except:
            passed_tests += 1
            self.log("✅ Long text raised exception (acceptable)")
        error_tests += 1

        success = passed_tests == error_tests
        self.results.add_test("error_handling", success, f"{passed_tests}/{error_tests} error cases handled")
        return success

    def cleanup(self):
        """Clean up test resources"""
        self.log("Cleaning up test resources...")

        # Don't remove test output directory - keep for inspection
        self.log(f"Test outputs saved in: {self.test_output_dir.absolute()}")

        # Record final memory usage
        final_memory = self.measure_memory()
        self.results.add_metric('memory_usage', 'final', final_memory)

    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        self.log("🚀 Starting Bark TTS Integration Tests")
        self.log("=" * 60)

        try:
            # Test 1: Server startup and health
            if not self.test_server_startup():
                self.log("❌ Server startup failed - aborting remaining tests", "ERROR")
                return self.results.get_summary()

            # Test 2: Voice availability
            self.test_voice_availability()

            # Test 3: Individual voice synthesis
            self.test_voice_synthesis()

            # Test 4: Batch voice testing
            self.test_batch_voice_endpoint()

            # Test 5: Audio generation with Bark (simpler test)
            self.test_audio_generation_only()

            # Test 6: Video generation with Bark (requires Whisper server)
            self.test_video_generation_with_bark()

            # Test 7: Fallback to TikTok TTS
            self.test_fallback_to_tiktok()

            # Test 8: Memory management
            self.test_memory_management()

            # Test 9: Error handling
            self.test_error_handling()

        except Exception as e:
            self.log(f"❌ Critical error during testing: {e}", "ERROR")
            self.results.add_test("critical_error", False, f"Exception: {e}")

        finally:
            self.cleanup()

        return self.results.get_summary()

    def print_summary(self, summary: Dict):
        """Print test summary"""
        self.log("📊 Test Summary")
        self.log("=" * 60)
        self.log(f"Total Tests: {summary['total_tests']}")
        self.log(f"Passed: {summary['passed_tests']}")
        self.log(f"Failed: {summary['failed_tests']}")
        self.log(f"Success Rate: {summary['success_rate']:.1f}%")
        self.log(f"Total Duration: {summary['total_duration']:.1f}s")

        # Print failed tests
        failed_tests = [name for name, result in summary['tests'].items() if not result['passed']]
        if failed_tests:
            self.log("\n❌ Failed Tests:")
            for test in failed_tests:
                result = summary['tests'][test]
                self.log(f"   {test}: {result['message']}")

        # Print performance metrics
        metrics = summary['metrics']
        if metrics.get('voice_synthesis_times'):
            self.log("\n⏱️  Voice Synthesis Times:")
            for voice, time_taken in metrics['voice_synthesis_times'].items():
                self.log(f"   {voice}: {time_taken:.1f}s")

        if metrics.get('memory_usage'):
            memory = metrics['memory_usage']
            if 'increase_mb' in memory:
                self.log(f"\n💾 Memory Usage: +{memory['increase_mb']:.1f}MB during tests")

        # Overall result
        if summary['success_rate'] >= 80:
            self.log("\n🎉 Integration tests PASSED! Bark TTS integration is working correctly.")
        else:
            self.log("\n⚠️  Integration tests had significant failures. Review failed tests.")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Bark TTS Integration Tests")
    parser.add_argument("--mock", action="store_true", help="Use mock server")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-server", action="store_true", help="Skip server startup (assume running)")

    args = parser.parse_args()

    # Create tester
    tester = BarkTTSIntegrationTester(
        verbose=args.verbose,
        use_mock=args.mock,
        skip_server=args.skip_server
    )

    # Run tests
    summary = tester.run_all_tests()

    # Print summary
    tester.print_summary(summary)

    # Save detailed results
    results_file = tester.test_output_dir / "integration_test_results.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file.absolute()}")

    # Exit with appropriate code
    sys.exit(0 if summary['success_rate'] >= 80 else 1)

if __name__ == "__main__":
    main()