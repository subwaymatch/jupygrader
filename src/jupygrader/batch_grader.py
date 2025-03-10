"""
Batch grading functionality for processing multiple Jupyter notebooks.
"""

import time
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
from datetime import datetime
from .grader import grade_notebook

def grade_notebooks(
    notebook_paths: List[Union[str, Path]],
    output_path: Optional[Union[str, Path]] = None,
    copy_files: Optional[Union[List[Union[str, Path]], Dict[Union[str, Path], Union[str, Path]]]] = None,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Grade multiple Jupyter notebooks and report progress.
    
    Parameters
    ----------
    notebook_paths : List[str or Path]
        List of paths to Jupyter notebooks to be graded.
    output_path : str or Path, optional
        Directory where all graded notebooks and results will be saved.
        If not provided, results will be saved in the parent directory of each notebook.
    copy_files : list[str | Path] or dict[str | Path, str | Path], optional
        Files to be copied to the temporary grading directory for each notebook.
        See grade_notebook() documentation for details.
    verbose : bool, default=True
        Whether to print progress information to stdout.
        
    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries containing grading results for each notebook.
    
    Notes
    -----
    This function processes notebooks sequentially and reports progress.
    Any errors encountered during grading are caught and reported, allowing
    the batch process to continue with remaining notebooks.
    """
    results = []
    total_notebooks = len(notebook_paths)
    
    if verbose:
        print(f"Starting batch grading of {total_notebooks} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
    
    start_time = time.time()
    
    for idx, notebook_path in enumerate(notebook_paths, 1):
        try:
            notebook_name = Path(notebook_path).name
            
            if verbose:
                print(f"[{idx}/{total_notebooks}] Grading: {notebook_name} ... ", end="", flush=True)
            
            # Grade individual notebook
            result = grade_notebook(
                notebook_path=notebook_path,
                output_path=output_path,
                copy_files=copy_files
            )
            
            # Add to results list
            results.append(result)
            
            if verbose:
                score = result.get('learner_autograded_score', 0)
                max_score = result.get('max_autograded_score', 0)
                print(f"Done. Score: {score}/{max_score}")
        
        except Exception as e:
            if verbose:
                print(f"Error: {str(e)}")
                print(f"Failed to grade notebook: {notebook_path}")
            
            # Add error information to results
            results.append({
                'filename': Path(notebook_path).name if hasattr(notebook_path, 'name') else str(notebook_path),
                'status': 'error',
                'error_message': str(e),
                'error_type': type(e).__name__
            })
    
    elapsed_time = time.time() - start_time
    
    if verbose:
        print("-" * 70)
        print(f"Completed grading {total_notebooks} notebook(s) in {elapsed_time:.2f} seconds")
        
        # Summary statistics
        successful = sum(1 for r in results if r.get('status', '') != 'error')
        failed = total_notebooks - successful
        print(f"Successfully graded: {successful}/{total_notebooks}")
        if failed > 0:
            print(f"Failed to grade: {failed}/{total_notebooks}")
    
    return results