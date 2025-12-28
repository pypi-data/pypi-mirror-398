from yta_constants.enum import YTAEnum as Enum


class ColorString(Enum):
    """
    The hexadecimal string that corresponds
    to the color.
    """
    
    WHITE = '#FFFFFF'
    BLACK = '#000000'
    RED = '#FF0000'
    GREEN = '#00FF00'
    BLUE = '#0000FF'

    # Primary and secondary colors
    YELLOW = '#FFFF00'
    CYAN = '#00FFFF'
    MAGENTA = '#FF00FF'

    # Grayscale
    GRAY = '#808080'
    LIGHT_GRAY = '#D3D3D3'
    DARK_GRAY = '#404040'

    # Common colors
    ORANGE = '#FFA500'
    PINK = '#FFC0CB'
    PURPLE = '#800080'
    BROWN = '#A52A2A'
    NAVY = '#000080'
    TEAL = '#008080'
    OLIVE = '#808000'
    MAROON = '#800000'
    LIME = '#32CD32'
    GOLD = '#FFD700'
    SILVER = '#C0C0C0'

    # TODO: Add colors from Manim or other libraries