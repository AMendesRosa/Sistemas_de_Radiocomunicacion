import json, pickle, numpy as np, networkx as nx
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, FancyArrow
from matplotlib.lines import Line2D
from shapely.geometry import shape, MultiPoint
plt.rcParams.update({'font.family':'serif','font.size':8})
G=pickle.load(open('G.pkl','rb')); D=json.load(open('diseno2.json')); R=json.load(open('regiones.json')); T=json.load(open('tablas.json'))
M=json.load(open('manzanas.json'))
S=D['sectores']; C=D['clusters']; HUB=D['HUB']; XY=lambda n:G.nodes[n]['xy']
COL=plt.get_cmap('tab20')
def base(ax,xlim,ylim,calles=True):
    for m in M:
        p=shape(m['geom'])
        if p.bounds[2]<xlim[0]-200 or p.bounds[0]>xlim[1]+200 or p.bounds[3]<ylim[0]-200 or p.bounds[1]>ylim[1]+200: continue
        xs,ys=p.exterior.xy; ax.fill(xs,ys,color='#f0f0f0' if m['tipo']=='urbana' else '#fafafa',ec='#c8c8c8',lw=.3,zorder=1)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
def escala(ax,L,xlim,ylim):
    x0=xlim[0]+0.05*(xlim[1]-xlim[0]); y0=ylim[0]+0.05*(ylim[1]-ylim[0]); h=0.012*(ylim[1]-ylim[0])
    for k in range(4):
        ax.add_patch(plt.Rectangle((x0+k*L/4,y0),L/4,h,fc='k' if k%2==0 else 'w',ec='k',lw=.6,zorder=20))
    ax.text(x0,y0+2*h,'0',ha='center',fontsize=7,zorder=20); ax.text(x0+L,y0+2*h,f'{L:.0f} m',ha='center',fontsize=7,zorder=20)
    xn=xlim[1]-0.06*(xlim[1]-xlim[0]); yn=ylim[1]-0.12*(ylim[1]-ylim[0])
    ax.annotate('',xy=(xn,yn+0.07*(ylim[1]-ylim[0])),xytext=(xn,yn),arrowprops=dict(arrowstyle='-|>',lw=1.5,color='k'),zorder=20)
    ax.text(xn,yn+0.085*(ylim[1]-ylim[0]),'N',ha='center',fontsize=10,weight='bold',zorder=20)
def divisoria(ax):
    xs,ys=shape(R['divisoria']).xy; ax.plot(xs,ys,'--',color='#c0392b',lw=1.6,zorder=5)
def hub(ax): x,y=XY(HUB); ax.plot(x,y,marker='*',color='#c0392b',ms=16,mec='k',zorder=15)
# ---------------- Plano 1: división Este/Oeste ----------------
fig,ax=plt.subplots(figsize=(7.5,7.5)); xl,yl=(-2700,2900),(-2000,3100); base(ax,xl,yl)
for reg,col in (('este','#2e86c1'),('oeste','#28b463')):
    p=shape(R[reg]); xs,ys=p.exterior.xy; ax.fill(xs,ys,color=col,alpha=.12,zorder=2); ax.plot(xs,ys,color=col,lw=1.2,zorder=3)
divisoria(ax); hub(ax)
ax.text(1300,-300,'REGIÓN ESTE',color='#1b4f72',fontsize=13,weight='bold',ha='center'); ax.text(-1300,-300,'REGIÓN OESTE',color='#186a3b',fontsize=13,weight='bold',ha='center')
ax.legend(handles=[Line2D([],[],ls='--',color='#c0392b',lw=1.6,label='Traza de la RP12 (divisoria)'),Line2D([],[],marker='*',color='#c0392b',ls='',ms=12,mec='k',label='Hub (COYSPU, 9 de Julio 99)'),
  plt.Rectangle((0,0),1,1,fc='#f0f0f0',ec='#c8c8c8',label='Manzana urbanizada')],loc='upper left',fontsize=7)
escala(ax,1000,xl,yl); plt.savefig('plano_regiones.pdf',bbox_inches='tight'); plt.close()
# ---------------- Plano 2: Región Este - clusters, troncal y recorridos extremos ----------------
fig,ax=plt.subplots(figsize=(7.5,8.6)); xl,yl=(-750,2750),(-1600,2300); base(ax,xl,yl)
for i,s in enumerate(S):
    pts=np.array([h for c in s['ctos'] for h in c['casas']]); ax.plot(pts[:,0],pts[:,1],'.',ms=1.2,color=COL(s['cluster']%20),zorder=2)
