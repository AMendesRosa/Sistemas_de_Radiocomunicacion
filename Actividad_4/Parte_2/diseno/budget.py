import json, math, networkx as nx
from reg import fn
D=json.load(open(fn('diseno2.json'))); TB=json.load(open(fn('tablas.json')))
S=D['sectores']; C=D['clusters']; r=D['recorridos']
# Árbol troncal para contar cajas de derivación atravesadas
T=nx.Graph(); [T.add_edge(a,b,l=l) for (a,b),f,l in D['tron_edges']]
nodos_tramo={t['desde'] for t in TB['tramos']}|{t['hasta'] for t in TB['tramos']}
def derivaciones(ci):
    p=nx.shortest_path(T,D['HUB'],C[ci]['nodo_ceo'])
    return [n for n in p[1:-1] if n in nodos_tramo]
EQ=dict(olt_tx=(3,7),olt_sens=-30,olt_sat=-12,ont_tx=(0,4),ont_sens=-27,ont_sat=-8)
A_RED=0.38; A_DROP=0.36; A_MIN=0.25
SP_MAX=7.1+13.7; SP_MIN=10*math.log10(4)+10*math.log10(16)
CON=0.30; N_CON=5; EMP=0.10; MS=3.0
def caso(rr,peor=True):
    s=S[rr['sector']]; ci=s['cluster']; nd=len(derivaciones(ci))
    Lr=rr['L_red']/1000; Ld=rr['drop_max']/1000
    n_emp=6+nd
    if peor:
        fib=Lr*A_RED+Ld*A_DROP; per=dict(splitters=SP_MAX,conectores=N_CON*CON,empalmes=n_emp*EMP,fibra=fib)
    else:
        fib=(Lr+Ld)*A_MIN; per=dict(splitters=SP_MIN,conectores=0.0,empalmes=0.0,fibra=fib)
    tot=sum(per.values())
    return dict(sector=rr['sector']+1,cluster=ci+1,L_red=rr['L_red'],drop=rr['drop_max'],n_emp=n_emp,deriv=nd,per=per,total=tot)
w=caso(r[-1],True); b=caso(r[0],False)
print('PEOR',w); print('MEJOR',b)
ds_w=EQ['olt_tx'][0]-w['total']; us_w=EQ['ont_tx'][0]-w['total']
ds_b=EQ['olt_tx'][1]-b['total']; us_b=EQ['ont_tx'][1]-b['total']
print(f"DS peor: Pr={ds_w:.2f} dBm, Pr-Sr={ds_w-EQ['ont_sens']:.2f}, sobrante={ds_w-EQ['ont_sens']-MS:.2f}")
print(f"US peor: Pr={us_w:.2f} dBm, Pr-Sr={us_w-EQ['olt_sens']:.2f}, sobrante={us_w-EQ['olt_sens']-MS:.2f}")
print(f"DS mejor: Pr={ds_b:.2f} dBm vs sat {EQ['ont_sat']} -> margen {EQ['ont_sat']-ds_b:.2f}")
print(f"US mejor: Pr={us_b:.2f} dBm vs sat {EQ['olt_sat']} -> margen {EQ['olt_sat']-us_b:.2f}")
# Clase B+ como comparación
print('B+ DS sobrante',round(1.5-w['total']+28-MS,2),'| B+ US sobrante',round(0-w['total']+28-MS,2))
# Cascada 1:2 en hub (primera etapa con medio puerto)
print('Con 1:2 extra en hub, DS sobrante',round(ds_w-3.7-0.3-EQ['ont_sens']-MS,2))
# Overlay: WDM del EDFA en el paso OLT (+0.8 dB)
print('Con WDM overlay (+0.8 dB): DS sobrante',round(ds_w-0.8-EQ['ont_sens']-MS,2),'US',round(us_w-0.8-EQ['olt_sens']-MS,2))
json.dump(dict(peor=w,mejor=b),open(fn('budget.json'),'w'))
