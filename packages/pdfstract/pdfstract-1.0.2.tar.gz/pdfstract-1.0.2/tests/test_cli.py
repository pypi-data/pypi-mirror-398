#!/usr/bin/env python3
"""
PDFStract CLI Test Suite
Tests all CLI commands and modes with sample PDFs
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class CLITester:
    """Test runner for PDFStract CLI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = Path(__file__).parent
        self.samples_dir = self.test_dir / "samples"
        self.results_dir = self.test_dir / "results"
        self.sample_pdfs = list(self.samples_dir.glob("*.pdf"))
        
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        
        if not self.sample_pdfs:
            print(f"❌ No PDF samples found in {self.samples_dir}")
            sys.exit(1)
        
        print(f"✓ Found {len(self.sample_pdfs)} sample PDFs")
    
    def cleanup(self):
        """Remove test results directory"""
        if self.results_dir.exists():
            shutil.rmtree(self.results_dir)
            print(f"✓ Cleaned up {self.results_dir}")
    
    def setup(self):
        """Setup test environment"""
        self.results_dir.mkdir(exist_ok=True)
        print(f"✓ Created results directory: {self.results_dir}")
    
    def run_command(self, cmd: List[str], cwd=None) -> Tuple[int, str, str]:
        """Run a CLI command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def test_help(self) -> bool:
        """Test: pdfstract --help"""
        print("\n📋 Test 1: pdfstract --help")
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "--help"
        ])
        
        passed = exit_code == 0 and "PDFStract" in stdout and "Commands:" in stdout
        
        if passed:
            print("✓ PASSED: Help command works")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "help",
            "passed": passed,
            "command": "pdfstract --help"
        })
        
        return passed
    
    def test_libs(self) -> bool:
        """Test: pdfstract libs"""
        print("\n📋 Test 2: pdfstract libs")
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "libs"
        ])
        
        # Check for success indicators in output
        passed = exit_code == 0 and ("Available" in stdout or "✓" in stdout or "Library" in stdout)
        
        if passed:
            print("✓ PASSED: Listed available libraries")
            # Count available libraries
            available_count = stdout.count("✓")
            unavailable_count = stdout.count("✗")
            print(f"  Found {available_count} available and {unavailable_count} unavailable libraries")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
            else:
                print(f"  stdout preview: {stdout[:200]}")
        
        self.results["tests"].append({
            "name": "libs",
            "passed": passed,
            "command": "pdfstract libs"
        })
        
        return passed
    
    def get_available_libraries(self) -> List[str]:
        """Get list of available libraries by running 'pdfstract libs'"""
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "libs"
        ])
        
        available_libs = []
        if exit_code == 0:
            # Parse output for library names marked as available
            lines = stdout.split('\n')
            for line in lines:
                if "✓ Available" in line:
                    # Extract library name from the line
                    parts = line.split('│')
                    if len(parts) >= 2:
                        lib_name = parts[1].strip()
                        if lib_name and lib_name not in ['Library', '']:
                            available_libs.append(lib_name)
        
        return available_libs
    
    def test_convert_single(self) -> bool:
        """Test: pdfstract convert (single file)"""
        print("\n📋 Test 3: pdfstract convert <file> --library pymupdf4llm")
        
        if not self.sample_pdfs:
            print("⊝ SKIPPED: No sample PDFs")
            return True
        
        sample_file = self.sample_pdfs[0]
        output_file = self.results_dir / "convert_single_output.md"
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "convert",
            str(sample_file),
            "--library", "pymupdf4llm",
            "--format", "markdown",
            "--output", str(output_file)
        ])
        
        passed = exit_code == 0 and output_file.exists() and output_file.stat().st_size > 0
        
        if passed:
            size = output_file.stat().st_size
            print(f"✓ PASSED: Converted {sample_file.name} ({size} bytes)")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "convert_single",
            "passed": passed,
            "command": "pdfstract convert --library pymupdf4llm",
            "output_file": str(output_file) if passed else None
        })
        
        return passed
    
    def test_convert_all_libraries(self) -> bool:
        """Test: pdfstract convert with all available libraries"""
        print("\n📋 Test 3.5: pdfstract convert with all available libraries")
        
        if not self.sample_pdfs:
            print("⊝ SKIPPED: No sample PDFs")
            return True
        
        # Get available libraries
        available_libs = self.get_available_libraries()
        
        if not available_libs:
            print("⊝ SKIPPED: No available libraries found")
            return True
        
        print(f"  Testing with {len(available_libs)} available libraries: {', '.join(available_libs)}")
        
        sample_file = self.sample_pdfs[0]
        passed_count = 0
        failed_libs = []
        
        for lib in available_libs:
            output_file = self.results_dir / f"convert_{lib}_output.md"
            
            exit_code, stdout, stderr = self.run_command([
                sys.executable, "cli.py", "convert",
                str(sample_file),
                "--library", lib,
                "--format", "markdown",
                "--output", str(output_file)
            ])
            
            lib_passed = exit_code == 0 and output_file.exists() and output_file.stat().st_size > 0
            
            if lib_passed:
                size = output_file.stat().st_size
                print(f"  ✓ {lib}: {size} bytes")
                passed_count += 1
            else:
                print(f"  ✗ {lib}: Failed (exit code {exit_code})")
                failed_libs.append(lib)
        
        passed = passed_count == len(available_libs)
        
        if passed:
            print(f"✓ PASSED: All {len(available_libs)} libraries successful")
        else:
            print(f"⚠️  PARTIAL: {passed_count}/{len(available_libs)} libraries successful")
            if failed_libs:
                print(f"  Failed: {', '.join(failed_libs)}")
        
        self.results["tests"].append({
            "name": "convert_all_libraries",
            "passed": passed,
            "command": "pdfstract convert with all libraries",
            "tested_libraries": available_libs,
            "passed_count": passed_count,
            "failed_libraries": failed_libs
        })
        
        return passed
    
    def test_convert_json(self) -> bool:
        """Test: pdfstract convert with JSON output"""
        print("\n📋 Test 4: pdfstract convert --format json")
        
        if not self.sample_pdfs:
            print("⊝ SKIPPED: No sample PDFs")
            return True
        
        sample_file = self.sample_pdfs[0]
        output_file = self.results_dir / "convert_json_output.json"
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "convert",
            str(sample_file),
            "--library", "pymupdf4llm",
            "--format", "json",
            "--output", str(output_file)
        ])
        
        passed = exit_code == 0 and output_file.exists()
        
        if passed and output_file.exists():
            try:
                with open(output_file) as f:
                    json.load(f)
                print(f"✓ PASSED: Generated valid JSON output")
            except json.JSONDecodeError:
                passed = False
                print(f"✗ FAILED: Invalid JSON output")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "convert_json",
            "passed": passed,
            "command": "pdfstract convert --format json"
        })
        
        return passed
    
    def test_compare(self) -> bool:
        """Test: pdfstract compare (multi-library)"""
        print("\n📋 Test 5: pdfstract compare -l pymupdf4llm -l markitdown")
        
        if not self.sample_pdfs:
            print("⊝ SKIPPED: No sample PDFs")
            return True
        
        sample_file = self.sample_pdfs[0]
        compare_dir = self.results_dir / "compare_output"
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "compare",
            str(sample_file),
            "-l", "pymupdf4llm",
            "-l", "markitdown",
            "--format", "markdown",
            "--output", str(compare_dir)
        ])
        
        # Check if results directory was created
        passed = exit_code == 0 and compare_dir.exists()
        result_files = list(compare_dir.glob("*.md")) if compare_dir.exists() else []
        
        if passed:
            print(f"✓ PASSED: Compared 2 libraries, generated {len(result_files)} result files")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "compare",
            "passed": passed,
            "command": "pdfstract compare -l pymupdf4llm -l markitdown",
            "result_files": len(result_files)
        })
        
        return passed
    
    def test_batch(self) -> bool:
        """Test: pdfstract batch (process multiple files)"""
        print("\n📋 Test 6: pdfstract batch ./tests/samples --library pymupdf4llm")
        
        if len(self.sample_pdfs) < 1:
            print("⊝ SKIPPED: Less than 1 sample PDF")
            return True
        
        batch_output_dir = self.results_dir / "batch_output"
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "batch",
            str(self.samples_dir),
            "--library", "pymupdf4llm",
            "--format", "markdown",
            "--output", str(batch_output_dir),
            "--parallel", "2"
        ])
        
        # Check if batch completed successfully
        passed = exit_code == 0 and batch_output_dir.exists()
        result_files = list(batch_output_dir.glob("*.md")) if batch_output_dir.exists() else []
        report_file = batch_output_dir / "batch_report.json" if batch_output_dir.exists() else None
        
        if passed and report_file and report_file.exists():
            try:
                with open(report_file) as f:
                    report = json.load(f)
                success_count = report.get("statistics", {}).get("success", 0)
                print(f"✓ PASSED: Batch converted {success_count} files, generated {len(result_files)} outputs")
            except json.JSONDecodeError:
                print(f"✓ PASSED: Batch completed but report JSON invalid")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "batch",
            "passed": passed,
            "command": "pdfstract batch --library pymupdf4llm",
            "result_files": len(result_files)
        })
        
        return passed
    
    def test_batch_compare(self) -> bool:
        """Test: pdfstract batch-compare (quality testing)"""
        print("\n📋 Test 7: pdfstract batch-compare -l pymupdf4llm -l markitdown")
        
        if len(self.sample_pdfs) < 1:
            print("⊝ SKIPPED: Less than 1 sample PDF")
            return True
        
        batch_compare_dir = self.results_dir / "batch_compare_output"
        
        exit_code, stdout, stderr = self.run_command([
            sys.executable, "cli.py", "batch-compare",
            str(self.samples_dir),
            "-l", "pymupdf4llm",
            "-l", "markitdown",
            "--format", "markdown",
            "--output", str(batch_compare_dir),
            "--max-files", "2"
        ])
        
        passed = exit_code == 0 and batch_compare_dir.exists()
        report_file = batch_compare_dir / "batch_comparison_report.json" if batch_compare_dir.exists() else None
        
        if passed and report_file and report_file.exists():
            try:
                with open(report_file) as f:
                    report = json.load(f)
                print(f"✓ PASSED: Batch-compare completed successfully")
            except json.JSONDecodeError:
                print(f"✓ PASSED: Batch-compare completed but report invalid")
        else:
            print(f"✗ FAILED: Exit code={exit_code}")
            if stderr:
                print(f"  stderr: {stderr[:200]}")
        
        self.results["tests"].append({
            "name": "batch_compare",
            "passed": passed,
            "command": "pdfstract batch-compare -l pymupdf4llm -l markitdown"
        })
        
        return passed
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("PDFStract CLI Test Suite")
        print("=" * 70)
        
        self.setup()
        
        tests = [
            self.test_help,
            self.test_libs,
            self.test_convert_single,
            self.test_convert_all_libraries,
            self.test_convert_json,
            self.test_compare,
            self.test_batch,
            self.test_batch_compare,
        ]
        
        for test in tests:
            try:
                self.results["total_tests"] += 1
                if test():
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                self.results["failed"] += 1
        
        self.print_summary()
        self.cleanup()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        passed = self.results["passed"]
        total = self.results["total_tests"]
        failed = self.results["failed"]
        
        print(f"\n✓ Passed: {passed}/{total}")
        print(f"✗ Failed: {failed}/{total}")
        
        if failed == 0:
            print(f"\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
        
        print("\nDetailed Results:")
        for test in self.results["tests"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            print(f"  {status}: {test['name']} - {test['command']}")
        
        print("\n" + "=" * 70)
        
        # Exit with appropriate code
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    tester = CLITester()
    tester.run_all_tests()