for (a,b),f,l in D['tron_edges']:
    (x1,y1),(x2,y2)=XY(a),XY(b); ax.plot([x1,x2],[y1,y2],color='#7d3c98',lw=0.8+f/48,solid_capstyle='round',zorder=6)
for i,c in enumerate(C):
    x,y=XY(c['nodo_ceo']); ax.plot(x,y,'o',color='#7d3c98',mec='k',ms=6,zorder=8); ax.text(x+40,y+40,f'C{i+1}',fontsize=8,weight='bold',color='#4a235a',zorder=9,bbox=dict(fc='w',ec='none',alpha=.7,pad=.5))
r=D['recorridos']
for rr,col,lab in ((r[-1],'#e74c3c','mayor'),(r[0],'#27ae60','menor')):
    s=S[rr['sector']]; c=C[s['cluster']]; cto=s['ctos'][rr['cto']]
    p=nx.shortest_path(G,HUB,c['nodo_ceo'],weight='length')+nx.shortest_path(G,c['nodo_ceo'],s['nodo_cd'],weight='length')[1:]+nx.shortest_path(G,s['nodo_cd'],cto['nodo'],weight='length')[1:]
    xs,ys=zip(*[XY(n) for n in p]); ax.plot(xs,ys,color=col,lw=2.2,alpha=.85,zorder=7)
    x,y=XY(cto['nodo']); ax.plot(x,y,'s',color=col,mec='k',ms=7,zorder=9)
divisoria(ax); hub(ax)
ax.legend(handles=[Line2D([],[],color='#7d3c98',lw=3,label='Cable troncal (ancho según cant. de fibras)'),Line2D([],[],marker='o',color='#7d3c98',mec='k',ls='',label='CEO de cluster (C1 a C12)'),
  Line2D([],[],color='#e74c3c',lw=2.2,label=f"Recorrido de mayor pérdida (sector {D['recorridos'][-1]['sector']+1})"),Line2D([],[],color='#27ae60',lw=2.2,label=f"Recorrido de menor pérdida (sector {D['recorridos'][0]['sector']+1})"),
  Line2D([],[],marker='.',ls='',color='gray',label='Viviendas (color por cluster)'),Line2D([],[],marker='*',color='#c0392b',ls='',ms=12,mec='k',label='Hub COYSPU'),Line2D([],[],ls='--',color='#c0392b',label='Divisoria RP12')],loc='upper left',fontsize=6.5)
escala(ax,500,xl,yl); plt.savefig('plano_este_troncal.pdf',bbox_inches='tight'); plt.close()
# ---------------- Plano 3: sectores ----------------
fig,ax=plt.subplots(figsize=(7.5,8.6)); base(ax,xl,yl)
for i,s in enumerate(S):
    pts=np.array([h for c in s['ctos'] for h in c['casas']]); hull=MultiPoint(pts).convex_hull.buffer(12)
    xs,ys=hull.exterior.xy; ax.fill(xs,ys,color=COL(s['cluster']%20),alpha=.35,ec=COL(s['cluster']%20),lw=.6,zorder=3)
    cx,cy=pts.mean(0); ax.text(cx,cy,str(i+1),fontsize=5.5,ha='center',va='center',zorder=6)
for i,c in enumerate(C):
    ax.text(*c['c'],f'C{i+1}',fontsize=11,weight='bold',color='#4a235a',ha='center',zorder=7,bbox=dict(fc='w',ec='#4a235a',alpha=.8,boxstyle='round,pad=0.2'))
divisoria(ax); hub(ax); escala(ax,500,xl,yl)
plt.savefig('plano_este_sectores.pdf',bbox_inches='tight'); plt.close()
# ---------------- Planos 4 y 5: sectores de detalle ----------------
def etiquetas_calles(ax,xl,yl):
    vistos=set()
    for a,b,dd in G.edges(data=True):
        n=dd['name']
        if not n or n in vistos or dd['length']<60: continue
        (x1,y1),(x2,y2)=XY(a),XY(b); xm,ym=(x1+x2)/2,(y1+y2)/2
        if not(xl[0]+40<xm<xl[1]-40 and yl[0]+40<ym<yl[1]-40): continue
        ang=np.degrees(np.arctan2(y2-y1,x2-x1)); ang=ang-180 if ang>90 else (ang+180 if ang<-90 else ang)
        ax.text(xm,ym,n,fontsize=5.5,color='#555',rotation=ang,ha='center',va='center',zorder=4,style='italic'); vistos.add(n)
