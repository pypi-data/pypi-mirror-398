from .progress_manager import ProgressManager  
from .renderers import VerticalProgressRenderer
from .color_manager import ColorManager
from .trackers import UrlRequestTracker, ForLoopTracker, CountingTracker
import random
from typing import Union, List, Iterator
from functools import wraps


_COLORS = [
    "red", "green", "yellow", "blue", "magenta", "cyan",
    "white", "black", "bright_red", "bright_green",
    "bright_yellow", "bright_blue", "bright_magenta",
    "bright_cyan", "bright_white"
]


_active_loops = {}
_loop_counter = 0

def vertical(*args, label=None, labels=None, color=None, colors=None, height=4, spacing=3, **kwargs):
    """
    Simplified function for creating vertical progress bar(s).
    
    Default values:
    - height: 4
    - color: random (if not specified)
    - spacing: 3 (ignored for single bar)
    
    Usage Modes:
    
    1. Generator Mode (default):
        for item in vertical(list_of_items, label="Processing"):
            process(item)
    
    2. Context Manager Mode (new):
        for item in list_of_items:
            with vertical(label="Processing"):
                process(item)
    
    3. Parallel Mode (multiple iterables):
        results = list(vertical(iterable1, iterable2, labels=["Task A", "Task B"]))
    
    Args:
        *args: Varies by usage mode:
            - Generator mode: A single iterable
            - Parallel mode: Multiple iterables
            - Context mode: No arguments (used with 'with')
        label: Name for the progress bar (single bar mode)
        labels: Names for multiple progress bars (parallel mode)
        color: Color for the progress bar (single bar mode)
        colors: Colors for multiple progress bars (parallel mode)
        height: Height of progress bar(s) in terminal lines
        spacing: Horizontal spacing between bars (parallel mode)
        **kwargs: Additional arguments passed to trackers
    
    Returns:
        Generator mode: Generator yielding items from the iterable
        Parallel mode: List of results from processing all iterables
        Context mode: Context manager for manual progress updates
    
    Raises:
        ValueError: If no iterable is provided in generator mode
    
    Example:
        # Single bar
        for item in vertical(range(100), label="Processing", color="blue"):
            time.sleep(0.1)
        
        # Parallel bars
        results = list(vertical(range(50), range(75), 
                                labels=["Task A", "Task B"],
                                colors=["green", "cyan"]))
        
        # Context manager
        for item in range(100):
            with vertical(label="Step", height=6):
                process_item(item)
    """
    ColorManager.init_colorama()
    
    # Context manager mode
    if len(args) == 0 and 'iterable' not in kwargs:
        return _context_manager(label=label, color=color, 
                              height=height, spacing=spacing, **kwargs)
    
    # Parallel mode (multiple iterables)
    is_parallel = len(args) > 1
    
    if is_parallel:
        if labels is None:
            labels = [f"Process {i+1}" for i in range(len(args))]
        elif isinstance(labels, str):
            labels = [labels]
        
        if colors is None:
            colors = [random.choice(_COLORS) for _ in range(len(args))]
        elif isinstance(colors, str):
            colors = [colors]
        
        if len(colors) < len(args):
            colors = colors + [random.choice(_COLORS) for _ in range(len(args) - len(colors))]
        
        # Setup parallel tracking
        renderer = VerticalProgressRenderer(height=height, spacing=spacing)
        manager = ProgressManager(renderer)
        
        tracker = ForLoopTracker(manager)
        
        return tracker.track_parallel(args, labels=labels, colors=colors)
    
    else:
        # Single bar mode
        if len(args) == 0:
            raise ValueError("At least one iterable must be provided")
        
        iterable = args[0]
        
        if color is None:
            color = random.choice(_COLORS)
        
        if label is None:
            label = "Progress"
        
        # Setup single bar tracking
        renderer = VerticalProgressRenderer(height=height, spacing=spacing)
        manager = ProgressManager(renderer)
        
        return manager.track(iterable, label=label, fore_color=color, **kwargs)

