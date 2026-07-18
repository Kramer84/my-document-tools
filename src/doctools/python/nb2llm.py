import typer
from pathlib import Path
import nbformat
from nbconvert import MarkdownExporter
from traitlets.config import Config
import ast

def truncate_text(text: str, n_lines: int) -> str:
    """Keep only the first N and last N lines of a string."""
    if not text:
        return ""
    
    lines = text.split('\n')
    if len(lines) <= 2 * n_lines:
        return text
        
    return '\n'.join(
        lines[:n_lines] + 
        [f"\n... [{len(lines) - 2*n_lines} lines truncated for LLM context] ...\n"] + 
        lines[-n_lines:]
    )

def minify_code_cell(source_code: str) -> str:
    """Parses Python code to AST, removes docstrings, and unparses to minify."""
    # Catch empty strings early
    if not source_code.strip():
        return source_code
        
    try:
        # 1. Parse into Abstract Syntax Tree (strips comments automatically)
        tree = ast.parse(source_code)
        
        # 2. Walk the tree to strip docstrings
        for node in ast.walk(tree):
            # Check modules, classes, and functions (sync and async)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                # If the first item in the body is a string expression, it's a docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    
                    node.body.pop(0) # Remove the docstring node
                    
        # 3. Unparse back to string (normalizes whitespace)
        return ast.unparse(tree)
        
    except SyntaxError:
        # Fallback for cells containing Jupyter magics (% or !) or invalid syntax
        return source_code

def process_notebook(
    file_path: Path, 
    keep_lines: int, 
    remove_images: bool, 
    remove_empty: bool,
    output_dir: Path | None,
    minify: bool = False
):
    """Processes a single notebook and exports it to Markdown."""
    try:
        # Read the notebook
        with open(file_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        
        filtered_cells = []
        
        for cell in nb.cells:
            # 1. Skip completely empty cells
            if remove_empty and not cell.source.strip():
                continue
                
            if cell.cell_type == 'code':
                # Strip execution counts
                cell.execution_count = None
                if minify:
                    cell.source = minify_code_cell(cell.source)
                
                if keep_lines == 0:
                    # Clear outputs entirely
                    cell.outputs = []
                else:
                    # Process and truncate outputs
                    processed_outputs = []
                    for output in cell.outputs:
                        if output.output_type == 'stream':
                            output.text = truncate_text(output.text, keep_lines)
                            processed_outputs.append(output)
                            
                        elif output.output_type in ('execute_result', 'display_data'):
                            # Strip images and HTML if requested
                            if remove_images:
                                keys_to_remove = [k for k in output.data.keys() if k.startswith('image/') or k == 'text/html']
                                for k in keys_to_remove:
                                    output.data.pop(k)
                                    output.data['text/plain'] = output.data.get('text/plain', '') + "\n[Image/Rich output removed for LLM context]"
                            
                            # Truncate text output
                            if 'text/plain' in output.data:
                                output.data['text/plain'] = truncate_text(output.data['text/plain'], keep_lines)
                            
                            # Only keep output if there is still data left after stripping images
                            if output.data:
                                processed_outputs.append(output)
                                
                        elif output.output_type == 'error':
                            # Truncate error tracebacks
                            if hasattr(output, 'traceback'):
                                output.traceback = [truncate_text(tb, keep_lines) for tb in output.traceback]
                            processed_outputs.append(output)
                            
                    cell.outputs = processed_outputs
            
            filtered_cells.append(cell)
            
        nb.cells = filtered_cells
        
        # Setup Markdown Exporter
        c = Config()
        # Prevent nbconvert from trying to extract images to separate files
        c.MarkdownExporter.exclude_input_prompt = True
        c.MarkdownExporter.exclude_output_prompt = True
        exporter = MarkdownExporter(config=c)
        
        # Export to Markdown
        body, _ = exporter.from_notebook_node(nb)
        
        # Determine output path
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_file = output_dir / f"{file_path.stem}.md"
        else:
            out_file = file_path.with_suffix('.md')
            
        # Write the file
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(body)
            
        typer.echo(f"✅ Converted: {file_path.name} -> {out_file.name}")
        
    except Exception as e:
        typer.echo(f"❌ Error processing {file_path.name}: {e}", err=True)

def nb2llm(
    target: Path = typer.Argument(..., help="Directory or single .ipynb file to process"),
    keep_lines: int = typer.Option(0, "--keep-lines", "-n", help="Lines of output to keep at start and end. 0 clears all outputs."),
    output_dir: Path = typer.Option(None, "--out-dir", "-o", help="Optional separate directory to save the Markdown files."),
    remove_images: bool = typer.Option(True, "--no-images/--keep-images", help="Strip base64 images and HTML from outputs"),
    remove_empty: bool = typer.Option(True, "--no-empty/--keep-empty", help="Remove completely empty cells"),
    minify: bool = typer.Option(False, "--minify")
):
    """
    Converts Jupyter Notebooks to Markdown while optimizing them for LLM context windows.
    Original notebooks are left untouched.
    """
    if not target.exists():
        typer.echo(f"Error: Path '{target}' does not exist.", err=True)
        raise typer.Exit(code=1)

    notebooks = []
    if target.is_file():
        if target.suffix != '.ipynb':
            typer.echo("Error: Target file is not a .ipynb notebook.", err=True)
            raise typer.Exit(code=1)
        notebooks.append(target)
    else:
        # Recursively find all .ipynb files, ignoring checkpoints
        notebooks = [p for p in target.rglob('*.ipynb') if '.ipynb_checkpoints' not in p.parts]
        
    if not notebooks:
        typer.echo("No Jupyter notebooks found.")
        raise typer.Exit()

    typer.echo(f"Found {len(notebooks)} notebook(s). Processing...")
    
    for nb_path in notebooks:
        process_notebook(nb_path, keep_lines, remove_images, remove_empty, output_dir, minify)
        
    typer.echo("🎉 All done!")

if __name__ == "__main__":
    app()