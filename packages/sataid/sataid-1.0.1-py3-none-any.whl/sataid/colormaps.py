"""
sataid_colormaps.py
Menyediakan skema warna kustom untuk visualisasi data satelit (EH, Rainbow, dll).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap, Normalize

# ============================================================
#  EH (Enhanced IR - BMKG Style)
# ============================================================

def _make_eh_colormap(units=None):
    """
    Skema 'EH' untuk channel IR (suhu puncak awan).
    """
    # Level default dalam Celcius (Source provided by user)
    levels_c = np.array(
        [-100., -80., -75., -69., -62., -56., -48., -41., -34., -28., -21., -13.,
         -7., 0., 8., 14., 21., 60.],
        dtype=float
    )

    # Penyesuaian jika unit adalah Kelvin
    if units is not None and "K" in str(units):
        levels = levels_c + 273.15
        label_units = "K"
    else:
        levels = levels_c
        label_units = "°C"

    # Source colors provided by user
    colors = (
        '#FE0000', '#FA5858', '#FFD4B8', '#FFC48D', '#FFA000', '#FF5D00',
        '#CD9A00', '#C5BB00', '#9CD300', '#8CFF00', '#00E686', '#00C091',
        '#43B0FF', '#4887FF', '#3462B4', '#0A4882', '#000000'
    )

    cmap = ListedColormap(colors, name="EH")
    norm = BoundaryNorm(levels, cmap.N)

    colorbar_label = f"Brightness Temperature ({label_units})"
    cbar_kwargs = {
        "ticks": levels,
        "spacing": "uniform",
    }
    return cmap, norm, colorbar_label, cbar_kwargs


# ============================================================
#  IR_GOES (GOES-16 Style)
# ============================================================

def _make_ir_goes_colormap(units=None):
    """
    Skema 'IR_GOES' (Replacing RAINBOW_IR).
    Style mirip GOES-16 Band 13 Clean IR.
    """
    # Levels (Celsius) matching general GOES enhancements:
    # Warm (Gray): > -30
    # Transition: -30 to -90ish
    # Cold (Purple/White): < -90
    
    # We define specific levels to capture the transitions.
    # Color segments will be uniform.
    levels_c = np.array(
        [-109, -100, -90,              # Cold tops (White/Purple/Pink)
         -80, -75, -70, -65, -60,     # Red/Black/Orange
         -55, -50, -45, -40,          # Yellow/Green
         -35, -30,                    # Blue/Cyan
         -20, -10, 0, 10, 20, 30, 40, 50, 60], # Grayscale warm
        dtype=float
    )

    if units is not None and "K" in str(units):
        levels = levels_c + 273.15
        label_units = "K"
    else:
        levels = levels_c
        label_units = "°C"

    # Hex colors approximating GOES-16 IR enhancement
    colors = [
        # < -90: White -> Pink -> Purple
        "#FFFFFF", "#FFC0CB", 
        # -90 to -80: Purple -> Black? Or just dark?
        # GOES often uses:
        # -80 to -60: Red to Dark Red / Black
        # Let's try to match image roughly:
        "#800080", # -90 to -80
        
        # -80 to -60: Black -> Red -> Orange ... wait
        # In image: 
        # Deepest cold (white/grey) surrounded by Red/Yellow/Green/Blue
        # Center of storm (coldest) is white/grey/black.
        # Ring 1 (Cold): Black/Red
        # Ring 2: Yellow
        # Ring 3: Green
        # Ring 4: Blue/Cyan
        
        # Let's follow tick levels:
        # -80 to -75: Dark Grey/Black
        "#000000",
        # -75 to -70: Dark Red
        "#8B0000",
        # -70 to -65: Red
        "#FF0000",
        # -65 to -60: Orange
        "#FF4500",
        
        # -60 to -55: Gold/Yellow
        "#FFD700",
        # -55 to -50: Yellow
        "#FFFF00",
        
        # -50 to -45: Green
        "#008000",
        # -45 to -40: Cyan/Teal
        "#00FFFF",
        
        # -40 to -35: Light Blue
        "#87CEEB",
        # -35 to -30: Blue
        "#0000FF",
        
        # -30 to 60: Grayscale (Warm)
        # 0 to 60 (7 intervals)
        "#404040", "#505050", "#606060", "#707070", "#808080", "#909090", "#A0A0A0", "#B0B0B0", "#C0C0C0"
    ]
    
    # Check count:
    # Levels length: 24
    # Expected colors: 23
    # My colors list: 2 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 9 = 22... need 1 more.
    # Let's adjust warm section or cold section.
    
    colors = [
        # < -100
        "#FFFFFF", 
        # -100 to -90
        "#E0A0E0", # Light Purple
        # -90 to -80
        "#800080", # Purple
        
        # -80 to -75
        "#000000", # Black
        # -75 to -70
        "#8B0000", # Dark Red
        # -70 to -65
        "#FF0000", # Red
        # -65 to -60
        "#FF8C00", # Dark Orange
        
        # -60 to -55
        "#FFA500", # Orange
        # -55 to -50
        "#FFFF00", # Yellow
        
        # -50 to -45
        "#00FF00", # Lime
        # -45 to -40
        "#008000", # Green
        
        # -40 to -35
        "#00FFFF", # Cyan
        # -35 to -30
        "#0000FF", # Blue
        
        # -30 to -20
        "#404040", 
        # -20 to -10
        "#505050",
        # -10 to 0
        "#606060",
        # 0 to 10
        "#707070",
        # 10 to 20
        "#808080",
        # 20 to 30
        "#909090",
        # 30 to 40
        "#A0A0A0",
        # 40 to 50
        "#B0B0B0",
        # 50 to 60
        "#C0C0C0"
    ]
    # Total colors: 23. Levels len 24. Correct.

    cmap = ListedColormap(colors, name="IR_GOES")
    norm = BoundaryNorm(levels, cmap.N)

    # Use 'uniform' spacing
    colorbar_label = f"Brightness Temperature ({label_units})"
    cbar_kwargs = {
        "ticks": levels,
        "spacing": "uniform",
    }
    return cmap, norm, colorbar_label, cbar_kwargs


# ============================================================
#  SW (Sandwich / Generic Gradient)
# ============================================================

def _make_sw_colormap(units=None):
    """
    Skema 'SW' (Sandwich / Generic Gradient).
    Combination of:
      - Top 25%: Jet Reversed (jet_r)
      - Bottom 75%: Binary (Grayscale)
    """
    # Create colormap by stacking jet_r and binary
    # 256 total steps: 64 steps jet_r (1/4), 192 steps binary (3/4)
    col1 = plt.cm.jet_r(np.linspace(0, 1, 64))
    col2 = plt.cm.binary(np.linspace(0, 1, 192))
    colors = np.vstack((col1, col2))
    
    cmap = LinearSegmentedColormap.from_list('SW', colors)
    
    # Range is explicitly set to -90 to 30 as per legacy script
    if units is not None and "K" in str(units):
        vmin, vmax = -90 + 273.15, 30 + 273.15
        label_units = "K"
    else:
        vmin, vmax = -90, 30
        label_units = "°C"
        
    norm = Normalize(vmin=vmin, vmax=vmax)
    
    colorbar_label = f"Brightness Temperature ({label_units})"
        
    cbar_kwargs = {}
    return cmap, norm, colorbar_label, cbar_kwargs


# ============================================================
#  WE (Water Vapor / Wet-Dry)
# ============================================================

def _make_we_colormap(units=None):
    """
    Skema 'WE' untuk Water Vapor.
    Colors: DarkBlue -> Blue -> White -> Black -> Orange -> DarkRed
    Range: -70 to 0 (typically)
    """
    colors = ['#151b54', '#0066cc', '#ffffff', '#000000', '#cc6600', '#660000']
    cmap = LinearSegmentedColormap.from_list('WE', colors)
    
    # User specified vmin=-70, vmax=0. 
    # Providing a Normalize object ensures consistent mapping.
    from matplotlib.colors import Normalize
    norm = Normalize(vmin=-70, vmax=0)
    
    if units:
        colorbar_label = f"Value ({units})"
    else:
        colorbar_label = "Value"
        
    cbar_kwargs = {}
    
    return cmap, norm, colorbar_label, cbar_kwargs


# ============================================================
#  FUNGSI PUBLIK (ENTRY POINT)
# ============================================================

def get_custom_colormap(name: str, channel_name: str = "", units: str = None):
    """
    Mengambil objek colormap berdasarkan nama.
    """
    if not isinstance(name, str):
        return None

    key = name.upper()
    
    # --- EH ---
    # Logika yang diperbarui: Langsung return jika nama cocok,
    # jangan terlalu peduli apakah channel-nya terdeteksi IR atau tidak.
    if key in ("EH", "EH_IR"):
        return _make_eh_colormap(units=units)

    # --- IR_GOES ---
    if key in ("IR_GOES", "RAINBOW_IR"): # Alias RAINBOW_IR to IR_GOES for now
        return _make_ir_goes_colormap(units=units)

    # --- SW ---
    if key == "SW":
        # Restrict to IR channels only (exclude Visible/NIR starting with V or N)
        if channel_name and channel_name[0].upper() in ('V', 'N'):
            print(f"Warning: Colormap '{name}' is not suitable for Visible/NIR channel '{channel_name}'. Using default.")
            # Return tuple of Nones to signal "Use Default"
            return None, None, None, None
        return _make_sw_colormap(units=units)

    # --- WE ---
    if key == "WE":
        # Check restrictions:
        # 1. Must be Water Vapor channel (starts with 'W')
        # 2. Units must be Brightness Temperature (not Reflectance)
        is_wv_channel = channel_name and channel_name.upper().startswith('W')
        is_temp_units = units and ('C' in str(units) or 'K' in str(units))
        
        if not is_wv_channel or not is_temp_units:
             print(f"Warning: Colormap '{name}' is restricted to Water Vapor channels. Using default.")
             # Return tuple of Nones to signal "Use Default"
             return None, None, None, None

        return _make_we_colormap(units=units)

    # Jika nama tidak ditemukan di daftar custom kami,
    # return None agar Matplotlib menggunakan colormap bawaannya (misal: 'jet', 'gray', 'rainbow')
    return None