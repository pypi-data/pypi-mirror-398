import os
import sys
import shutil
import webbrowser
from pathlib import Path
import pdoc


def generate_documentation():
    # Define paths relative to this file using pathlib
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent  # Adjust if needed
    docs_dir = project_root / 'docs'
    docs_build_dir = docs_dir / '_build'
    html_output_dir = docs_build_dir / 'html'

    # Clean up any previous build output
    if html_output_dir.exists():
        shutil.rmtree(str(html_output_dir))
    html_output_dir.mkdir(parents=True, exist_ok=True)

    # Name of the package you want to document
    package_name = "slrquerytester"  # Replace with your actual package name

    # Generate HTML documentation using pdoc's API
    pdoc.pdoc(package_name, output_directory=html_output_dir)

    # Optionally copy additional markdown files from docs/ to the output directory
    os.mkdir(str(html_output_dir / 'docs'))
    for filename in docs_dir.iterdir():
        if filename.suffix == ".md":
            shutil.copy(str(filename), str(html_output_dir / 'docs' / filename.name))

    # Open the generated index page in the default browser
    index_html = html_output_dir / "index.html"
    if index_html.exists():
        webbrowser.open_new_tab("file://" + str(index_html.resolve()))
    else:
        print("Index file not found.")


if __name__ == "__main__":
    # Ensure the project root is in sys.path
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir  # Adjust if needed
    sys.path.insert(0, str(project_root))

    generate_documentation()
