"""Configuraciones de la calculadora de backhaul de la cátedra (Calculadora_FTTH_GPON_XGSPON_TV_v8.html).

Genera un JSON importable por OLT y por etapa (primera etapa y cobertura final), con los abonados
reales de cada sector conectados a cada puerto PON y la mezcla de planes del informe. Los JSON se
cargan en la calculadora con "Importar JSON" para obtener los resultados.
"""
import json, math, os

ADOPCION = {'etapa1': 0.45, 'final': 0.90}
# Planes del informe: bajada 100/300/600 Mbps, subida 10 % de la bajada, mezcla 30/50/20 %
PLANES = [dict(id=1, name='100/10', down=100, up=10), dict(id=2, name='300/30', down=300, up=30),
          dict(id=3, name='600/60', down=600, up=60)]
MEZCLA = [0.30, 0.50, 0.20]
TV = dict(iptvMode='multicast', iptvPen='40', iptvStreams='1', iptvBitrate='8', iptvChannels='100',
          iptvDistinct='30', iptvSource='local', overlayOn='off', overlayPen='0')
OUT = os.environ.get('CALC_DIR', '../calculadora/')


def reparto(total, pesos):
    """Reparto entero por mayor resto."""
    exacto = [total * p for p in pesos]; base = [math.floor(x) for x in exacto]
    for i in sorted(range(len(pesos)), key=lambda i: base[i] - exacto[i])[:total - sum(base)]:
        base[i] += 1
    return base


def abonados_por_sector(D, adop):
    """Abonados de cada sector; el total de cada cluster se redondea hacia arriba, como en el informe."""
    ab = {}
    for c in D['clusters']:
        viv = [D['sectores'][i]['viv'] for i in c['sectores']]
        tot = math.ceil(sum(viv) * adop)
        for i, n in zip(c['sectores'], reparto(tot, [v / sum(viv) for v in viv])):
            ab[i] = n
    return ab


def main():
    os.makedirs(OUT, exist_ok=True)
    resumen = []
    for reg, suf, pre in (('E', '', 'E'), ('O', '_O', 'O')):
        D = json.load(open(f'diseno2{suf}.json'))
        for etapa, adop in ADOPCION.items():
            ab = abonados_por_sector(D, adop)
            for n in range(6):                                   # OLT-E1..E6 / OLT-O1..O6
                sectores = D['clusters'][2 * n]['sectores'] + D['clusters'][2 * n + 1]['sectores']
                ports = []
                for si in sectores:
                    k = reparto(ab[si], MEZCLA)
                    ports.append(dict(pct=100, split=64, tech='GPON', counts={1: k[0], 2: k[1], 3: k[2]}))
                cfg = dict(version=8, state=dict(plans=PLANES, ports=ports), television=TV,
                           parameters=dict(simd='5', simu='5', margin='25', aggCount='2', aggSpeed='10', backhaul='10'))
                nombre = f'OLT-{pre}{n + 1}_{etapa}'
                json.dump(cfg, open(os.path.join(OUT, nombre + '.json'), 'w'), indent=1)
                resumen.append((nombre, len(ports), sum(ab[s] for s in sectores), max(ab[s] for s in sectores)))
    for r in resumen:
        print(*r)


if __name__ == '__main__':
    main()
