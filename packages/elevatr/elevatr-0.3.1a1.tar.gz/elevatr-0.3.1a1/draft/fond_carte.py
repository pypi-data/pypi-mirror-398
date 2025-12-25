import contextily as ctx
import matplotlib.pyplot as plt
from shapely.geometry import box
import geopandas as gpd

# Créer un GeoDataFrame pour la zone entière
world_bounds = box(-11.25, 48.922499263758226, 5.624999999999999, 61.60639637138628)
gdf = gpd.GeoDataFrame({"geometry": [world_bounds]}, crs="EPSG:4326")

# Convertir en projection Web Mercator (nécessaire pour contextily)
gdf = gdf.to_crs(epsg=3857)

# Obtenir les limites de la bbox en projection Web Mercator
bounds = gdf.total_bounds  # xmin, ymin, xmax, ymax

# Calculer les proportions de la bbox
width = bounds[2] - bounds[0]
height = bounds[3] - bounds[1]
aspect_ratio = width / height

# Configurer la figure avec le bon ratio
fig, ax = plt.subplots(figsize=(12, 12 / aspect_ratio))

# Définir les limites de l'axe sur la bbox
ax.set_xlim(bounds[0], bounds[2])
ax.set_ylim(bounds[1], bounds[3])

# Suppression des axes
ax.axis("off")

# Ajouter le fond de carte satellite sans texte de source
ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, attribution=False)

# Enregistrer l'image en PNG uniquement pour la zone bbox
output_file = "carte_bbox_sans_deformation.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0)

# Afficher la carte avec les limites rouges (facultatif, uniquement pour affichage)
gdf.boundary.plot(ax=ax, edgecolor="red")  # Montrer les limites pour la visualisation
plt.show()

print(f"L'image a été enregistrée sous le nom : {output_file}")
