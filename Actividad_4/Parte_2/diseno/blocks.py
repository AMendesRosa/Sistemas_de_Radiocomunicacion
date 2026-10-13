import json, numpy as np
from shapely.geometry import LineString, Polygon, Point, mapping, shape
from shapely.ops import unary_union, polygonize, linemerge
from geo import *; from georef import *
d=load()
area=Polygon(px2xy(BORDE_PX)).buffer(0)
VIAS={'residential','secondary','tertiary','primary','unclassified','living_street','service','pedestrian','primary_link','secondary_link','tertiary_link'}
lines=[LineString(w['xy']) for w in d['ways'] if w['tags'].get('highway') in VIAS and len(w['xy'])>1 and w['tags'].get('service') not in ('parking_aisle','driveway')]
red=unary_union(lines+[area.exterior])
faces=[p for p in polygonize(red) if p.representative_point().within(area)]
# Línea divisoria: traza de la RP12 (extendida hasta el borde)
rp12=linemerge(unary_union([LineString(w['xy']) for w in d['ways'] if w['tags'].get('ref')=='RP12' and len(w['xy'])>1]))
print('area cobertura [km2]', round(area.area/1e6,2), 'caras', len(faces))
A=np.array([f.area for f in faces]); print('percentiles area m2', np.percentile(A,[5,25,50,75,95]).round())
json.dump({'area':mapping(area),'faces':[mapping(f) for f in faces],'rp12':mapping(rp12)},open('blocks.json','w'))
