"""
OptixLog Client SDK - Enhanced with colored output, validation, and return values

This module provides the main OptixClient class for logging experiments to OptixLog.
"""

import requests
import json
import io
import os
import base64
from typing import Optional, Dict, Any, List
from PIL import Image
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
except ImportError:
    # Fallback if rich is not installed
    console = None

from .validators import (
    validate_metrics,
    validate_file_path,
    validate_image,
    validate_step,
    validate_key,
    guess_content_type,
)
from .result_types import MetricResult, MediaResult, BatchResult
from .helpers import HelperMethodsMixin


def _print(message: str, style: str = ""):
    """Print with rich colors if available, otherwise plain text"""
    if console:
        console.print(message, style=style)
    else:
        print(message)


def _detect_mpi_environment():
    """
    Detect MPI environment and return rank information.
    Returns: (is_master, rank, size, mpi_comm)
    """
    is_master = True
    rank = 0
    size = 1
    mpi_comm = None
    
    # Check environment variables first (most reliable)
    if 'OMPI_COMM_WORLD_RANK' in os.environ:
        rank = int(os.environ['OMPI_COMM_WORLD_RANK'])
        size = int(os.environ['OMPI_COMM_WORLD_SIZE'])
        is_master = (rank == 0)
        return is_master, rank, size, None
    elif 'PMI_RANK' in os.environ:
        rank = int(os.environ['PMI_RANK'])
        size = int(os.environ['PMI_SIZE'])
        is_master = (rank == 0)
        return is_master, rank, size, None
    elif 'MPI_LOCALRANKID' in os.environ:
        rank = int(os.environ['MPI_LOCALRANKID'])
        size = int(os.environ['MPI_LOCALNRANKS'])
        is_master = (rank == 0)
        return is_master, rank, size, None
    
    # Try mpi4py as fallback
    try:
        import mpi4py.MPI as MPI
        try:
            mpi_comm = MPI.COMM_WORLD
            rank = mpi_comm.Get_rank()
            size = mpi_comm.Get_size()
            is_master = (rank == 0)
            return is_master, rank, size, mpi_comm
        except:
            if MPI.Is_initialized():
                mpi_comm = MPI.COMM_WORLD
                rank = mpi_comm.Get_rank()
                size = mpi_comm.Get_size()
                is_master = (rank == 0)
                return is_master, rank, size, mpi_comm
            else:
                return True, 0, 1, None
    except ImportError:
        pass
    
    # Fallback to Meep's MPI detection
    try:
        import meep as mp
        is_master = mp.am_master()
        rank = 0 if is_master else 1
        size = 2 if not is_master else 1
        return is_master, rank, size, None
    except ImportError:
        pass
    
    # No MPI detected - single process
    return True, 0, 1, None


class OxInvalidTaskError(Exception):
    """Raised when a task_id is invalid or doesn't belong to the project"""
    pass


