from contextlib import ExitStack
from typing import Any, Dict, List, Tuple

import numpy as np
import pyproj
import rasterio
import rioxarray  # noqa: F401
import xarray as xr
from rasterio.merge import merge
from rasterio.windows import from_bounds

from .utils import _convert_bbox_crs


def _merge_rasters(raster_list: List[str]) -> Tuple[np.ndarray, dict]:
    """Merge a list of rasters into a single raster.

    Parameters
    ----------
    raster_list : List[str]
        List of paths to rasters to merge.

    Returns
    ----------
    mosaic : np.ndarray
        The merged raster data as a NumPy array.
    meta : dict
        Metadata for the merged raster, including driver, CRS, height, width, and transform.

    Examples
    --------
    >>> raster_list = ["raster1.tif", "raster2.tif", "raster3.tif"]
    >>> mosaic, meta = merge_rasters(raster_list)
    """

    imagery_sources_set = set()

    with rasterio.open(raster_list[0]) as first_raster:
        with ExitStack() as stack:
            rasters = [first_raster] + [
                stack.enter_context(rasterio.open(raster)) for raster in raster_list[1:]
            ]
            mosaic, out_trans = merge(rasters, nodata=-9999)

            # Collect imagery sources from each raster
            for raster in rasters:
                sources = raster.tags().get("imagery_sources", "")
                imagery_sources_set.update(sources.split(", "))

            meta = first_raster.meta.copy()
            meta.update(
                {
                    "driver": "GTiff",
                    "crs": pyproj.CRS.from_epsg(3857),  # Web Mercator projection
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                    "nodata": -9999,
                    "imagery_sources": ", ".join(sorted(imagery_sources_set)),
                }
            )

    return mosaic, meta


def _clip_bbx(
    data: np.ndarray,
    meta: Dict[str, Any],
    bbx: Tuple[float, float, float, float],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Clip a raster to a bounding box.

    Parameters
    ----------
    data : np.ndarray
        The raster data as a NumPy array.
    meta : dict
        Metadata for the raster, including driver, CRS, height, width, and transform.
    bbx : tuple
        A tuple representing the bounding box with coordinates (xmin, ymin, xmax, ymax).
        xmin and xmax are the minimum and maximum longitudes, ymin and ymax are the minimum and
        maximum latitudes.

    Returns
    ----------
    data : np.ndarray
        The clipped raster data as a NumPy array.
    meta : dict
        Metadata for the clipped raster, including driver, CRS, height, width, and transform.
    """

    with rasterio.io.MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(data)

            web_mercator_bbox = _convert_bbox_crs(bbx, crs_from="EPSG:4326", crs_to="EPSG:3857")

            # Calculate the window to clip
            window = from_bounds(*web_mercator_bbox, transform=dataset.transform)

            # Read the data in this window
            data = dataset.read(window=window)
            transform = dataset.window_transform(window)

    meta.update(transform=transform, height=data.shape[1], width=data.shape[2])

    return data, meta


def _reproject_raster(data: np.ndarray, meta: Dict[str, Any], crs: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Reproject raster data to the desired CRS.

    Parameters
    ----------
    data : np.ndarray
        The raster data to be reprojected.
    meta : dict
        The metadata of the raster, containing information such as transform, crs, width, height.
    target_crs : str
        The target coordinate reference system (CRS) to reproject the raster to.

    Returns
    -------
    tuple
        A tuple containing the reprojected data (np.ndarray) and updated meta (dict).
    """
    # CRS verification
    try:
        _ = pyproj.CRS(crs)
    except pyproj.exceptions.CRSError:
        raise ValueError(f"Invalid CRS: {crs}")

    # Reprojection logic using xarray and rioxarray
    dataarray = xr.DataArray(
        data,
        dims=("y", "x"),
        coords={
            "x": np.linspace(
                meta["transform"][2],
                meta["transform"][2] + meta["transform"][0] * meta["width"],
                meta["width"],
            ),
            "y": np.linspace(
                meta["transform"][5],
                meta["transform"][5] + meta["transform"][4] * meta["height"],
                meta["height"],
            ),
        },
    )

    # Assign original CRS
    dataarray.rio.write_crs(meta.get("crs"), inplace=True)

    # Reproject to the target CRS
    reprojected = dataarray.rio.reproject(crs)

    # Update the meta dictionary with new values
    new_meta = meta.copy()
    new_meta.update(
        {
            "crs": crs,
            "transform": reprojected.rio.transform(),
            "height": reprojected.shape[0],
            "width": reprojected.shape[1],
            "bounds": (
                float(reprojected.x.min()),
                float(reprojected.y.max()),
                float(reprojected.x.max()),
                float(reprojected.y.min()),
            ),
        }
    )

    return reprojected.values, new_meta
