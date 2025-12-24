#!/usr/bin/env python3
"""
PDFStract CLI - Command-line interface for PDF extraction and conversion
Provides: single conversions, multi-library comparisons, batch processing
"""

import click
import json
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import csv
import sys

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from services.cli_factory import CLILazyFactory
from services.base import OutputFormat
from services.logger import logger

# Rich console for beautiful output
console = Console()

# Factory (lazy initialized - uses lightweight CLILazyFactory)
_factory = None

def get_factory():
    """Get factory instance (lazy initialization to speed up CLI startup)"""
    global _factory
    if _factory is None:
        _factory = CLILazyFactory()
    return _factory


class PDFStractCLI:
    """Main CLI class handling all operations"""
    
    def __init__(self, lazy=True):
        self.console = console
        self._lazy = lazy
        self._factory = None
    
    @property
    def factory(self):
        """Get factory with lazy loading"""
        if self._factory is None:
            if not self._lazy:
                # Eager load for help/libs commands
                self._factory = get_factory()
            else:
                # For action commands, factory is initialized on first use
                self._factory = get_factory()
        return self._factory
    
    def print_banner(self):
        """Print CLI banner"""
        banner = """
[bold cyan]╔════════════════════════════════════════╗[/bold cyan]
[bold cyan]║         PDFStract CLI v1.0             ║[/bold cyan]
[bold cyan]║      PDF Extraction & Conversion       ║[/bold cyan]
[bold cyan]╚════════════════════════════════════════╝[/bold cyan]
        """
        self.console.print(banner)
    
    def print_success(self, msg: str):
        """Print success message"""
        self.console.print(f"[bold green]✓[/bold green] {msg}")
    
    def print_error(self, msg: str):
        """Print error message"""
        self.console.print(f"[bold red]✗[/bold red] {msg}")
    
    def print_warning(self, msg: str):
        """Print warning message"""
        self.console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
    
    def print_info(self, msg: str):
        """Print info message"""
        self.console.print(f"[bold blue]ℹ[/bold blue] {msg}")
    
    def get_available_libraries(self) -> Dict:
        """Get all available libraries and their status"""
        return self.factory.list_all_converters()
    
    def get_available_formats(self) -> List[str]:
        """Get available output formats"""
        return [f.value for f in OutputFormat]


# Create CLI instance with lazy loading (don't load libraries until needed)
cli_app = PDFStractCLI(lazy=True)


@click.group()
def pdfstract():
    """PDFStract - Unified PDF Extraction CLI Tool
    
    Convert PDFs using 10+ extraction libraries with single/batch/compare modes.
    """
    pass


