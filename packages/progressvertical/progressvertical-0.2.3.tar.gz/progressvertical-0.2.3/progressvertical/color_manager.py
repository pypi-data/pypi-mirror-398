from colorama import Fore, Back, Style, init

class ColorManager:
    RESET = Style.RESET_ALL

    @classmethod
    def init_colorama(cls):
        init()

    @classmethod
    def get_fore_color(cls, color_name: str = None) -> str:
        if not color_name:
            return ""
        return getattr(Fore, color_name.upper(), "")

    @classmethod
    def get_back_color(cls, color_name: str = None) -> str:
        if not color_name:
            return ""
        return getattr(Back, color_name.upper(), "")

    @classmethod
    def get_style(cls, style_name: str = None) -> str:
        if not style_name:
            return ""
        return getattr(Style, style_name.upper(), "")

