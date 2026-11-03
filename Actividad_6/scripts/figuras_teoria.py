# -*- coding: utf-8 -*-
"""
Figuras conceptuales del TP6 (espectros de AM, FM, TV analógica PAL-N, ISDB-Tb y plan de longitudes de onda
de una red FTTH con RF Overlay). Son esquemas propios, no mediciones.

Uso:  python figuras_teoria.py      -> guarda los PNG en ../Figuras/teoria/
"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import jv, jn_zeros

OUT = '../Figuras/teoria'
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.size': 10})


def guardar(fig, nombre, rect=(0, 0, 1, 1)):
    fig.tight_layout(rect=rect)
    fig.savefig(f'{OUT}/{nombre}', dpi=150)
    plt.close(fig)


#%% AM: tono único y señal de programa
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
m = 0.5
f = np.array([-1, 0, 1])                                  # fc - fm, fc, fc + fm  (fm = 1 kHz)
niv = 20*np.log10(np.array([m/2, 1, m/2]))
a1.vlines(f, -60, niv, lw=2.5)
a1.plot(f, niv, 'o')
for x, y, t in zip(f, niv, ['$f_c-f_m$', '$f_c$', '$f_c+f_m$']):
    a1.annotate(t, (x, y), textcoords='offset points', xytext=(0, 6), ha='center')
a1.annotate('', xy=(1, niv[0]), xytext=(1, 0), arrowprops=dict(arrowstyle='<->', color='C3'))
a1.text(1.08, niv[0]/2, f'{-niv[0]:.1f} dB\n$=20\\log(2/m)$', color='C3', va='center', fontsize=9)
a1.set_xlim(-2, 2.3); a1.set_ylim(-40, 8)
a1.set_xlabel('Frecuencia relativa a $f_c$ [kHz]'); a1.set_ylabel('Nivel relativo [dBc]')
a1.set_title(f'AM con un tono ($m = {m}$, $f_m = 1$ kHz)'); a1.grid(alpha=.4)

fr = np.linspace(-7, 7, 1401)
rng = np.random.default_rng(3)
prog = -28 - 4*np.abs(fr) + 3*rng.standard_normal(fr.size).cumsum()/np.sqrt(fr.size)*4
prog[np.abs(fr) > 5] = -75 + 2*rng.standard_normal((np.abs(fr) > 5).sum())
prog[np.abs(fr) < 0.05] = -75
a2.plot(fr, prog, lw=.8, color='C0')
a2.vlines(0, -80, 0, lw=2.5, color='C0')
a2.axvspan(-5, 5, color='C2', alpha=.12, label='Canal de 10 kHz')
a2.text(-3.6, -14, 'BLI', ha='center'); a2.text(3.6, -14, 'BLS', ha='center'); a2.text(0.3, -4, 'Portadora')
a2.set_xlim(-7, 7); a2.set_ylim(-80, 5)
a2.set_xlabel('Frecuencia relativa a $f_c$ [kHz]'); a2.set_ylabel('Nivel relativo [dBc]')
a2.set_title('AM con señal de programa (esquema)'); a2.grid(alpha=.4); a2.legend(loc='lower right', fontsize=8)
guardar(fig, 'am_espectro.png')

#%% FM: funciones de Bessel y espectro con portadora nula
fig, (b1, b2) = plt.subplots(1, 2, figsize=(10, 3.8))
beta = np.linspace(0, 10, 1000)
for n in range(5):
    b1.plot(beta, jv(n, beta), label=f'$J_{n}(\\beta)$')
for z in jn_zeros(0, 3):
    b1.axvline(z, color='gray', ls=':', lw=.8)
    b1.text(z + 0.08, -0.47, f'{z:.3f}'.replace('.', ','), fontsize=8, color='gray')
b1.axhline(0, color='k', lw=.6)
b1.set_xlabel('Índice de modulación $\\beta$'); b1.set_ylabel('$J_n(\\beta)$')
b1.set_title('Coeficientes de Bessel'); b1.set_ylim(-0.5, 1.1); b1.grid(alpha=.4); b1.legend(fontsize=8, ncol=2)

b0 = jn_zeros(0, 1)[0]
n = np.arange(-8, 9)
amp = np.abs(jv(n, b0))
db = 20*np.log10(np.maximum(amp, 1e-4))
b2.vlines(n, -80, db, lw=2)
b2.plot(n, db, 'o', ms=4)
b2.annotate('Portadora nula\n($J_0 = 0$)', (0, -78), xytext=(2.5, -60), arrowprops=dict(arrowstyle='->'), fontsize=9)
b2.set_xlabel('Frecuencia relativa a $f_c$ [múltiplos de $f_m$]'); b2.set_ylabel('Nivel [dBc sin modular]')
b2.set_title(f'FM con un tono, $\\beta = {b0:.3f}$'.replace('.', '{,}')); b2.set_ylim(-80, 5); b2.grid(alpha=.4)
guardar(fig, 'fm_bessel.png')

#%% TV analógica PAL-N, canal de 6 MHz
fig, ax = plt.subplots(figsize=(10, 3.8))
fv, fsc, fa = 1.25, 1.25 + 3.582056, 1.25 + 4.5          # MHz desde el borde inferior del canal
x = np.linspace(0, 6, 3001)
env = np.interp(x, [0, 0.5, 1.25, 4.2 + 1.25 - 0.0, 1.25 + 4.2, 6], [-60, -60, -8, -8, -60, -60])
env[(x > 0.5) & (x < 1.25)] = np.interp(x[(x > 0.5) & (x < 1.25)], [0.5, 1.25], [-60, -8])
rng = np.random.default_rng(1)
lum = env - 6*np.abs(x - fv) - 3*np.abs(rng.standard_normal(x.size))
lum[x < fv - 0.75] = -60
lum[x > fv + 4.2] = -60
ax.fill_between(x, -60, lum, color='C0', alpha=.35, label='Luminancia (BLS completa y vestigio)')
ax.vlines(fv, -60, 0, lw=2.5, color='C0'); ax.text(fv, 2, 'Portadora de\nvideo', ha='center', fontsize=9)
cro = (x > fsc - 1.0) & (x < fsc + 0.6)
ax.fill_between(x[cro], -60, -32 - 12*np.abs(x[cro] - fsc), color='C1', alpha=.5, label='Crominancia (QAM)')
ax.vlines(fsc, -60, -20, lw=2, color='C1'); ax.text(fsc, -18, 'Subportadora\nde color', ha='center', fontsize=9)
ax.vlines(fa, -60, -12, lw=2.5, color='C3', label='Audio (FM)'); ax.text(fa, -10, 'Portadora\nde audio', ha='center', fontsize=9)
for xl in (0, 6):
    ax.axvline(xl, color='k', lw=1)
ax.annotate('', xy=(fv - 0.75, -50), xytext=(fv, -50), arrowprops=dict(arrowstyle='<->'))
ax.text(fv - 0.37, -48, '0,75', ha='center', fontsize=8)
ax.annotate('', xy=(fv + 4.2, -55), xytext=(fv, -55), arrowprops=dict(arrowstyle='<->'))
ax.text(fv + 2.1, -53, '4,2 MHz (video)', ha='center', fontsize=8)
ax.set_xticks([0, fv, fsc, fa, 6], ['0', '1,25', '4,83', '5,75', '6'])
ax.set_xlim(-0.3, 6.3); ax.set_ylim(-60, 10)
ax.set_xlabel('Frecuencia desde el borde inferior del canal [MHz]'); ax.set_ylabel('Nivel relativo [dB]')
ax.set_title('Canal de televisión analógica PAL-N de 6 MHz (esquema)'); ax.grid(alpha=.3)
fig.legend(loc='lower center', ncol=3, fontsize=8, frameon=False)
guardar(fig, 'tv_pal_n.png', rect=(0, 0.07, 1, 1))

#%% ISDB-Tb: segmentos y espectro OFDM
fig, (c1, c2) = plt.subplots(2, 1, figsize=(10, 5.6), gridspec_kw=dict(height_ratios=[1, 1.2]))
seg = 6/14                                             # MHz
orden = [11, 9, 7, 5, 3, 1, 0, 2, 4, 6, 8, 10, 12]     # numeración de segmentos de abajo hacia arriba
x0 = 3 - 6.5*seg
for i, s in enumerate(orden):
    capa = 'A' if s == 0 else 'B'
    c1.add_patch(plt.Rectangle((x0 + i*seg, 0), seg*0.97, 1, color='C1' if capa == 'A' else 'C0', alpha=.6))
    c1.text(x0 + (i + .5)*seg, .5, str(s), ha='center', va='center', fontsize=9)
c1.text(3, 1.12, 'Capa A: segmento 0 (one-seg, QPSK)', ha='center', color='C1', fontsize=9)
c1.text(1.05, 1.12, 'Capa B: 12 segmentos (HD, 64-QAM)', ha='center', color='C0', fontsize=9)
c1.axvline(0, color='k'); c1.axvline(6, color='k')
c1.set_xlim(-0.2, 6.2); c1.set_ylim(0, 1.35); c1.set_yticks([])
c1.set_xlabel('Frecuencia en el canal [MHz]')
c1.set_title('Canal ISDB-Tb: 13 segmentos de 428,57 kHz (5,57 MHz ocupados)')

xf = np.linspace(-0.5, 6.5, 4000)
banda = np.where(np.abs(xf - 3) <= 6.5*seg + 0.002, 0, -45 - 8*np.abs(np.abs(xf - 3) - 6.5*seg))
banda += 0.8*np.random.default_rng(2).standard_normal(xf.size)
c2.plot(xf, np.maximum(banda, -70), lw=.7)
c2.axvline(0, color='k'); c2.axvline(6, color='k')
c2.annotate('', xy=(3 - 6.5*seg, -20), xytext=(3 + 6.5*seg, -20), arrowprops=dict(arrowstyle='<->'))
c2.text(3, -17, '5,57 MHz', ha='center')
c2.set_xlim(-0.5, 6.5); c2.set_ylim(-70, 8)
c2.set_xlabel('Frecuencia en el canal [MHz]'); c2.set_ylabel('Nivel relativo [dB]')
c2.set_title('Forma del espectro OFDM: meseta plana y flancos abruptos (esquema)'); c2.grid(alpha=.3)
guardar(fig, 'isdbtb_segmentos.png')

#%% OFDM: subportadoras ortogonales
fig, ax = plt.subplots(figsize=(8, 3.2))
fo = np.linspace(-3, 7, 3000)
for k in range(5):
    ax.plot(fo, np.sinc(fo - k), lw=1.2)
    ax.plot(k, 1, 'ko', ms=3)
ax.axhline(0, color='k', lw=.6)
ax.set_xlabel('Frecuencia [múltiplos de $\\Delta f = 1/T_u$]'); ax.set_ylabel('Amplitud')
ax.set_title('Subportadoras OFDM: en el pico de cada una las demás valen cero'); ax.grid(alpha=.3)
guardar(fig, 'ofdm_subportadoras.png')

#%% Longitudes de onda en una FTTH con RF Overlay
fig, ax = plt.subplots(figsize=(10, 2.9))
bandas = [(1260, 1280, 'XGS-PON\nsubida', 'C4'), (1290, 1330, 'GPON\nsubida', 'C0'), (1480, 1500, 'GPON\nbajada', 'C2'),
          (1550, 1560, 'Video\nRF Overlay', 'C3'), (1575, 1581, 'XGS-PON\nbajada', 'C1')]
for a, b, t, c in bandas:
    ax.add_patch(plt.Rectangle((a, 0), b - a, 1, color=c, alpha=.6))
    ax.text((a + b)/2, 1.08, t, ha='center', va='bottom', fontsize=8)
ax.set_xlim(1240, 1600); ax.set_ylim(0, 1.7); ax.set_yticks([])
ax.set_xlabel('Longitud de onda [nm]')
ax.set_title('Plan de longitudes de onda habitual en una ODN compartida (G.984.5 / G.9807.1)')
guardar(fig, 'longitudes_onda.png')

print('Figuras guardadas en', os.path.abspath(OUT))
