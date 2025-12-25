import os
import shutil
from typing import Optional, Tuple
import numpy as np
from affine import Affine

from .downloader import _get_aws_terrain
from .raster_operations import _merge_rasters

def get_elev_point(
    location: Tuple[float, float],
    zoom: Optional[int] = 14,
    cache_folder: Optional[str] = "./cache",
    use_cache: Optional[bool] = True,
    delete_cache: Optional[bool] = True,
    verbose: Optional[bool] = True,
) -> float:
    """
    Get elevation for a specific point.

    Parameters
    ----------
    location : Tuple[float, float]
        Coordinates of the point (lon, lat) in WGS84/EPSG:4326.
    zoom : int
        Zoom level of the raster. Between 0 and 14.
    cache_folder : Optional[str], optional
        Folder to store the downloaded tiles, by default "./cache"
    use_cache : Optional[bool], optional
        Use the cache if available, by default True
    delete_cache : Optional[bool], optional
        Delete the cache folder after the raster is created, by default True
    verbose : Optional[bool], optional
        Print progress messages, by default True

    Returns
    -------
    float
        Elevation at the specified point.

    Examples
    --------
    >>> from elevatr import get_elev_point
    >>> location = (-122.5, 37.5)
    >>> zoom = 8
    >>> elevation = get_elev_point(location, zoom)
    """
    # Validate inputs
    is_valid_location = (
        isinstance(location, tuple)
        and len(location) == 2
        and all(isinstance(x, (int, float)) for x in location)
        and -180 <= location[0] <= 180  # Longitude
        and -90 <= location[1] <= 90  # Latitude
    )
    assert is_valid_location, (
        "location must be a tuple of length 2 containing only integers or floats. "
        "Longitude must be between -180 and 180. Latitude must be between -90 and 90."
    )

    assert (
        isinstance(zoom, int) and 0 <= zoom <= 14
    ), "zoom must be an integer between 0 and 14."
    assert isinstance(cache_folder, str), "cache_folder must be a string."
    assert isinstance(use_cache, bool), "use_cache must be a boolean."
    assert isinstance(delete_cache, bool), "delete_cache must be a boolean."
    assert isinstance(verbose, bool), "verbose must be a boolean."

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    # Create a bounding box around the point to download the necessary tiles
    lon, lat = location
    bbx = (lon - 0.0001, lat - 0.0001, lon + 0.0001, lat + 0.0001)

    downloaded_tiles = _get_aws_terrain(
        bbx=bbx,
        zoom=zoom,
        cache_folder=cache_folder,
        use_cache=use_cache,
        verbose=verbose,
    )

    if verbose:
        print("Mosaicing tiles.")
        mosaic, meta = _merge_rasters(downloaded_tiles)
    else:
        mosaic, meta = _merge_rasters(downloaded_tiles)
    
    print(max(mosaic[0].flatten()))
    print(min(mosaic[0].flatten()))

    transform = Affine.from_gdal(*meta['transform'][:6])
    inv_transform = ~transform

    col, row = inv_transform * (lon, lat)

    elevation = mosaic[0, int(row), int(col)]

    if delete_cache:
        shutil.rmtree(cache_folder)

    return elevation
