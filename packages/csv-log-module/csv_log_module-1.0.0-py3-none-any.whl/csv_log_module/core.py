import pandas as pd
from pathlib import Path
import warnings
import inspect
from tabulate import tabulate

import subprocess
import sys

##def ensure_rich():
##    try:
##        from rich import print as rprint  # noqa: F401
##        from rich.table import Table  # noqa: F401
##    except ImportError:
##        print("rich library not found. Installing automatically...")
##        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
##        print("rich installed successfully! Restart or re-run the script.")
##
##ensure_rich()
from rich.table import Table
from rich import print as rprint
from rich.console import Console
from rich.box import SQUARE  # Import the minimal box style


CSV_LOG_FILE = "csv_log.csv"
TXT_LOG_FILE = "csv_log.txt"  # The human-readable version






def _get_caller_directory():
    """
    Returns the directory of the script that called log_line or show_log_abs_path.
    This makes the log file location relative to the tester script, not the current working directory.
    """
    # Get the frame of the caller (outside this module)
    frame = inspect.stack()[-1]
    caller_path = Path(frame.filename)
    return caller_path.parent.resolve()

def _get_csv_path(directory: str | None = None) -> Path:
    """Resolve the CSV path. If directory is None, use the caller's script directory."""
    if directory is None:
        dir_path = _get_caller_directory()
    else:
        dir_path = Path(directory).resolve()
    
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / CSV_LOG_FILE

def log_line(person_name: str, score, directory: str | None = None):
    """
    Logs a score for a person. By default, saves csv_log.csv in the same folder as the calling script.
    
    Args:
        person_name (str): Column name (person's name)
        score: Value to log
        directory (str | None): Optional explicit directory. If None, uses caller's script directory.
    """
    csv_path = _get_csv_path(directory)
    
    # Load or create DataFrame
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()
    
    # Ensure column exists
    if person_name not in df.columns:
        df[person_name] = pd.NA
    
    # New row
    new_row = pd.DataFrame([{col: pd.NA for col in df.columns}])
    new_row[person_name] = score
    
    # Append
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        df = pd.concat([df, new_row], ignore_index=True)
    
    # Save
    df.to_csv(csv_path, index=False)
    print(f"Logged '{score}' into column '{person_name}' in\n  {csv_path}")

def show_log_abs_path(directory: str | None = None):
    """
    Shows the absolute path of the log file.
    By default, uses the same logic as log_line (caller's script directory).
    """
    csv_path = _get_csv_path(directory)
    print(f"Log file absolute path:\n  {csv_path}")
    print(f"Directory: {csv_path.parent}")
console = Console()  # Global console for rich output




from rich.console import Console

console = Console(record=True)  # Important: record=True enables export/capture

def view_log(directory: str | None = None, print_to_console: bool = True):
    """
    Displays a beautiful, colorful table using rich.
    Also saves a clean text version to csv_log.txt.
    """
    csv_path = _get_csv_path(directory)
    txt_path = csv_path.with_name(TXT_LOG_FILE)
    
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        message = f"[bold red]No log data found[/bold red]\nLocation: {csv_path}"
        if print_to_console:
            rprint(message)
        txt_path.write_text("No log data found.", encoding="utf-8")
        return
    
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame()
    
    if df.empty:
        message = "[yellow]Log is empty.[/yellow]"
        if print_to_console:
            rprint(message)
        txt_path.write_text("Log is empty.", encoding="utf-8")
        return
    
    # Replace NaN with empty string
    df_display = df.fillna("")
        

    # Create rich table
    table = Table(
        title="Score Log Viewer",
        box=SQUARE,
        show_header=True,
        header_style="bold magenta",
        title_style="bold green",
        pad_edge=False,
    )

    table.add_column("Row", style="dim", width=6, justify="right")

    for col in df_display.columns:
        table.add_column(col, justify="center", style="cyan")

    # Add rows — with "—" for empty cells
    if df_display.empty:
        # Show one placeholder row if completely empty
        table.add_row("—", *["—" for _ in df_display.columns])
    else:
        for idx, row in df_display.iterrows():
            row_data = [str(val) if val != "" else "—" for val in row]
            table.add_row(str(idx + 1), *row_data)
    # === CORRECT WAY: Capture the rendered table for plain text ===
    console.clear()  # Clear previous capture
    console.print(table, end="")  # Render to buffer without printing yet
    
    # Export as plain text (no colors/markup)
    plain_text = console.export_text()
    
    # Save to .txt file
    txt_path.write_text(plain_text, encoding="utf-8")
    
    # Now actually print the beautiful colored version
    if print_to_console:
        rprint("\n" + "="*80)
        rprint("[bold green]                  SCORE LOG VIEWER[/bold green]")
        rprint("="*80)
        console.print(table)  # This shows colors and proper borders
        rprint("="*80)
        rprint(f"[bold blue]Saved pretty text version to:[/bold blue] {txt_path}")
        rprint("="*80 + "\n")








