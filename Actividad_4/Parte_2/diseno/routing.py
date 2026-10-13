import json, pickle, math, numpy as np, networkx as nx, collections
from reg import fn
G=pickle.load(open('G.pkl','rb')); D=json.load(open(fn('diseno.json')))
ids=list(G.nodes); P=np.array([G.nodes[n]['xy'] for n in ids])
def snap(c): return ids[int(np.argmin(((P-np.asarray(c))**2).sum(1)))]
def plen(path): return sum(G[a][b]['length'] for a,b in zip(path,path[1:]))
HUB=snap((0,0))
dist_hub,paths_hub=nx.single_source_dijkstra(G,HUB,weight='length')
S=D['sectores']; C=D['clusters']
# Caja de distribución (splitter 1:4) del sector: nodo que minimiza la suma de recorridos a sus 4 CTO
for s in S:
    cand=np.argsort(((P-np.asarray(s['c']))**2).sum(1))[:30]
    best=None
    for j in cand:
        n=ids[j]; dd=nx.single_source_dijkstra_path_length(G,n,weight='length',cutoff=1500)
        cost=sum(dd.get(c['nodo'],9e9) for c in s['ctos'])
        if best is None or cost<best[0]: best=(cost,n)
    s['nodo_cd']=best[1]
# CEO de cluster: nodo del cluster más cercano al hub (entrada del troncal)
for c in C:
    c['nodo_ceo']=min((S[i]['nodo_cd'] for i in c['sectores']),key=lambda n:dist_hub[n])
FIBRAS_CLUSTER=24
def asignacion(n):   # fibras por cluster: uso, crecimiento, reserva, otras aplicaciones
    uso=n; crec=n; otras=2; res=FIBRAS_CLUSTER-uso-crec-otras; return dict(uso=uso,crec=crec,res=res,otras=otras)
# Troncal: árbol de caminos mínimos hub -> CEO, fibras acumuladas por arista
carga=collections.Counter()
for ci,c in enumerate(C):
    p=paths_hub[c['nodo_ceo']]; c['L_troncal']=plen(p)
    for a,b in zip(p,p[1:]): carga[frozenset((a,b))]+=FIBRAS_CLUSTER
tron_edges=[(tuple(e),f,G[tuple(e)[0]][tuple(e)[1]]['length']) for e,f in carga.items()]
L_tron=sum(l for *_,l in tron_edges)
# Cable de cluster: CEO -> cajas de distribución de sus sectores
L_clu=0; clu_edges={}
for ci,c in enumerate(C):
    dd,pp=nx.single_source_dijkstra(G,c['nodo_ceo'],weight='length')
    E=set()
    for i in c['sectores']:
        S[i]['L_cluster']=dd[S[i]['nodo_cd']]; p=pp[S[i]['nodo_cd']]
        E|={frozenset((a,b)) for a,b in zip(p,p[1:])}
    c['L_cable']=sum(G[tuple(e)[0]][tuple(e)[1]]['length'] for e in E); L_clu+=c['L_cable']; clu_edges[ci]=[tuple(e) for e in E]
# Distribución: caja de distribución -> CTO
L_dist=0
for s in S:
    dd,pp=nx.single_source_dijkstra(G,s['nodo_cd'],weight='length'); E=set()
    for c in s['ctos']:
        c['L_dist']=dd[c['nodo']]; p=pp[c['nodo']]; E|={frozenset((a,b)) for a,b in zip(p,p[1:])}
    s['L_cable_dist']=sum(G[tuple(e)[0]][tuple(e)[1]]['length'] for e in E); s['dist_edges']=[tuple(e) for e in E]; L_dist+=s['L_cable_dist']
# Recorrido óptico por CTO
rec=[]
for i,s in enumerate(S):
    c0=C[s['cluster']]
    for j,c in enumerate(s['ctos']):
        L=c0['L_troncal']+s['L_cluster']+c['L_dist']
        rec.append(dict(sector=i,cto=j,L_red=L,drop_max=c['drop_max'],L_max=L+c['drop_max']))
rec.sort(key=lambda r:r['L_max'])
D.update(HUB=HUB,tron_edges=[(list(e),f,l) for e,f,l in tron_edges],clu_edges={k:[list(e) for e in v] for k,v in clu_edges.items()},recorridos=rec,L_tron=L_tron,L_clu=L_clu,L_dist=L_dist)
for s in S: s['dist_edges']=[list(e) for e in s['dist_edges']]
json.dump(D,open(fn('diseno2.json'),'w'))
print('Longitudes de cable [km]: troncal',round(L_tron/1e3,2),'| clusters',round(L_clu/1e3,2),'| distribución',round(L_dist/1e3,2))
print('Fibras máx. en una arista troncal',max(f for *_,f in tron_edges))
print('Recorrido MAYOR: ',{k:round(v) if isinstance(v,float) else v for k,v in rec[-1].items()})
print('Recorrido MENOR: ',{k:round(v) if isinstance(v,float) else v for k,v in rec[0].items()})
print('L troncal por cluster',[round(c['L_troncal']) for c in C])
