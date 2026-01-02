import click
from udf_tools.converters.docx import DocxConverter
from udf_tools.converters.pdf import PDFConverter
from rich.console import Console

console = Console()

@click.group()
def main():
    """UDF-Tools: A library for working with UYAP UDF files."""
    pass

@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
def convert(input_path, output_path):
    """Convert between UDF and other formats."""
    if input_path.endswith('.docx') and output_path.endswith('.udf'):
        console.print(f"[yellow]Converting [bold]{input_path}[/] to [bold]{output_path}[/]...[/]")
        DocxConverter.to_udf(input_path, output_path)
        console.print("[green]Conversion complete![/]")
    elif input_path.endswith('.udf') and output_path.endswith('.pdf'):
        console.print(f"[yellow]Converting [bold]{input_path}[/] to [bold]{output_path}[/]...[/]")
        PDFConverter.from_udf(input_path, output_path)
        console.print("[green]Conversion complete![/]")
    else:
        console.print("[red]Unsupported conversion format.[/]")

if __name__ == "__main__":
    main()
