import pandas as pd
import os
import csv
import requests
from io import StringIO
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Initialize Rich Console (The engine for beautiful output)
console = Console()

def smart_read(path, sheet_name=0, dropna=False, fillna=None):
    """
    Goated CSV/Excel Reader with:
    - dashboard-style output (Rich)
    - specific Excel sheet selection
    - auto-delimiter detection
    - smart type summarization
    """
    console.print(f"\n[bold cyan]⚡ EssentiaX Loading:[/bold cyan] [underline]{path}[/underline]")

    try:
        df = None
        file_stats = {} # Store metadata for the report

        # ---------------------------------------------------------
        # 1. URL HANDLING
        # ---------------------------------------------------------
        if path.startswith(("http://", "https://")):
            with console.status("[bold green]Fetching data from URL...[/bold green]", spinner="dots"):
                response = requests.get(path)
                if response.status_code != 200:
                    console.print(f"[bold red]❌ URL Error:[/bold red] Status {response.status_code}")
                    return None
                data = StringIO(response.text)
                
                # Try CSV first, then Excel
                try:
                    df = pd.read_csv(data)
                    file_stats['Source'] = "URL (CSV)"
                except:
                    df = pd.read_excel(data, sheet_name=sheet_name)
                    file_stats['Source'] = "URL (Excel)"

        # ---------------------------------------------------------
        # 2. LOCAL FILE HANDLING
        # ---------------------------------------------------------
        else:
            if not os.path.exists(path):
                console.print(f"[bold red]❌ File Not Found:[/bold red] {path}")
                return None

            ext = os.path.splitext(path)[1].lower()
            file_stats['Size'] = f"{os.path.getsize(path) / 1024:.2f} KB"

            # --- CSV ---
            if ext == ".csv":
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(2048)
                    sniffer = csv.Sniffer()
                    try:
                        delimiter = sniffer.sniff(sample).delimiter
                    except:
                        delimiter = ',' # Fallback
                
                df = pd.read_csv(path, delimiter=delimiter)
                file_stats['Type'] = "CSV"
                file_stats['Delimiter'] = f"'{delimiter}'"

            # --- EXCEL ---
            elif ext in [".xls", ".xlsx"]:
                # Check sheets first
                xl = pd.ExcelFile(path)
                sheet_names = xl.sheet_names
                
                # If user didn't pick a specific name and there are multiple, warn them
                if len(sheet_names) > 1 and sheet_name == 0:
                    console.print(f"[yellow]ℹ Note: Multiple sheets found: {sheet_names}. Loading first one.[/yellow]")
                
                df = pd.read_excel(path, sheet_name=sheet_name)
                file_stats['Type'] = "Excel"
                file_stats['Sheet'] = str(sheet_name) if sheet_name else sheet_names[0]

            else:
                console.print("[bold red]❌ Unsupported file format.[/bold red]")
                return None

        # ---------------------------------------------------------
        # 3. PROCESSING (Drop/Fill)
        # ---------------------------------------------------------
        missing_count = df.isnull().sum().sum()
        
        if dropna and missing_count > 0:
            old_shape = df.shape
            df = df.dropna()
            console.print(f"[yellow]🧹 Dropped rows. Shape: {old_shape} -> {df.shape}[/yellow]")
        elif fillna is not None and missing_count > 0:
            df = df.fillna(fillna)
            console.print(f"[yellow]🧹 Filled missing values with '{fillna}'[/yellow]")

        # ---------------------------------------------------------
        # 4. THE "GOATED" DASHBOARD DISPLAY
        # ---------------------------------------------------------
        
        # A. MAIN SUMMARY TABLE
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        
        # Create the main table
        summary_table = Table(title="📊 Dataset Diagnostics", box=box.ROUNDED, show_header=True, header_style="bold white")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="bold green")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="bold green")

        # Calculate memory
        mem_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Add rows (2 metrics per row for compactness)
        summary_table.add_row("Rows", str(df.shape[0]), "Columns", str(df.shape[1]))
        summary_table.add_row("Memory", f"{mem_usage:.2f} MB", "Duplicates", str(df.duplicated().sum()))
        summary_table.add_row("Missing Cells", str(df.isnull().sum().sum()), "Data Types", str(len(df.dtypes.value_counts())))

        console.print(summary_table)

        # B. MISSING VALUES (Only if they exist)
        missing_series = df.isnull().sum()
        missing_series = missing_series[missing_series > 0]
        if not missing_series.empty:
            miss_table = Table(title="⚠ Missing Data Breakdown", box=box.SIMPLE, style="red")
            miss_table.add_column("Column Name", style="yellow")
            miss_table.add_column("Missing Count", style="red")
            miss_table.add_column("Percentage", style="dim")
            
            for col, val in missing_series.items():
                pct = (val / df.shape[0]) * 100
                miss_table.add_row(col, str(val), f"{pct:.1f}%")
            
            console.print(miss_table)

        # C. SMART DATA PREVIEW
        # Convert first 5 rows to a Rich Table
        preview_table = Table(title=f"🔎 First 5 Rows Preview", box=box.MINIMAL_DOUBLE_HEAD)
        
        # Add headers (limited to first 6 columns to prevent screen overflow)
        show_cols = df.columns[:8] 
        for col in show_cols:
            preview_table.add_column(col, overflow="fold")
        
        if len(df.columns) > 8:
            preview_table.add_column("...", style="dim")

        # Add rows
        for index, row in df.head().iterrows():
            row_data = [str(row[col]) if len(str(row[col])) < 50 else str(row[col])[:47]+"..." for col in show_cols]
            if len(df.columns) > 8:
                row_data.append("...")
            preview_table.add_row(*row_data)

        console.print(preview_table)
        print("\n") # Spacing
        
        return df

    except Exception as e:
        console.print(f"[bold red]❌ Critical Error:[/bold red] {e}")
        return None