import time
from .color_manager import ColorManager

class ProgressManager:
    def __init__(self, renderer):
        self.stages = []
        self.renderer = renderer
        self._trackers = None

    def add_stage(self, label, duration=1.0, fore_color=None, back_color=None, style=None):
        """Adiciona um novo estágio de progresso"""
        self.stages.append({
            'label': label,
            'duration': duration,
            'progress': 0,
            'complete': False,
            'fore_color': ColorManager.get_fore_color(fore_color),
            'back_color': ColorManager.get_back_color(back_color),
            'style': ColorManager.get_style(style)
        })

    def track(self, iterable, label="Progresso", fore_color=None, back_color=None, style=None):
        """
        Rastreia um iterável com uma barra de progresso
        
        Args:
            iterable: Lista/iterável a ser processada
            label: Nome da barra de progresso
            fore_color: Cor da barra (opcional)
        
        Yields:
            Itens do iterável um por um
        """
        stage_idx = None
        for i, stage in enumerate(self.stages):
            if stage['label'] == label:
                stage_idx = i
                break
        
        if stage_idx is None:
            self.add_stage(label=label, fore_color=fore_color,
                         back_color=back_color, style=style)
            stage_idx = len(self.stages) - 1

        total = len(iterable) if hasattr(iterable, '__len__') else None
        render_height = self.renderer.height

        for i, item in enumerate(iterable):
            if total:
                self.stages[stage_idx]['progress'] = min(
                    (i + 1) / total * render_height,
                    render_height
                )
            else:
                self.stages[stage_idx]['progress'] = min(
                    self.stages[stage_idx]['progress'] + (render_height / 10),
                    render_height
                )
            
            self.renderer.render(self.stages)
            yield item

        self.stages[stage_idx]['progress'] = render_height
        self.stages[stage_idx]['complete'] = True
        self.renderer.render(self.stages)
