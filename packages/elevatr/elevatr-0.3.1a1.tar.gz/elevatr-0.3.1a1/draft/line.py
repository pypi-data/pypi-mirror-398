import math
import numpy as np
import pandas as pd
from typing import Tuple

def _lonlat_to_tilenum(lon_deg: float, lat_deg: float, zoom: int) -> Tuple[int, int]:
    """Convert geographic coordinates (longitude, latitude) to tile numbers at a specific zoom level."""
    lon_rad = math.radians(lon_deg)
    lat_rad = math.radians(lat_deg)

    x = (1 + (lon_rad / math.pi)) / 2
    y = (1 - (math.asinh(math.tan(lat_rad)) / math.pi)) / 2

    n_tiles = 2**zoom

    xtile = max(0, min(n_tiles - 1, int(x * n_tiles)))
    ytile = max(0, min(n_tiles - 1, int(y * n_tiles)))

    return xtile, ytile

def _bresenham_line(x0: int, y0: int, x1: int, y1: int) -> list:
    """Bresenham's line algorithm to determine the points on a line between two tiles.

    Parameters
    ----------
    x0, y0 : int
        Starting tile coordinates.
    x1, y1 : int
        Ending tile coordinates.

    Returns
    -------
    list
        List of (x, y) tuples representing the tiles crossed by the line.
    """
    tiles = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        tiles.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return tiles

def _get_tile_xy_for_line(point1: dict, point2: dict, zoom: int) -> pd.DataFrame:
    """Generate a DataFrame of tile coordinates along a line defined by two points at a specific zoom level.

    Parameters
    ----------
    point1 : dict
        A dictionary representing the first point with keys 'lon' and 'lat'.
        - 'lon' : float
            Longitude of the first point.
        - 'lat' : float
            Latitude of the first point.
    point2 : dict
        A dictionary representing the second point with keys 'lon' and 'lat'.
        - 'lon' : float
            Longitude of the second point.
        - 'lat' : float
            Latitude of the second point.
    zoom : int
        Zoom level, a non-negative integer where higher values correspond to more detailed tiles.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the tile coordinates along the line at the specified zoom level.
        The DataFrame has two columns:
        - 'tile_x' : int
            The tile number along the x-axis (longitude).
        - 'tile_y' : int
            The tile number along the y-axis (latitude).
    """
    # Convert points to tile numbers
    start_tile = _lonlat_to_tilenum(point1['lon'], point1['lat'], zoom)
    end_tile = _lonlat_to_tilenum(point2['lon'], point2['lat'], zoom)

    # Use Bresenham's line algorithm for tiles
    tiles = _bresenham_line(start_tile[0], start_tile[1], end_tile[0], end_tile[1])

    # Create DataFrame
    tile_df = pd.DataFrame(tiles, columns=["tile_x", "tile_y"])
    return tile_df

# Example usage
point1 = {'lon': -5.14, 'lat': 41.33}
point2 = {'lon': 9.56, 'lat': 51.09}
zoom = 6
tiles_df = _get_tile_xy_for_line(point1, point2, zoom)
print(tiles_df)
