import time
from .color_manager import ColorManager
from .interfaces import ProgressTracker

class ForLoopTracker(ProgressTracker):
    def __init__(self, progress_manager):
        self.progress_manager = progress_manager
        self.original_height = None

    def track(self, iterable, label="Processing", **kwargs):
        """Track a single iterable with progress bar"""
        iterable = list(iterable)
        total = len(iterable)
        renderer = self.progress_manager.renderer
        
        # Store original height
        self.original_height = renderer.height
        
        try:
            # Auto-adjust height for small iterables
            if total <= renderer.height:
                renderer.height = total
            
            # Add progress stage
            self.progress_manager.add_stage(label=label, **kwargs)
            
            # Process items
            for i, item in enumerate(iterable, 1):
                progress = int((i / total) * renderer.height)
                self.progress_manager.stages[-1]['progress'] = progress
                self.progress_manager.renderer.render(self.progress_manager.stages)
                yield item
                
        finally:
            # Restore original settings
            if self.original_height:
                renderer.height = self.original_height
            # Complete the stage
            if self.progress_manager.stages:
                self.progress_manager.stages[-1]['progress'] = renderer.height
                self.progress_manager.stages[-1]['complete'] = True
                self.progress_manager.renderer.render(self.progress_manager.stages)

    def track_parallel(self, iterables, labels=None, colors=None):
        """Track multiple iterables with parallel progress bars"""
        iterables = [list(it) for it in iterables]
        max_steps = max(len(it) for it in iterables) if iterables else 0
        
        # Setup stages for each iterable
        for i, iterable in enumerate(iterables):
            label = labels[i] if labels else f"Process {i+1}"
            color = colors[i] if colors else None
            self.progress_manager.add_stage(label=label, fore_color=color)
        
        try:
            for step in range(max_steps):
                current_items = []
                for i, iterable in enumerate(iterables):
                    if step < len(iterable):
                        progress = int((step + 1) / len(iterable) * self.progress_manager.renderer.height)
                        self.progress_manager.stages[i]['progress'] = progress
                        current_items.append(iterable[step])
     
                self.progress_manager.renderer.render(self.progress_manager.stages)
    
                if len(iterables) == 1:
                    yield current_items[0] if current_items else None
                else:
                    yield current_items
                
                time.sleep(0.1)
                
        finally:
            
            for stage in self.progress_manager.stages:
                stage['progress'] = self.progress_manager.renderer.height
                stage['complete'] = True
            self.progress_manager.renderer.render(self.progress_manager.stages)


class CountingTracker(ProgressTracker):
    def __init__(self, progress_manager):
        self.progress_manager = progress_manager

    def track(self, total, label="Counting", **kwargs):
        """Track numeric progress from 0 to total"""
        renderer = self.progress_manager.renderer
        
        self.progress_manager.add_stage(label=label, **kwargs)
        
        try:
            for i in range(total + 1):
                progress = int((i / total) * renderer.height)
                self.progress_manager.stages[0]['progress'] = progress
                self.progress_manager.renderer.render(self.progress_manager.stages)
                yield i
        finally:
            # Complete the progress
            self.progress_manager.stages[0]['progress'] = renderer.height
            self.progress_manager.stages[0]['complete'] = True
            self.progress_manager.renderer.render(self.progress_manager.stages)


class UrlRequestTracker(ProgressTracker):
    def __init__(self, progress_manager):
        self.progress_manager = progress_manager

    def track(self, url, request_func, label="Downloading", **kwargs):
        """Track URL request progress"""
        renderer = self.progress_manager.renderer
        
        self.progress_manager.add_stage(label=label, **kwargs)
        
        def progress_callback(progress, total):
            if total > 0:
                current_progress = int((progress / total) * renderer.height)
                self.progress_manager.stages[0]['progress'] = current_progress
                self.progress_manager.renderer.render(self.progress_manager.stages)
        
        try:
            response = request_func(url, progress_callback=progress_callback)
            return response
        finally:
           
            self.progress_manager.stages[0]['progress'] = renderer.height
            self.progress_manager.stages[0]['complete'] = True
            self.progress_manager.renderer.render(self.progress_manager.stages)
