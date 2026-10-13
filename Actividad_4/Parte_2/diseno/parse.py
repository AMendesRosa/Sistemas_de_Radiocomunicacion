import xml.etree.ElementTree as ET, json, collections
t=ET.parse('map.osm').getroot()
nodes={n.get('id'):(float(n.get('lat')),float(n.get('lon'))) for n in t.iter('node')}
ways=[]
for w in t.iter('way'):
    tags={x.get('k'):x.get('v') for x in w.findall('tag')}
    refs=[nd.get('ref') for nd in w.findall('nd')]
    pts=[nodes[r] for r in refs if r in nodes]
    ways.append({'id':w.get('id'),'tags':tags,'pts':pts})
rels=[]
for r in t.iter('relation'):
    tags={x.get('k'):x.get('v') for x in r.findall('tag')}
    mem=[m.get('ref') for m in r.findall('member') if m.get('type')=='way']
    rels.append({'tags':tags,'ways':mem})
json.dump({'ways':ways,'rels':rels},open('osm.json','w'))
hw=[w for w in ways if 'highway' in w['tags']]
print('ways',len(ways),'highways',len(hw))
print(collections.Counter(w['tags']['highway'] for w in hw).most_common(12))
print('refs',collections.Counter(w['tags'].get('ref') for w in hw if w['tags'].get('ref')))
b=[w for w in ways if 'building' in w['tags']]; print('buildings',len(b),collections.Counter(w['tags']['building'] for w in b).most_common(6))
lu=[w for w in ways if 'landuse' in w['tags']]; print('landuse',collections.Counter(w['tags']['landuse'] for w in lu).most_common(8))
print('rels',[ (r['tags'].get('name'),r['tags'].get('ref'),r['tags'].get('type')) for r in rels][:30])
names=collections.Counter(w['tags'].get('name') for w in hw if w['tags'].get('name')); print(len(names)); print(names.most_common(40))
