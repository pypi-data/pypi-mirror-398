import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional
import time

from ..core.image import Image
from ..core.pipeline import Pipeline
from ..core.io import IO
from ..analysis import inspect as analyze_image
from ..utils.data import get_sample as fetch_sample

app = typer.Typer()
console = Console()

@app.command()
def resize(input_path: str, width: int, height: int, output_path: str = "output.jpg"):
    """Resize an image."""
    try:
        img = Image.open(input_path)
        resized = img.resize(width, height)
        resized.save(output_path)
        console.print(f"[green]Successfully resized {input_path} to {width}x{height} and saved to {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@app.command()
def inspect(input_path: str):
    """Inspect an image and show statistics."""
    try:
        if input_path.startswith("http"):
             # Handle URL
             arr = IO.from_url(input_path)
             img = Image(arr)
        elif input_path in ["lenna", "astronaut"]:
             img = fetch_sample(input_path)
        else:
             img = Image.open(input_path)
             
        report = analyze_image(img)
        
        table = Table(title=f"Inspection: {input_path}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Resolution", report["meta"]["resolution"])
        table.add_row("Channels", str(report["meta"]["channels"]))
        table.add_row("Mean Intensity", f"{report['basic_stats']['mean']:.2f}")
        table.add_row("Blur Variance", f"{report['quality']['blur_variance']:.2f}")
        table.add_row("Blurred?", str(report['quality']['is_likely_blurred']))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@app.command()
def pipeline(config_path: str, input_path: str, output_path: str = "output_pipeline.jpg"):
    """Run a pipeline from a YAML config file."""
    # We need to construct a transform registry dynamically or manually
    # For now, minimal registry
    from ..transforms import geometric, color, filtering
    
    registry = {
        "Resize": geometric.Resize,
        "Rotate": geometric.Rotate,
        "ToGray": color.ToGray,
        "GaussianBlur": filtering.GaussianBlur,
        # Add others...
    }
    
    try:
        pipe = Pipeline.load(config_path, registry)
        img = Image.open(input_path)
        
        start = time.perf_counter()
        result = pipe(img)
        end = time.perf_counter()
        
        result.save(output_path)
        console.print(f"[green]Pipeline finished in {end-start:.4f}s[/green]")
        console.print(pipe.benchmark())
        
    except Exception as e:
         console.print(f"[red]Error:[/red] {e}")

if __name__ == "__main__":
    app()
