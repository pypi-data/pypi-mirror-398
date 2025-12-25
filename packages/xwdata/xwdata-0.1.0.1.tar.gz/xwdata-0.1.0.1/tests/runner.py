#!/usr/bin/env python3
"""
#exonware/xwdata/tests/runner.py

Main test runner for xwdata - Production Excellence Edition
Orchestrates all test layer runners with Markdown output logging.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025

Usage:
    python tests/runner.py                # Run all tests
    python tests/runner.py --core         # Run only core tests
    python tests/runner.py --unit         # Run only unit tests
    python tests/runner.py --integration  # Run only integration tests
    python tests/runner.py --advance      # Run only advance tests (v1.0.0+)
    python tests/runner.py --security     # Run only security tests
    python tests/runner.py --performance  # Run only performance tests

Output:
    - Terminal: Colored, formatted output
    - File: runner_out.md (Markdown-friendly format)
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

# Try to use xwsystem utilities for better output
try:
    from exonware.xwsystem.utils.test_runner import (
        DualOutput, format_path, print_header, print_section, print_status
    )
    USE_XWSYSTEM_UTILS = True
except ImportError:
    USE_XWSYSTEM_UTILS = False


class SimpleDualOutput:
    """Simple fallback output handler."""
    
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.markdown_lines = []
    
    def print(self, text: str, markdown_format: str = None, color=None, emoji=None):
        """Print to terminal and capture for Markdown."""
        # Add emoji if provided
        if emoji and not USE_XWSYSTEM_UTILS:
            print(f"{emoji} {text}")
        else:
            print(text)
        
        self.markdown_lines.append(markdown_format if markdown_format else text)
    
    def save(self, metadata: dict = None):
        """Save Markdown output."""
        header = f"""# Test Runner Output

**Library:** xwdata
**Generated:** {datetime.now().strftime("%d-%b-%Y %H:%M:%S")}
**Runner:** Main Orchestrator

---

"""
        content = header + "\n".join(self.markdown_lines) + "\n"
        self.output_file.write_text(content, encoding='utf-8')


def run_sub_runner(runner_path: Path, description: str, output) -> int:
    """Run a sub-runner and return exit code."""
    if USE_XWSYSTEM_UTILS:
        print_section(description, output)
    else:
        print(f"\n{'='*80}")
        print(f"📂 {description}")
        print(f"{'='*80}\n")
    
    result = subprocess.run(
        [sys.executable, str(runner_path)],
        cwd=runner_path.parent
    )
    
    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
    
    if USE_XWSYSTEM_UTILS:
        print_status(result.returncode == 0, status, output)
    else:
        print(f"\n{status}\n")
    
    return result.returncode


def main():
    """Main test runner function following GUIDELINES_TEST.md."""
    test_dir = Path(__file__).parent
    output_file = test_dir / "runner_out.md"
    
    # Create output handler
    if USE_XWSYSTEM_UTILS:
        output = DualOutput(output_file)
        print_header("xwdata Test Runner - Production Excellence Edition", output)
    else:
        output = SimpleDualOutput(output_file)
        output.print("="*80, "# Test Execution Report")
        output.print("xwdata Test Runner - Production Excellence Edition",
                    "**Library:** xwdata\n**Type:** Main Orchestrator")
        output.print("="*80, "---")
    
    # Add src to Python path
    src_path = test_dir.parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Parse arguments
    args = sys.argv[1:]
    
    # Define sub-runners
    core_runner = test_dir / "0.core" / "runner.py"
    unit_runner = test_dir / "1.unit" / "runner.py"
    integration_runner = test_dir / "2.integration" / "runner.py"
    advance_runner = test_dir / "3.advance" / "runner.py"
    
    exit_codes = []
    
    # Determine which tests to run
    if "--core" in args:
        if core_runner.exists():
            exit_codes.append(run_sub_runner(core_runner, "Core Tests", output))
    
    elif "--unit" in args:
        if unit_runner.exists():
            exit_codes.append(run_sub_runner(unit_runner, "Unit Tests", output))
    
    elif "--integration" in args:
        if integration_runner.exists():
            exit_codes.append(run_sub_runner(integration_runner, "Integration Tests", output))
    
    elif "--advance" in args:
        if advance_runner.exists():
            exit_codes.append(run_sub_runner(advance_runner, "Advance Tests", output))
        else:
            msg = "⚠️  Advance tests not available (requires v1.0.0)"
            output.print(msg, f"> {msg}")
    
    else:
        # Run all tests in sequence
        output.print("\n🚀 Running: ALL Tests", "\n## Running All Test Layers")
        output.print("   Layers: 0.core → 1.unit → 2.integration", 
                    "**Execution Order:** 0.core → 1.unit → 2.integration\n")
        
        # Core tests
        if core_runner.exists():
            exit_codes.append(run_sub_runner(core_runner, "Layer 0: Core Tests", output))
        
        # Unit tests
        if unit_runner.exists():
            exit_codes.append(run_sub_runner(unit_runner, "Layer 1: Unit Tests", output))
        
        # Integration tests
        if integration_runner.exists():
            exit_codes.append(run_sub_runner(integration_runner, "Layer 2: Integration Tests", output))
    
    # Print summary
    output.print(f"\n{'='*80}", "\n---\n\n## 📊 Test Execution Summary")
    output.print("📊 TEST EXECUTION SUMMARY", "")
    output.print(f"{'='*80}", "")
    
    total_runs = len(exit_codes)
    passed = sum(1 for code in exit_codes if code == 0)
    failed = total_runs - passed
    
    output.print(f"Total Layers: {total_runs}", f"- **Total Layers:** {total_runs}")
    output.print(f"Passed: {passed}", f"- **Passed:** {passed}")
    output.print(f"Failed: {failed}", f"- **Failed:** {failed}")
    
    # Final status
    if all(code == 0 for code in exit_codes):
        final_msg = "✅ ALL TESTS PASSED!"
        output.print(f"\n{final_msg}", f"\n### {final_msg}")
        
        if USE_XWSYSTEM_UTILS:
            output.save({'library': 'xwdata', 'layer': 'main', 'description': 'Main Orchestrator'})
        else:
            output.save()
        
        print(f"\n📝 Test results saved to: {output_file}")
        sys.exit(0)
    else:
        final_msg = "❌ SOME TESTS FAILED!"
        output.print(f"\n{final_msg}", f"\n### {final_msg}")
        
        if USE_XWSYSTEM_UTILS:
            output.save({'library': 'xwdata', 'layer': 'main', 'description': 'Main Orchestrator'})
        else:
            output.save()
        
        print(f"\n📝 Test results saved to: {output_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
