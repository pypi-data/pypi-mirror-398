from rich.console import Console

console = Console()

#Замена принту

def info(msg: str):
    console.print(f"[cyan]ℹ {msg}[/cyan]")

def success(msg: str):
    console.print(f"[green]✔ {msg}[/green]")

def warning(msg: str):
    console.print(f"[yellow]⚠ {msg}[/yellow]")

def error(msg: str):
    console.print(f"[red]✖ {msg}[/red]")

def hint(msg: str):
    console.print(f"[white]? {msg}[/white] ")