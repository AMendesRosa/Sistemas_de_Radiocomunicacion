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

# Por región: REG=E (Este) o REG=O (Oeste). DETALLE = sectores a desarrollar (índices desde 0)
export REG=E DETALLE=27,89     # Región Este: sectores 28 y 90
# export REG=O DETALLE=41,76   # Región Oeste: sectores O42 y O77
python design.py     # viviendas, sectores, CTO y clusters
python routing.py    # ruteo de cables y recorridos ópticos
python tablas.py     # tramos del troncal y clusters
python budget.py     # presupuesto óptico de los recorridos extremos
python planos.py     # planos en PDF (copiarlos luego a ../Planos/)
python gen_tex.py    # tablas LaTeX para el informe (sufijo _O para el Oeste)

# Después de correr ambas regiones:
python instituciones.py   # instituciones y plazas con fibra dedicada (ambas regiones)
python calculadora.py     # configuraciones JSON por OLT para la calculadora de la cátedra (../calculadora/)
```

## Calculadora de backhaul de la cátedra

`calculadora.py` genera en `../calculadora/` un JSON por OLT y por etapa (`OLT-E1_etapa1.json`, ...)
con los abonados de cada sector y la mezcla de planes. Se cargan en
`Calculadora_FTTH_GPON_XGSPON_TV_v8.html` (raíz del repo) con "Importar JSON"; la simultaneidad se
cambia en el campo de la calculadora (5 % diseño, 10 % conservador). `../calculadora/resultados.csv`
resume los resultados de las 24 configuraciones en ambos escenarios. `../calculadora/captura.html`
abre la calculadora original con una configuración cargada, para las capturas del informe
(servir la raíz del repo con `python -m http.server` y abrir
`/Actividad_4/Parte_2/calculadora/captura.html?cfg=OLT-E1_final.json&simd=5&agg=4&bh=25`).

## Troncal

`routing.py` arma el troncal como un árbol que reaprovecha el cable ya tendido: cada cluster se
deriva del punto del troncal existente desde el que llega con menor costo, con una penalización de
150 m por cada giro mayor que 35° (`GIRO_M`, `GIRO_ANG`).

## Supuestos principales (ver sección 4 del informe)
- Viviendas: 12.135 (Censo 2022, localidad de Marcos Juárez), repartidas en forma uniforme
  sobre la superficie de manzanas urbanizadas.
- Sector de diseño: 1 puerto PON, splitter 1:4 + 4 CTO 1:16 (1:64), máximo 68 viviendas.
- CTO: máximo 17 viviendas (16 abonados al 90 %).
- Cluster: hasta 8 sectores, alimentados por 24 fibras del troncal.
- Manzana urbanizada: entre 0,25 y 2,5 ha y menos del 50 % de su superficie con usos no residenciales
  (rural, industrial, parques, deportes, cementerio, escuelas y hospitales), ver `classify.py`.
- Instituciones (educación, salud, seguridad, gobierno y biblioteca) y plazas de 1000 m2 o más: fibras dedicadas
  desde el ODF (4 por hospital con cable MINI-RA propio desde la CD, 1 en los demás casos),
  F17 en adelante del bloque del cluster y F9 en adelante del cable de distribución, sin splitters.

`geo.py` define la proyección local (origen en el hub, coordenadas en metros).
`georef.py` contiene los puntos de control y el borde del área de cobertura digitalizado de la consigna.
`reg.py` define la región y los prefijos de nombres (C/O para clusters, O para sectores del Oeste).
