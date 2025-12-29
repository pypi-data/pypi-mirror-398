#!/usr/bin/env python
import sys
import os
import random
import time
import concurrent.futures
import traceback
import inspect
from typing import List, Callable, Dict, Any, Tuple
import unittest
from unittest.mock import patch
import json
from datetime import datetime
import asyncio
import aiohttp

# Add the parent directory to the sys.path to allow imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import the test class that contains all the test methods
from botrun_flow_lang.tests.api_functional_tests import TestAPIFunctionality


class StressTest:
    def __init__(
        self,
        num_users: int = 50,
        num_rounds: int = 2,
        base_url: str = "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
        include_tests: List[str] = None,
    ):
        """
        Initialize the stress test with configuration parameters.

        Args:
            num_users: Number of concurrent users to simulate
            num_rounds: Number of testing rounds to perform
            base_url: The base URL for the API
            include_tests: List of test function names to include
        """
        self.num_users = num_users
        self.num_rounds = num_rounds
        self.base_url = base_url
        self.include_tests = include_tests or [
            "test_langgraph_react_agent_social_housing"
        ]

        # Get all test methods from TestAPIFunctionality class
        self.test_methods = self._get_test_methods()

        # Stats for tracking results
        self.total_tests = 0
        self.successful_tests = 0
        self.failed_tests = 0
        self.test_durations = {}
        self.start_time = None
        self.end_time = None

    def _get_test_methods(self) -> List[str]:
        """Get all test methods from TestAPIFunctionality class, excluding the ones in include_tests."""
        all_methods = [
            method_name
            for method_name, method in inspect.getmembers(
                TestAPIFunctionality, predicate=inspect.isfunction
            )
            if method_name.startswith("test_") and method_name in self.include_tests
        ]
        return all_methods

    def run_single_test(self, user_id: int, test_name: str) -> Tuple[bool, float, str]:
        """
        Run a single test function.

        Args:
            user_id: ID of the simulated user
            test_name: Name of the test function to run

        Returns:
            Tuple of (success, duration, error_message)
        """
        start_time = time.time()
        print(f"User {user_id}: Running {test_name}")

        test_instance = TestAPIFunctionality(methodName="setUp")
        test_instance.base_url = self.base_url

        # Run the setUp method to initialize the test instance
        test_instance.setUp()

        # Get the actual test method
        test_method = getattr(test_instance, test_name)

        success = True
        error_message = ""

        try:
            # Execute the test method
            test_method()
        except Exception as e:
            success = False
            error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            print(
                f"User {user_id}: Error in {test_name} - {type(e).__name__}: {str(e)}"
            )
        finally:
            # Always call tearDown to clean up resources
            if hasattr(test_instance, "tearDown"):
                test_instance.tearDown()

        duration = time.time() - start_time
        print(
            f"User {user_id}: Completed {test_name} in {duration:.2f}s - {'Success' if success else 'Failed'}"
        )

        return success, duration, error_message

    def user_workflow(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Simulates a user workflow by randomly selecting and running tests.

        Args:
            user_id: ID of the simulated user

        Returns:
            List of test results
        """
        results = []

        for round_num in range(self.num_rounds):
            # Select a random test method
            test_name = random.choice(self.test_methods)

            # Run the test
            success, duration, error_message = self.run_single_test(user_id, test_name)

            # Record the result
            result = {
                "user_id": user_id,
                "round": round_num + 1,
                "test_name": test_name,
                "success": success,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "error_message": error_message,
            }
            results.append(result)

            # Sleep for a short period to simulate some user think time (optional)
            time.sleep(random.uniform(0.1, 0.5))

        return results

    def run_stress_test(self) -> Dict[str, Any]:
        """
        Run the stress test with concurrent users.

        Returns:
            Dictionary with test results and statistics
        """
        self.start_time = time.time()
        all_results = []
        self.test_durations = {}

        print(
            f"Starting stress test with {self.num_users} concurrent users for {self.num_rounds} rounds"
        )
        print(f"Using test methods: {', '.join(self.test_methods)}")
        print("-" * 70)

        # Use concurrent.futures to run tests in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_users
        ) as executor:
            future_to_user = {
                executor.submit(self.user_workflow, user_id): user_id
                for user_id in range(1, self.num_users + 1)
            }

            for future in concurrent.futures.as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    print(f"User {user_id} generated an exception: {e}")

        # Calculate statistics
        self.end_time = time.time()
        self.total_tests = len(all_results)
        self.successful_tests = sum(1 for r in all_results if r["success"])
        self.failed_tests = self.total_tests - self.successful_tests

        # Calculate average duration per test type
        test_type_durations = {}
        for result in all_results:
            test_name = result["test_name"]
            if test_name not in test_type_durations:
                test_type_durations[test_name] = {"count": 0, "total_duration": 0}

            test_type_durations[test_name]["count"] += 1
            test_type_durations[test_name]["total_duration"] += result["duration"]

        for test_name, data in test_type_durations.items():
            avg_duration = data["total_duration"] / data["count"]
            test_type_durations[test_name]["avg_duration"] = avg_duration

        # Prepare summary report
        summary = {
            "config": {
                "num_users": self.num_users,
                "num_rounds": self.num_rounds,
                "base_url": self.base_url,
                "included_tests": self.include_tests,
            },
            "statistics": {
                "total_tests": self.total_tests,
                "successful_tests": self.successful_tests,
                "failed_tests": self.failed_tests,
                "success_rate": (
                    (self.successful_tests / self.total_tests) * 100
                    if self.total_tests > 0
                    else 0
                ),
                "total_duration_seconds": self.end_time - self.start_time,
                "avg_test_duration": (
                    sum(r["duration"] for r in all_results) / len(all_results)
                    if all_results
                    else 0
                ),
                "test_type_statistics": {
                    test_name: {
                        "count": data["count"],
                        "avg_duration": data["avg_duration"],
                        "success_rate": (
                            sum(
                                1
                                for r in all_results
                                if r["test_name"] == test_name and r["success"]
                            )
                            / data["count"]
                            * 100
                        ),
                    }
                    for test_name, data in test_type_durations.items()
                },
            },
            "detailed_results": all_results,
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print a human-readable summary of the stress test results."""
        print("\n" + "=" * 70)
        print(f"STRESS TEST SUMMARY")
        print("=" * 70)

        stats = summary["statistics"]
        config = summary["config"]

        print(f"Configuration:")
        print(f"  Users: {config['num_users']}")
        print(f"  Rounds per user: {config['num_rounds']}")
        print(f"  API Base URL: {config['base_url']}")
        print(f"  Included tests: {', '.join(config['included_tests'])}")

        print("\nOverall Statistics:")
        print(f"  Total tests run: {stats['total_tests']}")
        print(f"  Successful tests: {stats['successful_tests']}")
        print(f"  Failed tests: {stats['failed_tests']}")
        print(f"  Success rate: {stats['success_rate']:.2f}%")
        print(f"  Total duration: {stats['total_duration_seconds']:.2f} seconds")
        print(f"  Average test duration: {stats['avg_test_duration']:.2f} seconds")

        print("\nTest Type Statistics:")
        for test_name, test_stats in stats["test_type_statistics"].items():
            print(f"  {test_name}:")
            print(f"    Count: {test_stats['count']}")
            print(f"    Average duration: {test_stats['avg_duration']:.2f} seconds")
            print(f"    Success rate: {test_stats['success_rate']:.2f}%")

        print("\nFailed Tests:")
        failed_tests = [r for r in summary["detailed_results"] if not r["success"]]
        if failed_tests:
            for i, test in enumerate(
                failed_tests[:10], 1
            ):  # Show only first 10 failures
                print(
                    f"  {i}. User {test['user_id']}, Round {test['round']}: {test['test_name']}"
                )
                error_first_line = test["error_message"].split("\n")[0]
                print(f"     Error: {error_first_line}")

            if len(failed_tests) > 10:
                print(f"  ... and {len(failed_tests) - 10} more failures")
        else:
            print("  None")

        print("=" * 70)

        # Add a clear final summary line
        print(
            f"\n🏆 FINAL RESULT: {stats['successful_tests']} PASSED ✅ | {stats['failed_tests']} FAILED ❌ | {stats['success_rate']:.2f}% SUCCESS RATE"
        )
        print("=" * 70)


def main():
    """Main entry point for the stress test."""
    # Configuration parameters - adjust these as needed
    num_users = 50
    num_rounds = 2
    base_url = "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app"
    include_tests = [
        "test_langgraph_react_agent_social_housing"
    ]  # 只執行社宅入住資格審查測試

    # Create and run the stress test
    stress_tester = StressTest(
        num_users=num_users,
        num_rounds=num_rounds,
        base_url=base_url,
        include_tests=include_tests,  # 改用 include_tests 來指定要執行的測試
    )

    results = stress_tester.run_stress_test()

    # Get success and failure counts for final output
    successful_tests = results["statistics"]["successful_tests"]
    failed_tests = results["statistics"]["failed_tests"]
    success_rate = results["statistics"]["success_rate"]

    # Optionally save the results to a JSON file
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # results_file = f"stress_test_results_{timestamp}.json"

    # with open(results_file, "w") as f:
    #     json.dump(results, f, indent=2)

    # print(f"\nResults saved to {results_file}")

    # Display final status for quick reference
    print("\n" + "=" * 70)
    print(
        f"STRESS TEST COMPLETED: {successful_tests} PASSED, {failed_tests} FAILED, {success_rate:.2f}% SUCCESS RATE"
    )

    # Return non-zero exit code if any tests failed (useful for CI/CD pipelines)
    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
