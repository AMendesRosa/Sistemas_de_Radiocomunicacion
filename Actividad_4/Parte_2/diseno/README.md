# Scripts del diseño de la red FTTH (Región Este)

Estos scripts generan los datos, las tablas (`../secciones/tablas/`) y los planos (`../Planos/`)
del informe. Requieren Python 3 con `numpy`, `scipy`, `matplotlib`, `shapely` y `networkx`.

## Orden de ejecución

```bash
# 1. Descargar los datos de OpenStreetMap del área (licencia ODbL)
curl -A "UNC-FCEFyN-TP" -o map.osm "https://api.openstreetmap.org/api/0.6/map?bbox=-62.130,-32.722,-62.075,-32.672"
python parse.py      # map.osm -> osm.json
python blocks.py     # manzanas dentro del área de cobertura (georreferenciada en georef.py)
python regions.py    # división Este/Oeste según la traza de la RP12
python classify.py   # manzanas urbanizadas por región
python graph.py      # grafo de calles para el ruteo
python design.py     # viviendas, sectores, CTO y clusters
python routing.py    # ruteo de cables y recorridos ópticos
python tablas.py     # tramos del troncal y clusters
python budget.py     # presupuesto óptico de los recorridos extremos
python planos.py     # planos en PDF (copiarlos luego a ../Planos/)
python gen_tex.py    # tablas LaTeX para el informe
```

## Supuestos principales (ver sección 4 del informe)
- Viviendas: 12.135 (Censo 2022, localidad de Marcos Juárez), repartidas en forma uniforme
  sobre la superficie de manzanas urbanizadas.
- Sector de diseño: 1 puerto PON, splitter 1:4 + 4 CTO 1:16 (1:64), máximo 68 viviendas.
- CTO: máximo 17 viviendas (16 abonados al 90 %).
- Cluster: hasta 8 sectores, alimentados por 24 fibras del troncal.

`geo.py` define la proyección local (origen en el hub, coordenadas en metros).
`georef.py` contiene los puntos de control y el borde del área de cobertura digitalizado de la consigna.
Para la Región Oeste basta con cambiar `'E'` por `'O'` en `design.py`.
