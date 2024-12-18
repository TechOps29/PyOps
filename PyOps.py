import os
import sys
import psutil
import logging
from rich.console import Console
from rich.table import Table
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko
from celery import Celery
import time
import subprocess


# Setup logging
logger = logging.getLogger("PyOps")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Rich Console for rich text output
console = Console()

# Initialize Celery for background task processing
app = Celery('pyops', broker='redis://localhost:6379/0')

# Task Queue (Celery)
@app.task
def example_background_task():
    logger.info("Executing background task...")
    time.sleep(2)
    logger.info("Background task completed!")

# Monitor system processes with psutil
def monitor_system_processes():
    console.print("[bold cyan]System Processes Monitor[/bold cyan]", style="bold yellow")
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            console.print(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, Status: {proc.info['status']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# Cross-platform file system monitoring using watchdog
class FileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        console.print(f"[bold green]File modified:[/bold green] {event.src_path}")

    def on_created(self, event):
        if event.is_directory:
            return
        console.print(f"[bold blue]File created:[/bold blue] {event.src_path}")

def monitor_file_system(path_to_watch):
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    console.print(f"Started monitoring file system at: [bold cyan]{path_to_watch}[/bold cyan]")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Remote SSH Automation with Paramiko
def remote_ssh_task(host, port, username, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        console.print(f"[bold green]Command Output:[/bold green]\n{output}")
        if error:
            console.print(f"[bold red]Error:[/bold red]\n{error}")
        client.close()
    except Exception as e:
        console.print(f"[bold red]SSH Error:[/bold red] {e}")

# Print system resource usage
def print_system_usage():
    console.print("[bold magenta]System Resource Usage[/bold magenta]")
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    console.print(f"CPU Usage: {cpu_usage}%")
    console.print(f"Memory Usage: {memory_info.percent}% of {memory_info.total / (1024 ** 3):.2f} GB")
    console.print(f"Disk Usage: {disk_usage.percent}% of {disk_usage.total / (1024 ** 3):.2f} GB")

# Table displaying system processes
def display_process_table():
    table = Table(title="System Processes")
    table.add_column("PID", justify="right")
    table.add_column("Name")
    table.add_column("Status")

    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            table.add_row(str(proc.info['pid']), proc.info['name'], proc.info['status'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    console.print(table)

# Main execution function
def main():
    console.print("[bold yellow]Welcome to PyOps - Python System Management Tool[/bold yellow]")
    
    # Check command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor-processes":
            monitor_system_processes()
        elif sys.argv[1] == "--monitor-filesystem":
            if len(sys.argv) > 2:
                monitor_file_system(sys.argv[2])
            else:
                console.print("[bold red]Please provide a path to monitor![/bold red]")
        elif sys.argv[1] == "--remote-ssh":
            if len(sys.argv) > 5:
                remote_ssh_task(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6])
            else:
                console.print("[bold red]Please provide all required SSH details![/bold red]")
        elif sys.argv[1] == "--background-task":
            example_background_task.apply_async()
        elif sys.argv[1] == "--system-usage":
            print_system_usage()
        elif sys.argv[1] == "--process-table":
            display_process_table()
        else:
            console.print("[bold red]Unknown command! Use --help for usage information.[/bold red]")
    else:
        console.print("[bold green]Available Commands[/bold green]")
        console.print("[bold cyan]--monitor-processes[/bold cyan] - Monitor system processes")
        console.print("[bold cyan]--monitor-filesystem <path>[/bold cyan] - Monitor file system changes at specified path")
        console.print("[bold cyan]--remote-ssh <host> <port> <username> <password> <command>[/bold cyan] - Run a remote SSH command")
        console.print("[bold cyan]--background-task[/bold cyan] - Run a background task with Celery")
        console.print("[bold cyan]--system-usage[/bold cyan] - Display system resource usage")
        console.print("[bold cyan]--process-table[/bold cyan] - Display system processes in a table")

if __name__ == "__main__":
    main()
