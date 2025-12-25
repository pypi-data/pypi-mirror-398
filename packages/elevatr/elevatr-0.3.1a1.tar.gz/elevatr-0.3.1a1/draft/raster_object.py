import math

import contextily as ctx
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio.plot import plotting_extent


class Raster:
    def __init__(self, data: np.ndarray, meta: dict):
        self.data = data[0]
        self.meta = meta
        self.driver = "GTiff"
        self.crs = meta.get("crs", None)
        self.height = meta.get("height", None)
        self.width = meta.get("width", None)
        self.count = meta.get("count", 1)
        self.dtype = meta.get("dtype", None)
        self.nodata = meta.get("nodata", None)
        self.transform = meta.get("transform", None)
        self.shape = (self.height, self.width)

    def plot(self, clip_zero: bool = False):

        if clip_zero:
            data = np.where(self.data < 0, np.nan, self.data)
        else:
            data = self.data

        extent = plotting_extent(self.data, self.transform)
        fig, ax = plt.subplots(figsize=(10, 10))
        cax = ax.imshow(data, cmap="terrain", extent=extent)

        divider = make_axes_locatable(ax)
        cax_cb = divider.append_axes("right", size="3%", pad=0.05)
        fig.colorbar(cax, cax=cax_cb)

        plt.show()

    def to_tif(self, output_path: str):
        meta = self.meta.copy()
        meta.update(
            {
                "count": 1,
                "height": self.data.shape[0],
                "width": self.data.shape[1],
                "dtype": self.data.dtype,
            }
        )
        with rasterio.open(output_path, "w", **meta) as dest:
            dest.write(self.data, 1)

    def to_numpy(self):
        return self.data

    def to_png(self, output_path: str, clip_zero: bool = False, cmap: str = "terrain"):
        if clip_zero:
            data = np.where(self.data < 0, np.nan, self.data)
        else:
            data = self.data

        cmap = plt.get_cmap(cmap)
        cmap.set_bad(color="white")
        plt.imsave(
            output_path, data, cmap=cmap, format="png", vmin=0, vmax=np.nanmax(data)
        )

    # def to_obj(self, output_path: str, texture_path: str = None, clip_zero: bool = False, zscale: float = 1.0):
    #     if clip_zero:
    #         data = np.where(self.data < 0, np.nan, self.data)
    #     else:
    #         data = self.data

    #     height, width = data.shape

    #     with open(output_path, 'w') as f:
    #         # Write vertices
    #         for y in range(height):
    #             for x in range(width):
    #                 z = data[y, x] * zscale
    #                 if np.isnan(z):
    #                     z = 0  # Handle NaN values
    #                 f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

    #         # Write texture coordinates
    #         if texture_path:
    #             for y in range(height):
    #                 for x in range(width):
    #                     u = x / (width - 1)
    #                     v = 1 - y / (height - 1)  # Correct v-axis inversion
    #                     f.write(f"vt {u} {v}\n")

    #         # Write faces
    #         for y in range(height - 1):
    #             for x in range(width - 1):
    #                 v1 = y * width + x + 1
    #                 v2 = v1 + 1
    #                 v3 = v1 + width
    #                 v4 = v3 + 1
    #                 if texture_path:
    #                     f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
    #                 else:
    #                     f.write(f"f {v1} {v3} {v4} {v2}\n")

    #     # Write the material file if texture is provided
    #     if texture_path:
    #         mtl_path = output_path.replace('.obj', '.mtl')
    #         with open(mtl_path, 'w') as f:
    #             f.write("newmtl material_0\n")
    #             f.write(f"map_Kd {texture_path}\n")

    #         # Add reference to the material file in the OBJ file
    #         with open(output_path, 'r+') as f:
    #             content = f.read()
    #             f.seek(0, 0)
    #             f.write(f"mtllib {mtl_path}\n" + content)

    # def to_obj(self, output_path: str, texture_path: str = None, clip_zero: bool = False, zscale: float = 1.0, reduce_quality: int = 1, add_base: bool = False):
    #         if clip_zero:
    #             data = np.where(self.data < 0, np.nan, self.data)
    #         else:
    #             data = self.data

    #         height, width = data.shape

    #         with open(output_path, 'w') as f:
    #             # Write vertices
    #             for y in range(0, height, reduce_quality):
    #                 for x in range(0, width, reduce_quality):
    #                     z = data[y, x] * zscale
    #                     if np.isnan(z):
    #                         z = 0  # Handle NaN values
    #                     f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

    #             # Write texture coordinates
    #             if texture_path:
    #                 for y in range(0, height, reduce_quality):
    #                     for x in range(0, width, reduce_quality):
    #                         u = x / (width - 1)
    #                         v = 1 - y / (height - 1)  # Correct v-axis inversion
    #                         f.write(f"vt {u} {v}\n")

    #             # Write faces
    #             for y in range(0, height - reduce_quality, reduce_quality):
    #                 for x in range(0, width - reduce_quality, reduce_quality):
    #                     v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
    #                     v2 = v1 + 1
    #                     v3 = v1 + (width // reduce_quality)
    #                     v4 = v3 + 1
    #                     if texture_path:
    #                         f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
    #                     else:
    #                         f.write(f"f {v1} {v3} {v4} {v2}\n")

    #             # Add base if requested
    #             if add_base:
    #                 base_height = -100  # Adjust the height of the base as needed
    #                 for y in range(0, height, reduce_quality):
    #                     for x in range(0, width, reduce_quality):
    #                         f.write(f"v {x} {height - 1 - y} {base_height}\n")

    #                 base_offset = (height // reduce_quality) * (width // reduce_quality)
    #                 for y in range(0, height - reduce_quality, reduce_quality):
    #                     for x in range(0, width - reduce_quality, reduce_quality):
    #                         v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
    #                         v2 = v1 + 1
    #                         v3 = v1 + (width // reduce_quality)
    #                         v4 = v3 + 1
    #                         b1 = v1 + base_offset
    #                         b2 = v2 + base_offset
    #                         b3 = v3 + base_offset
    #                         b4 = v4 + base_offset
    #                         f.write(f"f {v1} {v2} {b2} {b1}\n")
    #                         f.write(f"f {v3} {v4} {b4} {b3}\n")
    #                         f.write(f"f {v1} {v3} {b3} {b1}\n")
    #                         f.write(f"f {v2} {v4} {b4} {b2}\n")

    #         # Write the material file if texture is provided
    #         if texture_path:
    #             mtl_path = output_path.replace('.obj', '.mtl')
    #             with open(mtl_path, 'w') as f:
    #                 f.write("newmtl material_0\n")
    #                 f.write(f"map_Kd {texture_path}\n")

    #             # Add reference to the material file in the OBJ file
    #             with open(output_path, 'r+') as f:
    #                 content = f.read()
    #                 f.seek(0, 0)
    #                 f.write(f"mtllib {mtl_path}\n" + content)

    def to_obj(
        self,
        output_path: str,
        texture_path: str = None,
        clip_zero: bool = False,
        zscale: float = 1.0,
        reduce_quality: int = 1,
        add_base: bool = False,
    ):
        if clip_zero:
            data = np.where(self.data < 0, np.nan, self.data)
        else:
            data = self.data

        height, width = data.shape

        # Generate background texture if not provided
        # if texture_path is None:
        #     extent = plotting_extent(self.data, self.transform)
        #     fig, ax = plt.subplots(figsize=(10, 10))
        #     ax.set_xlim(extent[0], extent[2])
        #     ax.set_ylim(extent[1], extent[3])
        #     ax.axis('off')
        #     ctx.add_basemap(ax, crs=pyproj.CRS.from_epsg(3857), source=ctx.providers.Esri.WorldImagery) # crs=pyproj.CRS.from_epsg(3857)
        #     fig.canvas.draw()
        #     texture_path = output_path.replace('.obj', '_texture.png')
        #     fig.savefig(texture_path, bbox_inches='tight', pad_inches=0, transparent=True)
        #     plt.close(fig)

        def calculate_zoom_level(extent):
            """Calculate the appropriate zoom level based on the extent.

            This is a simple heuristic and may need adjustment based on your specific requirements.
            """
            lon_diff = extent[2] - extent[0]
            lat_diff = extent[3] - extent[1]

            # Calculate the zoom level based on the larger difference
            max_diff = max(lon_diff, lat_diff)

            # This is a heuristic formula to calculate zoom level
            zoom_level = int(math.log2(360 / max_diff))

            # Ensure the zoom level is within a reasonable range
            zoom_level = max(0, min(zoom_level, 18))

            return zoom_level

        if texture_path is None:
            extent = plotting_extent(self.data, self.transform)
            fig, ax = plt.subplots(
                figsize=(10, 10)
            )  # Further increase figsize and dpi for higher resolution
            ax.set_xlim(extent[0], extent[2])
            ax.set_ylim(extent[1], extent[3])
            ax.axis("off")

            # Calculate appropriate zoom level
            zoom_level = calculate_zoom_level(extent)
            ctx.add_basemap(
                ax,
                crs=pyproj.CRS.from_epsg(3857),
                zoom=zoom_level,
                source=ctx.providers.OpenStreetMap.Mapnik,
            )

            fig.canvas.draw()
            texture_path = output_path.replace(".obj", "_texture.png")
            fig.savefig(
                texture_path, bbox_inches="tight", pad_inches=0, transparent=True
            )
            plt.close(fig)

        with open(output_path, "w") as f:
            # Write vertices
            for y in range(0, height, reduce_quality):
                for x in range(0, width, reduce_quality):
                    z = data[y, x] * zscale
                    if np.isnan(z):
                        z = 0  # Handle NaN values
                    f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

            # Write texture coordinates
            if texture_path:
                for y in range(0, height, reduce_quality):
                    for x in range(0, width, reduce_quality):
                        u = x / (width - 1)
                        v = 1 - y / (height - 1)  # Correct v-axis inversion
                        f.write(f"vt {u} {v}\n")

            # Write faces
            for y in range(0, height - reduce_quality, reduce_quality):
                for x in range(0, width - reduce_quality, reduce_quality):
                    v1 = (
                        (y // reduce_quality) * (width // reduce_quality)
                        + (x // reduce_quality)
                        + 1
                    )
                    v2 = v1 + 1
                    v3 = v1 + (width // reduce_quality)
                    v4 = v3 + 1
                    if texture_path:
                        f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
                    else:
                        f.write(f"f {v1} {v3} {v4} {v2}\n")

            # Add base if requested
            if add_base:
                base_height = -100  # Adjust the height of the base as needed
                for y in range(0, height, reduce_quality):
                    for x in range(0, width, reduce_quality):
                        f.write(f"v {x} {height - 1 - y} {base_height}\n")

                base_offset = (height // reduce_quality) * (width // reduce_quality)
                for y in range(0, height - reduce_quality, reduce_quality):
                    for x in range(0, width - reduce_quality, reduce_quality):
                        v1 = (
                            (y // reduce_quality) * (width // reduce_quality)
                            + (x // reduce_quality)
                            + 1
                        )
                        v2 = v1 + 1
                        v3 = v1 + (width // reduce_quality)
                        v4 = v3 + 1
                        b1 = v1 + base_offset
                        b2 = v2 + base_offset
                        b3 = v3 + base_offset
                        b4 = v4 + base_offset
                        f.write(f"f {v1} {v2} {b2} {b1}\n")
                        f.write(f"f {v3} {v4} {b4} {b3}\n")
                        f.write(f"f {v1} {v3} {b3} {b1}\n")
                        f.write(f"f {v2} {v4} {b4} {b2}\n")

        # Write the material file if texture is provided
        if texture_path:
            mtl_path = output_path.replace(".obj", ".mtl")
            with open(mtl_path, "w") as f:
                f.write("newmtl material_0\n")
                f.write(f"map_Kd {texture_path}\n")

            # Add reference to the material file in the OBJ file
            with open(output_path, "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write(f"mtllib {mtl_path}\n" + content)
