#!/usr/bin/env python3
"""
PDFStract Batch Job Scheduler
Utility for scheduling and managing batch processing jobs
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.table import Table

console = Console()


class BatchJobManager:
    """Manages batch processing jobs"""
    
    def __init__(self, jobs_dir: str = "./batch_jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(exist_ok=True)
    
    def create_job_config(
        self,
        job_name: str,
        input_dir: str,
        output_dir: str,
        library: str,
        format: str = "markdown",
        parallel: int = 4,
        skip_errors: bool = False,
        description: str = ""
    ) -> Path:
        """Create a batch job configuration"""
        
        config = {
            "name": job_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "input_directory": input_dir,
            "output_directory": output_dir,
            "library": library,
            "format": format,
            "parallel_workers": parallel,
            "skip_errors": skip_errors
        }
        
        job_file = self.jobs_dir / f"{job_name}.json"
        with open(job_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✓[/green] Job config created: {job_file}")
        return job_file
    
    def run_job(self, job_name: str) -> int:
        """Execute a batch job"""
        
        job_file = self.jobs_dir / f"{job_name}.json"
        if not job_file.exists():
            console.print(f"[red]✗[/red] Job not found: {job_name}")
            return 1
        
        with open(job_file) as f:
            config = json.load(f)
        
        console.print(f"[cyan]Running job: {config['name']}[/cyan]")
        console.print(f"[dim]{config.get('description', '')}[/dim]")
        
        cmd = [
            "pdfstract", "batch",
            config["input_directory"],
            "--library", config["library"],
            "--format", config["format"],
            "--output", config["output_directory"],
            "--parallel", str(config["parallel_workers"])
        ]
        
        if config.get("skip_errors"):
            cmd.append("--skip-errors")
        
        # Run conversion
        result = subprocess.run(cmd)
        
        # Log job execution
        log_entry = {
            "job_name": job_name,
            "executed_at": datetime.now().isoformat(),
            "exit_code": result.returncode,
            "status": "success" if result.returncode == 0 else "failed"
        }
        
        log_file = self.jobs_dir / f"{job_name}_log.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return result.returncode
    
    def list_jobs(self) -> List[Dict]:
        """List all configured jobs"""
        
        jobs = []
        for job_file in self.jobs_dir.glob("*.json"):
            if "_log" not in job_file.name:
                with open(job_file) as f:
                    config = json.load(f)
                jobs.append(config)
        
        return sorted(jobs, key=lambda x: x.get("created_at", ""))
    
    def view_job_history(self, job_name: str) -> Optional[List[Dict]]:
        """View execution history for a job"""
        
        log_file = self.jobs_dir / f"{job_name}_log.jsonl"
        if not log_file.exists():
            return None
        
        history = []
        with open(log_file) as f:
            for line in f:
                history.append(json.loads(line))
        
        return history


@click.group()
def batch_scheduler():
    """Batch job scheduler for PDFStract"""
    pass


@batch_scheduler.command()
@click.argument('job_name')
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('output_dir', type=click.Path())
@click.option('--library', '-l', required=True, help='Extraction library')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), 
              default='markdown')
@click.option('--parallel', '-p', type=int, default=4)
@click.option('--skip-errors', is_flag=True)
@click.option('--description', '-d', default='')
def create(job_name, input_dir, output_dir, library, format, parallel, skip_errors, description):
    """Create a batch job configuration"""
    
    manager = BatchJobManager()
    manager.create_job_config(
        job_name=job_name,
        input_dir=input_dir,
        output_dir=output_dir,
        library=library,
        format=format,
        parallel=parallel,
        skip_errors=skip_errors,
        description=description
    )


@batch_scheduler.command()
@click.argument('job_name')
def run(job_name):
    """Run a scheduled batch job"""
    
    manager = BatchJobManager()
    exit_code = manager.run_job(job_name)
    sys.exit(exit_code)


@batch_scheduler.command()
def list():
    """List all configured batch jobs"""
    
    manager = BatchJobManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        console.print("[yellow]No jobs configured[/yellow]")
        return
    
    table = Table(title="Configured Batch Jobs", show_lines=True)
    table.add_column("Job Name", style="cyan")
    table.add_column("Library", style="green")
    table.add_column("Input", style="yellow")
    table.add_column("Workers", style="magenta")
    table.add_column("Created", style="dim")
    
    for job in jobs:
        created = datetime.fromisoformat(job["created_at"]).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            job["name"],
            job["library"],
            Path(job["input_directory"]).name,
            str(job["parallel_workers"]),
            created
        )
    
    console.print(table)


@batch_scheduler.command()
@click.argument('job_name')
def history(job_name):
    """View execution history for a job"""
    
    manager = BatchJobManager()
    logs = manager.view_job_history(job_name)
    
    if not logs:
        console.print(f"[yellow]No execution history for job: {job_name}[/yellow]")
        return
    
    table = Table(title=f"Execution History: {job_name}", show_lines=True)
    table.add_column("Executed", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Exit Code", style="yellow")
    
    for log in logs:
        executed = datetime.fromisoformat(log["executed_at"]).strftime("%Y-%m-%d %H:%M:%S")
        status = "[bold green]✓ Success[/bold green]" if log["status"] == "success" else "[bold red]✗ Failed[/bold red]"
        table.add_row(
            executed,
            status,
            str(log["exit_code"])
        )
    
    console.print(table)


if __name__ == '__main__':
    batch_scheduler()

