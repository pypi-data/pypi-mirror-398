#!/usr/bin/env python3
"""
OrKa Examples Runner with Namespace Isolation
==============================================

This script iterates through all example YAML files in the examples directory
and runs them using the OrKa CLI with appropriate input text for each workflow.

Key Features:
- Isolated test namespace option to avoid polluting production data
- Automatic cleanup of test namespace after execution
- Unicode encoding support for OrKa emoji output
- Comprehensive reporting and filtering options
- Extract and display individual agent responses (not just final output)
- Clean agent-only output mode for focused logging
- Automatic filtering of common non-critical warnings (Redis, RuntimeWarnings, etc.)

Usage:
    python run_all_examples.py [OPTIONS]

Options:
    --dry-run                Show what would be executed without actually running
    --verbose                Show detailed output from each execution
    --filter PATTERN         Only run examples matching the given pattern (case-insensitive)
    --test-namespace         Run in isolated test namespace and cleanup afterward
    --namespace NAME         Custom test namespace name (default: orka_test_runner)
    --skip-cleanup           Don't cleanup test namespace (useful for debugging)
    --agent-responses-only   Only display agent responses, suppress other output (cleaner logs)
    --use-trace-files        Extract agent responses from trace JSON files (more detailed)
    --show-all-warnings      Show all warnings including common non-critical ones (default: filtered)

Output Files:
    orka_examples_results.json       Full detailed results including stdout/stderr
    orka_agent_responses.json        Agent responses only for easy review

Common Filtered Warnings (unless --show-all-warnings is used):
    - RuntimeWarning about orka.orka_cli in sys.modules
    - Redis search modules not available messages
    - DuckDuckGo package rename warnings
    - Deprecation warnings for shutil.which
    - Resource warnings for unclosed transports
"""

import argparse
import glob
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Tuple

import yaml


# Color codes for output formatting
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_input_for_workflow(filename: str) -> str:
    """
    Determines the appropriate input text for a given workflow file.
    For veterinary specialist workflows, selects a random JSON input file from the examples/inputs folder.
    """
    filename_lower = filename.lower()

    # Veterinary specialist workflow detection (deep or linear)
    if "veterinary_specialists_convergence" in filename_lower:
        # Find all JSON files in examples/inputs
        input_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), "inputs")
        json_files = glob.glob(os.path.join(input_dir, "input_case_*.json"))
        if json_files:
            return random.choice(json_files)
        # fallback if no JSON files found
        return "examples/inputs/input_case_15.json"

    # Pattern-based defaults for other workflows
    if "routed_binary_memory_writer" in filename_lower:
        return "25"
    elif "memory" in filename_lower:
        return "What is the importance of data structures in computer science?"
    elif "validation" in filename_lower or "structuring" in filename_lower:
        return "What are the key principles of software architecture?"
    elif "local_llm" in filename_lower or "llm" in filename_lower:
        return "Artificial intelligence and machine learning research methodologies"
    elif "failover" in filename_lower or "reliability" in filename_lower:
        return "What are the best practices for system reliability?"
    elif "fork" in filename_lower or "join" in filename_lower:
        return "What are the benefits of parallel processing in computing?"
    elif "routing" in filename_lower or "router" in filename_lower:
        return "How do computer networks handle data routing?"
    elif "classification" in filename_lower:
        return "What are the different types of machine learning algorithms?"
    elif "loop" in filename_lower:
        return "You are an llm agent running within an orchestration framework. Do you get any benefit from this setup? Explain your perspective. How this compare to running standalone or in other frameworks?"
    elif "self_reflection" in filename_lower or "self_discovery" in filename_lower:
        return "Provide a detailed analysis of the system you are currently in and how it works."
    elif "temporal_change_" in filename_lower:
        return "symbolic AI vs connectionist AI"
    # Default general-purpose input
    return "What are the key innovations in modern technology?"