class OptixClient(HelperMethodsMixin):
    """
    OptixLog client for logging experiments, metrics, images, and files.
    
    Supports:
    - Colored console output with rich
    - Input validation
    - Return values with URLs
    - Context manager for auto-cleanup
    - Batch operations
    - MPI awareness
    - Helper methods for matplotlib, plots, histograms, etc. (via HelperMethodsMixin)
    
    Example:
        with optixlog.run("my_experiment") as client:
            client.log(step=0, loss=0.5)
            client.log_matplotlib("plot", fig)
    """
    
    def __init__(self, api_url: str, api_key: str, project_id: str, 
                 run_name: Optional[str] = None, 
                 config: Optional[Dict[str, Any]] = None, 
                 task_id: Optional[str] = None):
        # Detect MPI environment
        self.is_master, self.rank, self.size, self.mpi_comm = _detect_mpi_environment()
        
        # Store basic info
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.project_id = project_id
        self.run_name = run_name
        self.config = config or {}
        self.task_id = task_id
        
        # Only master process initializes API connection
        if self.is_master:
            self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            self._initialize_run()
        else:
            self.headers = None
            self.run_id = None
            _print(f"[dim]Worker process (rank {self.rank}) initialized[/dim]", "yellow")
    
    def _initialize_run(self):
        """Initialize the run on master process only"""
        try:
            # Get project ID from project name
            projects_response = requests.get(f"{self.api_url}/api/sdk/initialize-run-check", headers=self.headers)
            
            # Handle authentication errors
            if projects_response.status_code == 401:
                _print("✗ Invalid API Key", "red bold")
                raise ValueError("Get your API key from https://optixlog.com")
            elif projects_response.status_code == 403:
                _print("✗ API Key access denied", "red bold")
                raise ValueError("Your API key may not have required permissions")
            elif projects_response.status_code == 404:
                _print("✗ OptixLog server not responding", "red bold")
                raise ValueError("Check if server is running")
            elif not projects_response.ok:
                _print(f"✗ Server error ({projects_response.status_code})", "red bold")
                raise ValueError(projects_response.text)

            projects = projects_response.json()["projects"]
            
            # Find the project by name OR id (user can pass either)
            project_id = None
            for p in projects:
                if p["id"] == self.project_id or p["name"] == self.project_id:
                    project_id = p["id"] 
                    break
            
            if not project_id:
                available = [p['name'] for p in projects]
                _print(f"✗ Project '{self.project_id}' not found", "red bold")
                _print(f"Available: {', '.join(available)}", "dim")
                raise ValueError(f"Project '{self.project_id}' not found. Use create_project_if_not_exists=True or pick from: {available}")
            
            # Create run
            r = requests.post(f"{self.api_url}/api/sdk/create-run", headers=self.headers, json={
                "name": self.run_name, 
                "config": self.config,
                "project_id": project_id
            })
            
            if r.status_code == 401:
                _print("✗ Invalid API Key for run creation", "red bold")
                raise ValueError("Check API key")
            elif not r.ok:
                _print(f"✗ Failed to create run ({r.status_code})", "red bold")
                raise ValueError(r.text)
            
            self.run_id = r.json()["id"]
            _print(f"✓ Run initialized: {self.run_id}", "green bold")
            
            # Link to task if provided
            if self.task_id is not None:
                self._link_run_to_task()
                
        except requests.exceptions.ConnectionError:
            _print("✗ Cannot connect to OptixLog server", "red bold")
            raise ValueError(f"Check if server is running at {self.api_url}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        if self.is_master and exc_type is None:
            _print("✓ Run completed successfully", "green")
        elif self.is_master and exc_type is not None:
            _print(f"⚠ Run ended with error: {exc_val}", "yellow")
        return False
    
    def get_mpi_info(self) -> Dict[str, Any]:
        """Get MPI process information"""
        return {
            "is_master": self.is_master,
            "rank": self.rank,
            "size": self.size,
            "has_mpi": self.mpi_comm is not None
        }
    
    def barrier(self):
        """MPI barrier synchronization"""
        if self.mpi_comm is not None:
            self.mpi_comm.Barrier()
    
    def broadcast_run_id(self):
        """Broadcast run_id from master to all workers"""
        if self.mpi_comm is not None and self.is_master:
            self.mpi_comm.bcast(self.run_id, root=0)
        elif self.mpi_comm is not None and not self.is_master:
            self.run_id = self.mpi_comm.bcast(None, root=0)

    def log(self, step: int, **kv) -> Optional[MetricResult]:
        """
        Log metrics for a specific step
        
        Args:
            step: Step number (must be non-negative integer)
            **kv: Metric key-value pairs (no NaN/Inf allowed)
        
        Returns:
            MetricResult with success status, or None for worker processes
            
        Example:
            result = client.log(step=0, loss=0.5, accuracy=0.95)
            if result:
                print(f"Logged to: {result}")
        """
        if not self.is_master:
            return None
        
        # Validate step
        valid, error = validate_step(step)
        if not valid:
            _print(f"✗ Invalid step: {error}", "red")
            return MetricResult(step=step, metrics=kv, success=False, error=error)
        
        # Validate metrics
        valid, error = validate_metrics(kv)
        if not valid:
            _print(f"✗ Invalid metrics: {error}", "red")
            return MetricResult(step=step, metrics=kv, success=False, error=error)
        
        try:
            payload = {"run_id": self.run_id, "step": step, "kv": kv}
            r = requests.post(f"{self.api_url}/api/sdk/log-metric", headers=self.headers, json=payload)
            
            if r.status_code == 401:
                error = "Invalid API Key"
                _print(f"✗ {error}", "red")
                return MetricResult(step=step, metrics=kv, success=False, error=error)
            elif not r.ok:
                error = f"Server error ({r.status_code})"
                _print(f"✗ {error}", "red")
                return MetricResult(step=step, metrics=kv, success=False, error=error)
            
            return MetricResult(
                step=step,
                metrics=kv,
                success=True,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            error = str(e)
            _print(f"✗ Failed to log metrics: {error}", "red")
            return MetricResult(step=step, metrics=kv, success=False, error=error)

    def log_source_code(self, source: str, content: str, environment: str, 
                        signature: Optional[str] = None) -> bool:
        """
        Log source code for this run
        
        Args:
            source: Source file path or name
            content: Raw source code content (will be base64 encoded)
            environment: File type (".ipynb", ".py", "colab", "interactive", "unknown")
            signature: OptixLog signature for notebooks (stored in metadata.optixlog.signature)
                       If provided, used for matching instead of content hash.
                       This ensures all runs from the same notebook link together.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_master:
            return False
        
        if not content:
            _print("⚠ No source code content to log", "yellow")
            return False
        
        try:
            # Encode content as base64 for transport
            content_bytes = content.encode("utf-8")
            content_base64 = base64.b64encode(content_bytes).decode("utf-8")
            
            payload = {
                "run_id": self.run_id,
                "source": source or "unknown",
                "content": content_base64,
                "environment": environment if environment in [".ipynb", ".py", "colab", "interactive", "unknown"] else "unknown",
            }
            
            # Include signature for notebooks (used for matching instead of content hash)
            if signature:
                payload["signature"] = signature
            
            r = requests.post(f"{self.api_url}/api/sdk/log-source-code", headers=self.headers, json=payload)
            
            if not r.ok:
                _print(f"⚠ Failed to log source code ({r.status_code})", "yellow")
                return False
            
            response_data = r.json()
            if response_data.get("reused"):
                _print(f"✓ Source code linked (reused existing)", "green")
            else:
                _print(f"✓ Source code uploaded", "green")
            return True
            
        except Exception as e:
            _print(f"⚠ Failed to log source code: {e}", "yellow")
            return False

    def log_image(self, key: str, pil_image: Image.Image, 
                   meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Log an image
        
        Args:
            key: Identifier for this image
            pil_image: PIL Image object
            meta: Optional metadata dictionary
        
        Returns:
            MediaResult with URL, or None for worker processes
            
        Example:
            result = client.log_image("plot", fig_image)
            print(f"View at: {result.url}")
        """
        if not self.is_master:
            return None
        
        # Validate key
        valid, error = validate_key(key)
        if not valid:
            _print(f"✗ Invalid key: {error}", "red")
            return MediaResult(key=key, success=False, error=error)
        
        # Validate image
        valid, error = validate_image(pil_image)
        if not valid:
            _print(f"✗ Invalid image: {error}", "red")
            return MediaResult(key=key, success=False, error=error)
        
        try:
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            image_bytes = buf.getvalue()
            file_size = len(image_bytes)
            
            # Encode image as base64 for JSON transport
            blob_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            payload = {
                "run_id": self.run_id,
                "kind": "image",
                "key": key,
                "meta": json.dumps(meta or {}),
                "blob": blob_base64,
                "filename": "image.png",
                "content_type": "image/png",
            }
            
            r = requests.post(f"{self.api_url}/api/sdk/log-image", headers=self.headers, json=payload)
            
            if not r.ok:
                error = f"Upload failed ({r.status_code})"
                _print(f"✗ {error}", "red")
                return MediaResult(key=key, success=False, error=error)
            
            response_data = r.json()
            media_id = response_data.get("id", None)
            path = response_data.get("path", None)
            url = f"{self.api_url}/media/{media_id}" if media_id else None
            
            _print(f"✓ Image '{key}' uploaded", "green")
            return MediaResult(
                key=key,
                success=True,
                media_id=media_id,
                url=url,
                file_size=file_size,
                content_type="image/png"
            )
            
        except Exception as e:
            error = str(e)
            _print(f"✗ Failed to upload image: {error}", "red")
            return MediaResult(key=key, success=False, error=error)

    def log_file(self, key: str, path: str, 
                  content_type: Optional[str] = None,
                  meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Log a file (with auto-detection of content type)
        
        Args:
            key: Identifier for this file
            path: Path to file
            content_type: MIME type (auto-detected if None)
            meta: Optional metadata dictionary
        
        Returns:
            MediaResult with URL, or None for worker processes
            
        Example:
            result = client.log_file("data", "results.csv")
            print(f"View at: {result.url}")
        """
        if not self.is_master:
            return None
        
        # Validate key
        valid, error = validate_key(key)
        if not valid:
            _print(f"✗ Invalid key: {error}", "red")
            return MediaResult(key=key, success=False, error=error)
        
        # Validate file path
        valid, error = validate_file_path(path)
        if not valid:
            _print(f"✗ Invalid file: {error}", "red")
            return MediaResult(key=key, success=False, error=error)
        
        # Auto-detect content type
        if content_type is None:
            content_type = guess_content_type(path)
        
        try:
            with open(path, "rb") as f:
                file_bytes = f.read()
                file_size = len(file_bytes)
            
            # Encode file as base64 for JSON transport
            blob_base64 = base64.b64encode(file_bytes).decode("utf-8")
            filename = os.path.basename(path)
            
            payload = {
                "run_id": self.run_id,
                "kind": "file",
                "key": key,
                "meta": json.dumps(meta or {}),
                "blob": blob_base64,
                "filename": filename,
                "content_type": content_type,
            }
            
            r = requests.post(f"{self.api_url}/api/sdk/log-image", headers=self.headers, json=payload)
            
            if not r.ok:
                error = f"Upload failed ({r.status_code})"
                _print(f"✗ {error}", "red")
                return MediaResult(key=key, success=False, error=error)
            
            response_data = r.json()
            media_id = response_data.get("id", None)
            url = f"{self.api_url}/media/{media_id}" if media_id else None
            
            _print(f"✓ File '{key}' uploaded ({file_size / 1024:.1f} KB)", "green")
            return MediaResult(
                key=key,
                success=True,
                media_id=media_id,
                url=url,
                file_size=file_size,
                content_type=content_type
            )
            
        except Exception as e:
            error = str(e)
            _print(f"✗ Failed to upload file: {error}", "red")
            return MediaResult(key=key, success=False, error=error)
    
    def log_batch(self, metrics_list: List[Dict[str, Any]], max_workers: int = 4) -> Optional[BatchResult]:
        """
        Log multiple metrics in parallel
        
        Args:
            metrics_list: List of dicts with 'step' and metric key-value pairs
            max_workers: Number of parallel workers
        
        Returns:
            BatchResult with success statistics
            
        Example:
            results = client.log_batch([
                {"step": 0, "loss": 0.5},
                {"step": 1, "loss": 0.4},
            ])
            print(f"Success rate: {results.success_rate:.1f}%")
        """
        if not self.is_master:
            return None
        
        total = len(metrics_list)
        successful = 0
        failed = 0
        results = []
        errors = []
        
        _print(f"Logging {total} metric batches...", "cyan")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for item in metrics_list:
                step = item.pop("step", 0)
                future = executor.submit(self.log, step, **item)
                futures[future] = step
            
            for future in as_completed(futures):
                result = future.result()
                if result and result.success:
                    successful += 1
                else:
                    failed += 1
                    if result and result.error:
                        errors.append(result.error)
                results.append(result)
        
        batch_result = BatchResult(
            total=total,
            successful=successful,
            failed=failed,
            results=results,
            errors=errors
        )
        
        if failed == 0:
            _print(f"✓ Batch complete: {successful}/{total} successful", "green bold")
        else:
            _print(f"⚠ Batch complete: {successful}/{total} successful, {failed} failed", "yellow")
        
        return batch_result
    
    def _link_run_to_task(self):
        """Validate task and link the current run to it"""
        if not self.is_master or not self.run_id or not self.task_id:
            return
        
        try:
            projects_response = requests.get(f"{self.api_url}/projects", headers=self.headers)
            if not projects_response.ok:
                raise OxInvalidTaskError(f"Failed to fetch projects: {projects_response.status_code}")
            
            projects = projects_response.json()
            project_id = self.project_id
            
            if not project_id:
                raise OxInvalidTaskError(f"Project with id '{self.project_id}' not found")
            
            # Validate the task
            validate_response = requests.get(
                f"{self.api_url}/tasks/validate",
                headers=self.headers,
                params={"project_id": project_id, "task_id": self.task_id}
            )

            project = projects.json()["projects"].find(lambda x: x["id"] == self.project_id)
            
            if validate_response.status_code == 404:
                raise OxInvalidTaskError(f"Task '{self.task_id}' not found in project '{project['name']}'")
            elif not validate_response.ok:
                raise OxInvalidTaskError(f"Task validation failed: {validate_response.status_code}")
            
            # Link the run to the task
            link_response = requests.post(
                f"{self.api_url}/tasks/{self.task_id}/runs/{self.run_id}",
                headers=self.headers,
                json={}
            )
            
            if not link_response.ok:
                raise OxInvalidTaskError(f"Failed to link run to task: {link_response.status_code}")
            
            _print(f"✓ Linked to task {self.task_id}", "green")
            
        except OxInvalidTaskError as e:
            _print(f"⚠ Task linking failed: {e}", "yellow")
    
    def add_run_to_task(self, run_id: str, task_id: str):
        """Manually link a run to a task"""
        if not self.is_master:
            return
        
        try:
            link_response = requests.post(
                f"{self.api_url}/tasks/{task_id}/runs/{run_id}",
                headers=self.headers,
                json={}
            )
            
            if link_response.status_code == 404:
                raise OxInvalidTaskError(f"Task '{task_id}' or run '{run_id}' not found")
            elif not link_response.ok:
                raise OxInvalidTaskError(f"Failed to link: {link_response.status_code}")
            
            _print(f"✓ Linked run {run_id} to task {task_id}", "green")
            
        except OxInvalidTaskError as e:
            _print(f"✗ {e}", "red")


def create_project(api_url: str, api_key: str, project_name: str) -> Optional[str]:
    """
    Create a new project if it doesn't exist
    
    Returns:
        Project ID or None for worker processes
    """
    is_master, rank, size, mpi_comm = _detect_mpi_environment()
    
    if not is_master:
        return None
    
    api_url = api_url.rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        # Use the SDK endpoint to create project (handles both checking and creating)
        r = requests.post(
            f"{api_url}/api/sdk/create-project", 
            headers=headers, 
            json={"name": project_name}
        )
        
        if r.status_code == 401:
            _print("✗ Invalid API Key", "red bold")
            raise ValueError("Get your API key from https://optixlog.com")
        elif not r.ok:
            _print(f"✗ Failed to create project ({r.status_code})", "red")
            raise ValueError(r.text)
        
        result = r.json()
        project_id = result["id"]
        
        if result.get("created", True):
            _print(f"✓ Project '{project_name}' created", "green bold")
        else:
            _print(f"✓ Project '{project_name}' found", "green")
        
        return project_id
        
    except requests.exceptions.ConnectionError:
        _print("✗ Cannot connect to server", "red bold")
        raise ValueError(f"Check if server is running at {api_url}")


def init(api_url: str, api_key: str, project: str, 
         run_name: Optional[str] = None, 
         config: Optional[Dict[str, Any]] = None, 
         create_project_if_not_exists: bool = False, 
         task_id: Optional[str] = None) -> OptixClient:
    """
    Initialize OptixLog client with automatic MPI detection
    
    Args:
        api_url: API endpoint URL
        api_key: User API key
        project: Project name
        run_name: Name for this run
        config: Configuration dictionary
        create_project_if_not_exists: Create project if it doesn't exist
        task_id: Optional task ID to link runs to
    
    Returns:
        OptixClient instance
    """
    is_master, rank, size, mpi_comm = _detect_mpi_environment()
    
    if create_project_if_not_exists and is_master:
        create_project(api_url, api_key, project)
    
    return OptixClient(api_url, api_key, project, run_name, config, task_id)
