"""Instituciones con fibra dedicada (un pelo extra por institución).

Extrae de OpenStreetMap las instituciones del área de cobertura, las asigna a la
CTO más cercana por la red de calles y les reserva una fibra propia desde el ODF,
sin pasar por los splitters. Genera instituciones.json y la tabla LaTeX.
"""
import json, math, os, pickle, unicodedata
import xml.etree.ElementTree as ET
import networkx as nx
from shapely.geometry import Point, shape
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
EXCLUIR = ('first english',)          # academias privadas etiquetadas como college
NOMBRE_DEF = {'kindergarten': 'Jardín de infantes', 'courthouse': 'Tribunales'}
DEDUP = 100.0                          # [m] dos elementos de la misma categoría más cerca que esto son la misma institución


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def extraer():
    root = ET.parse('map.osm').getroot()
    nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node')}
    out = []
    for el in list(root.iter('node')) + list(root.iter('way')):
        t = {tg.get('k'): tg.get('v') for tg in el.findall('tag')}
        a = t.get('amenity')
        if a not in CAT:
            continue
        nombre = t.get('name', '')
        if any(x in norm(nombre) for x in EXCLUIR):
            continue
        if el.tag == 'node':
            lat, lon = nodes[el.get('id')]
        else:
            pts = [nodes[nd.get('ref')] for nd in el.findall('nd') if nd.get('ref') in nodes]
            lat = sum(p[0] for p in pts) / len(pts); lon = sum(p[1] for p in pts) / len(pts)
        p = xy(lat, lon)
        reg = next((r for r, g in REG.items() if Point(p).within(g)), None)
        if reg:
            out.append(dict(tipo=a, cat=CAT[a], nombre=nombre or NOMBRE_DEF.get(a, a), xy=p, reg=reg))
    # Fusión de duplicados (nodo y contorno del mismo edificio, o dos etiquetas del mismo colegio)
    res = []
    for o in sorted(out, key=lambda o: -len(o['nombre'])):
        if not any(r['cat'] == o['cat'] and math.dist(r['xy'], o['xy']) < DEDUP for r in res):
            res.append(o)
    return res


G = pickle.load(open('G.pkl', 'rb'))
NXY = {n: d['xy'] for n, d in G.nodes(data=True)}


def nodo_cercano(p):
    return min(NXY, key=lambda n: math.dist(NXY[n], p))


def region(reg):
    suf = '' if reg == 'E' else '_O'
    D = json.load(open(f'diseno2{suf}.json')); TB = json.load(open(f'tablas{suf}.json'))
    T = nx.Graph(); [T.add_edge(a, b) for (a, b), f, l in D['tron_edges']]
    nodos_tramo = {t['desde'] for t in TB['tramos']} | {t['hasta'] for t in TB['tramos']}
    nombres = {t['hasta']: t['hasta_n'] for t in TB['tramos']}
    rec = {(r['sector'], r['cto']): r['L_red'] for r in D['recorridos']}
    return D, T, nodos_tramo, nombres, rec, TB['esquinas']


