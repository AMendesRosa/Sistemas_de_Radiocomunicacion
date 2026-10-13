"""Genera las tablas LaTeX de la Parte 2 a partir de los resultados del diseño."""
import json, math, numpy as np
from reg import REG, NOMBRE, PC, PS, SUF, DETALLE, fn

R = "../secciones/tablas/"
D = json.load(open(fn('diseno2.json'))); T = json.load(open(fn('tablas.json'))); E = T['esquinas']
S = D['sectores']; C = D['clusters']
FIN = r" \\ \hline"


def f(x, n=0):
    return f"{x:,.{n}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def tex(s):
    return s.replace('&', r'\&').replace('_', r'\_')


def guardar(nombre, lineas, sufijo=True):
    open(R + (fn(nombre) if sufijo else nombre), 'w', encoding='utf8').write('\n'.join(lineas) + '\n')


# ---------------- Tramos del troncal ----------------
enc = r"\textbf{Tramo} & \textbf{Desde} & \textbf{Hasta} & \textbf{L [m]} & \textbf{Fibras} & \textbf{Cable} & \textbf{Recorrido (calles)}"
L = [r"\footnotesize\setlength{\tabcolsep}{4pt}\begin{longtable}{|c|l|l|r|r|c|p{4.2cm}|}",
     r"\caption{Tramos del cable troncal de la Región " + NOMBRE + r".}\label{tab:tramos" + SUF + r"}\\ \hline",
     enc + FIN + r" \endfirsthead",
     r"\hline " + enc + FIN + r" \endhead"]
tot = 0
for i, t in enumerate(T['tramos']):
    tot += t['L']
    L.append(f"CT-{PS}{i+1:02d} & {t['desde_n']} & {t['hasta_n']} & {f(t['L'])} & {t['fibras']} & {t['cable']} & {tex(', '.join(t['nombres'][:3]))}" + FIN)
L.append(r"\multicolumn{3}{|r|}{\textbf{Total de traza}} & \textbf{" + f(tot) + r"} & \multicolumn{3}{l|}{}" + FIN)
L.append(r"\end{longtable}")
guardar('tramos_troncal.tex', L)

# ---------------- Ubicación de los nodos del troncal ----------------
nodos = {}
for t in T['tramos']:
    nodos[t['desde_n']] = t['desde']; nodos[t['hasta_n']] = t['hasta']


def orden(n):
    if n.startswith('Hub'):
        return (0, 0)
    return (1 if n.startswith('CEO') else 2, int(''.join(c for c in n if c.isdigit())))


L = [r"\begin{table}[H]\centering\footnotesize",
     r"\caption{Ubicación de las cajas de empalme del troncal de la Región " + NOMBRE + r".}\label{tab:nodos" + SUF + r"}",
     r"\begin{tabular}{|l|l|}\hline \textbf{Identificación} & \textbf{Ubicación (intersección de calles)}" + FIN]
for n in sorted(nodos, key=orden):
    ub = '9 de Julio 99 (Cooperativa COYSPU)' if n.startswith('Hub') else tex(E[nodos[n]])
    L.append(f"{n} & {ub}" + FIN)
L.append(r"\end{tabular}\end{table}")
guardar('nodos_troncal.tex', L)

# ---------------- Clusters ----------------
L = [r"\begin{table}[H]\centering\footnotesize",
     r"\caption{Clusters de la Región " + NOMBRE + r": viviendas, abonados y longitudes.}\label{tab:clusters" + SUF + r"}",
     r"\setlength{\tabcolsep}{3pt}\begin{tabular}{|c|c|r|r|r|r|r|p{3.6cm}|}\hline \textbf{Cluster} & \textbf{Sect.} & \textbf{Viv.} & \textbf{Ab. 1.\textsuperscript{a} et.} & \textbf{Ab. final} & \textbf{L troncal [m]} & \textbf{Cable cl. [m]} & \textbf{Ubicación del CEO}" + FIN]
sv = sa1 = saf = 0
for i, c in enumerate(C):
    v = c['viv']; a1 = math.ceil(v * .45); af = math.ceil(v * .9)
    sv += v; sa1 += a1; saf += af
    L.append(f"{PC}{i+1} & {len(c['sectores'])} & {f(v)} & {f(a1)} & {f(af)} & {f(c['L_troncal'])} & {f(c['L_cable'])} & {tex(E[c['nodo_ceo']])}" + FIN)
L.append(r"\textbf{Total} & \textbf{" + str(len(S)) + r"} & \textbf{" + f(sv) + r"} & \textbf{" + f(sa1) + r"} & \textbf{" + f(saf) + r"} & \multicolumn{3}{l|}{}" + FIN)
L.append(r"\end{tabular}\end{table}")
guardar('clusters.tex', L)

# ---------------- Anexo: todos los sectores ----------------
enc = r"\textbf{Sect.} & \textbf{Clúst.} & \textbf{Viv.} & \textbf{CTO} & \textbf{Caja de distribución (CD)} & \textbf{Red [m]} & \textbf{Distr. [m]} & \textbf{Drop [m]}"
L = [r"\footnotesize\setlength{\tabcolsep}{4pt}\begin{longtable}{|c|c|r|c|p{4.2cm}|r|r|r|}",
     r"\caption{Sectores de diseño de la Región " + NOMBRE + r".}\label{tab:sectores" + SUF + r"}\\ \hline",
     enc + FIN + r" \endfirsthead",
     r"\hline " + enc + FIN + r" \endhead"]
for i, s in enumerate(S):
    c = C[s['cluster']]; Lred = c['L_troncal'] + s['L_cluster']
    L.append(f"{PS}{i+1} & {PC}{s['cluster']+1} & {s['viv']} & {len(s['ctos'])} & {tex(E[s['nodo_cd']])} & {f(Lred)} & {f(s['L_cable_dist'])} & {f(max(t['drop_max'] for t in s['ctos']))}" + FIN)
L.append(r"\end{longtable}")
guardar('anexo_sectores.tex', L)

# ---------------- Detalle de los dos sectores de diseño ----------------
for si in DETALLE:
    s = S[si]
    L = [r"\begin{table}[H]\centering\footnotesize",
         f"\\caption{{Cajas terminales del sector {PS}{si+1} (cluster {PC}{s['cluster']+1}).}}\\label{{tab:sector{PS}{si+1}}}",
         r"\begin{tabular}{|c|p{4.0cm}|r|r|r|c|}\hline \textbf{CTO} & \textbf{Ubicación} & \textbf{Viv.} & \textbf{Desde CD [m]} & \textbf{Drop máx. [m]} & \textbf{Fibra/salida}" + FIN]
    for j, t in enumerate(s['ctos']):
        L.append(f"CTO-{PS}{si+1}.{j+1} & {tex(E[t['nodo']])} & {t['viv']} & {f(t['L_dist'])} & {f(t['drop_max'])} & F{j+1} / {j+1}" + FIN)
    L.append(r"\end{tabular}\end{table}")
    guardar(f'sector_{PS}{si+1}.tex', L, sufijo=False)

# ---------------- Estadísticas para el texto ----------------
casas = [(h, t['xy']) for s in S for t in s['ctos'] for h in t['casas']]
drops = np.array([abs(h[0] - xy[0]) + abs(h[1] - xy[1]) for h, xy in casas])
st = dict(drop_med=float(drops.mean()), drop_p90=float(np.percentile(drops, 90)), drop_total_km=float(drops.sum() / 1000))
json.dump(st, open(fn('stats.json'), 'w'))
print(st)
