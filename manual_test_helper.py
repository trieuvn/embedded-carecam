"""
Manual Testing Helper Script
Provides utilities to assist with manual testing measurements and validation
"""

import time
import json
import sys
import os
from datetime import datetime

# Try to import sounddevice, but don't fail if not available
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    print("Warning: sounddevice not installed. Audio device enumeration will be limited.")
    print("Install with: pip install sounddevice")


class TestingHelper:
    """Helper class for manual testing procedures"""
    
    def __init__(self):
        self.test_results = {
            "test_date": datetime.now().isoformat(),
            "tester": "",
            "results": []
        }
    
    def check_prerequisites(self):
        """Check if all prerequisites are met for testing"""
        print("=== Testing Prerequisites Check ===\n")
        
        checks = []
        
        # Check audio devices
        if HAS_SOUNDDEVICE:
            try:
                devices = sd.query_devices()
                print("✓ Audio devices detected:")
                for i, device in enumerate(devices):
                    if device['max_input_channels'] > 0:
                        print(f"  - Input: {device['name']}")
                    if device['max_output_channels'] > 0:
                        print(f"  - Output: {device['name']}")
                checks.append(("Audio Devices", True))
            except Exception as e:
                print(f"✗ Audio devices error: {e}")
                checks.append(("Audio Devices", False))
        else:
            print("⚠ sounddevice not installed - skipping audio device check")
            checks.append(("Audio Devices", None))
        
        print()
        
        # Check Ollama
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                print("✓ Ollama service running")
                print(f"  Models available:\n{result.stdout}")
                checks.append(("Ollama", True))
            else:
                print("✗ Ollama service not responding")
                checks.append(("Ollama", False))
        except Exception as e:
            print(f"✗ Ollama check failed: {e}")
            checks.append(("Ollama", False))
        
        print()
        
        # Check position config
        config_path = "position_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                print("✓ Position config found:")
                print(f"  - Mic button: ({config.get('mic_button_x')}, {config.get('mic_button_y')})")
                print(f"  - Speaker button: ({config.get('speaker_button_x')}, {config.get('speaker_button_y')})")
                checks.append(("Position Config", True))
            except Exception as e:
                print(f"✗ Position config invalid: {e}")
                checks.append(("Position Config", False))
        else:
            print("⚠ Position config not found (will use defaults)")
            checks.append(("Position Config", None))
        
        print()
        
        # Check VB-Cable
        vbcable_found = False
        if HAS_SOUNDDEVICE:
            try:
                devices = sd.query_devices()
                for device in devices:
                    if 'CABLE' in device['name'].upper():
                        vbcable_found = True
                        print(f"✓ VB-Cable detected: {device['name']}")
                if not vbcable_found:
                    print("⚠ VB-Cable not found (Basic mode only)")
                checks.append(("VB-Cable", vbcable_found if vbcable_found else None))
            except:
                print("⚠ Could not check for VB-Cable")
                checks.append(("VB-Cable", None))
        else:
            print("⚠ sounddevice not installed - skipping VB-Cable check")
            checks.append(("VB-Cable", None))
        
        print()
        
        # Summary
        print("=== Prerequisites Summary ===")
        passed = sum(1 for _, status in checks if status is True)
        failed = sum(1 for _, status in checks if status is False)
        warnings = sum(1 for _, status in checks if status is None)
        
        print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")
        
        if failed > 0:
            print("\n⚠ Some prerequisites failed. Testing may not work correctly.")
            return False
        else:
            print("\n✓ All critical prerequisites met. Ready for testing.")
            return True
    
    def measure_latency(self, test_name="Latency Test"):
        """Interactive latency measurement tool"""
        print(f"\n=== {test_name} ===")
        print("Instructions:")
        print("1. Press ENTER when you START speaking")
        print("2. Press ENTER when TTS audio STARTS playing")
        print("3. The time difference will be measured")
        print("\nReady? Press ENTER to begin...")
        input()
        
        print("\nSpeak your command now...")
        start_time = time.time()
        input("Press ENTER when TTS audio starts playing...")
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        print(f"\nMeasured latency: {latency_ms:.0f} ms")
        
        target = 4000
        if latency_ms < target:
            print(f"✓ Within target (<{target}ms)")
            status = "PASS"
        else:
            print(f"✗ Exceeds target (>{target}ms)")
            status = "FAIL"
        
        self.test_results["results"].append({
            "test": test_name,
            "latency_ms": latency_ms,
            "target_ms": target,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        return latency_ms
    
    def batch_latency_test(self, num_tests=10):
        """Run multiple latency tests and compute statistics"""
        print(f"\n=== Batch Latency Test ({num_tests} measurements) ===")
        print("This will help you collect data for the performance section.")
        print(f"You will perform {num_tests} complete voice interactions.\n")
        
        latencies = []
        
        for i in range(num_tests):
            print(f"\n--- Test {i+1}/{num_tests} ---")
            latency = self.measure_latency(f"Latency Test {i+1}")
            latencies.append(latency)
            
            if i < num_tests - 1:
                print("\nWait for system to return to default state...")
                time.sleep(2)
        
        # Statistics
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        within_target = sum(1 for l in latencies if l < 4000)
        
        print("\n=== Latency Test Results ===")
        print(f"Measurements: {num_tests}")
        print(f"Average: {avg_latency:.0f} ms")
        print(f"Min: {min_latency:.0f} ms")
        print(f"Max: {max_latency:.0f} ms")
        print(f"Within target (<4000ms): {within_target}/{num_tests} ({within_target/num_tests*100:.0f}%)")
        
        if avg_latency < 4000 and within_target >= num_tests * 0.9:
            print("\n✓ PASS: Performance requirements met")
        else:
            print("\n✗ FAIL: Performance requirements not met")
        
        return {
            "average": avg_latency,
            "min": min_latency,
            "max": max_latency,
            "within_target": within_target,
            "total": num_tests
        }
    
    def test_wake_word_variations(self):
        """Interactive test for wake word variations"""
        print("\n=== Wake Word Variation Test ===")
        
        variations = [
            ("Tỷ Tỷ (standard)", "Standard Vietnamese pronunciation"),
            ("ty ty (fast)", "Fast pronunciation"),
            ("ti ti (soft i)", "Soft 'i' sound"),
            ("Tỷỷỷ Tỷỷỷ (elongated)", "Elongated pronunciation"),
            ("tỷ... tỷ (with pause)", "With pause between syllables")
        ]
        
        results = []
        
        for variation, description in variations:
            print(f"\n--- Testing: {variation} ---")
            print(f"Description: {description}")
            print("\nSpeak this variation now, then observe the system.")
            
            detected = input("Was it detected? (y/n): ").lower().strip() == 'y'
            
            if detected:
                latency = input("Approximate detection latency in ms (or press Enter to skip): ").strip()
                latency = int(latency) if latency.isdigit() else None
                
                confidence = input("Was confidence high? (y/n/unknown): ").lower().strip()
                confidence = {"y": "high", "n": "low", "u": "unknown"}.get(confidence[0] if confidence else "u", "unknown")
            else:
                latency = None
                confidence = None
            
            results.append({
                "variation": variation,
                "detected": detected,
                "latency_ms": latency,
                "confidence": confidence
            })
            
            print(f"Result: {'✓ DETECTED' if detected else '✗ NOT DETECTED'}")
        
        # Summary
        print("\n=== Wake Word Variation Results ===")
        detected_count = sum(1 for r in results if r["detected"])
        total = len(results)
        detection_rate = detected_count / total * 100
        
        print(f"Detection rate: {detected_count}/{total} ({detection_rate:.0f}%)")
        
        for result in results:
            status = "✓" if result["detected"] else "✗"
            latency_str = f"{result['latency_ms']}ms" if result['latency_ms'] else "N/A"
            print(f"{status} {result['variation']}: {latency_str}")
        
        if detection_rate >= 90:
            print("\n✓ PASS: Detection rate ≥90%")
        else:
            print("\n✗ FAIL: Detection rate <90%")
        
        self.test_results["results"].append({
            "test": "Wake Word Variations",
            "detection_rate": detection_rate,
            "results": results,
            "status": "PASS" if detection_rate >= 90 else "FAIL"
        })
        
        return results
    
    def test_noise_robustness(self):
        """Interactive test for noise robustness"""
        print("\n=== Noise Robustness Test ===")
        
        noise_levels = [
            ("Quiet (< 40 dB)", "Baseline quiet environment", 95),
            ("Light (50-60 dB)", "Background music, TV, fan", 85),
            ("Moderate (60-70 dB)", "Conversation, kitchen sounds", 70),
            ("Heavy (70+ dB)", "Vacuum, loud TV", 50)
        ]
        
        results = []
        
        for level, description, target_accuracy in noise_levels:
            print(f"\n--- Testing: {level} ---")
            print(f"Description: {description}")
            print(f"Target accuracy: ≥{target_accuracy}%")
            print("\nPerform 3-5 voice commands with this noise level.")
            
            total_commands = int(input("How many commands did you try? "))
            successful = int(input("How many were recognized correctly? "))
            false_triggers = int(input("How many false wake word triggers? "))
            
            accuracy = (successful / total_commands * 100) if total_commands > 0 else 0
            
            passed = accuracy >= target_accuracy
            status = "✓ PASS" if passed else "✗ FAIL"
            
            print(f"\nAccuracy: {accuracy:.0f}% ({successful}/{total_commands})")
            print(f"False triggers: {false_triggers}")
            print(f"{status}")
            
            results.append({
                "noise_level": level,
                "total_commands": total_commands,
                "successful": successful,
                "false_triggers": false_triggers,
                "accuracy": accuracy,
                "target": target_accuracy,
                "passed": passed
            })
        
        # Summary
        print("\n=== Noise Robustness Results ===")
        for result in results:
            status = "✓" if result["passed"] else "✗"
            print(f"{status} {result['noise_level']}: {result['accuracy']:.0f}% "
                  f"(target: ≥{result['target']}%)")
        
        self.test_results["results"].append({
            "test": "Noise Robustness",
            "results": results
        })
        
        return results
    
    def save_results(self, filename="manual_test_results.json"):
        """Save test results to JSON file"""
        self.test_results["tester"] = input("\nEnter tester name: ")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Results saved to {filename}")
    
    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "="*60)
        print("MANUAL TESTING REPORT SUMMARY")
        print("="*60)
        
        print(f"\nTest Date: {self.test_results['test_date']}")
        print(f"Tester: {self.test_results.get('tester', 'N/A')}")
        print(f"\nTotal Tests Run: {len(self.test_results['results'])}")
        
        passed = sum(1 for r in self.test_results['results'] 
                    if r.get('status') == 'PASS')
        failed = sum(1 for r in self.test_results['results'] 
                    if r.get('status') == 'FAIL')
        
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if len(self.test_results['results']) > 0:
            pass_rate = passed / len(self.test_results['results']) * 100
            print(f"Pass Rate: {pass_rate:.0f}%")
        
        print("\n" + "="*60)


def main():
    """Main interactive testing menu"""
    helper = TestingHelper()
    
    print("="*60)
    print("MANUAL TESTING HELPER")
    print("CareCam Voice Chatbot 'Tỷ Tỷ'")
    print("="*60)
    
    while True:
        print("\n--- Main Menu ---")
        print("1. Check Prerequisites")
        print("2. Measure Single Latency")
        print("3. Batch Latency Test (10 measurements)")
        print("4. Wake Word Variation Test")
        print("5. Noise Robustness Test")
        print("6. Generate Report")
        print("7. Save Results to File")
        print("0. Exit")
        
        choice = input("\nSelect option (0-7): ").strip()
        
        if choice == '1':
            helper.check_prerequisites()
        elif choice == '2':
            helper.measure_latency()
        elif choice == '3':
            helper.batch_latency_test()
        elif choice == '4':
            helper.test_wake_word_variations()
        elif choice == '5':
            helper.test_noise_robustness()
        elif choice == '6':
            helper.generate_report()
        elif choice == '7':
            helper.save_results()
        elif choice == '0':
            print("\nExiting. Thank you for testing!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
        sys.exit(0)
