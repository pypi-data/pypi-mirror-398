import subprocess
import os
import threading
import sys
import time
from pathlib import Path
from collections import deque
from typing import List, Dict, Any, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID
from rich.table import Table
from rich.live import Live
from .core import Project

console = Console()

def run_project_command_tail(project_path: Path, command: str, tail_lines: int = 50, timeout: int = 600) -> Dict[str, Any]:
    """
    Runs a command and only keeps the last N lines of output to prevent memory/buffer overflow.
    """
    output_tail = deque(maxlen=tail_lines)
    
    try:
        process = subprocess.Popen(
            command,
            cwd=project_path,
            shell=isinstance(command, str),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_tail.append(line.strip())
        
        returncode = process.poll()
        return {
            "returncode": returncode,
            "stdout": "\n".join(output_tail),
            "stderr": ""
        }
        
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": f"Error: {str(e)}",
            "stderr": ""
        }

def run_project_command(project_path: Path, command: str, capture_output: bool = False) -> bool:
    """
    Backward compatibility wrapper.
    """
    res = run_project_command_tail(project_path, command, tail_lines=50 if capture_output else 1000)
    return res["returncode"] == 0

def execute_in_parallel(
    projects: List[Project],
    command_provider: Callable[[Project], List[str]],
    max_workers: Optional[int] = None,
    fail_fast: bool = False,
    cwd: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Parallel executor with live status table and crash protection.
    """
    project_map = {p.name: p for p in projects}
    deps = {p.name: [d for d in p.dependencies if d in project_map] for p in projects}
    
    submitted: Set[str] = set()
    completed: Set[str] = set()
    failed: Set[str] = set()
    results: List[Dict[str, Any]] = []
    results_lock = threading.Lock()
    
    if max_workers is None:
        max_workers = os.cpu_count() or 4

    def get_status_table():
        table = Table(title="Parallel Execution Status", box=None, expand=True)
        table.add_column("Project", style="cyan")
        table.add_column("Status", justify="center")
        
        with results_lock:
            for p in projects:
                if p.name in failed:
                    status = "[bold red]FAILED[/bold red]"
                elif p.name in completed:
                    status = "[bold green]FINISHED[/bold green]"
                elif p.name in submitted:
                    status = "[bold yellow]RUNNING[/bold yellow]"
                else:
                    status = "[dim]Pending[/dim]"
                table.add_row(p.name, status)
        return table

    def run_task(project: Project):
        cmd = command_provider(project)
        task_cwd = cwd or project.path
        res_data = run_project_command_tail(task_cwd, cmd, tail_lines=50)
        
        with results_lock:
            success = (res_data["returncode"] == 0)
            results.append({
                "name": project.name,
                "success": success,
                "path": project.path,
                "stdout": res_data["stdout"],
                "stderr": res_data["stderr"],
                "returncode": res_data["returncode"]
            })
            if success:
                completed.add(project.name)
            else:
                failed.add(project.name)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
    overall_task = progress.add_task("[bold blue]Progress", total=len(projects))

    # Live display shows the progress bar and the summary table
    with Live(get_status_table(), console=console, refresh_per_second=4) as live:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            running_futures = {}
            
            while len(completed | failed) < len(projects):
                if fail_fast and failed:
                    break
                
                with results_lock:
                    ready = [
                        p for p in projects 
                        if p.name not in submitted 
                        and all(d in (completed | failed) for d in deps[p.name])
                    ]
                    
                    if not ready and not running_futures and len(submitted) < len(projects):
                        blocked = [p for p in projects if p.name not in submitted]
                        if blocked: ready = [blocked[0]]
                    
                    slots_available = max_workers - len(running_futures)
                    for p in ready[:slots_available]:
                        submitted.add(p.name)
                        future = executor.submit(run_task, p)
                        running_futures[future] = p

                # Update live display
                live.update(get_status_table())

                if running_futures:
                    done, _ = wait(running_futures.keys(), timeout=0.2, return_when=FIRST_COMPLETED)
                    for f in done:
                        running_futures.pop(f)
                        progress.advance(overall_task)
                else:
                    time.sleep(0.1)
                    
        live.update(get_status_table())

    return results