def plano_sector(si,nombre):
    s=S[si]; ci=s['cluster']; c=C[ci]
    pts=np.array([h for t in s['ctos'] for h in t['casas']]+[XY(t['nodo']) for t in s['ctos']]+[XY(s['nodo_cd'])])
    cx,cy=pts.mean(0); half=max(np.ptp(pts[:,0]),np.ptp(pts[:,1]))/2+140
    xl,yl=(cx-half,cx+half),(cy-half,cy+half)
    fig,ax=plt.subplots(figsize=(7.5,7.5)); base(ax,xl,yl)
    for a,b in [tuple(e) for e in D['clu_edges'][str(ci)]]:
        (x1,y1),(x2,y2)=XY(a),XY(b); ax.plot([x1,x2],[y1,y2],color='#7d3c98',lw=2.4,zorder=5)
    for a,b in s['dist_edges']:
        (x1,y1),(x2,y2)=XY(a),XY(b); ax.plot([x1,x2],[y1,y2],color='#1f77b4',lw=1.8,zorder=6)
    cols=['#e67e22','#16a085','#c0392b','#2c3e50']
    for j,t in enumerate(s['ctos']):
        H=np.array(t['casas']); x,y=XY(t['nodo'])
        ax.plot(H[:,0],H[:,1],'o',ms=3,color=cols[j],zorder=7)
        far=H[np.argmax(np.abs(H-[x,y]).sum(1))]; ax.plot([x,far[0],far[0]],[y,y,far[1]],':',color=cols[j],lw=1,zorder=6)
        ax.plot(x,y,'s',ms=9,color=cols[j],mec='k',zorder=9)
        ax.text(x+18,y+18,f'CTO-{si+1}.{j+1}\n{t["viv"]} viv.',fontsize=6.5,weight='bold',zorder=10,bbox=dict(fc='w',ec=cols[j],pad=.6,alpha=.9))
    x,y=XY(s['nodo_cd']); ax.plot(x,y,'^',ms=12,color='#1f77b4',mec='k',zorder=11)
    ax.text(x-25,y-55,f'CD-{si+1}\n(splitter 1:4)',fontsize=6.5,weight='bold',ha='right',zorder=12,bbox=dict(fc='w',ec='#1f77b4',pad=.6,alpha=.9))
    x,y=XY(c['nodo_ceo'])
    if xl[0]<x<xl[1] and yl[0]<y<yl[1]: ax.plot(x,y,'o',ms=20,mfc='none',mec='#7d3c98',mew=2,zorder=13); ax.text(x+30,y-30,f'CEO-C{ci+1}',fontsize=6.5,color='#4a235a',weight='bold',zorder=13)
    etiquetas_calles(ax,xl,yl)
    ax.legend(handles=[Line2D([],[],color='#7d3c98',lw=2.4,label=f'Cable de cluster C{ci+1} (24F)'),Line2D([],[],color='#1f77b4',lw=1.8,label='Cable de distribución (12F)'),
      Line2D([],[],marker='^',color='#1f77b4',mec='k',ls='',ms=9,label='Caja de distribución (CD) con splitter 1:4'),Line2D([],[],marker='s',color='w',mec='k',ls='',ms=8,label='CTO con splitter 1:16'),Line2D([],[],marker='o',mfc='none',mec='#7d3c98',mew=2,ls='',ms=10,label='CEO de cluster (derivación)'),
      Line2D([],[],marker='o',color='gray',ls='',ms=3,label='Vivienda (color según CTO)'),Line2D([],[],ls=':',color='gray',label='Drop a la vivienda más lejana')],loc='lower right',fontsize=6.5)
    escala(ax,100 if half<400 else 200,xl,yl); plt.savefig(nombre,bbox_inches='tight'); plt.close()
plano_sector(27,'plano_sector_28.pdf'); plano_sector(89,'plano_sector_90.pdf')
print('ok')