@pdfstract.command()
def libs():
    """List all available extraction libraries and their status"""
    cli_app.print_banner()
    
    # Initialize factory ONLY when listing libraries
    libraries = get_factory().list_all_converters()
    
    table = Table(title="Available PDF Extraction Libraries", show_lines=True)
    table.add_column("Library", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Error/Notes", style="yellow")
    
    for lib in libraries:
        status = "[bold green]✓ Available[/bold green]" if lib["available"] else "[bold red]✗ Unavailable[/bold red]"
        error = lib.get("error", "N/A") or "Ready to use"
        table.add_row(lib["name"], status, error if not lib["available"] else "")
    
    console.print(table)
    console.print()
    console.print("[dim]Use 'pdfstract convert --help' to get started[/dim]")


@pdfstract.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--library', '-l', required=True, help='Extraction library to use')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), 
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path (optional, auto-generates if not specified)')
def convert(input_file: Path, library: str, format: str, output: Optional[str]):
    """Convert a single PDF file
    
    Without --output: Creates file with same name as input PDF (e.g., sample.pdf → sample.md)
    
    Examples:
        pdfstract convert sample.pdf --library unstructured
        pdfstract convert sample.pdf --library unstructured --format markdown --output result.md
    """
    cli_app.print_banner()
    
    # Validate inputs
    if not input_file.exists():
        cli_app.print_error(f"File not found: {input_file}")
        sys.exit(1)
    
    if not input_file.suffix.lower() == '.pdf':
        cli_app.print_error("Only PDF files are supported")
        sys.exit(1)
    
    # Get converter (lazy load factory only when needed)
    converter = get_factory().get_converter(library)
    if not converter:
        available = [lib["name"] for lib in cli_app.get_available_libraries() if lib["available"]]
        cli_app.print_error(f"Library '{library}' not available")
        cli_app.print_info(f"Available: {', '.join(available)}")
        sys.exit(1)
    
    cli_app.print_info(f"Converting: {input_file.name}")
    cli_app.print_info(f"Library: {library} | Format: {format}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Converting...", total=None)
            
            # Run conversion
            output_format = OutputFormat(format)
            result = get_factory().convert(
                converter_name=library,
                file_path=str(input_file),
                output_format=output_format
            )
            
            progress.stop()
        
        cli_app.print_success(f"Conversion completed successfully")
        
        # Handle output
        if output:
            output_path = Path(output)
        else:
            # Auto-generate output filename if not specified
            ext = 'json' if format == 'json' else 'md' if format == 'markdown' else 'txt'
            output_path = Path(input_file.stem + '.' + ext)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json' and isinstance(result, dict):
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            with open(output_path, 'w') as f:
                f.write(str(result))
        
        cli_app.print_success(f"Output saved to: {output_path.absolute()}")
        
    except Exception as e:
        cli_app.print_error(f"Conversion failed: {str(e)}")
        logger.exception("Full error traceback:")
        sys.exit(1)


@pdfstract.command()
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--libraries', '-l', multiple=True, required=True, 
              help='Libraries to compare (can specify multiple times)')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), 
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output directory for results')
def compare(input_file: Path, libraries: tuple, format: str, output: str):
    """Compare multiple extraction libraries on a single PDF
    
    Example: pdfstract compare sample.pdf -l unstructured -l marker -l docling --format markdown --output ./results
    """
    cli_app.print_banner()
    
    if not input_file.exists():
        cli_app.print_error(f"File not found: {input_file}")
        sys.exit(1)
    
    if not input_file.suffix.lower() == '.pdf':
        cli_app.print_error("Only PDF files are supported")
        sys.exit(1)
    
    if not libraries or len(libraries) < 2:
        cli_app.print_error("Please specify at least 2 libraries to compare")
        sys.exit(1)
    
    if len(libraries) > 5:
        cli_app.print_warning(f"Limiting to 5 libraries (you specified {len(libraries)})")
        libraries = libraries[:5]
    
    # Validate libraries
    available_libs = get_factory().list_available_converters()
    for lib in libraries:
        if lib not in available_libs:
            cli_app.print_error(f"Library '{lib}' not available")
            sys.exit(1)
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cli_app.print_info(f"Comparing {len(libraries)} libraries on: {input_file.name}")
    cli_app.print_info(f"Libraries: {', '.join(libraries)}")
    cli_app.print_info(f"Format: {format}")
    
    results = {}
    output_format = OutputFormat(format)
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Converting...", total=len(libraries))
        
        for lib in libraries:
            progress.update(task, description=f"Processing {lib}...")
            
            try:
                result = get_factory().convert(
                    converter_name=lib,
                    file_path=str(input_file),
                    output_format=output_format
                )
                
                # Save result
                ext = 'json' if format == 'json' else 'md' if format == 'markdown' else 'txt'
                result_file = output_dir / f"{lib}_result.{ext}"
                
                if format == 'json' and isinstance(result, dict):
                    with open(result_file, 'w') as f:
                        json.dump(result, f, indent=2)
                else:
                    with open(result_file, 'w') as f:
                        f.write(str(result))
                
                results[lib] = {
                    "status": "success",
                    "file": str(result_file),
                    "size_bytes": result_file.stat().st_size
                }
                
            except Exception as e:
                results[lib] = {
                    "status": "failed",
                    "error": str(e)
                }
            
            progress.advance(task)
    
    # Save comparison summary
    summary_file = output_dir / "comparison_summary.json"
    summary = {
        "input_file": input_file.name,
        "format": format,
        "timestamp": datetime.now().isoformat(),
        "libraries": libraries,
        "results": results
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print results
    table = Table(title="Comparison Results", show_lines=True)
    table.add_column("Library", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Output Size", style="yellow")
    table.add_column("Details", style="dim")
    
    for lib, result in results.items():
        status_text = "[bold green]✓ Success[/bold green]" if result["status"] == "success" else "[bold red]✗ Failed[/bold red]"
        size_text = f"{result.get('size_bytes', 0) / 1024:.1f} KB" if result["status"] == "success" else "N/A"
        details = result.get("error", "")
        table.add_row(lib, status_text, size_text, details)
    
    console.print(table)
    cli_app.print_success(f"Comparison complete! Results saved to: {output_dir.absolute()}")
    cli_app.print_info(f"Summary: {summary_file}")


@pdfstract.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--library', '-l', required=True, help='Extraction library to use')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), 
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output directory for converted files')
@click.option('--parallel', '-p', type=int, default=2, 
              help='Number of parallel workers')
@click.option('--pattern', type=str, default='*.pdf',
              help='File pattern to match (e.g., "*.pdf" or "invoice_*.pdf")')
@click.option('--skip-errors', is_flag=True, help='Skip PDFs that fail conversion')
def batch(input_dir: Path, library: str, format: str, output: str, parallel: int, pattern: str, skip_errors: bool):
    """Batch convert all PDFs in a directory
    
    Example: pdfstract batch ./pdfs --library unstructured --format markdown --output ./converted --parallel 4
    """
    cli_app.print_banner()
    
    if not input_dir.is_dir():
        cli_app.print_error(f"Directory not found: {input_dir}")
        sys.exit(1)
    
    # Find PDFs
    pdf_files = sorted(input_dir.glob(pattern))
    pdf_files = [f for f in pdf_files if f.suffix.lower() == '.pdf']
    
    if not pdf_files:
        cli_app.print_warning(f"No PDF files found matching pattern '{pattern}'")
        sys.exit(0)
    
    cli_app.print_info(f"Found {len(pdf_files)} PDF files to convert")
    cli_app.print_info(f"Library: {library} | Format: {format} | Workers: {parallel}")
    
    # Validate library
    converter = cli_app.factory.get_converter(library)
    if not converter:
        available = [lib["name"] for lib in cli_app.get_available_libraries() if lib["available"]]
        cli_app.print_error(f"Library '{library}' not available")
        cli_app.print_info(f"Available: {', '.join(available)}")
        sys.exit(1)
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track results
    results = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "files": {}
    }
    
    output_format = OutputFormat(format)
    
    def convert_single_pdf(pdf_file: Path) -> tuple:
        """Convert a single PDF - for parallel execution"""
        try:
            result = get_factory().convert(
                converter_name=library,
                file_path=str(pdf_file),
                output_format=output_format
            )
            
            # Save result
            ext = 'json' if format == 'json' else 'md' if format == 'markdown' else 'txt'
            output_file = output_dir / f"{pdf_file.stem}.{ext}"
            
            if format == 'json' and isinstance(result, dict):
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                with open(output_file, 'w') as f:
                    f.write(str(result))
            
            return (pdf_file.name, "success", None, output_file.stat().st_size)
        
        except Exception as e:
            error_msg = str(e)
            if skip_errors:
                return (pdf_file.name, "skipped", error_msg, 0)
            else:
                return (pdf_file.name, "failed", error_msg, 0)
    
    # Run parallel conversion
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Converting...", total=len(pdf_files))
        
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [executor.submit(convert_single_pdf, pdf) for pdf in pdf_files]
            
            for future in futures:
                filename, status, error, size = future.result()
                results["files"][filename] = {
                    "status": status,
                    "error": error,
                    "size_bytes": size
                }
                
                if status == "success":
                    results["success"] += 1
                elif status == "failed":
                    results["failed"] += 1
                else:
                    results["skipped"] += 1
                
                progress.advance(task)
    
    # Save batch report
    report_file = output_dir / "batch_report.json"
    report = {
        "input_directory": str(input_dir.absolute()),
        "output_directory": str(output_dir.absolute()),
        "library": library,
        "format": format,
        "timestamp": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "statistics": {
            "success": results["success"],
            "failed": results["failed"],
            "skipped": results["skipped"]
        },
        "files": results["files"]
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary table
    table = Table(title="Batch Conversion Summary", show_lines=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Total Files", str(len(pdf_files)))
    table.add_row("[bold green]✓ Successful[/bold green]", f"[bold green]{results['success']}[/bold green]")
    table.add_row("[bold red]✗ Failed[/bold red]", f"[bold red]{results['failed']}[/bold red]")
    table.add_row("[bold yellow]⊝ Skipped[/bold yellow]", f"[bold yellow]{results['skipped']}[/bold yellow]")
    table.add_row("Success Rate", f"{(results['success'] / len(pdf_files) * 100):.1f}%")
    
    console.print(table)
    cli_app.print_success(f"Batch conversion complete!")
    cli_app.print_info(f"Output directory: {output_dir.absolute()}")
    cli_app.print_info(f"Report: {report_file}")
    
    # Exit with error if there were failures and not skipping
    if results["failed"] > 0 and not skip_errors:
        sys.exit(1)


@pdfstract.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--libraries', '-l', multiple=True, required=True,
              help='Libraries to compare (can specify multiple times)')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']),
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output directory for results')
@click.option('--max-files', type=int, default=None,
              help='Limit number of files to process')
def batch_compare(input_dir: Path, libraries: tuple, format: str, output: str, max_files: Optional[int]):
    """Compare multiple libraries on all PDFs in a directory
    
    Generates comparative analysis of extraction quality across multiple libraries.
    
    Example: pdfstract batch-compare ./pdfs -l unstructured -l marker -l docling --output ./comparison
    """
    cli_app.print_banner()
    
    # Find PDFs
    pdf_files = sorted(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        cli_app.print_warning(f"No PDF files found in {input_dir}")
        sys.exit(0)
    
    if max_files:
        pdf_files = pdf_files[:max_files]
        cli_app.print_info(f"Processing first {max_files} files")
    
    cli_app.print_info(f"Found {len(pdf_files)} PDF files")
    cli_app.print_info(f"Libraries: {', '.join(libraries)}")
    
    # Validate libraries
    available_libs = get_factory().list_available_converters()
    for lib in libraries:
        if lib not in available_libs:
            cli_app.print_error(f"Library '{lib}' not available")
            sys.exit(1)
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_format = OutputFormat(format)
    comparison_results = {}
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        file_task = progress.add_task("Processing files...", total=len(pdf_files))
        
        for pdf_file in pdf_files:
            progress.update(file_task, description=f"Processing {pdf_file.name}...")
            file_results = {}
            
            for lib in libraries:
                try:
                    result = get_factory().convert(
                        converter_name=lib,
                        file_path=str(pdf_file),
                        output_format=output_format
                    )
                    
                    file_results[lib] = {
                        "status": "success",
                        "size_bytes": len(str(result).encode())
                    }
                
                except Exception as e:
                    file_results[lib] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            comparison_results[pdf_file.name] = file_results
            progress.advance(file_task)
    
    # Save comparison report
    report_file = output_dir / "batch_comparison_report.json"
    report = {
        "input_directory": str(input_dir.absolute()),
        "libraries": list(libraries),
        "format": format,
        "timestamp": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "results": comparison_results
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    cli_app.print_success(f"Batch comparison complete!")
    cli_app.print_info(f"Report: {report_file}")
    
    # Calculate success rates
    table = Table(title="Batch Comparison Summary", show_lines=True)
    table.add_column("Library", style="cyan")
    table.add_column("Success Rate", style="green")
    table.add_column("Avg Size (KB)", style="yellow")
    
    for lib in libraries:
        successes = sum(
            1 for file_results in comparison_results.values()
            if file_results.get(lib, {}).get("status") == "success"
        )
        success_rate = (successes / len(pdf_files) * 100) if pdf_files else 0
        
        avg_size = 0
        if successes > 0:
            total_size = sum(
                file_results.get(lib, {}).get("size_bytes", 0)
                for file_results in comparison_results.values()
                if file_results.get(lib, {}).get("status") == "success"
            )
            avg_size = total_size / successes / 1024
        
        table.add_row(lib, f"{success_rate:.1f}%", f"{avg_size:.1f}")
    
    console.print(table)


if __name__ == '__main__':
    pdfstract()

