import json, numpy as np
from shapely.geometry import shape, LineString, Polygon, mapping
from shapely.ops import split
B=json.load(open('blocks.json'))
g=shape(B['rp12']); parts=list(getattr(g,'geoms',[g]))
def part(a,b):
    for p in parts:
        c=[tuple(map(round,x)) for x in p.coords]
        if c[0]==a and c[-1]==b: return list(p.coords)
        if c[0]==b and c[-1]==a: return list(p.coords)[::-1]
    raise KeyError((a,b))
pts=[(435,3296)]+part((277,2540),(3,1264))+part((-245,1315),(-476,-1364))+[(-497,-1424),(-507,-1457),(-513,-1518)]
sur=part((-513,-1518),(-5871,-25616)); pts+= [p for p in sur if p[1]>-3500][:]+[sur[min(len(sur)-1,12)]]
divisoria=LineString(pts)
area=shape(B['area'])
piezas=split(area,divisoria).geoms
piezas=sorted(piezas,key=lambda p:p.area,reverse=True)[:2]
este=max(piezas,key=lambda p:p.centroid.x); oeste=min(piezas,key=lambda p:p.centroid.x)
print('Este km2',round(este.area/1e6,2),'Oeste km2',round(oeste.area/1e6,2), 'total', round(area.area/1e6,2))
json.dump({'divisoria':mapping(divisoria),'este':mapping(este),'oeste':mapping(oeste)},open('regiones.json','w'))
