import json, pickle, math, collections, numpy as np, networkx as nx
from reg import fn, PC, PD
G=pickle.load(open('G.pkl','rb')); D=json.load(open(fn('diseno2.json')))
S=D['sectores']; C=D['clusters']; HUB=D['HUB']
def esquina(n):
    ns=sorted({G[n][m]['name'] for m in G[n] if G[n][m]['name']})
    return ' y '.join(ns[:2]) if ns else 'sin nombre'
# ---- Troncal: árbol con carga de fibras, tramos entre bifurcaciones
T=nx.Graph()
for (a,b),f,l in D['tron_edges']: T.add_edge(a,b,f=f,l=l)
deg=dict(T.degree()); claves={HUB}|{c['nodo_ceo'] for c in C}|{n for n in T if deg[n]!=2}
tramos=[]; vis=set()
for s in claves:
    for nb in T[s]:
        e=frozenset((s,nb))
        if e in vis: continue
        path=[s,nb]; vis.add(e)
        while path[-1] not in claves:
            nx_=[m for m in T[path[-1]] if m!=path[-2]][0]; vis.add(frozenset((path[-1],nx_))); path.append(nx_)
        L=sum(T[a][b]['l'] for a,b in zip(path,path[1:])); f=T[path[0]][path[1]]['f']
        dh=[nx.shortest_path_length(T,HUB,p,weight='l') for p in (path[0],path[-1])]
        if dh[0]>dh[1]: path=path[::-1]
        tramos.append(dict(desde=path[0],hasta=path[-1],L=L,fibras=f,nombres=sorted({G[a][b]['name'] for a,b in zip(path,path[1:]) if G[a][b]['name']})))
tramos.sort(key=lambda t:(nx.shortest_path_length(T,HUB,t['desde'],weight='l'),t['L']))
# Fusionar derivaciones separadas por menos de 15 m (misma esquina con calzada dividida)
ceos={c['nodo_ceo'] for c in C}
while True:
    corto=[t for t in tramos if t['L']<15 and t['hasta'] not in ceos and t['desde']!=HUB]
    if not corto: break
    t=corto[0]; tramos.remove(t)
    for u in tramos:
        if u['desde']==t['hasta']: u['desde']=t['desde']; u['L']+=t['L']
def cap(f):
    for c in (24,36,48,72,96,144):
        if f<=c: return f'1x{c}F'
    n=math.ceil(f/144); return f'{n}x144F'
nombre_nodo={HUB:'Hub COYSPU'}
for i,c in enumerate(C): nombre_nodo[c['nodo_ceo']]=f'CEO-{PC}{i+1}'
k=1
for t in tramos:
    for n in (t['desde'],t['hasta']):
        if n not in nombre_nodo: nombre_nodo[n]=f'{PD}{k}'; k+=1
print('TRAMOS TRONCAL')
for i,t in enumerate(tramos):
    print(f"T{i+1:02d} {nombre_nodo[t['desde']]:>10} -> {nombre_nodo[t['hasta']]:<10} L={t['L']:6.0f} m  fibras={t['fibras']:3d} cable={cap(t['fibras'])}  por {', '.join(t['nombres'][:3])}")
print('Nodos:',{v:esquina(k_) for k_,v in nombre_nodo.items()})
print('\nCLUSTERS')
for i,c in enumerate(C):
    viv=c['viv']; print(f"{PC}{i+1:02d} sect={len(c['sectores'])} viv={viv} ab1={math.ceil(viv*.45)} abF={math.ceil(viv*.9)} Ltr={c['L_troncal']:.0f} Lcable={c['L_cable']:.0f} CEO en {esquina(c['nodo_ceo'])}")
json.dump(dict(tramos=[dict(t,desde_n=nombre_nodo[t['desde']],hasta_n=nombre_nodo[t['hasta']],cable=cap(t['fibras'])) for t in tramos],
  esquinas={n:esquina(n) for n in set([c['nodo_ceo'] for c in C]+[s['nodo_cd'] for s in S]+[c['nodo'] for s in S for c in s['ctos']]+[HUB]+[t['desde'] for t in tramos]+[t['hasta'] for t in tramos])}),open(fn('tablas.json'),'w'))
