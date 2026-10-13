import json, math, pickle, numpy as np
from reg import REG, NOMBRE, fn
from shapely.geometry import shape
from capkm import cap_kmeans, cap_assign
VIV_CENSO=12135; ADOP_FINAL=0.90
VIV_CTO=17; CTO_SECTOR=4; VIV_SECTOR=VIV_CTO*CTO_SECTOR      # 68 viviendas -> 61 abonados al 90 %
M=json.load(open('manzanas.json')); urb=[m for m in M if m['tipo']=='urbana']
dens=VIV_CENSO/sum(m['area'] for m in urb)
E=[m for m in urb if m['reg']==REG]
X=[]; MZ=[]; acc=0.0
for i,m in enumerate(E):
    p=shape(m['geom']); v=m['area']*dens; acc+=v; n=int(round(acc))-int(round(acc-v))
    ring=p.buffer(-8).exterior if p.buffer(-8).area>0 else p.exterior
    for k in range(n):
        q=ring.interpolate((k+0.5)/n,normalized=True); X.append((q.x,q.y)); MZ.append(i)
X=np.array(X); H=len(X)
def bisect(idx,k):
    if k==1 or len(idx)<=1: return [idx]
    pts=X[idx]; ax=0 if np.ptp(pts[:,0])>=np.ptp(pts[:,1]) else 1
    idx=idx[np.argsort(pts[:,ax])]; k1=k//2; cut=int(round(len(idx)*k1/k))
    return bisect(idx[:cut],k1)+bisect(idx[cut:],k-k1)
# Grupos de viviendas conexos (separación menor a 100 m): ningún sector cruza zonas sin viviendas
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
pares=cKDTree(X).query_pairs(100,output_type='ndarray')
from scipy.sparse import coo_matrix
A=coo_matrix((np.ones(len(pares)),(pares[:,0],pares[:,1])),shape=(H,H))
ncomp,comp=connected_components(A,directed=False)
lab=np.zeros(H,int); ks=0
for k in range(ncomp):
    I=np.where(comp==k)[0]
    for g in bisect(I,math.ceil(len(I)/VIV_SECTOR)): lab[g]=ks; ks+=1
print('grupos de viviendas conexos',ncomp,sorted([int((comp==k).sum()) for k in range(ncomp)],reverse=True)[:8])
G=pickle.load(open('G.pkl','rb')); ids=list(G.nodes); P=np.array([G.nodes[n]['xy'] for n in ids])
def mejor_nodo(pts,usados=()):
    c=pts.mean(0); cand=[j for j in np.argsort(((P-c)**2).sum(1))[:60] if ids[j] not in usados][:40]
    costo=[np.max(np.abs(pts-P[j]).sum(1)) for j in cand]
    j=cand[int(np.argmin(costo))]; return ids[j],P[j],float(min(costo))
sectores=[]
for s in range(ks):
    I=np.where(lab==s)[0]; Y=X[I]
    NC=min(CTO_SECTOR,math.ceil(len(Y)/VIV_CTO))
    def resolver(init):
        l2,_=cap_kmeans(Y,NC,VIV_CTO,init)
        for _ in range(3):
            nodos=[]
            for j in range(NC): nodos.append(mejor_nodo(Y[l2==j],{n[0] for n in nodos}))
            l2=cap_assign(Y,np.array([n[1] for n in nodos]),VIV_CTO)
        nodos=[]
        for j in range(NC): nodos.append(mejor_nodo(Y[l2==j],{n[0] for n in nodos}))
        return (max(n[2] for n in nodos), sum(n[2] for n in nodos)), l2, nodos
    rs=np.random.RandomState(s)
    inits=[[Y[g].mean(0) for g in bisect(np.arange(len(Y)),NC)]]+[Y[rs.choice(len(Y),NC,replace=False)] for _ in range(12)]
    costo,l2,nodos=min((resolver(i) for i in inits),key=lambda r:r[0])
    ctos=[]
    for j,(nd,xy,dm) in enumerate(nodos):
        ctos.append({'viv':int((l2==j).sum()),'nodo':nd,'xy':xy.tolist(),'drop_max':dm,'casas':Y[l2==j].tolist()})
    sectores.append({'viv':len(I),'c':Y.mean(0).tolist(),'ctos':ctos,'manzanas':sorted({MZ[i] for i in I})})
kc=math.ceil(ks/8); SC=np.array([s['c'] for s in sectores])
labc=np.zeros(ks,int)
XS=X; X=SC
for j,g in enumerate(bisect(np.arange(ks),kc)): labc[g]=j
X=XS
clusters=[]
for ci in range(kc):
    idx=[int(i) for i in np.where(labc==ci)[0]]
    for i in idx: sectores[i]['cluster']=ci
    clusters.append({'sectores':idx,'c':SC[idx].mean(0).tolist(),'viv':sum(sectores[i]['viv'] for i in idx)})
json.dump({'dens':dens,'H':H,'manzanas':[{'id':i,'geom':m['geom']} for i,m in enumerate(E)],'sectores':sectores,'clusters':clusters},open(fn('diseno.json'),'w'))
v=[s['viv'] for s in sectores]; cv=[c['viv'] for s in sectores for c in s['ctos']]; dm=np.array([c['drop_max'] for s in sectores for c in s['ctos']])
print('casas pasadas',NOMBRE,H,'| sectores',ks,'| clusters',kc,'| viv/sector',min(v),max(v),'| viv/CTO',min(cv),max(cv))
print('drop max p50/p90/max',np.percentile(dm,[50,90,100]).round(),'| >200 m:',(dm>200).sum(),'de',len(dm),'| sect/cluster',[len(c['sectores']) for c in clusters])