def main():
    inst = extraer()
    datos = {r: region(r) for r in 'EO'}
    usados_cl, usados_ds = {}, {}
    filas = []
    for o in sorted(inst, key=lambda o: (o['reg'], o['cat'], o['nombre'])):
        D, T, nodos_tramo, nombres, rec, esq = datos[o['reg']]
        n0 = nodo_cercano(o['xy']); off = math.dist(NXY[n0], o['xy'])
        dist = nx.single_source_dijkstra_path_length(G, n0, weight='length')
        best = None
        for si, s in enumerate(D['sectores']):
            for j, c in enumerate(s['ctos']):
                L = dist.get(c['nodo'])
                if L is not None and (best is None or L < best[0]):
                    best = (L, si, j)
        L, si, j = best
        s = D['sectores'][si]; ci = s['cluster']
        # Fibra del bloque del cluster: primero F17-F18 (otras aplicaciones), luego la reserva F19-F24
        k = usados_cl.get((o['reg'], ci), 0); usados_cl[(o['reg'], ci)] = k + 1
        fib_cl = 17 + k
        # Fibra del cable de distribución: reserva F9-F12
        m = usados_ds.get((o['reg'], si), 0); usados_ds[(o['reg'], si)] = m + 1
        fib_ds = 9 + m
        p = nx.shortest_path(T, D['HUB'], D['clusters'][ci]['nodo_ceo'])
        deriv = [n for n in p[1:-1] if n in nodos_tramo]
        drop = L + off + 15                      # recorrido por la calle + ingreso al edificio
        L_red = rec[(si, j)]
        n_emp = 5 + len(deriv)                   # pigtail ODF, CEO, CD (paso), CTO (al drop), roseta + derivaciones
        perd = L_red / 1000 * 0.38 + drop / 1000 * 0.36 + 4 * 0.30 + n_emp * 0.10
        pre = '' if o['reg'] == 'E' else 'O'
        pc = 'C' if o['reg'] == 'E' else 'O'
        esquina = esq.get(n0) or min(esq.items(), key=lambda kv: math.dist(NXY.get(kv[0], (1e9, 1e9)), o['xy']))[1]
        filas.append(dict(nombre=o['nombre'], cat=o['cat'], reg=o['reg'], esquina=esquina,
                          sector=f'{pre}{si + 1}', cto=f'CTO-{pre}{si + 1}.{j + 1}', cluster=f'{pc}{ci + 1}',
                          fibra=f'{pc}{ci + 1}-F{fib_cl}', fibra_ds=f'DS-{pre}{si + 1} F{fib_ds}',
                          L_red=L_red, drop=drop, deriv=len(deriv), n_emp=n_emp, perdida=perd))
    json.dump(filas, open('instituciones.json', 'w'), ensure_ascii=False, indent=1)
    for f in filas:
        print(f"{f['reg']} {f['cat']:10s} {f['nombre'][:45]:45s} {f['cto']:12s} {f['fibra']:8s} {f['fibra_ds']:10s} red={f['L_red']:6.0f} drop={f['drop']:5.0f} A={f['perdida']:.2f}")
    print('max por cluster', max(usados_cl.values()), 'max por sector', max(usados_ds.values()))
    print('total', len(filas), {r: sum(1 for f in filas if f['reg'] == r) for r in 'EO'})
    for r in 'EO':
        fr = [f for f in filas if f['reg'] == r]
        print(r, 'drops', round(sum(f['drop'] for f in fr)), 'm | max perdida', max(fr, key=lambda f: f['perdida'])['nombre'])
    tex(filas)


def esc(s):
    return s.replace('&', '\\&').replace('#', '\\#').replace('"', "''").replace('Nº', 'N.°').replace('Institito', 'Instituto')


def tex(filas):
    L = ['\\footnotesize\\setlength{\\tabcolsep}{3pt}',
         '\\begin{longtable}{|c|>{\\raggedright\\arraybackslash}p{3.8cm}|l|l|l|l|r|r|}',
         '\\caption{Instituciones con fibra dedicada.}\\label{tab:instituciones}\\\\ \\hline']
    cab = ('\\textbf{ID} & \\textbf{Institución} & \\textbf{Tipo} & \\textbf{CTO} & \\textbf{Troncal} & '
           '\\textbf{Distribución} & \\textbf{Drop [m]} & \\textbf{A [dB]} \\\\ \\hline')
    L += [cab + ' \\endfirsthead', '\\hline ' + cab + ' \\endhead']
    for i, f in enumerate(filas, 1):
        perd = f"{f['perdida']:.2f}".replace('.', '{,}')
        L.append(f"I-{i:02d} & {esc(f['nombre'])} & {f['cat']} & {f['cto']} & {f['fibra']} & {f['fibra_ds']} & "
                 f"{f['drop']:.0f} & {perd} \\\\ \\hline")
    L.append('\\end{longtable}')
    s = '\n'.join(L)
    open(os.path.join(os.environ.get('TEX_DIR', '../secciones/tablas/'), 'instituciones.tex'), 'w', encoding='utf-8').write(s + '\n')


if __name__ == '__main__':
    main()
