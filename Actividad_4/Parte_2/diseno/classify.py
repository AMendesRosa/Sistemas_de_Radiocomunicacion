import json, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import shape, Polygon, mapping
from shapely.ops import unary_union
from geo import *
d=load(); B=json.load(open('blocks.json')); R=json.load(open('regiones.json'))
este=shape(R['este']); oeste=shape(R['oeste'])
NOURB={'farmland','grass','forest','industrial','farmyard','meadow','railway','cemetery','recreation_ground','orchard','brownfield','greenfield'}
lu=[]
for w in d['ways']:
    t=w['tags']
    if (t.get('landuse') in NOURB or t.get('leisure') in ('park','pitch','stadium','sports_centre') or t.get('amenity') in ('school','university','hospital','grave_yard')) and len(w['xy'])>3:
        try: lu.append(Polygon(w['xy']).buffer(0))
        except: pass
nourb=unary_union(lu)
out=[]
for f in B['faces']:
    p=shape(f); a=p.area
    frac=p.intersection(nourb).area/a if a>0 else 0
    reg='E' if p.representative_point().within(este) else 'O'
    tipo='urbana' if 2500<=a<=25000 and frac<0.5 else ('chica' if a<2500 else 'no_urbana')
    out.append({'geom':f,'area':a,'reg':reg,'tipo':tipo,'frac':frac})
json.dump(out,open('manzanas.json','w'))
for r in 'EO':
    u=[o for o in out if o['reg']==r and o['tipo']=='urbana']
    print(r,'manzanas urbanas',len(u),'area ha',round(sum(o['area'] for o in u)/1e4,1),'| no urbanas',sum(1 for o in out if o['reg']==r and o['tipo']=='no_urbana'))
fig,ax=plt.subplots(figsize=(12,10)); col={'urbana':'#9ecae1','chica':'#fdd0a2','no_urbana':'#d9d9d9'}
for o in out:
    p=shape(o['geom']); xs,ys=p.exterior.xy; ax.fill(xs,ys,color=col[o['tipo']] if o['reg']=='E' or o['tipo']!='urbana' else '#a1d99b',ec='k',lw=.2)
xs,ys=shape(R['divisoria']).xy; ax.plot(xs,ys,'r-',lw=2); ax.plot(0,0,'k*',ms=15)
ax.set_xlim(-2400,2800); ax.set_ylim(-2000,2700); ax.set_aspect('equal')
plt.savefig('manzanas.png',dpi=70,bbox_inches='tight')
