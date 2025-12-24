from abc import ABC, abstractmethod

class ProgressRenderer(ABC):
    @abstractmethod
    def render(self, progress_data: list) -> None:
        pass

class ProgressTracker(ABC):
    @abstractmethod
    def track(self, *args, **kwargs):
        pass
