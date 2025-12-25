#!/usr/bin/env python3
"""
Multimodal Integration Test Runner

Runs read_media tool tests across all backends and validates results.
The test image is an educational infographic about "multimodality" from HelpfulProfessor.com.

Usage:
    uv run python massgen/tests/integration/multimodal/run_multimodal_tests.py
    uv run python massgen/tests/integration/multimodal/run_multimodal_tests.py --backend gemini
    uv run python massgen/tests/integration/multimodal/run_multimodal_tests.py --verbose
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    """Result of a single backend test."""

    backend: str
    config_file: str
    success: bool
    duration_seconds: float
    answer_file: Optional[str]
    answer_preview: str
    validation_passed: bool
    validation_details: str
    error: Optional[str] = None


# Keywords that should appear in a correct answer about the multimodality.jpg image
EXPECTED_KEYWORDS = [
    # Must match at least one from each group
    {"multimodal", "multimodality"},  # Topic
    {"professor", "helpfulprofessor", "helpful professor", "infographic"},  # Source or format
]

# Keywords that indicate hallucination (should NOT appear)
HALLUCINATION_KEYWORDS = [
    "ai brain",
    "robot",
    "neural network diagram",
    "circuit",
    "macaw",
    "parrot",
    "puppy",
    "dog",
    "woman in library",
]


def validate_answer(answer: str) -> tuple[bool, str]:
    """
    Validate that the answer correctly describes the multimodality.jpg image.

    Returns:
        (passed, details) tuple
    """
    answer_lower = answer.lower()

    # Check for hallucination keywords
    hallucinations_found = []
    for keyword in HALLUCINATION_KEYWORDS:
        if keyword in answer_lower:
            hallucinations_found.append(keyword)

    if hallucinations_found:
        return False, f"Hallucination detected: {hallucinations_found}"

    # Check for expected keywords (at least one from each group)
    missing_groups = []
    for i, keyword_group in enumerate(EXPECTED_KEYWORDS):
        found = any(kw in answer_lower for kw in keyword_group)
        if not found:
            missing_groups.append(f"Group {i+1}: {keyword_group}")

    if missing_groups:
        return False, f"Missing expected keywords from: {missing_groups}"

    return True, "All validations passed"


def run_test(config_file: str, backend_name: str, verbose: bool = False) -> TestResult:
    """Run a single backend test."""
    print(f"\n{'='*60}")
    print(f"Testing: {backend_name}")
    print(f"Config: {config_file}")
    print(f"{'='*60}")

    start_time = datetime.now()
    prompt = "Describe what you see in this image. Be specific about the content."

    try:
        # Run massgen with automation flag
        cmd = [
            "uv",
            "run",
            "massgen",
            "--automation",
            "--config",
            config_file,
            prompt,
        ]

        if verbose:
            print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        duration = (datetime.now() - start_time).total_seconds()
        output = result.stdout + result.stderr

        if verbose:
            print(f"\n--- Raw Output ---\n{output}\n--- End Output ---\n")

        # Parse output for answer file location
        answer_file = None
        answer_preview = ""

        # Look for ANSWER_FILE in output
        for line in output.split("\n"):
            if line.startswith("ANSWER_FILE:"):
                answer_file = line.split(":", 1)[1].strip()
            elif line.startswith("ANSWER_PREVIEW:"):
                # Get the preview (may span multiple lines)
                preview_start = output.find("ANSWER_PREVIEW:")
                preview_end = output.find("\n\nCOMPLETED:")
                if preview_start != -1 and preview_end != -1:
                    answer_preview = output[preview_start + 15 : preview_end].strip()

        # Read full answer if file exists
        full_answer = ""
        if answer_file and Path(answer_file).exists():
            full_answer = Path(answer_file).read_text()
            # Remove any leading numbers (sometimes present)
            full_answer = re.sub(r"^\d+\.?\d*\s*", "", full_answer).strip()

        if not full_answer and answer_preview:
            full_answer = answer_preview

        # Validate the answer
        if full_answer:
            validation_passed, validation_details = validate_answer(full_answer)
        else:
            validation_passed = False
            validation_details = "No answer found in output"

        # Print result summary
        status = "PASS" if validation_passed else "FAIL"
        print(f"\nResult: {status}")
        print(f"Duration: {duration:.1f}s")
        print(f"Validation: {validation_details}")
        if full_answer:
            # Show first 200 chars of answer
            preview = full_answer[:200] + "..." if len(full_answer) > 200 else full_answer
            print(f"Answer Preview: {preview}")

        return TestResult(
            backend=backend_name,
            config_file=config_file,
            success=result.returncode == 0,
            duration_seconds=duration,
            answer_file=answer_file,
            answer_preview=full_answer[:500] if full_answer else "",
            validation_passed=validation_passed,
            validation_details=validation_details,
        )

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\nResult: TIMEOUT after {duration:.1f}s")
        return TestResult(
            backend=backend_name,
            config_file=config_file,
            success=False,
            duration_seconds=duration,
            answer_file=None,
            answer_preview="",
            validation_passed=False,
            validation_details="Test timed out",
            error="Timeout after 120s",
        )
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\nResult: ERROR - {e}")
        return TestResult(
            backend=backend_name,
            config_file=config_file,
            success=False,
            duration_seconds=duration,
            answer_file=None,
            answer_preview="",
            validation_passed=False,
            validation_details=f"Error: {e}",
            error=str(e),
        )


def main():
    parser = argparse.ArgumentParser(description="Run multimodal integration tests")
    parser.add_argument(
        "--backend",
        choices=["gemini", "claude", "openai", "all"],
        default="all",
        help="Backend to test (default: all)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )
    args = parser.parse_args()

    # Define test configs
    test_dir = Path("massgen/tests/integration/multimodal")
    tests = {
        "gemini": test_dir / "test_gemini_image.yaml",
        "claude": test_dir / "test_claude_image.yaml",
        "openai": test_dir / "test_openai_image.yaml",
    }

    # Select tests to run
    if args.backend == "all":
        backends_to_test = list(tests.keys())
    else:
        backends_to_test = [args.backend]

    print("\n" + "=" * 60)
    print("MULTIMODAL INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Test Image: multimodality.jpg (HelpfulProfessor.com infographic)")
    print(f"Backends: {', '.join(backends_to_test)}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Run tests
    results: list[TestResult] = []
    for backend in backends_to_test:
        config = tests[backend]
        if not config.exists():
            print(f"\nSkipping {backend}: Config file not found at {config}")
            continue
        result = run_test(str(config), backend, verbose=args.verbose)
        results.append(result)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.validation_passed)
    total = len(results)

    for result in results:
        status = "PASS" if result.validation_passed else "FAIL"
        print(f"  [{status}] {result.backend}: {result.validation_details} ({result.duration_seconds:.1f}s)")

    print(f"\nTotal: {passed}/{total} passed")

    # Save results to JSON
    results_file = test_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "results": [
            {
                "backend": r.backend,
                "config_file": r.config_file,
                "success": r.success,
                "duration_seconds": r.duration_seconds,
                "validation_passed": r.validation_passed,
                "validation_details": r.validation_details,
                "answer_preview": r.answer_preview[:200] if r.answer_preview else "",
                "error": r.error,
            }
            for r in results
        ],
    }
    results_file.write_text(json.dumps(results_data, indent=2))
    print(f"\nResults saved to: {results_file}")

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
