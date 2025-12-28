from enum import Enum

# https://rich.readthedocs.io/en/stable/appendix/colors.html
class ColorScheme(str, Enum):
    GIT_HEADLESS = "orange_red1"
    WARNING = "orange_red1"
    USEFUL_INFO = "deep_sky_blue1"
    SUCCESS = "green"
