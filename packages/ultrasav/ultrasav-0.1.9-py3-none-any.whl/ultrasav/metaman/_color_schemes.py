"""
Pastel Color Schemes for alternating_group_formats
These color sets can be used with the write_excel_with_merge and map_to_excel functions
to create professional, visually appealing Excel outputs with subtle pastel colors.

Each color set follows the pattern:
- First format: Darker pastel shade
- Second format: Lighter/white shade
- Both use professional font colors and subtle grey borders
"""


# Classic Grey Scale (current default)
CLASSIC_GREY = (
    {
        "bg_color": "#F5F5F5",      # Light grey
        "font_color": "#1A1A1A",     # Near black
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    },
    {
        "bg_color": "#FFFFFF",      # Pure white
        "font_color": "#2C2C2C",     # Charcoal grey
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    }
)

# Alternative Pastel Green (More Muted)
# Subtle, professional green tones that are easy on the eyes
PASTEL_GREEN_MUTED = (
    {
        "bg_color": "#ECF0EC",      # Muted sage
        "font_color": "#1A1A1A",     # Near black
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    },
    {
        "bg_color": "#F8FAF8",      # Barely green white
        "font_color": "#2C2C2C",     # Charcoal grey
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    }
)

# Alternative Pastel Blue (Cooler)
# Cool, calming blue-grey tones for a modern look
PASTEL_BLUE_COOL = (
    {
        "bg_color": "#E8EFF5",      # Cool blue-grey
        "font_color": "#1A1A1A",     # Near black
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    },
    {
        "bg_color": "#F5F8FB",      # Ice blue white
        "font_color": "#2C2C2C",     # Charcoal grey
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    }
)

# Alternative Pastel Purple (Warmer)
# Warm, soft purple tones for a sophisticated appearance
PASTEL_PURPLE_WARM = (
    {
        "bg_color": "#F2E9F3",      # Soft mauve
        "font_color": "#1A1A1A",     # Near black
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    },
    {
        "bg_color": "#FAF6FB",      # Whisper purple
        "font_color": "#2C2C2C",     # Charcoal grey
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    }
)

# Alternative Pastel Indigo
# Deep, calming indigo tones for a refined, elegant look
PASTEL_INDIGO = (
    {
        "bg_color": "#E8EAF6",      # Soft indigo
        "font_color": "#1A1A1A",     # Near black
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    },
    {
        "bg_color": "#F5F6FA",      # Whisper indigo
        "font_color": "#2C2C2C",     # Charcoal grey
        "border": 1,
        "border_color": "#D9D9D9",
        "valign": "vcenter"
    }
)


# Usage examples:
"""
from func_meta_df_write_to_excel_v5 import map_to_excel
from pastel_color_schemes import PASTEL_GREEN_MUTED, PASTEL_BLUE_COOL, PASTEL_PURPLE_WARM
import polars as pl

# Your DataFrame
df = pl.DataFrame({...})

# Use Muted Green scheme
map_to_excel(
    df, 
    "output_green.xlsx",
    alternating_group_formats=PASTEL_GREEN_MUTED
)

# Use Cool Blue scheme
map_to_excel(
    df,
    "output_blue.xlsx", 
    alternating_group_formats=PASTEL_BLUE_COOL
)

# Use Warm Purple scheme
map_to_excel(
    df,
    "output_purple.xlsx",
    alternating_group_formats=PASTEL_PURPLE_WARM
)
"""





# Quick reference for all color schemes
COLOR_SCHEMES = {
    "classic_grey": CLASSIC_GREY,
    "pastel_green": PASTEL_GREEN_MUTED,
    "pastel_blue": PASTEL_BLUE_COOL,
    "pastel_purple": PASTEL_PURPLE_WARM,
    "pastel_indigo": PASTEL_INDIGO,
}


def get_color_scheme(name: str):
    """
    Get a color scheme by name.
    
    Parameters
    ----------
    name : str
        Name of the color scheme. Options:
        - 'classic_grey': Classic grey scale (default)
        - 'pastel_green': Muted pastel green
        - 'pastel_blue': Cool pastel blue
        - 'pastel_purple': Warm pastel purple
        - 'pastel_indigo': Deep pastel indigo
    
    Returns
    -------
    tuple
        Alternating group formats for the specified color scheme
    
    Raises
    ------
    ValueError
        If the color scheme name is not recognized
    
    Example
    -------
    >>> from pastel_color_schemes import get_color_scheme
    >>> map_to_excel(df, "output.xlsx", alternating_group_formats=get_color_scheme("blue_cool"))
    """
    if name not in COLOR_SCHEMES:
        available = ", ".join(COLOR_SCHEMES.keys())
        raise ValueError(f"Unknown color scheme: {name}. Available: {available}")
    return COLOR_SCHEMES[name]
