import xml.etree.ElementTree as ET, networkx as nx, pickle, math
from geo import xy
VIAS={'residential','secondary','tertiary','primary','unclassified','living_street','primary_link','secondary_link','tertiary_link'}
t=ET.parse('map.osm').getroot()
nodes={n.get('id'):xy(float(n.get('lat')),float(n.get('lon'))) for n in t.iter('node')}
G=nx.Graph()
for w in t.iter('way'):
    tags={x.get('k'):x.get('v') for x in w.findall('tag')}
    if tags.get('highway') not in VIAS: continue
    refs=[nd.get('ref') for nd in w.findall('nd') if nd.get('ref') in nodes]
    for a,b in zip(refs,refs[1:]):
        (x1,y1),(x2,y2)=nodes[a],nodes[b]
        G.add_edge(a,b,length=math.hypot(x2-x1,y2-y1),name=tags.get('name',''))
for n in G.nodes: G.nodes[n]['xy']=nodes[n]
G=G.subgraph(max(nx.connected_components(G),key=len)).copy()
pickle.dump(G,open('G.pkl','wb'))
print(G.number_of_nodes(),G.number_of_edges(), round(sum(d['length'] for *_,d in G.edges(data=True))/1000,1),'km de calles')
