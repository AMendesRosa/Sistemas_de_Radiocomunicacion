"""Instituciones y plazas con fibra dedicada.

Extrae de OpenStreetMap las instituciones y las plazas del área de cobertura, las
asigna a la CTO más cercana por la red de calles y les reserva fibras propias desde
el ODF, sin pasar por los splitters: cuatro por hospital, con un cable propio de
4 fibras desde la caja de distribución, y una por cada institución o plaza restante. Genera instituciones.json y la tabla LaTeX.
"""
import json, math, os, pickle, unicodedata
import xml.etree.ElementTree as ET
import networkx as nx
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import linemerge, polygonize, unary_union
from geo import xy

R = json.load(open('regiones.json'))
REG = {'E': shape(R['este']), 'O': shape(R['oeste'])}

# Categorías consideradas institución (servicio público o comunitario esencial)
CAT = {
    'school': 'Educación', 'kindergarten': 'Educación', 'college': 'Educación', 'university': 'Educación',
    'hospital': 'Salud', 'clinic': 'Salud',
    'police': 'Seguridad', 'fire_station': 'Seguridad',
    'townhall': 'Gobierno', 'courthouse': 'Gobierno',
    'library': 'Cultura',
}
FIBRAS = {'hospital': 4}               # fibras por institución (1 si no figura)
CABLE_PROPIO = {'hospital'}            # llegan con un cable MINI-RA de 4 F propio desde la caja de distribución
EXCLUIR = ('first english',)          # academias privadas etiquetadas como college
NOMBRE_DEF = {'kindergarten': 'Jardín de infantes', 'courthouse': 'Tribunales'}
DEDUP = 60.0                           # [m] dos elementos de la misma categoría que se tocan o cuyos centros
                                       # están más cerca que esto son el mismo (nodo y contorno, o predio compartido)
PLAZA_MIN = 1000.0                     # [m2] superficie mínima de una plaza (descarta canteros de bulevar)


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def en_region(g):
    return next((r for r, reg in REG.items() if g.representative_point().within(reg)), None)


def extraer():
    root = ET.parse('map.osm').getroot()
    nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node')}
    ways = {w.get('id'): [xy(*nodes[nd.get('ref')]) for nd in w.findall('nd') if nd.get('ref') in nodes]
            for w in root.iter('way')}
    inst, plazas = [], []
    for el in list(root.iter('node')) + list(root.iter('way')) + list(root.iter('relation')):
        t = {tg.get('k'): tg.get('v') for tg in el.findall('tag')}
        a = t.get('amenity'); nombre = t.get('name', '')
        es_plaza = t.get('leisure') == 'park'
        if (a not in CAT and not es_plaza) or any(x in norm(nombre) for x in EXCLUIR):
            continue
        if el.tag == 'node':
            g = Point(xy(*nodes[el.get('id')]))
        elif el.tag == 'way':
            pts = ways[el.get('id')]
            g = Polygon(pts).buffer(0) if len(pts) > 2 else Point(pts[0])
        else:
            lineas = [LineString(ways[m.get('ref')]) for m in el.findall('member')
                      if m.get('type') == 'way' and m.get('role') == 'outer' and len(ways.get(m.get('ref'), [])) > 1]
            g = unary_union(list(polygonize(linemerge(lineas))))
        reg = en_region(g)
        if not reg:
            continue
        if es_plaza:
            if g.area >= PLAZA_MIN:
                plazas.append(dict(tipo='plaza', cat='Plaza', nombre=nombre, geom=g, reg=reg, n_fib=1, pref='P'))
        else:
            inst.append(dict(tipo=a, cat=CAT[a], nombre=nombre or NOMBRE_DEF.get(a, a), geom=g, reg=reg,
                             n_fib=FIBRAS.get(a, 1), pref='I'))
    # Fusión de duplicados (nodo y contorno del mismo edificio, o dos etiquetas del mismo colegio)
    res = []
    for o in sorted(inst, key=lambda o: (-o['n_fib'], -len(o['nombre']))):
        if not any(r['cat'] == o['cat'] and (r['geom'].distance(o['geom']) < 1
                                             or r['geom'].centroid.distance(o['geom'].centroid) < DEDUP) for r in res):
            res.append(o)
    orden = lambda o: (o['reg'], o['cat'], o['nombre'])
    return sorted(res, key=orden) + sorted(plazas, key=lambda o: (o['reg'], o['nombre'] == '', o['nombre']))


