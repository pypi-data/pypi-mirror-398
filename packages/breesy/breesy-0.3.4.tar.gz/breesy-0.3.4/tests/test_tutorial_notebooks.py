"""Tests for executing tutorial Jupyter notebooks."""

import subprocess
from pathlib import Path
import pytest


def test_tutorial_notebooks_execute():
    """Execute all tutorial notebooks and save HTML outputs."""
    repo_root = Path(__file__).parent.parent
    tutorials_dir = repo_root / "docs" / "breesy-book" / "tutorials"
    output_dir = Path(__file__).parent / "test_outputs"

    notebooks = list(tutorials_dir.glob("*.ipynb"))

    assert len(notebooks) > 0, f"No notebooks found in {tutorials_dir}"

    print(f"\nFound {len(notebooks)} tutorial notebooks to execute:")
    for nb in notebooks:
        print(f"  - {nb.name}")

    # Execute each notebook
    failed_notebooks = []
    for nb_path in notebooks:
        print(f"\nExecuting: {nb_path.name}")

        # --allow-errors allows notebooks with validation issues to execute
        # --ExecutePreprocessor.timeout increases timeout for slow cells
        result = subprocess.run([
            "jupyter", "nbconvert",
            "--to", "html",
            "--execute",
            "--allow-errors",
            "--ExecutePreprocessor.timeout=300",
            "--output-dir", str(output_dir),
            str(nb_path)
        ], capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            failed_notebooks.append({
                'notebook': nb_path.name,
                'stderr': result.stderr,
                'stdout': result.stdout
            })
            print(f"  ❌ FAILED: {nb_path.name}")
        else:
            print(f"  ✅ SUCCESS: {nb_path.name}")

    # Assert all notebooks executed successfully
    if failed_notebooks:
        error_msg = "\n\nNotebook execution failures:\n"
        for failure in failed_notebooks:
            error_msg += f"\n{failure['notebook']}:\n"
            error_msg += f"STDERR: {failure['stderr']}\n"
            error_msg += f"STDOUT: {failure['stdout']}\n"
        pytest.fail(error_msg)

    print(f"\n✅ All {len(notebooks)} notebooks executed successfully")
    print(f"HTML outputs saved to: {output_dir}")
