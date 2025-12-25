"""
OptixLog SDK - Experiment tracking for photonic simulations

Enhanced with:
- Colored console output
- Input validation
- Return values with URLs
- Context manager support
- Batch operations
- Query capabilities
- Convenience helpers

Example:
    import optixlog
    
    # Context manager approach (recommended)
    with optixlog.run("my_experiment", config={"lr": 0.001}) as client:
        client.log(step=0, loss=0.5)
        client.log_matplotlib("plot", fig)
    
    # Traditional approach
    client = optixlog.init(run_name="my_experiment")
    client.log(step=0, loss=0.5)
"""

from .client import OptixClient, create_project, _detect_mpi_environment, OxInvalidTaskError
from .result_types import MetricResult, MediaResult, BatchResult, RunInfo, ArtifactInfo, ProjectInfo, ComparisonResult
from .validators import ValidationError
from .helpers import add_helper_methods
import os
import inspect
import json
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

__version__ = "0.1.0"
__all__ = [
    # Main functions
    "init",
    "run",
    "create_project",
    
    # Client class
    "OptixClient",
    
    # Result types
    "MetricResult",
    "MediaResult",
    "BatchResult",
    "RunInfo",
    "ArtifactInfo",
    "ProjectInfo",
    "ComparisonResult",
    
    # Exceptions
    "ValidationError",
    "OxInvalidTaskError",
    
    # Query functions (lazy loaded)
    "list_runs",
    "get_run",
    "get_artifacts",
    "download_artifact",
    "get_metrics",
    "compare_runs",
    "list_projects",
    
    # Utility
    "get_mpi_info",
    "is_master_process",
]

DEFAULT_API_URL = "https://optixlog.com"

OPTIX_API_URL = os.getenv("OPTIX_API_URL", DEFAULT_API_URL)
OPTIX_API_KEY = os.getenv("OPTIX_API_KEY", None)
OPTIX_PROJECT = os.getenv("OPTIX_PROJECT", "dev")


# =============================================================================
# Source Detection (like W&B, MLflow)
# =============================================================================

def _in_notebook() -> bool:
    """Check if running in a Jupyter/Colab notebook environment."""
    try:
        from IPython import get_ipython  # type: ignore
        shell = get_ipython()
        if shell is None:
            return False
        return shell.__class__.__name__ in ("ZMQInteractiveShell", "Shell")
    except:
        return False


def _in_colab() -> bool:
    """Check if running in Google Colab."""
    try:
        import google.colab  # type: ignore
        return True
    except ImportError:
        return False


def _get_notebook_name() -> Optional[str]:
    """
    Try to get notebook name/path.
    Works for: VS Code notebooks, Jupyter Lab/Notebook.
    Does NOT work reliably for: Google Colab.
    """
    try:
        from IPython import get_ipython  # type: ignore
        ipython = get_ipython()
        if ipython is None:
            return None
        
        # Method 1: VS Code notebooks
        vsc_path = ipython.user_ns.get('__vsc_ipynb_file__')
        if vsc_path:
            return vsc_path
        
        # Method 2: Jupyter notebook server API
        try:
            import json
            import requests
            from notebook import notebookapp  # type: ignore
            import ipykernel  # type: ignore
            
            connection_file = ipykernel.connect.get_connection_file()
            kernel_id = os.path.basename(connection_file).split('-', 1)[1].split('.')[0]
            
            for srv in notebookapp.list_running_servers():
                try:
                    url = srv['url'] + 'api/sessions'
                    token = srv.get('token', '')
                    response = requests.get(url, params={'token': token}, timeout=2)
                    if response.ok:
                        for sess in response.json():
                            if sess.get('kernel', {}).get('id') == kernel_id:
                                return sess.get('notebook', {}).get('path')
                except:
                    continue
        except:
            pass
        
        return None
    except:
        return None


def _get_calling_file() -> Optional[str]:
    """
    Walk up the call stack to find the first non-SDK file.
    Works for regular Python scripts.
    """
    try:
        for frame_info in inspect.stack():
            filename = frame_info.filename
            # Skip SDK internals
            if 'optixlog' not in filename and not filename.startswith('<'):
                return os.path.abspath(filename)
        return None
    except:
        return None


