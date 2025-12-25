import numpy as np

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

    with open(output_path, "w") as f:
        # Write vertices
        for y in range(0, height, reduce_quality):
            for x in range(0, width, reduce_quality):
                z = data[y, x] * zscale
                if np.isnan(z):
                    z = 0  # Handle NaN values
                f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

        if add_base:
            # Find the deepest point for the base depth
            min_z = np.nanmin(data) * zscale if not np.isnan(data).all() else 0
            base_z = min_z - 1  # Extend the base slightly below the lowest point

            # Add vertices for the base
            for y in range(0, height, reduce_quality):
                for x in range(0, width, reduce_quality):
                    f.write(f"v {x} {height - 1 - y} {base_z}\n")

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
                v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
                v2 = v1 + 1
                v3 = v1 + (width // reduce_quality)
                v4 = v3 + 1
                if texture_path:
                    f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
                else:
                    f.write(f"f {v1} {v3} {v4} {v2}\n")

        if add_base:
            # Connect the top mesh to the base
            top_offset = 0
            base_offset = (height // reduce_quality) * (width // reduce_quality)

            for y in range(0, height - reduce_quality, reduce_quality):
                for x in range(0, width - reduce_quality, reduce_quality):
                    top_v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
                    top_v2 = top_v1 + 1
                    base_v1 = top_v1 + base_offset
                    base_v2 = top_v2 + base_offset

                    # Connect the base to the top mesh
                    f.write(f"f {top_v1} {base_v1} {base_v2} {top_v2}\n")

            # Add the base faces (bottom side)
            for y in range(0, height - reduce_quality, reduce_quality):
                for x in range(0, width - reduce_quality, reduce_quality):
                    base_v1 = (
                        (y // reduce_quality) * (width // reduce_quality)
                        + (x // reduce_quality)
                        + 1
                        + base_offset
                    )
                    base_v2 = base_v1 + 1
                    base_v3 = base_v1 + (width // reduce_quality)
                    base_v4 = base_v3 + 1
                    f.write(f"f {base_v1} {base_v2} {base_v4} {base_v3}\n")

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

    def _download_basemap(self, file_path:str, zoom: Union[str, int] = 'auto') -> None:
        
        basemap_bounds = self.bounds
        basemap_bounds = box(*basemap_bounds)

        gdf = gpd.GeoDataFrame({"geometry": [basemap_bounds]}, crs="EPSG:3857")

        bounds = gdf.bounds

        fig, ax = plt.subplots()
        ax.set_xlim(bounds['minx'][0], bounds['maxx'][0])
        ax.set_ylim(bounds['miny'][0], bounds['maxy'][0])
        ax.axis("off")

        ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, attribution=False, zoom=zoom)

        plt.savefig(file_path, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)
    
from shapely.geometry import box
import geopandas as gpd
import contextily as ctx
Union