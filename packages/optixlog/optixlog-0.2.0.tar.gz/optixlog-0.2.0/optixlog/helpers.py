"""
Convenience helper functions for OptixLog SDK

This module provides zero-boilerplate helpers for common logging tasks.
"""

import io
import os
import tempfile
from typing import Optional, Dict, Any, List, Tuple, Union, TYPE_CHECKING
from PIL import Image

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import matplotlib
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .result_types import MediaResult

if TYPE_CHECKING:
    import numpy as np

__all__ = [
    "log_matplotlib",
    "log_plot",
    "log_array_as_image",
    "log_histogram",
    "log_scatter",
    "log_multiple_plots",
    "HelperMethodsMixin",
    "add_helper_methods",
]


def log_matplotlib(client, key: str, fig, meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Log a matplotlib figure directly (auto-converts to PIL Image)
    
    Args:
        client: OptixClient instance
        key: Identifier for this plot
        fig: Matplotlib figure object
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        fig, ax = plt.subplots()
        ax.plot(x, y)
        result = client.log_matplotlib("my_plot", fig)
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    if not hasattr(fig, 'savefig'):
        raise ValueError(f"Expected matplotlib figure, got {type(fig).__name__}")
    
    # Convert figure to PIL Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    pil_image = Image.open(buf)
    
    # Log the image
    result = client.log_image(key, pil_image, meta)
    
    # Cleanup
    buf.close()
    
    return result


def log_plot(client, key: str, 
              x_data: Union[List, 'np.ndarray'], 
              y_data: Union[List, 'np.ndarray'],
              title: Optional[str] = None,
              xlabel: Optional[str] = None,
              ylabel: Optional[str] = None,
              figsize: Tuple[int, int] = (8, 6),
              style: str = '-',
              meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Create and log a simple plot from data (zero matplotlib boilerplate!)
    
    Args:
        client: OptixClient instance
        key: Identifier for this plot
        x_data: X-axis data
        y_data: Y-axis data
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size (width, height)
        style: Line style ('-', '--', 'o', etc.)
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        result = client.log_plot("loss_curve", steps, losses, 
                                  title="Training Loss", ylabel="Loss")
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(x_data, y_data, style)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Log it
    result = log_matplotlib(client, key, fig, meta)
    
    # Cleanup
    plt.close(fig)
    
    return result


def log_array_as_image(client, key: str, 
                         array: 'np.ndarray',
                         cmap: str = 'viridis',
                         title: Optional[str] = None,
                         colorbar: bool = True,
                         figsize: Tuple[int, int] = (8, 6),
                         meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Convert numpy array to heatmap and log it
    
    Args:
        client: OptixClient instance
        key: Identifier for this image
        array: 2D numpy array
        cmap: Colormap name ('viridis', 'hot', 'plasma', etc.)
        title: Plot title
        colorbar: Whether to show colorbar
        figsize: Figure size (width, height)
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        result = client.log_array_as_image("field_data", field_array, 
                                            cmap='hot', title="E-field")
    """
    if not HAS_NUMPY:
        raise ImportError("NumPy not installed. Install with: pip install numpy")
    
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    if not isinstance(array, np.ndarray):
        raise ValueError(f"Expected numpy array, got {type(array).__name__}")
    
    if array.ndim != 2:
        raise ValueError(f"Expected 2D array, got {array.ndim}D array")
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(array, cmap=cmap, aspect='auto', interpolation='nearest')
    
    if title:
        ax.set_title(title)
    
    if colorbar:
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    
    # Log it
    result = log_matplotlib(client, key, fig, meta)
    
    # Cleanup
    plt.close(fig)
    
    return result


def log_histogram(client, key: str, 
                   data: Union[List, 'np.ndarray'],
                   bins: int = 50,
                   title: Optional[str] = None,
                   xlabel: Optional[str] = None,
                   ylabel: str = "Count",
                   figsize: Tuple[int, int] = (8, 6),
                   meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Create and log a histogram
    
    Args:
        client: OptixClient instance
        key: Identifier for this histogram
        data: Data to plot
        bins: Number of bins
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        result = client.log_histogram("residuals", residuals, bins=100)
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    # Create histogram
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(data, bins=bins, alpha=0.7, edgecolor='black')
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Log it
    result = log_matplotlib(client, key, fig, meta)
    
    # Cleanup
    plt.close(fig)
    
    return result


def log_scatter(client, key: str,
                 x_data: Union[List, 'np.ndarray'],
                 y_data: Union[List, 'np.ndarray'],
                 title: Optional[str] = None,
                 xlabel: Optional[str] = None,
                 ylabel: Optional[str] = None,
                 figsize: Tuple[int, int] = (8, 6),
                 s: int = 20,
                 alpha: float = 0.7,
                 meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Create and log a scatter plot
    
    Args:
        client: OptixClient instance
        key: Identifier for this plot
        x_data: X-axis data
        y_data: Y-axis data
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        s: Marker size
        alpha: Marker transparency
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        result = client.log_scatter("correlation", x_vals, y_vals)
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    # Create scatter plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x_data, y_data, s=s, alpha=alpha)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Log it
    result = log_matplotlib(client, key, fig, meta)
    
    # Cleanup
    plt.close(fig)
    
    return result


def log_multiple_plots(client, key: str,
                        plots_data: List[Tuple[Union[List, 'np.ndarray'], Union[List, 'np.ndarray'], str]],
                        title: Optional[str] = None,
                        xlabel: Optional[str] = None,
                        ylabel: Optional[str] = None,
                        figsize: Tuple[int, int] = (10, 6),
                        meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
    """
    Create and log multiple lines on the same plot
    
    Args:
        client: OptixClient instance
        key: Identifier for this plot
        plots_data: List of (x_data, y_data, label) tuples
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        meta: Optional metadata
    
    Returns:
        MediaResult with URL
        
    Example:
        result = client.log_multiple_plots("comparison", [
            (steps, train_loss, "Train"),
            (steps, val_loss, "Validation"),
        ], title="Loss Curves")
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("Matplotlib not installed. Install with: pip install matplotlib")
    
    # Create plot with multiple lines
    fig, ax = plt.subplots(figsize=figsize)
    
    for x_data, y_data, label in plots_data:
        ax.plot(x_data, y_data, label=label)
    
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Log it
    result = log_matplotlib(client, key, fig, meta)
    
    # Cleanup
    plt.close(fig)
    
    return result


class HelperMethodsMixin:
    """
    Mixin class that adds helper methods to OptixClient.
    
    OptixClient should inherit from this to get all the helper methods
    with proper type hints.
    """
    
    def log_matplotlib(self, key: str, fig, meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Log a matplotlib figure directly (auto-converts to PIL Image)
        
        Args:
            key: Identifier for this plot
            fig: Matplotlib figure object
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_matplotlib(self, key, fig, meta)  # type: ignore
    
    def log_plot(self, key: str, 
                 x_data: Union[List, 'np.ndarray'], 
                 y_data: Union[List, 'np.ndarray'],
                 title: Optional[str] = None,
                 xlabel: Optional[str] = None,
                 ylabel: Optional[str] = None,
                 figsize: Tuple[int, int] = (8, 6),
                 style: str = '-',
                 meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Create and log a simple plot from data (zero matplotlib boilerplate!)
        
        Args:
            key: Identifier for this plot
            x_data: X-axis data
            y_data: Y-axis data
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size (width, height)
            style: Line style ('-', '--', 'o', etc.)
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_plot(self, key, x_data, y_data, title=title, xlabel=xlabel,  # type: ignore
                       ylabel=ylabel, figsize=figsize, style=style, meta=meta)
    
    def log_array_as_image(self, key: str, 
                           array: 'np.ndarray',
                           cmap: str = 'viridis',
                           title: Optional[str] = None,
                           colorbar: bool = True,
                           figsize: Tuple[int, int] = (8, 6),
                           meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Convert numpy array to heatmap and log it
        
        Args:
            key: Identifier for this image
            array: 2D numpy array
            cmap: Colormap name ('viridis', 'hot', 'plasma', etc.)
            title: Plot title
            colorbar: Whether to show colorbar
            figsize: Figure size (width, height)
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_array_as_image(self, key, array, cmap=cmap, title=title,  # type: ignore
                                  colorbar=colorbar, figsize=figsize, meta=meta)
    
    def log_histogram(self, key: str, 
                      data: Union[List, 'np.ndarray'],
                      bins: int = 50,
                      title: Optional[str] = None,
                      xlabel: Optional[str] = None,
                      ylabel: str = "Count",
                      figsize: Tuple[int, int] = (8, 6),
                      meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Create and log a histogram
        
        Args:
            key: Identifier for this histogram
            data: Data to plot
            bins: Number of bins
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_histogram(self, key, data, bins=bins, title=title,  # type: ignore
                            xlabel=xlabel, ylabel=ylabel, figsize=figsize, meta=meta)
    
    def log_scatter(self, key: str,
                    x_data: Union[List, 'np.ndarray'],
                    y_data: Union[List, 'np.ndarray'],
                    title: Optional[str] = None,
                    xlabel: Optional[str] = None,
                    ylabel: Optional[str] = None,
                    figsize: Tuple[int, int] = (8, 6),
                    s: int = 20,
                    alpha: float = 0.7,
                    meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Create and log a scatter plot
        
        Args:
            key: Identifier for this plot
            x_data: X-axis data
            y_data: Y-axis data
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size
            s: Marker size
            alpha: Marker transparency
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_scatter(self, key, x_data, y_data, title=title, xlabel=xlabel,  # type: ignore
                          ylabel=ylabel, figsize=figsize, s=s, alpha=alpha, meta=meta)
    
    def log_multiple_plots(self, key: str,
                           plots_data: List[Tuple[Union[List, 'np.ndarray'], Union[List, 'np.ndarray'], str]],
                           title: Optional[str] = None,
                           xlabel: Optional[str] = None,
                           ylabel: Optional[str] = None,
                           figsize: Tuple[int, int] = (10, 6),
                           meta: Optional[Dict[str, Any]] = None) -> Optional[MediaResult]:
        """
        Create and log multiple lines on the same plot
    
    Args:
            key: Identifier for this plot
            plots_data: List of (x_data, y_data, label) tuples
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size
            meta: Optional metadata
        
        Returns:
            MediaResult with URL
        """
        return log_multiple_plots(self, key, plots_data, title=title, xlabel=xlabel,  # type: ignore
                                  ylabel=ylabel, figsize=figsize, meta=meta)


# Legacy function - kept for backwards compatibility
def add_helper_methods(client):
    """
    Add helper methods to an OptixClient instance (legacy, use HelperMethodsMixin instead)
    """
    client.log_matplotlib = lambda key, fig, meta=None: log_matplotlib(client, key, fig, meta)
    client.log_plot = lambda key, x, y, **kwargs: log_plot(client, key, x, y, **kwargs)
    client.log_array_as_image = lambda key, array, **kwargs: log_array_as_image(client, key, array, **kwargs)
    client.log_histogram = lambda key, data, **kwargs: log_histogram(client, key, data, **kwargs)
    client.log_scatter = lambda key, x, y, **kwargs: log_scatter(client, key, x, y, **kwargs)
    client.log_multiple_plots = lambda key, plots_data, **kwargs: log_multiple_plots(client, key, plots_data, **kwargs)
    return client