G = pickle.load(open('G.pkl', 'rb'))
NXY = {n: d['xy'] for n, d in G.nodes(data=True)}


def borde(g):
    return g.exterior if isinstance(g, Polygon) else (g.boundary if g.geom_type == 'MultiPolygon' else g)


def nodo_cercano(g):
    b = borde(g)
    n = min(NXY, key=lambda n: b.distance(Point(NXY[n])))
    return n, b.distance(Point(NXY[n]))


def region(reg):
    suf = '' if reg == 'E' else '_O'
    D = json.load(open(f'diseno2{suf}.json')); TB = json.load(open(f'tablas{suf}.json'))
    T = nx.Graph(); [T.add_edge(a, b) for (a, b), f, l in D['tron_edges']]
    nodos_tramo = {t['desde'] for t in TB['tramos']} | {t['hasta'] for t in TB['tramos']}
    rec = {(r['sector'], r['cto']): r['L_red'] for r in D['recorridos']}
    return D, T, nodos_tramo, rec, TB['esquinas']


def rango(prefijo, a, n):
    return f'{prefijo}{a}' if n == 1 else f'{prefijo}{a} a F{a + n - 1}'


def main():
    items = extraer()
    datos = {r: region(r) for r in 'EO'}
    usados_cl, usados_ds = {}, {}
    filas, cont = [], {'I': 0, 'P': 0}
    for o in items:
        D, T, nodos_tramo, rec, esq = datos[o['reg']]
        n0, off = nodo_cercano(o['geom'])
        dist = nx.single_source_dijkstra_path_length(G, n0, weight='length')
        propio = o['tipo'] in CABLE_PROPIO
        if propio:
            # Cable propio desde la caja de distribución más cercana, sin pasar por CTO
            L, si = min((dist[s['nodo_cd']], si) for si, s in enumerate(D['sectores']) if s['nodo_cd'] in dist)
            j = None
        else:
            L, si, j = min((dist[c['nodo']], si, j) for si, s in enumerate(D['sectores'])
                           for j, c in enumerate(s['ctos']) if c['nodo'] in dist)
        s = D['sectores'][si]; ci = s['cluster']; n = o['n_fib']
        # Bloque del cluster: F17 en adelante (después de uso F1-F8 y crecimiento F9-F16)
        k = usados_cl.get((o['reg'], ci), 0); usados_cl[(o['reg'], ci)] = k + n
        p = nx.shortest_path(T, D['HUB'], D['clusters'][ci]['nodo_ceo'])
        deriv = [x for x in p[1:-1] if x in nodos_tramo]
        drop = L + off + 15                      # recorrido por la calle + ingreso al edificio o a la plaza
        if propio:
            L_red = D['clusters'][ci]['L_troncal'] + s['L_cluster']
            n_emp = 4 + len(deriv)               # pigtail ODF, CEO, CD (al cable propio), roseta + derivaciones
        else:
            # Cable de distribución: reserva F9-F12
            m = usados_ds.get((o['reg'], si), 0); usados_ds[(o['reg'], si)] = m + n
            L_red = rec[(si, j)]
            n_emp = 5 + len(deriv)               # pigtail ODF, CEO, CD (paso), CTO (al drop), roseta + derivaciones
        perd = L_red / 1000 * 0.38 + drop / 1000 * 0.36 + 4 * 0.30 + n_emp * 0.10
        pre = '' if o['reg'] == 'E' else 'O'
        pc = 'C' if o['reg'] == 'E' else 'O'
        nombradas = {k: v for k, v in esq.items() if 'sin nombre' not in v and k in NXY}
        esquina = nombradas.get(n0) or min(nombradas.items(), key=lambda kv: math.dist(NXY[kv[0]], NXY[n0]))[1]
        cont[o['pref']] += 1
        filas.append(dict(id=f"{o['pref']}-{cont[o['pref']]:02d}", nombre=o['nombre'] or f'Plaza en {esquina}',
                          cat=o['cat'], reg=o['reg'], n_fib=n, esquina=esquina,
                          sector=f'{pre}{si + 1}', cluster=f'{pc}{ci + 1}',
                          cto=f'CD-{pre}{si + 1}' if propio else f'CTO-{pre}{si + 1}.{j + 1}',
                          fibra=rango(f'{pc}{ci + 1}-F', 17 + k, n),
                          fibra_ds='MINI-RA 4 F propio' if propio else rango(f'DS-{pre}{si + 1} F', 9 + m, n),
                          L_red=L_red, drop=drop, deriv=len(deriv), n_emp=n_emp, perdida=perd))
    json.dump(filas, open('instituciones.json', 'w'), ensure_ascii=False, indent=1)
    for f in filas:
        print(f"{f['id']} {f['reg']} {f['cat']:10s} {f['nombre'][:40]:40s} {f['cto']:11s} {f['fibra']:14s} "
              f"{f['fibra_ds']:15s} red={f['L_red']:5.0f} drop={f['drop']:4.0f} A={f['perdida']:.2f}")
    print('fibras por cluster (max)', max(usados_cl.values()), '| por sector (max)', max(usados_ds.values()))
    libres = {(r, ci): 24 - 2 * len(datos[r][0]['clusters'][ci]['sectores']) - n for (r, ci), n in usados_cl.items()}
    print('fibras libres del bloque (min)', min(libres.values()), min(libres, key=libres.get))
    for r in 'EO':
        fr = [f for f in filas if f['reg'] == r]
        print(r, 'inst', sum(f['id'][0] == 'I' for f in fr), 'plazas', sum(f['id'][0] == 'P' for f in fr),
              'fibras', sum(f['n_fib'] for f in fr), 'drops', round(sum(f['drop'] for f in fr)), 'm')
    tex(filas)


