# -*- coding: utf-8 -*-
"""Figuras de la parte teórica del TP5: RCS de la esfera y de la placa plana, chirp y compresión, y respuesta
en frecuencia de los canceladores. Se guardan en ../Figuras/teoria/."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import spherical_jn, spherical_yn
from scipy.fft import fft, ifft, fftfreq, fftshift

OUT = '../Figuras/teoria'
os.makedirs(OUT, exist_ok=True)

# ---------------- RCS de una esfera conductora (serie de Mie) ----------------
def rcs_esfera(x, nmax=None):
    """sigma/(pi a^2) monoestática de una esfera perfectamente conductora, x = ka = 2 pi a / lambda."""
    nmax = nmax or int(x + 4*x**(1/3) + 10)
    n = np.arange(1, nmax + 1)
    jn, yn = spherical_jn(n, x), spherical_yn(n, x)
    jnp, ynp = spherical_jn(n, x, True), spherical_yn(n, x, True)
    hn, hnp = jn + 1j*yn, jnp + 1j*ynp
    a = jn/hn                                  # coeficiente TM
    b = (jn + x*jnp)/(hn + x*hnp)              # coeficiente TE: [x j_n(x)]' / [x h_n(x)]'
    s = np.sum((-1)**n*(2*n + 1)*(a - b))
    return abs(s)**2/x**2

x = np.logspace(-1, np.log10(20), 600)
s = np.array([rcs_esfera(v) for v in x])
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.loglog(x, s, lw=2, label='Serie de Mie')
ax.loglog(x[x < 0.6], 9*x[x < 0.6]**4, 'k--', label=r'Rayleigh: $9(ka)^4$')
ax.axhline(1, color='gray', ls=':', label=r'Óptica: $\sigma = \pi a^2$')
for xx, txt in ((0.25, 'Rayleigh'), (2.2, 'Mie (resonancia)'), (12, 'Óptica')):
    ax.text(xx, 4, txt, ha='center', fontsize=10, bbox=dict(fc='w', ec='gray', alpha=.8))
ax.set_xlabel(r'$ka = 2\pi a/\lambda$'); ax.set_ylabel(r'$\sigma / \pi a^2$')
ax.set_ylim(1e-4, 10); ax.grid(True, which='both', alpha=.4); ax.legend(loc='lower right')
ax.set_title('RCS normalizada de una esfera conductora')
fig.tight_layout(); fig.savefig(f'{OUT}/rcs_esfera.png', dpi=150); plt.close(fig)
print('esfera: ka=0.1 ->', rcs_esfera(0.1), '(9x^4 =', 9e-4, ') | ka=1 ->', rcs_esfera(1.0), '| ka=20 ->', rcs_esfera(20))

# ---------------- RCS de una placa plana cuadrada ----------------
lam = 0.03                 # 10 GHz
L = 1.0                    # placa de 1 m x 1 m
th = np.radians(np.linspace(-90, 90, 2001))
kL = 2*np.pi/lam*L
sigma = 4*np.pi*L**4/lam**2*np.cos(th)**2*np.sinc(kL*np.sin(th)/np.pi)**2
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(np.degrees(th), 10*np.log10(sigma + 1e-6))
ax.set_ylim(-20, 45); ax.grid(True, alpha=.4)
ax.set_xlabel(r'Ángulo de incidencia respecto de la normal [$^\circ$]'); ax.set_ylabel(r'$\sigma$ [dBsm]')
ax.set_title(r'Placa plana de $1 \times 1$ m a 10 GHz (óptica física)')
fig.tight_layout(); fig.savefig(f'{OUT}/rcs_placa.png', dpi=150); plt.close(fig)
print('placa: sigma normal =', 10*np.log10(4*np.pi*L**4/lam**2), 'dBsm')

# ---------------- Chirp y compresión con los parámetros del TP ----------------
Tp, BW, fs = 10e-6, 2e6, 100e6
t = np.arange(-Tp/2, Tp/2, 1/fs)
chirp = np.exp(1j*np.pi*BW/Tp*t**2)
mf = np.conj(chirp[::-1])
comp = np.convolve(chirp, mf)/len(chirp)
tc = (np.arange(len(comp)) - (len(comp) - 1)/2)/fs
fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
axes[0].plot(t*1e6, chirp.real, label='Real'); axes[0].plot(t*1e6, chirp.imag, label='Imaginaria')
axes[0].set_xlabel(r't [$\mu$s]'); axes[0].set_title('Chirp transmitido'); axes[0].legend(loc='lower left', fontsize=8)
axes[1].plot(t*1e6, BW/Tp*t/1e6); axes[1].set_xlabel(r't [$\mu$s]'); axes[1].set_ylabel('Frecuencia [MHz]')
axes[1].set_title('Frecuencia instantánea')
axes[2].plot(tc*1e6, 20*np.log10(np.abs(comp) + 1e-9)); axes[2].set_xlim(-3, 3); axes[2].set_ylim(-40, 2)
axes[2].axhline(-13.2, color='gray', ls=':'); axes[2].text(1.2, -12, '$-13{,}2$ dB', fontsize=8)
axes[2].set_xlabel(r't [$\mu$s]'); axes[2].set_ylabel('dB'); axes[2].set_title('Salida del filtro apareado')
for a in axes:
    a.grid(True, alpha=.4)
fig.tight_layout(); fig.savefig(f'{OUT}/chirp_compresion.png', dpi=150); plt.close(fig)
ancho = np.sum(np.abs(comp) >= np.abs(comp).max()/np.sqrt(2))/fs
print('ancho a -3 dB del pulso comprimido:', ancho*1e6, 'us ->', ancho*3e8/2, 'm')

# ---------------- Respuesta de los canceladores ----------------
PRF, wlen = 1500, 3e8/1.3e9
v = np.linspace(-200, 200, 2001)
fd = 2*v/wlen
w = 2*np.pi*fd/PRF
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(v, 20*np.log10(np.abs(1 - np.exp(-1j*w)) + 1e-6), label=r'MTI simple: $|1 - z^{-1}|$')
ax.plot(v, 20*np.log10(np.abs(1 - 2*np.exp(-1j*w) + np.exp(-2j*w)) + 1e-6), label=r'MTI doble: $|1 - z^{-1}|^2$')
ax.plot(v, 20*np.log10(np.abs(1 + np.exp(-1j*w)) + 1e-6), label=r'STI simple: $|1 + z^{-1}|$')
for vb in (-wlen*PRF/2, 0, wlen*PRF/2):
    ax.axvline(vb, color='gray', ls=':')
ax.set_ylim(-40, 15); ax.grid(True, alpha=.4); ax.legend(loc='lower right', fontsize=9)
ax.set_xlabel('Velocidad radial [m/s]'); ax.set_ylabel('Ganancia [dB]')
ax.set_title(r'Respuesta de los canceladores (PRF = 1500 Hz, $\lambda$ = 23,1 cm)')
fig.tight_layout(); fig.savefig(f'{OUT}/respuesta_canceladores.png', dpi=150); plt.close(fig)
print('velocidad ciega v_b =', wlen*PRF/2, 'm/s')
