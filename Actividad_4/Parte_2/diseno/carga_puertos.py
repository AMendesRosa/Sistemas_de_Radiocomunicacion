"""Carga de un puerto GPON en función del factor de simultaneidad (Fs) y límite de saturación.

Usa el mismo modelo que la calculadora de la cátedra: demanda = suma comercial x Fs + IPTV multicast del
puerto (abonados con IPTV = 40 %, una pantalla, hasta 30 canales distintos de 8 Mbps). Genera
../Figuras/carga_puertos.png e imprime los valores de la tabla del informe.
"""
import math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C_GPON_D, C_GPON_U = 2.488, 1.244          # capacidad nominal por puerto [Gbps]
UMBRAL = 0.80                              # umbral de revisión de la calculadora
PLANES = [(100, 10), (300, 30), (600, 60)] # bajada / subida [Mbps]
MEZCLA = [0.30, 0.50, 0.20]


def reparto(n, pesos):
    exacto = [n*p for p in pesos]; base = [math.floor(x) for x in exacto]
    for i in sorted(range(len(pesos)), key=lambda i: base[i] - exacto[i])[:n - sum(base)]:
        base[i] += 1
    return base


def puerto(n):
    k = reparto(n, MEZCLA)
    com_d = sum(ki*p[0] for ki, p in zip(k, PLANES))/1000
    com_u = sum(ki*p[1] for ki, p in zip(k, PLANES))/1000
    iptv = min(100, 30, math.ceil(round(n*0.4)*1))*8/1000
    return com_d, com_u, iptv


casos = [(31, 'Primera etapa (31 abonados)'), (61, 'Cobertura final (61 abonados)'), (64, 'Puerto lleno (64 ONT)')]
fs = np.linspace(0, 0.20, 401)
fig, ax = plt.subplots(figsize=(8.5, 5))
for n, etiqueta in casos:
    d, u, tv = puerto(n)
    ax.plot(fs*100, d*fs + tv, lw=2, label=etiqueta)
    fs_sat = (C_GPON_D - tv)/d; fs_80 = (UMBRAL*C_GPON_D - tv)/d
    print(f'{n} ab: suma comercial {d:.2f}/{u:.3f} Gbps, IPTV {tv:.3f} | Fs 5 % -> {d*0.05+tv:.3f} Gbps '
          f'({(d*0.05+tv)/C_GPON_D*100:.0f} %) | Fs 10 % -> {d*0.10+tv:.3f} ({(d*0.10+tv)/C_GPON_D*100:.0f} %) | '
          f'Fs 80 % = {fs_80*100:.1f} % | Fs sat = {fs_sat*100:.1f} % | Mbps/ab en saturación = {(C_GPON_D-tv)/n*1000:.1f} '
          f'| Fs sat subida = {C_GPON_U/u*100:.0f} %')
ax.axhline(C_GPON_D, color='red', lw=1.5, ls='--', label='Capacidad nominal GPON (2,488 Gbps)')
ax.axhline(UMBRAL*C_GPON_D, color='orange', lw=1.2, ls=':', label='Umbral de revisión (80 %)')
for f0, t in ((5, 'Diseño'), (10, 'Conservador')):
    ax.axvline(f0, color='gray', lw=0.8)
    ax.text(f0 + 0.2, 0.15, t, rotation=90, fontsize=8, color='gray')
ax.set_xlabel('Factor de simultaneidad $F_s$ [%]'); ax.set_ylabel('Demanda de bajada del puerto [Gbps]')
ax.set_xlim(0, 20); ax.set_ylim(0, 3.2); ax.grid(True, alpha=.4); ax.legend(loc='upper left', fontsize=8)
ax.set_title('Carga de un puerto GPON en función de la simultaneidad')
fig.tight_layout()
os.makedirs('../Figuras', exist_ok=True)
fig.savefig('../Figuras/carga_puertos.png', dpi=150)