def esc(s):
    return (s.replace('&', '\\&').replace('#', '\\#').replace('"', "''").replace('Nº', 'N.°')
            .replace('Institito', 'Instituto'))


def tex(filas):
    L = ['\\footnotesize\\setlength{\\tabcolsep}{3pt}',
         '\\begin{longtable}{|c|>{\\raggedright\\arraybackslash}p{3.3cm}|l|l|>{\\raggedright\\arraybackslash}p{1.6cm}|>{\\raggedright\\arraybackslash}p{1.9cm}|r|r|}',
         '\\caption{Instituciones y plazas con fibra dedicada.}\\label{tab:instituciones}\\\\ \\hline']
    cab = ('\\textbf{ID} & \\textbf{Nombre} & \\textbf{Tipo} & \\textbf{CTO} & \\textbf{Troncal} & '
           '\\textbf{Distrib.} & \\textbf{Drop [m]} & \\textbf{A [dB]} \\\\ \\hline')
    L += [cab + ' \\endfirsthead', '\\hline ' + cab + ' \\endhead']
    for f in filas:
        perd = f"{f['perdida']:.2f}".replace('.', '{,}')
        L.append(f"{f['id']} & {esc(f['nombre'])} & {f['cat']} & {f['cto']} & {f['fibra']} & {f['fibra_ds']} & "
                 f"{f['drop']:.0f} & {perd} \\\\ \\hline")
    L.append('\\end{longtable}')
    open(os.path.join(os.environ.get('TEX_DIR', '../secciones/tablas/'), 'instituciones.tex'), 'w',
         encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
