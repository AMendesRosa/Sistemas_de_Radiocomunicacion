import json, math
LAT0, LON0 = -32.6986546, -62.1033524   # hub COYSPU (9 de Julio 99)
KX = math.cos(math.radians(LAT0))*111320.0
KY = 110574.0
def xy(lat, lon): return ((lon-LON0)*KX, (lat-LAT0)*KY)
def ll(x, y): return (LAT0 + y/KY, LON0 + x/KX)
def load():
    d=json.load(open('osm.json'))
    for w in d['ways']:
        w['xy']=[xy(*p) for p in w['pts']]
    return d
