import hashlib
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pyproj import CRS
from rasterio.plot import plotting_extent
from shapely.geometry import box

from . import settings
from .raster_operations import _reproject_raster


@dataclass
class Raster:
    """A class to manage raster data."""

    data: np.ndarray
    meta: Dict[str, Any]
    driver: str = field(init=False, default="GTiff")
    crs: Optional[Any] = field(init=False)
    height: Optional[int] = field(init=False)
    width: Optional[int] = field(init=False)
    count: int = field(init=False, default=1)
    dtype: Optional[str] = field(init=False)
    nodata: Optional[Any] = field(init=False)
    transform: Optional[Any] = field(init=False)
    bounds: Optional[Tuple[float, float, float, float]] = field(init=False)
    resolution: Optional[Dict[str, Any]] = field(init=False)
    imagery_sources: Optional[str] = field(init=False)

    def __post_init__(self):
        """Post-initialization method."""
        self.data = self.data[0]
        self.crs = self.meta.get("crs", None)
        self.height = self.meta.get("height", None)
        self.width = self.meta.get("width", None)
        self.dtype = self.meta.get("dtype", None)
        self.nodata = self.meta.get("nodata", None)
        self.transform = self.meta.get("transform", None)
        self.bounds = (
            float(self.transform[2]),
            float(self.transform[5] + self.height * self.transform[4]),
            float(self.transform[2] + self.width * self.transform[0]),
            float(self.transform[5]),
        )
        self.resolution = self._resolution()
        self.imagery_sources = self.meta.get("imagery_sources", None)

    def _resolution(self) -> Dict[str, Any]:
        resolution = (abs(self.transform[0]), abs(self.transform[4]))  # type: ignore

        if self.crs:
            crs_obj = CRS.from_user_input(self.crs)
            resolution_unit = crs_obj.axis_info[0].unit_name
        else:
            resolution_unit = "unknown"

        return {"x": resolution[0], "y": resolution[1], "unit": resolution_unit}

    def show(
        self,
        cmap: Optional[str] = "viridis",
        figsize: Optional[tuple] = (10, 10),
        clip_zero: Optional[bool] = False,
        clip_color: Optional[str] = "white",
        show_extras: Optional[bool] = True,
        file_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Display the raster data as an image.

        Parameters
        ----------
        cmap : str, optional
            The colormap to use for the image, by default "viridis".
        figsize : tuple, optional
            The size of the figure, by default (10, 10).
        clip_zero : bool, optional
            Whether to clip negative values to zero, by default False.
        clip_color : str, optional
            The color to use for clipped values, by default "white".
        show_extras : bool, optional
            Whether to show the colorbar and axis, by default True.
        file_path : str, optional
            The path to save the image to, by default None.
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.imshow`.
        """

        data = np.where(self.data < 0, np.nan, self.data) if clip_zero else self.data

        cmap = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap  # type: ignore
        if cmap is not None:
            cmap.set_bad(color=clip_color)  # type: ignore

        extent = plotting_extent(self.data, self.transform)
        fig, ax = plt.subplots(figsize=figsize)
        cax = ax.imshow(data, extent=extent, cmap=cmap, **kwargs)

        if show_extras:
            divider = make_axes_locatable(ax)
            cax_cb = divider.append_axes("right", size="3%", pad=0.05)
            fig.colorbar(cax, cax=cax_cb)
            ax.set_axis_on()
        else:  # pragma: no cover
            ax.axis("off")

        if file_path:  # pragma: no cover
            plt.savefig(file_path, bbox_inches="tight", pad_inches=0, dpi=300)

        plt.show()

    def to_numpy(self) -> np.ndarray:
        """Return the raster data as a NumPy array.

        Returns
        -------
        np.ndarray
            The raster data as a NumPy array.
        """
        return self.data

    def to_tif(self, path: str, compress: Optional[str] = None) -> None:
        """Write the raster data to a GeoTIFF file.

        Parameters
        ----------
        path : str
            The path to write the GeoTIFF file.
        compress : str, optional
            The compression type to use for the GeoTIFF file, by default None. Options are:

            - None: no compression
            - "lzw": Lempel-Ziv-Welch (LZW) compression, lossless, good for general use
            - "packbits": PackBits compression, simple and fast, but less efficient
            - "deflate": DEFLATE compression, lossless, balances speed and compression ratio
            - "zstd": Zstandard compression, lossless, high compression ratio and fast decompression
            - "lzma": LZMA compression, lossless, very high compression ratio but slower
        """
        valid_compressions = [None, "lzw", "packbits", "deflate", "zstd", "lzma"]
        if compress not in valid_compressions:
            raise ValueError(f"Invalid compression type: {compress}. Valid options are {valid_compressions}")

        self.meta.update(compress=compress)
        with rasterio.open(path, "w", **self.meta) as dst:
            dst.write(self.data, 1)

    def reproject(self, crs: str) -> None:
        """
        Reproject raster data to the desired CRS.

        Parameters
        ----------
        crs : str
            The target coordinate reference system (CRS) to reproject the raster to.

        Notes
        -----
        This method updates the class attributes in place. The original raster data is overwritten.
        """
        if self.crs != crs:
            self.data, self.meta = _reproject_raster(self.data, self.meta, crs)

            # Update the class attributes
            self.crs = self.meta["crs"]
            self.transform = self.meta["transform"]
            self.height, self.width = self.meta["height"], self.meta["width"]
            self.bounds = (
                float(self.transform[2]),
                float(self.transform[5] + self.height * self.transform[4]),
                float(self.transform[2] + self.width * self.transform[0]),
                float(self.transform[5]),
            )
            self.resolution = self._resolution()

    def to_obj(
        self,
        output_path: str,
        clip_zero: bool = False,
        zscale: float = 1.0,
        solid: bool = False,
        texture_path: Optional[str] = None,
    ):
        """
        Write the raster data to an OBJ file.

        Parameters
        ----------
        output_path : str
            The path to write the OBJ file.
        clip_zero : bool, optional
            Whether to clip negative values to zero (sea level), by default False.
        zscale : float, optional
            The scaling factor to apply to the z-axis. Decrease to attenuate elevation and increase
            to accentuate it, by default 1.0.
        solid : bool, optional
            Whether to add a base below the surface to create a solid object, by default False.
        texture_path : str, optional
            The path to the texture image file, by default None.
        """
        if clip_zero:
            data = np.where(self.data < 0, np.nan, self.data)
        else:  # pragma: no cover
            data = self.data

        if self.resolution:
            res = (self.resolution["x"] + self.resolution["y"]) / 2
            zscale = (1 / res) * zscale
        else:  # pragma: no cover
            raise ValueError("Resolution is not defined.")

        height, width = data.shape
        min_z = np.nanmin(data) * zscale if solid else 0  # Minimum z-value

        with open(output_path, "w") as f:
            # Write vertices
            for y in range(0, height):
                for x in range(0, width):
                    z = data[y, x] * zscale
                    if np.isnan(z):  # pragma: no cover
                        z = 0  # Handle NaN values
                    f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

            if solid:
                # Write base vertices
                for y in range(0, height):
                    for x in range(0, width):
                        f.write(f"v {x} {height - 1 - y} {min_z}\n")  # Base vertex

            # Write texture coordinates if texture_path is provided
            if texture_path:
                for y in range(0, height):
                    for x in range(0, width):
                        u = x / (width - 1)
                        v = (height - 1 - y) / (height - 1)
                        f.write(f"vt {u} {v}\n")

            # Write faces
            for y in range(0, height - 1):
                for x in range(0, width - 1):
                    v1 = y * width + x + 1
                    v2 = v1 + 1
                    v3 = v1 + width
                    v4 = v3 + 1
                    if texture_path:
                        f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
                    else:
                        f.write(f"f {v1} {v3} {v4} {v2}\n")

            if solid:
                base_offset = height * width
                # Write side faces
                for y in range(0, height - 1):
                    for x in range(0, width - 1):
                        v1 = y * width + x + 1
                        v2 = v1 + 1
                        v3 = v1 + width
                        v4 = v3 + 1
                        bv1 = v1 + base_offset
                        bv2 = v2 + base_offset
                        bv3 = v3 + base_offset
                        bv4 = v4 + base_offset
                        f.write(f"f {v1} {v2} {bv2} {bv1}\n")
                        f.write(f"f {v2} {v4} {bv4} {bv2}\n")
                        f.write(f"f {v4} {v3} {bv3} {bv4}\n")
                        f.write(f"f {v3} {v1} {bv1} {bv3}\n")

                # Write bottom face
                bottom_vertices = [
                    (0, 0),
                    (width - 1, 0),
                    (width - 1, height - 1),
                    (0, height - 1),
                ]
                bottom_indices = [y * width + x + 1 + base_offset for x, y in bottom_vertices]
                f.write(f"f {' '.join(map(str, bottom_indices))}\n")

        # Write the material file if texture_path is provided
        if texture_path:
            mtl_path = output_path.replace(".obj", ".mtl")
            with open(mtl_path, "w") as mtl_file:
                mtl_file.write("newmtl material_0\n")
                mtl_file.write(f"map_Kd {texture_path}\n")
            with open(output_path, "a") as f:
                f.write(f"mtllib {mtl_path}\n")

    def _download_basemap(
        self,
        file_path: str,
        zoom: Union[str, int] = "auto",
    ) -> None:
        """
        Download a basemap image of the raster data extent.

        Parameters
        ----------
        file_path : str
            The path to save the basemap image to.
        zoom : Union[str, int], optional
            The zoom level of the basemap image, by default 'auto'. Big zoom levels will result in
            higher resolution images.
        """

        basemap_bounds = self.bounds
        basemap_bounds = box(*basemap_bounds)

        gdf = gpd.GeoDataFrame({"geometry": [basemap_bounds]}, crs="EPSG:3857")
        bounds = gdf.bounds

        fig, ax = plt.subplots()
        ax.set_xlim(bounds["minx"][0], bounds["maxx"][0])
        ax.set_ylim(bounds["miny"][0], bounds["maxy"][0])
        ax.axis("off")

        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, attribution=False, zoom=zoom)

        plt.savefig(file_path, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)

    def show_3d(
        self,
        clip_zero: bool = False,
        zscale: float = 1.0,
        solid: bool = False,
        basemap_quality: Union[str, int] = "auto",
        transparent_background: bool = False,
        render_quality: int = 5,
        phi: float = 30,
        theta: float = 0,
        zoom: float = 1,
        light_intensity: float = 0.5,
        file_path: Optional[str] = None,
        cache_folder: Optional[str] = None,
        show: bool = True,
        verbose: bool = True,
    ):  # pragma: no cover
        """
        Display the raster data as a 3D model.

        Parameters
        ----------
        clip_zero : bool, optional
            Whether to clip negative values to zero (sea level), by default False.
        zscale : float, optional
            The scaling factor to apply to the z-axis. Decrease to attenuate elevation and increase
            to accentuate it, by default 1.0.
        solid : bool, optional
            Whether to add a base below the surface to create a solid object, by default False.
        basemap_quality : Union[str, int], optional
            The zoom level of the basemap image, by default 'auto'. Big zoom levels will result in
            higher resolution images.
        transparent_background : bool, optional
            Whether to use a transparent background for the rendered image, by default False.
        render_quality : int, optional
            The quality of the rendered image, by default 5. Higher values will result in higher resolution images.
        phi : float, optional
            The elevation angle in degrees, by default 30.
        theta : float, optional
            The angle of rotation around the z-axis in degrees, by default 0.
        zoom : float, optional
            The zoom level of the camera, by default 1.
        light_intensity : float, optional
            The intensity of the light source, by default 0.5.
        file_path : str, optional
            The path to save the rendered image to, by default None.
        cache_folder : str, optional
            The folder to store the cached basemap image, OBJ file, and rendered image, by default settings.cache_folder.
            NOTE: If you want to change the cache folder, it is recommended to set it with settings.cache_folder = "your_folder"
            just after the import to standardize the cache folder across the package.
        show : bool, optional
            Whether to display the rendered image, by default True.
        verbose : bool, optional
            Whether to display progress messages, by default True.

        Notes
        -----
        We use sha256 hashes to cache the basemap image, OBJ file, and rendered image. This allows us to avoid downloading
        the same basemap image multiple times and to avoid regenerating the OBJ file and rendering the image when the input
        parameters are the same.
        """

        cache_folder = cache_folder or settings.cache_folder
        cache_folder = os.path.abspath(cache_folder)
        os.makedirs(cache_folder, exist_ok=True)

        # Download basemap image
        basemap_hash = hashlib.sha256(
            str(
                {
                    "bounds": self.bounds,
                    "zoom": basemap_quality,
                }
            ).encode()
        ).hexdigest()
        basemap_path = os.path.join(cache_folder, f"basemap_{basemap_hash}.png")
        if not os.path.exists(basemap_path):
            if verbose:
                print("Downloading basemap image...")
            self._download_basemap(basemap_path, zoom=basemap_quality)

        # Generate OBJ file
        obj_hash = hashlib.sha256(
            str(
                {
                    "bounds": self.bounds,
                    "clip_zero": clip_zero,
                    "zscale": zscale,
                    "solid": solid,
                }
            ).encode()
        ).hexdigest()
        obj_path = os.path.join(cache_folder, f"raster_{obj_hash}.obj")

        if not os.path.exists(obj_path):
            if verbose:
                print("Generating 3D model...")
            self.to_obj(
                output_path=obj_path,
                clip_zero=clip_zero,
                zscale=zscale,
                solid=solid,
                texture_path=basemap_path,
            )

        # Display OBJ file
        render_hash = hashlib.sha256(
            str(
                {
                    "obj_path": obj_path,
                    "basemap_path": basemap_path,
                    "phi": phi,
                    "theta": theta,
                    "zoom": zoom,
                    "light_intensity": light_intensity,
                    "transparent_background": transparent_background,
                    "render_quality": render_quality,
                }
            ).encode()
        ).hexdigest()
        render_path = os.path.join(cache_folder, f"render_{render_hash}.png")

        if not os.path.exists(render_path):
            if verbose:
                print("Rendering 3D model...")

            mesh = pv.read(obj_path)
            texture = pv.read_texture(basemap_path)

            bounds = mesh.bounds
            x_center = (bounds[0] + bounds[1]) / 2
            y_center = (bounds[2] + bounds[3]) / 2
            z_center = (bounds[4] + bounds[5]) / 2
            max_extent = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
            camera_distance = 2 * max_extent

            p = pv.Plotter(off_screen=True)
            p.add_mesh(mesh, texture=texture)
            p.camera.position = (x_center + camera_distance, y_center + camera_distance, z_center)
            p.camera.focal_point = (x_center, y_center, z_center)
            p.camera.zoom(zoom)
            p.camera.elevation = phi
            p.camera.azimuth = theta

            light = pv.Light()
            light.intensity = light_intensity
            p.add_light(light)

            p.screenshot(render_path, transparent_background=transparent_background, scale=render_quality)
            p.close()

        if file_path:  # pragma: no cover
            shutil.copy(render_path, file_path)

        if show:
            plt.figure(figsize=(10, 10))
            plt.imshow(plt.imread(render_path))
            plt.axis("off")
            plt.tight_layout()
            plt.show()

    def quit(self, cache_folder: Optional[str] = None) -> None:
        """Delete the cache directory."""
        cache_folder = cache_folder or settings.cache_folder
        cache_folder = os.path.abspath(cache_folder)
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder)