class _VerticalContext:
    """
    Context manager for manual progress updates.
    
    Used internally by the vertical() function to provide context manager mode.
    
    Attributes:
        label (str): Label for the progress bar
        color (str): Color for the progress bar
        height (int): Height of the progress bar
        spacing (int): Spacing between bars (unused in single mode)
        loop_id (str, optional): ID for loop tracking
        manager (ProgressManager): Progress manager instance
        renderer (VerticalProgressRenderer): Renderer instance
    """
    def __init__(self, label, color, height, spacing, loop_id=None):
        self.label = label
        self.color = color
        self.height = height
        self.spacing = spacing
        self.loop_id = loop_id
        self.manager = None
        self.renderer = None
        
        if color is None:
            self.color = random.choice(_COLORS)
        
        if label is None:
            self.label = "Progress"
    
    def __enter__(self):
        """
        Enter the context manager.
        
        Updates progress if in a tracked loop, or initializes a new progress bar.
        """
        global _active_loops
        
        if self.loop_id and self.loop_id in _active_loops:
            # Update existing tracked loop
            data = _active_loops[self.loop_id]
            data['current'] += 1
            
            progress = min(
                (data['current'] / data['total']) * self.height,
                self.height
            )
            
            data['manager'].stages[0]['progress'] = progress
            data['renderer'].render(data['manager'].stages)
            
            if data['current'] >= data['total']:
                data['manager'].stages[0]['progress'] = self.height
                data['manager'].stages[0]['complete'] = True
                data['renderer'].render(data['manager'].stages)
                del _active_loops[self.loop_id]
        else:
            # Initialize new progress bar
            self.renderer = VerticalProgressRenderer(height=self.height, spacing=self.spacing)
            self.manager = ProgressManager(self.renderer)
            self.manager.add_stage(label=self.label, fore_color=self.color)
        
        return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

def _context_manager(label, color, height, spacing, **kwargs):
    """
    Creates a context manager for use with 'with' statement.
    
    Args:
        label: Label for the progress bar
        color: Color for the progress bar
        height: Height of the progress bar
        spacing: Spacing between bars
        **kwargs: Additional arguments
    
    Returns:
        _VerticalContext: Context manager instance
    """
    return _VerticalContext(label, color, height, spacing)

def track_loop(iterable, label=None, color=None, height=4, spacing=3):
    """
    Decorator for automatically tracking loop progress.
    
    Wraps a function to track progress while processing each item in an iterable.
    
    Default values:
    - height: 4
    - color: random
    
    Args:
        iterable: Iterable to process
        label: Label for the progress bar
        color: Color for the progress bar
        height: Height of the progress bar
        spacing: Spacing between bars
    
    Returns:
        function: Decorated function that tracks progress
    
    Example:
        @track_loop(range(100), label="Processing", color="green")
        def process_item(item):
            time.sleep(0.1)
            return item * 2
        
        results = process_item()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize progress tracking
            if color is None:
                use_color = random.choice(_COLORS)  # DEFAULT: random
            else:
                use_color = color
            
            if label is None:
                use_label = "Progress"
            else:
                use_label = label
            
            renderer = VerticalProgressRenderer(height=height, spacing=spacing)
            manager = ProgressManager(renderer)
            
            result = []
            for i, item in enumerate(iterable, 1):
                progress = min((i / len(iterable)) * height, height)
                manager.stages[0]['progress'] = progress
                renderer.render(manager.stages)
                
                result.append(func(item, *args, **kwargs))
            
            manager.stages[0]['progress'] = height
            manager.stages[0]['complete'] = True
            renderer.render(manager.stages)
            
            return result
        return wrapper
    return decorator

__all__ = [
    'ProgressManager', 
    'VerticalProgressRenderer',
    'ColorManager',
    'UrlRequestTracker',
    'ForLoopTracker',
    'CountingTracker',
    'vertical',
    'track_loop'
]

"""
Vertical Progress Bar Module

This module provides a comprehensive toolkit for creating and managing
vertical progress bars in terminal applications. It supports multiple
usage patterns including generators, context managers, and decorators.

Main Components:
    - ProgressManager: Central controller for progress tracking
    - VerticalProgressRenderer: Renders vertical progress bars to terminal
    - ColorManager: Handles terminal color codes and formatting
    - Various trackers for different use cases (URL requests, loops, counting)
    
Key Features:
    - Multiple progress bars running in parallel
    - Customizable colors, labels, and heights
    - Smooth terminal updates without flickering
    - Support for different progress tracking patterns
    - Automatic color selection

Typical Usage:
    import vertprogress as vp
    
    # Simple single bar
    for item in vp.vertical(range(100), label="Processing"):
        process(item)
    
    # Parallel processing
    results = list(vp.vertical(list1, list2, labels=["A", "B"]))
    
    # Using context manager
    for task in tasks:
        with vp.vertical(label="Task"):
            execute_task(task)
"""
