# Public data sources

The worked global-health example records candidate sources under `evidence`, alongside `claim`, `status`, and `notes`. These portals are starting points, not verified evidence or endorsements for a particular analysis. No dataset was retrieved for the example, and the notebooks do not check links or claims automatically.

| Source | Link | Notes |
|---|---|---|
| WHO Global Health Observatory | https://www.who.int/data/gho | Global health indicators and country-level statistics. |
| WHO GHO OData API | https://www.who.int/data/gho/info/gho-odata-api | Programmatic retrieval of GHO indicators. |
| World Bank Open Data | https://data.worldbank.org/ | Development, population, socioeconomic, environment, and health indicators. |
| NASA Earthdata | https://www.earthdata.nasa.gov/ | Earth-observation and environmental data. |
| NOAA Climate Data Online | https://www.ncei.noaa.gov/cdo-web/ | Weather and climate observations. |
| Copernicus Climate Data Store | https://cds.climate.copernicus.eu/ | Climate reanalysis and derived products. |
| Humanitarian Data Exchange | https://data.humdata.org/ | Humanitarian and crisis-response datasets. |
| UNAIDS resources | https://www.unaids.org/en/resources/documents | HIV/AIDS reports and data products; confirm the current download product and license. |

## Data-quality checklist

Before using a source, record the dataset version, retrieval date, license, geographic unit, time coverage, missingness, denominator definitions, uncertainty, and any transformations you apply. For small-area health maps, explicitly assess privacy and re-identification risk before publication.

Keep these details in evidence `notes` and distinguish an observed result from an assumption, candidate source, or information gap in `status`. Every annotation survives the JSON, SVG, Markdown, and HTML exports. An unverified source should remain visibly unverified in the Purple synthesis.