def extract_final_output(stdout: str) -> str:
    """Extract the final meaningful output from orka_cli stdout.

    Strategy:
    - Prefer the ORKA-FINAL block where the next line contains the quoted response
    - Fallback to CLI echo line (orka.cli.core - INFO - ...)
    - Otherwise return the last non-empty, non-meta line
    """
    try:
        import re

        lines = [ln.rstrip("\n") for ln in stdout.splitlines()]

        # 1) ORKA-FINAL multi-line: quoted response is typically on the next line
        for i in range(len(lines) - 1, -1, -1):
            if "[ORKA-FINAL]" in lines[i]:
                # Scan a few lines ahead to find the actual response
                for j in range(i + 1, min(i + 6, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    # If quoted, strip quotes
                    if candidate.startswith('"'):
                        return candidate.strip('"').strip()
                    return candidate
                # As a last resort, try to extract quoted text from the same line
                ln = lines[i]
                first = ln.find('"')
                last = ln.rfind('"')
                if first != -1 and last != -1 and last > first:
                    return ln[first + 1 : last].strip()

        # 2) Fallback: CLI echo line - find last occurrence and capture remaining content
        cli_pattern = r"orka\.cli\.core\s+-\s+INFO\s+-\s+"
        cli_matches = list(re.finditer(cli_pattern, stdout))
        if cli_matches:
            # Get position of last match
            last_match = cli_matches[-1]
            # Extract everything after the log prefix
            output_content = stdout[last_match.end():].strip()
            if output_content:
                return output_content

        # 3) Fallback: last non-empty, non-meta line
        meta_markers = {"ORKA EXECUTION META REPORT", "====", "Total Execution Time", "Total LLM Calls"}
        for ln in reversed(lines):
            if ln.strip() and not any(m in ln for m in meta_markers):
                return ln.strip()
        return ""
    except Exception:
        # Return last 2000 chars instead of 500 to avoid truncation
        return stdout.strip()[-2000:]


def extract_final_agent(stdout: str) -> str:
    """Extract the final agent id from the ORKA-FINAL line if present."""
    try:
        import re

        m = re.search(r"\[ORKA-FINAL\].*final agent:\s*([\w\-]+)", stdout)
        if m:
            return m.group(1).strip()
        return ""
    except Exception:
        return ""


def extract_agent_responses_from_trace(trace_file: str) -> List[Dict[str, str]]:
    """Extract agent responses from OrKa trace JSON file.

    Returns a list of dicts with 'agent' and 'response' keys.
    """
    try:
        if not os.path.exists(trace_file):
            return []

        with open(trace_file, "r", encoding="utf-8") as f:
            trace_data = json.load(f)

        agent_responses = []

        # Check for execution_log which contains agent entries
        if "execution_log" in trace_data:
            for entry in trace_data["execution_log"]:
                if "node_id" in entry and "response" in entry:
                    node_id = entry["node_id"]
                    response = entry.get("response", "")

                    # Extract meaningful response text
                    if isinstance(response, dict):
                        # Try to get the actual response content
                        if "response" in response:
                            response = response["response"]
                        elif "result" in response:
                            response = response["result"]
                        elif "output" in response:
                            response = response["output"]
                        else:
                            response = json.dumps(response, ensure_ascii=False)[:200]
                    elif isinstance(response, str):
                        response = response.strip()

                    # Only include non-empty responses
                    if response and len(str(response).strip()) > 0:
                        agent_responses.append(
                            {"agent": node_id, "response": str(response)[:500]}  # Limit length
                        )

        return agent_responses

    except Exception as e:
        return []


def find_latest_trace_file() -> str:
    """Find the most recently created trace file in logs directory."""
    try:
        trace_files = glob.glob("logs/orka_trace_*.json")
        if not trace_files:
            return None
        # Sort by modification time, most recent first
        trace_files.sort(key=os.path.getmtime, reverse=True)
        return trace_files[0]
    except Exception:
        return None


def extract_agent_responses(stdout: str, trace_file: str = None) -> List[Dict[str, str]]:
    """Extract individual agent responses from stdout or trace file, filtering out debug/info logs.

    Returns a list of dicts with 'agent' and 'response' keys.
    """
    try:
        import re

        # First, try to get from trace file if provided
        if trace_file:
            trace_responses = extract_agent_responses_from_trace(trace_file)
            if trace_responses:
                return trace_responses

        agent_responses = []
        lines = stdout.splitlines()

        # Pattern 1: Look for agent execution patterns like "Agent [agent_id] response:"
        # Pattern 2: Look for lines that contain actual agent outputs (after INFO/DEBUG filtering)
        # Pattern 3: Look for ORKA agent execution markers

        current_agent = None
        response_lines = []

        for line in lines:
            # Skip debug, info, and warning logs
            if any(
                marker in line.upper() for marker in ["DEBUG", "INFO -", "WARNING -", "ERROR -"]
            ):
                continue

            # Skip meta report lines
            if any(
                marker in line
                for marker in ["====", "ORKA EXECUTION META REPORT", "Total Execution Time"]
            ):
                continue

            # Look for agent markers - common patterns in OrKa output
            agent_match = re.search(r"(?:Agent|agent)[\s:]+([a-zA-Z0-9_-]+)", line)
            if agent_match:
                # Save previous agent's response if exists
                if current_agent and response_lines:
                    agent_responses.append(
                        {"agent": current_agent, "response": " ".join(response_lines).strip()}
                    )
                    response_lines = []
                current_agent = agent_match.group(1)
                continue

            # Look for response indicators
            if re.search(r"(?:response|output|result)[\s:]+", line, re.IGNORECASE):
                # Extract the response part
                response_part = re.sub(
                    r"^.*?(?:response|output|result)[\s:]+", "", line, flags=re.IGNORECASE
                )
                if response_part.strip():
                    response_lines.append(response_part.strip())
                continue

            # Collect non-empty, non-marker lines as potential response content
            cleaned = line.strip()
            if cleaned and current_agent and not cleaned.startswith("["):
                response_lines.append(cleaned)

        # Save last agent's response
        if current_agent and response_lines:
            agent_responses.append(
                {"agent": current_agent, "response": " ".join(response_lines).strip()}
            )

        # If no agent-specific responses found, try to extract from ORKA-FINAL style output
        if not agent_responses:
            for line in lines:
                if "[ORKA-FINAL]" in line or "final agent:" in line:
                    # Extract agent ID and look for associated response
                    agent_match = re.search(r"final agent:\s*([a-zA-Z0-9_-]+)", line)
                    if agent_match:
                        agent_id = agent_match.group(1)
                        # Look for quoted response in following lines
                        idx = lines.index(line)
                        for i in range(idx + 1, min(idx + 10, len(lines))):
                            if lines[i].strip().startswith('"'):
                                response = lines[i].strip().strip('"')
                                agent_responses.append({"agent": agent_id, "response": response})
                                break

        return agent_responses

    except Exception as e:
        print_colored(f"Warning: Failed to extract agent responses: {e}", Colors.WARNING)
        return []


def validate_output_simple(final_output: str) -> Tuple[bool, str]:
    """
    Validate that the output is non-empty and does not contain failure indicators.
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not isinstance(final_output, str) or not final_output.strip():
        return False, "final output is empty"
    
    output_lower = final_output.lower()
    
    # Check for explicit failure indicators
    failure_patterns = [
        "failed to meet all required criteria",
        "score of 0.0",
        "not ready for production execution",
        "validation failure",
        "execution path was never executed",
        "no agents ran",
        "execution status was error",
        "graphscout failed",
        "path scored 0",
        "resulted in a score of 0",
        "failed all path variants",
        "could not extract",
        "extraction failed"
    ]
    
    for pattern in failure_patterns:
        if pattern in output_lower:
            return False, f"output indicates failure: '{pattern}'"
    
    # Check for empty/minimal responses that indicate failure
    minimal_failures = [
        "n/a",
        "no output",
        "no result",
        "error:",
        "[error]"
    ]
    
    # Only flag if the entire output is one of these minimal failures
    output_stripped = output_lower.strip()
    if output_stripped in minimal_failures or output_stripped.startswith("error:"):
        return False, "output indicates minimal/error response"
    
    return True, "non-empty and valid"


def find_example_files(examples_dir: str, include_subdirs: bool = False) -> List[str]:
    """
    Finds YAML example files in the examples directory.

    Args:
        examples_dir: The directory to search for example files
        include_subdirs: If True, also search subdirectories recursively
    """
    yaml_patterns = ["*.yml", "*.yaml"]
    example_files = []

    for pattern in yaml_patterns:
        # Search in examples directory (root level)
        pattern_path = os.path.join(examples_dir, pattern)
        example_files.extend(glob.glob(pattern_path))

        # Search in subdirectories if requested
        if include_subdirs:
            subdir_pattern = os.path.join(examples_dir, "**", pattern)
            example_files.extend(glob.glob(subdir_pattern, recursive=True))

    # Remove duplicates and sort
    example_files = sorted(list(set(example_files)))

    # Filter out non-example files if any
    filtered_files = []
    for file in example_files:
        # Skip if it's not in examples directory or subdirectories
        rel_path = os.path.relpath(file, examples_dir)
        if include_subdirs:
            # Include if in examples dir or subdirs
            if not rel_path.startswith(".."):
                filtered_files.append(file)
        else:
            # Include only if directly in examples dir (no path separator)
            if not rel_path.startswith("..") and os.sep not in rel_path:
                filtered_files.append(file)

    return filtered_files


def modify_yaml_namespace(yaml_file_path: str, test_namespace: str, temp_dir: str) -> str:
    """
    Modify a YAML file to use the test namespace and save to temp directory.
    Returns the path to the modified file.
    """
    try:
        with open(yaml_file_path, encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        # Track if any modifications were made
        modified = False

        # Recursively search for namespace fields in agents
        def modify_namespaces(obj, path=""):
            nonlocal modified
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "namespace":
                        old_namespace = value
                        obj[key] = test_namespace
                        modified = True
                        print_colored(
                            f"    └─ Modified namespace: {old_namespace} → {test_namespace}",
                            Colors.OKCYAN,
                        )
                    else:
                        modify_namespaces(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    modify_namespaces(item, f"{path}[{i}]")

        # Apply namespace modifications
        modify_namespaces(yaml_content)

        # Create temp file path
        rel_path = os.path.relpath(yaml_file_path, "examples")
        temp_file_path = os.path.join(temp_dir, rel_path)

        # Ensure temp subdirectories exist
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        # Save modified YAML
        with open(temp_file_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True)

        if modified:
            print_colored(f"    ✓ Created test version: {temp_file_path}", Colors.OKGREEN)
        else:
            print_colored("    → No namespaces found, using original", Colors.WARNING)

        return temp_file_path

    except Exception as e:
        print_colored(f"    ✗ Error modifying YAML: {e!s}", Colors.FAIL)
        return yaml_file_path  # Return original on error


def cleanup_test_namespace(test_namespace: str, verbose: bool = False) -> Dict[str, any]:
    """
    Clean up all memory data for the test namespace.
    """
    try:
        print_colored(f"\n🧹 Cleaning up test namespace: {test_namespace}", Colors.WARNING)

        # Import the memory cleanup functionality
        sys.path.insert(0, "orka")
        from orka.memory_logger import create_memory_logger

        cleanup_stats = {
            "namespace": test_namespace,
            "total_cleaned": 0,
            "backend_results": [],
            "errors": [],
        }

        # Try different backends for comprehensive cleanup
        backends = ["redisstack", "redis"]
        redis_urls = {
            "redisstack": "redis://localhost:6380/0",
            "redis": "redis://localhost:6379/0",
        }

        for backend in backends:
            try:
                print_colored(f"  🔧 Cleaning {backend} backend...", Colors.OKBLUE)

                memory_logger = create_memory_logger(
                    backend=backend,
                    redis_url=redis_urls[backend],
                )

                # Get all memory keys for this namespace
                if hasattr(memory_logger, "redis_client"):
                    client = memory_logger.redis_client
                elif hasattr(memory_logger, "client"):
                    client = memory_logger.client
                else:
                    print_colored(f"    ⚠️ No Redis client found for {backend}", Colors.WARNING)
                    continue

                # Find all memory keys
                pattern = "orka_memory:*"
                keys = client.keys(pattern)

                namespace_keys = []
                for key in keys:
                    try:
                        # Get memory data to check namespace
                        memory_data = client.hgetall(key)
                        if memory_data:
                            # Handle both bytes and string keys
                            namespace_field = memory_data.get(b"namespace") or memory_data.get(
                                "namespace",
                            )
                            if namespace_field:
                                if isinstance(namespace_field, bytes):
                                    namespace_value = namespace_field.decode()
                                else:
                                    namespace_value = namespace_field

                                if namespace_value == test_namespace:
                                    namespace_keys.append(key)
                    except Exception as e:
                        if verbose:
                            print_colored(f"    ⚠️ Error checking key {key}: {e}", Colors.WARNING)

                # Delete namespace-specific keys
                if namespace_keys:
                    deleted_count = client.delete(*namespace_keys)
                    cleanup_stats["total_cleaned"] += deleted_count
                    cleanup_stats["backend_results"].append(
                        {
                            "backend": backend,
                            "keys_found": len(namespace_keys),
                            "keys_deleted": deleted_count,
                        },
                    )
                    print_colored(
                        f"    ✓ Deleted {deleted_count} keys from {backend}",
                        Colors.OKGREEN,
                    )
                else:
                    print_colored(
                        f"    → No keys found in {backend} for namespace {test_namespace}",
                        Colors.OKCYAN,
                    )
                    cleanup_stats["backend_results"].append(
                        {
                            "backend": backend,
                            "keys_found": 0,
                            "keys_deleted": 0,
                        },
                    )

                # Close the logger
                if hasattr(memory_logger, "close"):
                    memory_logger.close()

            except ImportError as e:
                print_colored(f"    ⚠️ {backend} backend not available: {e}", Colors.WARNING)
                cleanup_stats["errors"].append(f"{backend}: {e}")
            except Exception as e:
                print_colored(f"    ✗ Error cleaning {backend}: {e}", Colors.FAIL)
                cleanup_stats["errors"].append(f"{backend}: {e}")

        total_cleaned = cleanup_stats["total_cleaned"]
        if total_cleaned > 0:
            print_colored(
                f"🎉 Cleanup complete! Removed {total_cleaned} memory entries",
                Colors.OKGREEN,
            )
        else:
            print_colored("✨ Namespace was clean (no entries found)", Colors.OKCYAN)

        return cleanup_stats

    except Exception as e:
        error_msg = f"Failed to cleanup namespace {test_namespace}: {e}"
        print_colored(f"✗ {error_msg}", Colors.FAIL)
        return {
            "namespace": test_namespace,
            "total_cleaned": 0,
            "backend_results": [],
            "errors": [error_msg],
        }


def filter_common_warnings(stderr: str) -> str:
    """Filter out common, non-critical warnings from stderr."""
    if not stderr:
        return stderr

    # List of warning patterns to filter out
    filter_patterns = [
        "RuntimeWarning: 'orka.orka_cli' found in sys.modules",
        "Redis search modules not available - vector search disabled",
        "RuntimeWarning: This package (`duckduckgo_search`) has been renamed",
        "DeprecationWarning: Use shutil.which instead of find_executable",
        "ResourceWarning: unclosed transport",
        "<frozen runpy>:128:",
    ]

    lines = stderr.splitlines()
    filtered_lines = []

    for line in lines:
        # Check if line contains any of the filter patterns
        if not any(pattern in line for pattern in filter_patterns):
            filtered_lines.append(line)

    return "\n".join(filtered_lines)


def run_orka_workflow(
    example_file: str,
    input_text: str,
    verbose: bool = False,
    filter_warnings: bool = True,
) -> Tuple[bool, str, str]:
    """
    Runs a single OrKa workflow and returns success status, stdout, and stderr.
    For veterinary specialist workflows, passes --json-input before run and uses the JSON file as input.
    """
    filename_lower = example_file.lower()
    # If this is a veterinary specialist workflow, use --json-input before run
    if "veterinary_specialists_convergence" in filename_lower:
        command = [
            "orka",
            "--json-input",
            "--verbose",
            "run",
            example_file,
            input_text,
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "orka.orka_cli",
            "run",
            example_file,
            input_text,
        ]

    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env=env,
        )
        success = result.returncode == 0
        stderr = result.stderr
        if filter_warnings and not verbose:
            stderr = filter_common_warnings(stderr)
        return success, result.stdout, stderr
    except subprocess.TimeoutExpired:
        return False, "", "Execution timed out after 10 minutes"
    except UnicodeDecodeError as e:
        return False, "", f"Unicode encoding error: {e!s}"
    except Exception as e:
        return False, "", f"Execution failed: {e!s}"


def print_colored(text: str, color: str = Colors.ENDC) -> None:
    """Prints colored text to stdout."""
    print(f"{color}{text}{Colors.ENDC}")


def print_separator(title: str = "") -> None:
    """Prints a separator line with optional title."""
    if title:
        print_colored(f"\n{'=' * 60}", Colors.HEADER)
        print_colored(f"  {title}", Colors.HEADER)
        print_colored(f"{'=' * 60}", Colors.HEADER)
    else:
        print_colored(f"{'=' * 60}", Colors.HEADER)


def main():
    parser = argparse.ArgumentParser(
        description="Run all OrKa example workflows with appropriate input text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output from each execution",
    )

    parser.add_argument(
        "--filter",
        type=str,
        help="Only run examples matching the given pattern (case-insensitive)",
    )

    parser.add_argument(
        "--examples-dir",
        type=str,
        default="examples",
        help="Path to examples directory (default: examples)",
    )

    parser.add_argument(
        "--test-namespace",
        action="store_true",
        help="Run examples in isolated test namespace and cleanup afterward",
    )

    parser.add_argument(
        "--namespace",
        type=str,
        default="orka_test_runner",
        help="Custom test namespace name (default: orka_test_runner)",
    )

    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Don't cleanup test namespace after execution (useful for debugging)",
    )

    parser.add_argument(
        "--include-subdirs",
        action="store_true",
        help="Include examples from subdirectories (default: only root examples)",
    )

    parser.add_argument(
        "--agent-responses-only",
        action="store_true",
        help="Only display agent responses, suppress other output (cleaner logs)",
    )

    parser.add_argument(
        "--use-trace-files",
        action="store_true",
        help="Extract agent responses from trace JSON files (more detailed)",
    )

    parser.add_argument(
        "--show-all-warnings",
        action="store_true",
        help="Show all warnings including common non-critical ones (default: filtered)",
    )

    args = parser.parse_args()

    # Check if examples directory exists
    if not os.path.exists(args.examples_dir):
        print_colored(f"Error: Examples directory '{args.examples_dir}' not found!", Colors.FAIL)
        sys.exit(1)

    # Find example files (root level by default)
    example_files = find_example_files(args.examples_dir, include_subdirs=args.include_subdirs)

    if not example_files:
        print_colored(f"No example files found in '{args.examples_dir}'", Colors.WARNING)
        sys.exit(1)

    # Apply filter if specified
    if args.filter:
        example_files = [f for f in example_files if args.filter.lower() in f.lower()]
        if not example_files:
            print_colored(f"No example files match filter '{args.filter}'", Colors.WARNING)
            sys.exit(1)

    # No hardcoded per-file inputs; use pattern-based defaults only

    print_separator("OrKa Examples Runner with Namespace Isolation")
    print_colored(f"Found {len(example_files)} example files to process", Colors.OKBLUE)

    if args.test_namespace:
        print_colored(f"🔒 Test namespace mode: {args.namespace}", Colors.OKCYAN)
        if not args.skip_cleanup:
            print_colored("🧹 Cleanup will be performed after execution", Colors.OKCYAN)
        else:
            print_colored("⚠️ Cleanup skipped (debug mode)", Colors.WARNING)

    if args.dry_run:
        print_colored("DRY RUN MODE - No actual execution", Colors.WARNING)

    # Setup temporary directory for modified YAML files
    temp_dir = None
    modified_files = {}

    if args.test_namespace and not args.dry_run:
        temp_dir = tempfile.mkdtemp(prefix="orka_test_")
        print_colored(f"📁 Created temporary directory: {temp_dir}", Colors.OKBLUE)

        # Modify YAML files to use test namespace
        print_colored("\n🔧 Modifying workflows for test namespace...", Colors.HEADER)
        for example_file in example_files:
            rel_path = os.path.relpath(example_file, args.examples_dir)
            print_colored(f"  📝 Processing: {rel_path}", Colors.OKBLUE)

            modified_path = modify_yaml_namespace(example_file, args.namespace, temp_dir)
            modified_files[example_file] = modified_path

    # Results tracking
    results = {
        "total": len(example_files),
        "successful": 0,
        "failed": 0,
        "test_namespace": args.namespace if args.test_namespace else None,
        "temp_dir": temp_dir,
        "details": [],
    }

    try:
        # Process each example file
        for i, example_file in enumerate(example_files, 1):
            # Get relative path for display
            rel_path = os.path.relpath(example_file, args.examples_dir)

            # Use modified file if in test namespace mode
            actual_file = (
                modified_files.get(example_file, example_file)
                if args.test_namespace
                else example_file
            )

            # Get appropriate input text
            input_text = get_input_for_workflow(rel_path)

            if not args.agent_responses_only:
                print_separator(f"Example {i}/{len(example_files)}: {rel_path}")
                print_colored(f"Input: {input_text}", Colors.OKCYAN)

                if args.test_namespace:
                    print_colored(f"Namespace: {args.namespace}", Colors.OKCYAN)
            else:
                # Minimal output for agent-responses-only mode
                print_colored(f"\n[{i}/{len(example_files)}] {rel_path}", Colors.HEADER)

            if args.dry_run:
                command = f'python -m orka.orka_cli run {actual_file} "{input_text}"'
                print_colored(f"Would execute: {command}", Colors.WARNING)
                continue

            # Run the workflow
            if not args.agent_responses_only:
                print_colored("Executing...", Colors.OKBLUE)
            start_time = time.time()

            # Record the latest trace file before execution
            trace_before = find_latest_trace_file()

            success, stdout, stderr = run_orka_workflow(
                actual_file, input_text, args.verbose, filter_warnings=not args.show_all_warnings
            )

            execution_time = time.time() - start_time

            # Find the new trace file created during execution
            trace_after = find_latest_trace_file()
            trace_file = trace_after if trace_after != trace_before else None

            # Extract final output and validate (minimal)
            final_output = extract_final_output(stdout)
            final_agent = extract_final_agent(stdout)
            agent_responses = extract_agent_responses(stdout, trace_file)
            output_ok, output_reason = validate_output_simple(final_output)
            success = success and output_ok

            # Record result
            result_detail = {
                "file": rel_path,
                "input": input_text,
                "success": success,
                "execution_time": execution_time,
                "final_output": final_output,
                "agent_responses": agent_responses,
                "output_validation": output_reason,
                "stdout": stdout if args.verbose else "",
                "stderr": stderr,
                "test_namespace": args.namespace if args.test_namespace else None,
            }
            results["details"].append(result_detail)

            if success:
                results["successful"] += 1
                if not args.agent_responses_only:
                    print_colored(f"✓ SUCCESS (took {execution_time:.2f}s)", Colors.OKGREEN)
                else:
                    print_colored(f"  ✓ Success ({execution_time:.2f}s)", Colors.OKGREEN)

                # Display individual agent responses
                if agent_responses:
                    if not args.agent_responses_only:
                        print_colored("\n📋 Agent Responses:", Colors.HEADER)
                    for idx, agent_resp in enumerate(agent_responses, 1):
                        print_colored(f"  {idx}. [{agent_resp['agent']}]:", Colors.OKBLUE)
                        print_colored(f"     {agent_resp['response']}", Colors.OKCYAN)

                # Always surface the final output for quick review
                if final_output and not args.agent_responses_only:
                    print_colored("\n🎯 Final Output:", Colors.HEADER)
                    if final_agent:
                        print_colored(f"  [{final_agent}]: {final_output}", Colors.OKGREEN)
                    else:
                        print_colored(f"  {final_output}", Colors.OKGREEN)
                elif final_output and args.agent_responses_only:
                    # Show compact final output in agent-responses-only mode
                    print_colored(
                        f"  → Final: {final_output[:100]}{'...' if len(final_output) > 100 else ''}",
                        Colors.OKGREEN,
                    )

                if args.verbose and stdout and not args.agent_responses_only:
                    print_colored("\n📝 Full stdout:", Colors.OKBLUE)
                    print(stdout)
            else:
                results["failed"] += 1
                if not args.agent_responses_only:
                    print_colored(f"✗ FAILED (took {execution_time:.2f}s)", Colors.FAIL)
                else:
                    print_colored(f"  ✗ FAILED ({execution_time:.2f}s)", Colors.FAIL)

                # Display individual agent responses even on failure for debugging
                if agent_responses:
                    if not args.agent_responses_only:
                        print_colored("\n📋 Agent Responses (for debugging):", Colors.WARNING)
                    for idx, agent_resp in enumerate(agent_responses, 1):
                        print_colored(f"  {idx}. [{agent_resp['agent']}]:", Colors.WARNING)
                        print_colored(f"     {agent_resp['response']}", Colors.OKCYAN)

                if final_output and not args.agent_responses_only:
                    print_colored("\n🎯 Final Output (for debugging):", Colors.WARNING)
                    if final_agent:
                        print_colored(f"  [{final_agent}]: {final_output}", Colors.WARNING)
                    else:
                        print_colored(f"  {final_output}", Colors.WARNING)

                if not args.agent_responses_only:
                    print_colored(f"\n⚠️ Validation: {output_reason}", Colors.WARNING)
                    if stderr:
                        print_colored("\n❌ Error:", Colors.FAIL)
                        print(stderr)
                else:
                    # Compact error output in agent-responses-only mode
                    if stderr:
                        print_colored(
                            f"  ❌ {stderr[:100]}{'...' if len(stderr) > 100 else ''}", Colors.FAIL
                        )

                if args.verbose and stdout and not args.agent_responses_only:
                    print_colored("\n📝 Full stdout:", Colors.WARNING)
                    print(stdout)

        # Print summary
        if not args.dry_run:
            print_separator("EXECUTION SUMMARY")
            print_colored(f"Total workflows: {results['total']}", Colors.OKBLUE)
            print_colored(f"Successful: {results['successful']}", Colors.OKGREEN)
            print_colored(
                f"Failed: {results['failed']}",
                Colors.FAIL if results["failed"] > 0 else Colors.OKBLUE,
            )

            success_rate = (results["successful"] / results["total"]) * 100
            print_colored(
                f"Success rate: {success_rate:.1f}%",
                Colors.OKGREEN if success_rate >= 80 else Colors.WARNING,
            )

            # Show failed workflows
            if results["failed"] > 0:
                print_colored("\nFailed workflows:", Colors.FAIL)
                for detail in results["details"]:
                    if not detail["success"]:
                        print_colored(
                            f"  - {detail['file']}: {detail['stderr'][:100]}...",
                            Colors.FAIL,
                        )

            # Perform namespace cleanup if requested
            if args.test_namespace and not args.skip_cleanup:
                cleanup_stats = cleanup_test_namespace(args.namespace, args.verbose)
                results["cleanup_stats"] = cleanup_stats

            # Save detailed results to JSON file
            results_file = "orka_examples_results.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            print_colored(f"\nDetailed results saved to: {results_file}", Colors.OKBLUE)

            # Save agent responses summary to separate file for easy review
            agent_responses_file = "orka_agent_responses.json"
            agent_responses_summary = []
            for detail in results["details"]:
                agent_responses_summary.append(
                    {
                        "workflow": detail["file"],
                        "input": detail["input"],
                        "success": detail["success"],
                        "execution_time": detail["execution_time"],
                        "agent_responses": detail.get("agent_responses", []),
                        "final_output": detail["final_output"],
                    }
                )

            with open(agent_responses_file, "w", encoding="utf-8") as f:
                json.dump(agent_responses_summary, f, indent=2, ensure_ascii=False)
            print_colored(f"Agent responses saved to: {agent_responses_file}", Colors.OKBLUE)

    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print_colored(f"🗑️ Cleaned up temporary directory: {temp_dir}", Colors.OKBLUE)
            except Exception as e:
                print_colored(f"⚠️ Failed to cleanup temp directory: {e}", Colors.WARNING)


if __name__ == "__main__":
    main()
