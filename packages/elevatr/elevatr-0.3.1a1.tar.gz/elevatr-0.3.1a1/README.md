<!---------------------------------------------->
<a name="readme-top"></a>
<!---------------------------------------------->
<h1 align="center">
  <br>
  <a href="https://github.com/titouanlegourrierec/elevatr"><img src="https://raw.githubusercontent.com/titouanlegourrierec/elevatr/main/assets/elv.png" alt="elevatr" width="120"></a>
  <br>
  elevatr
  <br>
</h1>

<h4 align="center">A Python package to simplify downloading and processing elevation data. </br>Enjoy exploring the heights of the world with <span style="color:#C49977">elevatr</span>! 🏔️🚀</h4>

<!---------------------------------------------->

<p align="center">
  <a href="https://pypi.org/project/elevatr/">
  <img src="https://img.shields.io/pypi/v/elevatr.svg"
    alt="PyPI Version">
  </a>
  <a href="https://github.com/titouanlegourrierec/elevatr/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-green.svg"
    alt="MIT License">
  </a>
  <a href="https://github.com/titouanlegourrierec/elevatr/actions/workflows/ci.yml">
  <img src="https://github.com/titouanlegourrierec/elevatr/actions/workflows/ci.yml/badge.svg"
    alt="CI status">
  </a>
  <a href="https://elevatr.readthedocs.io/">
  <img src="https://readthedocs.org/projects/elevatr/badge/?version=latest"
    alt="Docs status">
  </a>
  <a href="https://codecov.io/gh/titouanlegourrierec/elevatr">
  <img src="https://codecov.io/gh/titouanlegourrierec/elevatr/graph/badge.svg?token=zOM5QzMre6"
    alt="Coverage">
  </a>
  <a href="https://github.com/psf/black">
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg"
    alt="Code Style: Black">
  </a>
</p>

<p align="center">
    <br />
    <a href="https://elevatr.readthedocs.io/"><strong>Explore the docs »</strong></a>
    <br />
  </p>

<!---------------------------------------------->

## 🌄 Overview

`elevatr` is a Python library designed for downloading and processing elevation data. It is particularly useful for geospatial analyses and visualizations. The library supports high-resolution raster data and offers easy-to-use tools for displaying and exporting elevation information. 🗺️📊

<!---------------------------------------------->

## 📦 Installation

To install `elevatr`, run the following command:

```bash
pip install elevatr
```

<!---------------------------------------------->

## 🛠️ How To Use

### 📥 Download Elevation Data

Here is a simple example of how to use `elevatr` to download elevation data:

```python
import elevatr as elv

# Define the bounding box of the area of interest (min_lon, min_lat, max_lon, max_lat)
bbx = (-5.14, 41.33, 9.56, 51.09)

# Set the level of precision (between 0 and 14)
zoom = 6

# Access the elevation data
raster = elv.get_elev_raster(locations=bbx, zoom=zoom)
```
> **📝 Note:**
> Please choose the zoom level incrementally, a high level of zoom on a large area can take a lot of time and memory.

### 🖼️ Display the elevation data:

```python
raster.show(cmap='terrain', clip_zero=True)
```
#### 🌍 Example output:
<div style="text-align: center;">
    <img src="https://raw.githubusercontent.com/titouanlegourrierec/elevatr/main/assets/raster_example.png" alt="alt text" width="50%">
</div>

### 💾 Save to TIFF File

```python
raster.to_tif("elevation.tif")
```
Save your elevation data to a TIFF file for further use! 🗂️✨

<!---------------------------------------------->

## 🌐 Data Sources

### List of Sources

The underlying data sources are a mix of:

- **[3DEP](http://nationalmap.gov/elevation.html)**: Formerly NED and NED Topobathy in the United States, 10 meters outside of Alaska, 3 meters in select land and territorial water areas.
- **[ArcticDEM](http://nga.maps.arcgis.com/apps/MapSeries/index.html?appid=cf2fba21df7540fb981f8836f2a97e25)**: Strips of 5 meter mosaics across all of the land north of 60° latitude, including Alaska, Canada, Greenland, Iceland, Norway, Russia, and Sweden.
- **[CDEM](http://geogratis.gc.ca/api/en/nrcan-rncan/ess-sst/c40acfba-c722-4be1-862e-146b80be738e.html)**: Canadian Digital Elevation Model in Canada, with variable spatial resolution (from 20-400 meters) depending on the latitude.
- **[data.gov.uk](http://environment.data.gov.uk/ds/survey/index.jsp#/survey)**: 2 meters over most of the United Kingdom.
- **[data.gv.at](https://www.data.gv.at/katalog/dataset/b5de6975-417b-4320-afdb-eb2a9e2a1dbf)**: 10 meters over Austria.
- **[ETOPO1](https://www.ngdc.noaa.gov/mgg/global/global.html)**: For ocean bathymetry, 1 arc-minute resolution globally.
- **[EUDEM](https://www.eea.europa.eu/data-and-maps/data/eu-dem#tab-original-data)**: In most of Europe at 30 meter resolution, including Albania, Austria, Belgium, Bosnia and Herzegovina, Bulgaria, Croatia, Cyprus, Czechia, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Ireland, Italy, Kosovo, Latvia, Liechtenstein, Lithuania, Luxembourg, Macedonia, Malta, Montenegro, Netherlands, Norway, Poland, Portugal, Romania, Serbia, Slovakia, Slovenia, Spain, Sweden, Switzerland, and United Kingdom.
- **[Geoscience Australia's DEM of Australia](https://ecat.ga.gov.au/geonetwork/srv/eng/search#!22be4b55-2465-4320-e053-10a3070a5236)**: 5 meters around coastal regions in South Australia, Victoria, and Northern Territory.
- **[GMTED](http://topotools.cr.usgs.gov/gmted_viewer/)**: Globally, coarser resolutions at 7.5", 15", and 30" in land areas.
- **[INEGI](http://en.www.inegi.org.mx/temas/mapas/relieve/continental/)**: Continental relief in Mexico.
- **[Kartverket](http://data.kartverket.no/download/content/digital-terrengmodell-10-m-utm-33)**: Digital Terrain Model, 10 meters over Norway.
- **[LINZ](https://data.linz.govt.nz/layer/1768-nz-8m-digital-elevation-model-2012/)**: 8 meters over New Zealand.
- **[SRTM](https://lta.cr.usgs.gov/SRTM)**: Globally except high latitudes, 30 meters (90 meters nominal quality) in land areas.

### Data Sources per Zoom Level

| Zoom | Ocean | Land |
|------|-------|------|
| **0**  | `ETOPO1` | `ETOPO1` |
| **1**  | `ETOPO1` | `ETOPO1` |
| **2**  | `ETOPO1` | `ETOPO1` |
| **3**  | `ETOPO1` | `ETOPO1` |
| **4**  | `ETOPO1` | `GMTED` |
| **5**  | `ETOPO1` | `GMTED` |
| **6**  | `ETOPO1` | `GMTED` |
| **7**  | `ETOPO1` | `SRTM`, `NRCAN` in Canada, with `GMTED` in high latitudes above 60° |
| **8**  | `ETOPO1` | `SRTM`, `NRCAN` in Canada, with `GMTED` in high latitudes above 60° |
| **9**  | `ETOPO1` | `SRTM`, `NRCAN` in Canada, `EUDEM` in Europe, with `GMTED` in high latitudes above 60° |
| **10** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |
| **11** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec and 1/9 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |
| **12** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec and 1/9 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |
| **13** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec and 1/9 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |
| **14** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec and 1/9 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |
| **15** | `ETOPO1`, `NED Topobathy` in California | `SRTM`, `data.gov.at` in Austria, `NRCAN` in Canada, `SRTM`, `NED/3DEP` 1/3 arcsec and 1/9 arcsec, `data.gov.uk` in United Kingdom, `INEGI` in Mexico, `ArcticDEM` in latitudes above 60°, `LINZ` in New Zealand, `Kartverket` in Norway |

> **📝 Note:**
> Information about data sources is provided [here](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md).

<!---------------------------------------------->

## ⚖️ License

Elevatr is licensed under the **MIT License**. This means you are free to use, modify, and distribute this software. However, the software is provided “as is”, without warranty of any kind.

## 🙏 Acknowledgments

This package is inspired by the great [`elevatr`](https://github.com/USEPA/elevatr) package for the R language. It was this package that inspired me to create a similar package to ease access to this data for Python users.

<!---------------------------------------------->
<p align="right"><a href="#readme-top">back to top</a></p>
<!---------------------------------------------->


---

> GitHub [@titouanlegourrierec](https://github.com/titouanlegourrierec) &nbsp;&middot;&nbsp;
> Email [titouanlegourrierec@icloud.com](mailto:titouanlegourrierec@icloud.com)