def _read_file_content(filepath: str) -> Optional[str]:
    """Read raw file content (preserves .ipynb as-is JSON)."""
    if not filepath or not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None


def _safe_read_file(filepath: str, max_retries: int = 3, delay: float = 0.1) -> Optional[str]:
    """
    Read file with retry logic for VSCode save handling.
    Checks if file size is stable before reading.
    """
    if not filepath or not os.path.exists(filepath):
        return None
    
    for attempt in range(max_retries):
        try:
            # Check if file is stable (not being written)
            size1 = os.path.getsize(filepath)
            time.sleep(delay)
            size2 = os.path.getsize(filepath)
            
            if size1 == size2:  # File is stable
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
        except (IOError, OSError):
            pass
        
        # Exponential backoff
        time.sleep(delay * (2 ** attempt))
    
    # Final attempt without stability check
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None


def get_or_create_notebook_signature(notebook_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get existing OptixLog signature from notebook metadata, or create one.
    
    The signature is stored at: metadata.optixlog.signature
    This ensures all runs from the same notebook link together, regardless
    of code changes or cell re-runs.
    
    Args:
        notebook_path: Path to the .ipynb file
    
    Returns:
        Tuple of (signature, content):
            - signature: The UUID signature (existing or newly created)
            - content: The notebook content (may be modified if signature was created)
    
    Note:
        If a new signature is created, it is written back to the notebook file.
    """
    if not notebook_path or not os.path.exists(notebook_path):
        return None, None
    
    if not notebook_path.endswith('.ipynb'):
        return None, None
    
    try:
        # Read notebook with retry logic (handles VSCode save timing)
        content = _safe_read_file(notebook_path)
        if not content:
            return None, None
        
        notebook = json.loads(content)
        
        # Ensure metadata structure exists
        if "metadata" not in notebook:
            notebook["metadata"] = {}
        
        metadata = notebook["metadata"]
        
        if "optixlog" not in metadata:
            metadata["optixlog"] = {}
        
        optixlog_meta = metadata["optixlog"]
        
        # Check if signature already exists
        if "signature" in optixlog_meta and optixlog_meta["signature"]:
            # Signature exists, return it with current content
            return optixlog_meta["signature"], content
        
        # Create new signature
        new_signature = str(uuid.uuid4())
        optixlog_meta["signature"] = new_signature
        optixlog_meta["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Write the modified notebook back to file
        try:
            with open(notebook_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1)
            
            # Re-read to get the exact content we wrote
            with open(notebook_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            # If we can't write, still return the signature for this session
            # but the content will have the signature embedded
            content = json.dumps(notebook)
            print(f"⚠ Could not persist OptixLog signature to file: {e}")
        
        return new_signature, content
        
    except json.JSONDecodeError:
        # Not a valid JSON notebook
        return None, None
    except Exception as e:
        print(f"⚠ Error processing notebook signature: {e}")
        return None, None


def _get_file_extension(filepath: Optional[str]) -> str:
    """Get file extension from path (e.g., '.py', '.ipynb')."""
    if not filepath:
        return "unknown"
    ext = os.path.splitext(filepath)[1].lower()
    return ext if ext else "unknown"


def detect_source(source_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect the source file/notebook that called the SDK.
    
    Combines multiple heuristics + allows explicit override.
    Used by W&B, MLflow, and other ML frameworks.
    
    For notebooks (.ipynb), this also handles the OptixLog signature:
    - If signature exists in metadata.optixlog.signature, it's used
    - If not, a new UUID signature is created and written to the file
    
    Args:
        source_override: Explicit source path/name (takes priority)
    
    Returns:
        Dict with keys:
            - environment: file extension (".py", ".ipynb") or "colab" | "interactive"
            - source: filepath or name (or None)
            - content: raw file content as string (or None)
            - signature: OptixLog signature for notebooks (or None for .py files)
    """
    result = {
        "environment": "unknown",
        "source": None,
        "content": None,
        "signature": None,
    }
    
    # 1. If user provided explicit override, use it
    if source_override:
        result["environment"] = _get_file_extension(source_override)
        result["source"] = source_override
        
        # For notebooks, get or create signature
        if source_override.endswith('.ipynb'):
            signature, content = get_or_create_notebook_signature(source_override)
            result["content"] = content
            result["signature"] = signature
        else:
            result["content"] = _read_file_content(source_override)
        
        return result
    
    # 2. Check if in Colab (cannot auto-detect notebook name)
    if _in_colab():
        result["environment"] = "colab"
        # For Colab, generate a session-only signature (not persisted)
        result["signature"] = str(uuid.uuid4())
        return result
    
    # 3. Check if in Jupyter notebook
    if _in_notebook():
        notebook_path = _get_notebook_name()
        result["environment"] = _get_file_extension(notebook_path) if notebook_path else ".ipynb"
        result["source"] = notebook_path
        
        if notebook_path:
            # Get or create persistent signature
            signature, content = get_or_create_notebook_signature(notebook_path)
            result["content"] = content
            result["signature"] = signature
        else:
            # No path detected, generate session signature
            result["signature"] = str(uuid.uuid4())
        
        return result
    
    # 4. Try to find calling .py file
    script_path = _get_calling_file()
    if script_path:
        result["environment"] = _get_file_extension(script_path)
        result["source"] = script_path
        result["content"] = _read_file_content(script_path)
        # .py files don't use signatures - they use content hash
        return result
    
    # 5. Fallback: interactive/unknown
    result["environment"] = "interactive"
    result["signature"] = str(uuid.uuid4())  # Session signature
    return result


# =============================================================================
# Main API
# =============================================================================

def init(api_key: Optional[str] = None, 
         api_url: Optional[str] = None, 
         project_id: Optional[str] = None, 
         run_name: Optional[str] = None, 
         config: Optional[Dict[str, Any]] = None, 
         task_id: Optional[str] = None,
         source: Optional[str] = None,
         skip_file: bool = False,
         create_project_if_not_exists: bool = True) -> OptixClient:
    """
    Initialize OptixLog client
    
    Args:
        api_key: API key (or use OPTIX_API_KEY env var)
        api_url: API URL (or use OPTIX_API_URL env var)
        project_id: Project ID (or use OPTIX_PROJECT env var)
        run_name: Name for this run
        config: Configuration dictionary
        task_id: Optional task ID to link to
        source: Explicit source file path (for Colab or CLI usage)
        skip_file: Skip source file detection (default: False)
        create_project_if_not_exists: Automatically create project if it doesn't exist (default: True)
    
    Returns:
        OptixClient instance with helper methods added
        
    Example:
        client = optixlog.init(run_name="experiment_1")
        client.log(step=0, loss=0.5)
        
        # For Colab, provide source explicitly:
        client = optixlog.init(run_name="exp", source="colab_experiment.ipynb")
        
        # Skip file detection entirely:
        client = optixlog.init(run_name="exp", skip_file=True)
        
        # Disable auto-create project:
        client = optixlog.init(project_id="my_project", create_project_if_not_exists=False)
    """
    global OPTIX_API_URL, OPTIX_API_KEY, OPTIX_PROJECT

    final_api_url = (api_url or OPTIX_API_URL or "").strip()
    _api_key = api_key or OPTIX_API_KEY
    final_api_key = _api_key.strip() if _api_key else None
    final_project_id = (project_id or OPTIX_PROJECT or "").strip()

    if final_api_key is None:
        raise ValueError(
            "Missing OPTIX_API_KEY. Set it via environment variable or pass api_key parameter.\n"
            "Get your API key from: https://optixlog.com"
        )

    final_config = config.copy() if config else {}
    source_code = {}
    
    # Detect source environment (unless skipped)
    if not skip_file:
        source_info = detect_source(source)
        source_code = {
            "environment": source_info["environment"],
            "source": source_info["source"],
            "content": source_info["content"],
        }

    is_master = _detect_mpi_environment()
    
    try:
        client = OptixClient(final_api_url, final_api_key, final_project_id, run_name, final_config, task_id)
        
        # Log source code to the server (after client is created so we have run_id)
        if not skip_file and source_code.get("content") and is_master:
            client.log_source_code(
                source=source_code.get("source") or "unknown",
                content=source_code.get("content") or "",
                environment=source_code.get("environment") or "unknown",
                signature=source_code.get("signature"),  # Pass signature for notebooks
            )
        
        # Add helper methods to make it easier to use
        if is_master:
            add_helper_methods(client)
        
        return client
        
    except ValueError as e:
        if "not found" in str(e):
            # Try to create project if enabled
            if create_project_if_not_exists and is_master:
                try:
                    from rich.console import Console
                    console = Console()
                    console.print(f"[yellow]⚙ Creating project '{final_project_id}'...[/yellow]")
                except ImportError:
                    print(f"Creating project '{final_project_id}'...")
                
                try:
                    created_project_id = create_project(final_api_url, final_api_key, final_project_id)
                    if created_project_id:
                        # Retry with the created project ID (not name!)
                        client = OptixClient(final_api_url, final_api_key, created_project_id, run_name, final_config, task_id)
                        
                        # Log source code to the server (after client is created so we have run_id)
                        if not skip_file and source_code.get("content") and is_master:
                            client.log_source_code(
                                source=source_code.get("source") or "unknown",
                                content=source_code.get("content") or "",
                                environment=source_code.get("environment") or "unknown",
                                signature=source_code.get("signature"),  # Pass signature for notebooks
                            )
                        
                        # Add helper methods to make it easier to use
                        if is_master:
                            add_helper_methods(client)
                        
                        return client
                except Exception as create_error:
                    error_suggest = ""
                    if "Available projects:" in str(e):
                        available = str(e).split("Available projects:")[1] if "Available projects:" in str(e) else ""
                        error_suggest = f"\nHint: Go to https://optixlog.com to create a project: {available.strip()}"
                    raise ValueError(f"Project '{final_project_id}' not found and could not be created: {create_error}{error_suggest}")
            
            # Project not found and auto-create is disabled
            error_suggest = ""
            if "Available projects:" in str(e):
                available = str(e).split("Available projects:")[1] if "Available projects:" in str(e) else ""
                error_suggest = f"\nHint: Go to https://optixlog.com to create a project or use create_project_if_not_exists=True: {available.strip()}"
            raise ValueError(f"Project '{final_project_id}' not found{error_suggest}")
        else:
            raise


def run(run_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        project_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        source: Optional[str] = None,
        skip_file: bool = False,
        create_project_if_not_exists: bool = True) -> OptixClient:
    """
    Create OptixLog client as a context manager (recommended approach)
    
    Args:
        run_name: Name for this run
        api_key: API key (or use OPTIX_API_KEY env var)
        api_url: API URL (or use OPTIX_API_URL env var)
        project_id: Project ID (or use OPTIX_PROJECT env var)
        config: Configuration dictionary
        task_id: Optional task ID to link to
        source: Explicit source file path (for Colab or CLI usage)
        skip_file: Skip source file detection (default: False)
    
    Returns:
        OptixClient instance (use with 'with' statement)
        
    Example:
        with optixlog.run("experiment_1", config={"lr": 0.001}) as client:
            for step in range(100):
                loss = train_step()
                client.log(step=step, loss=loss)
        
        # For Colab:
        with optixlog.run("exp", source="my_colab_notebook.ipynb") as client:
            ...
        
        # Skip file detection:
        with optixlog.run("exp", skip_file=True) as client:
            ...
    """
    return init(
        api_key=api_key,
        api_url=api_url,
        project_id=project_id,
        run_name=run_name,
        config=config,
        task_id=task_id,
        source=source,
        skip_file=skip_file,
        create_project_if_not_exists=create_project_if_not_exists,
    )


def get_mpi_info() -> Dict[str, Any]:
    """
    Get current MPI environment information
    
    Returns:
        Dictionary with is_master, rank, size, has_mpi
        
    Example:
        info = optixlog.get_mpi_info()
        if info["is_master"]:
            print("I'm the master process!")
    """
    is_master, rank, size, mpi_comm = _detect_mpi_environment()
    return {
        "is_master": is_master,
        "rank": rank,
        "size": size,
        "has_mpi": mpi_comm is not None
    }


def is_master_process() -> bool:
    """
    Check if current process is the master process
    
    Returns:
        True if master, False otherwise
        
    Example:
        if optixlog.is_master_process():
            print("Only the master process prints this")
    """
    is_master, _, _, _ = _detect_mpi_environment()
    return is_master


# Lazy load query functions to avoid import overhead
def __getattr__(name):
    """Lazy load query functions"""
    if name in ["list_runs", "get_run", "get_artifacts", "download_artifact", 
                "get_metrics", "compare_runs", "list_projects"]:
        from . import query
        return getattr(query, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
