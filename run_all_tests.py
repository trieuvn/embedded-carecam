#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Tỷ Tỷ Chatbot
Task 20: Final validation and checkpoint

This script runs all unit tests, integration tests, and validation checks.
"""

import sys
import os
import unittest
import time
from io import StringIO
from datetime import datetime

# Test file mapping
TEST_FILES = {
    "Unit Tests": [
        "test_ui_config_tool",
        "test_context_manager",
        "test_prompt_builder",
        "test_conversation_manager",
        "test_error_handler",
        "test_system_initializer_unit",
        "test_ollama_service",
        "test_wake_word_engine",
        "test_vad_unit",
        "test_vad_requirements",
        "test_audio_router",
    ],
    "Integration Tests": [
        "test_conversation_integration",
        "test_ai_service_integration",
        "test_carecam_controller_position_config",
        "test_conversation_manager_silence",
    ],
    "System Tests": [
        "test_graceful_degradation",
        "test_logging_complete",
        "test_main_refactor",
    ]
}

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_section(title):
    """Print section divider"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80 + "\n")

def run_test_suite(suite_name, test_files):
    """Run a suite of tests and return results"""
    print_section(f"{suite_name}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "tests": []
    }
    
    for test_file in test_files:
        print(f"\n📝 Running {test_file}...")
        
        try:
            # Import test module
            test_module = __import__(test_file)
            
            # Load tests from module
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=1, stream=StringIO())
            result = runner.run(suite)
            
            # Collect results
            test_result = {
                "name": test_file,
                "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
                "failed": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "total": result.testsRun
            }
            
            results["tests"].append(test_result)
            results["passed"] += test_result["passed"]
            results["failed"] += test_result["failed"]
            results["errors"] += test_result["errors"]
            results["skipped"] += test_result["skipped"]
            
            # Print result
            if test_result["failed"] == 0 and test_result["errors"] == 0:
                print(f"  ✅ {test_file}: {test_result['passed']}/{test_result['total']} passed")
            else:
                print(f"  ❌ {test_file}: {test_result['passed']}/{test_result['total']} passed, "
                      f"{test_result['failed']} failed, {test_result['errors']} errors")
                
        except Exception as e:
            print(f"  ⚠️  {test_file}: Failed to run - {str(e)}")
            results["errors"] += 1
            results["tests"].append({
                "name": test_file,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "skipped": 0,
                "total": 0
            })
    
    return results

def print_summary(all_results):
    """Print comprehensive test summary"""
    print_header("TEST SUMMARY")
    
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0
    
    for suite_name, results in all_results.items():
        print(f"\n{suite_name}:")
        print(f"  Passed:  {results['passed']}")
        print(f"  Failed:  {results['failed']}")
        print(f"  Errors:  {results['errors']}")
        print(f"  Skipped: {results['skipped']}")
        
        total_passed += results['passed']
        total_failed += results['failed']
        total_errors += results['errors']
        total_skipped += results['skipped']
    
    print("\n" + "-" * 80)
    print(f"\nOVERALL TOTALS:")
    print(f"  ✅ Passed:  {total_passed}")
    print(f"  ❌ Failed:  {total_failed}")
    print(f"  ⚠️  Errors:  {total_errors}")
    print(f"  ⏭️  Skipped: {total_skipped}")
    
    total_tests = total_passed + total_failed + total_errors
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"\n  Success Rate: {success_rate:.1f}%")
    
    print("\n" + "=" * 80)
    
    return total_failed == 0 and total_errors == 0

def run_all_tests():
    """Main test runner"""
    print_header("Tỷ Tỷ Chatbot - Comprehensive Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    all_results = {}
    
    # Run each test suite
    for suite_name, test_files in TEST_FILES.items():
        results = run_test_suite(suite_name, test_files)
        all_results[suite_name] = results
    
    # Print summary
    elapsed_time = time.time() - start_time
    success = print_summary(all_results)
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Time: {elapsed_time:.2f} seconds")
    
    return success

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
