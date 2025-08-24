#!/usr/bin/env python3
"""
Test runner for the Agentic AI Architect system.
Run individual tests or the full test suite.
"""

import asyncio
import argparse
import os
import sys
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_full_workflow import (
    test_azure_devops_integration,
    test_workflow_state_management,
    test_openai_code_generation,
    test_full_workflow,
    load_test_config
)


async def run_specific_tests(test_names: List[str], config: dict) -> dict:
    """Run specific tests by name."""
    test_functions = {
        "ado": test_azure_devops_integration,
        "state": test_workflow_state_management,
        "codegen": test_openai_code_generation,
        "workflow": test_full_workflow
    }
    
    results = {}
    
    for test_name in test_names:
        if test_name in test_functions:
            print(f"\n🧪 Running {test_name} test...")
            try:
                result = await test_functions[test_name](config)
                results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{test_name.upper()} test: {status}")
            except Exception as e:
                print(f"❌ {test_name.upper()} test failed with error: {str(e)}")
                results[test_name] = False
        else:
            print(f"⚠️  Unknown test: {test_name}")
            results[test_name] = False
    
    return results


async def run_all_tests(config: dict) -> dict:
    """Run all available tests."""
    print("🚀 Running all tests...")
    
    results = {}
    
    # Test Azure DevOps integration
    print("\n🧪 Testing Azure DevOps Integration...")
    results["ado"] = await test_azure_devops_integration(config)
    
    # Test workflow state management
    print("\n🧪 Testing Workflow State Management...")
    results["state"] = await test_workflow_state_management(config)
    
    # Test OpenAI code generation
    print("\n🧪 Testing OpenAI Code Generation...")
    results["codegen"] = await test_openai_code_generation(config)
    
    # Test full workflow
    print("\n🧪 Testing Full Workflow...")
    results["workflow"] = await test_full_workflow(config)
    
    return results


def print_results(results: dict):
    """Print test results summary."""
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        print(f"{test_name.upper()}: {status}")
    
    passed_tests = sum(1 for result in results.values() if result is True)
    failed_tests = sum(1 for result in results.values() if result is False)
    skipped_tests = sum(1 for result in results.values() if result is None)
    total_tests = len(results)
    
    print(f"\nOverall Results:")
    print(f"  • Passed: {passed_tests}")
    print(f"  • Failed: {failed_tests}")
    print(f"  • Skipped: {skipped_tests}")
    print(f"  • Total: {total_tests}")
    
    if failed_tests == 0 and passed_tests > 0:
        print("\n🎉 All tests passed! The system is working correctly.")
    elif failed_tests > 0:
        print(f"\n⚠️  {failed_tests} test(s) failed. Check the logs for details.")
    else:
        print("\nℹ️  No tests were executed.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Agentic AI Architect tests")
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        choices=["ado", "state", "codegen", "workflow"],
        help="Specific tests to run"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--config", "-c",
        default="test_config.env",
        help="Configuration file path (default: test_config.env)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if os.path.exists(args.config):
        print(f"📁 Loading configuration from {args.config}")
        # Load environment variables from file
        with open(args.config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print(f"⚠️  Configuration file {args.config} not found, using environment variables")
    
    config = load_test_config()
    
    print("🚀 Agentic AI Architect - Test Runner")
    print("=" * 50)
    
    try:
        if args.tests:
            # Run specific tests
            results = asyncio.run(run_specific_tests(args.tests, config))
        elif args.all:
            # Run all tests
            results = asyncio.run(run_all_tests(config))
        else:
            # Default: run all tests
            results = asyncio.run(run_all_tests(config))
        
        print_results(results)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test execution failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
