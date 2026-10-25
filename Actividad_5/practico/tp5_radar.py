# -*- coding: utf-8 -*-
"""
Procesamiento de la señal de radar del TP5: compresión con filtro apareado, ventana CFAR,
canceladores MTI simple, STI simple y MTI doble, y filtrado Doppler.

Basado en cfar_doppler_processing_alumnos.py (fdadam). Uso:
    python tp5_radar.py 1      # procesa signal_1.csv
Las figuras se guardan en ../Figuras/senal_<n>/ y los resultados en ../Figuras/senal_<n>/resultados.json
"""

#%% Libs and functions
import os, sys, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
if len(sys.argv) > 1:
    matplotlib.use('Agg')            # sin ventanas cuando se ejecuta desde la línea de comandos
import matplotlib.pyplot as plt
import pandas as pd
from scipy.fft import fft, ifft, fftshift


def fastconv(A, B):
    """Convolución rápida por FFT (función provista por la cátedra)."""
    out_len = len(A) + len(B) - 1
    sizefft = int(2**(np.ceil(np.log2(out_len))))      # potencia de 2 más próxima
    Afilled = np.concatenate((A, np.zeros(sizefft - len(A))))
    Bfilled = np.concatenate((B, np.zeros(sizefft - len(B))))
    out = ifft(fft(Afilled) * fft(Bfilled))
    return out[0:out_len]


#%% Parameters (los de la cátedra)

SENAL = int(sys.argv[1]) if len(sys.argv) > 1 else 1
c = 3e8                 # speed of light [m/s]
fc = 1.3e9              # Carrier freq
fs = 10e6               # Sampling freq
Np = 100                # Intervalos de sampling (pulsos)
ts = 1/fs

Te = 5e-6               # Tx recovery Time [s]
Tp = 10e-6              # Tx Pulse Width [s]
BW = 2e6                # Tx Chirp bandwidth [Hz]
PRF = 1500              # Pulse repetition Frequency [Hz]

wlen = c/fc                         # Wavelength [m]
PRI = PRF**(-1)                     # Pulse repetition interval [s]
ru = (c*(PRI-Tp-Te))/2              # Unambigous Range [m]
vu_ms = wlen*PRF/2                  # Unambigous Velocity [m/s]
rank_min = (Tp/2+Te)*c/2            # Minimum Range [m]
rank_max = 30e3                     # Maximum Range [m]
rank_res = ts*c/2                   # Range Step [m]
tmax = 2*rank_max/c                 # Maximum Simulation Time
res_rango = c/(2*BW)                # Resolución en rango del chirp comprimido [m]

# Parámetros del CFAR (CA-CFAR)
N_REF = 64              # celdas de referencia (cómputo), 32 de cada lado
N_GAP = 8               # celdas de guarda de cada lado de la celda bajo prueba
PFA = 1e-6              # probabilidad de falsa alarma de diseño
ALFA = N_REF*(PFA**(-1/N_REF) - 1)   # factor del umbral en potencia (detector cuadrático)
GANANCIA = np.sqrt(ALFA)             # factor del umbral en amplitud

OUT = f'../Figuras/senal_{SENAL}'
os.makedirs(OUT, exist_ok=True)

radar_signal = pd.read_csv(f'signal_{SENAL}.csv', index_col=None)
radar_signal = np.array(radar_signal['real'] + 1j*radar_signal['imag'])
radar_signal = radar_signal.reshape(Np, -1)        # filas: tiempo lento (pulsos); columnas: tiempo rápido (rango)

print(f'Señal {SENAL}: {radar_signal.shape[0]} pulsos x {radar_signal.shape[1]} muestras')
print(f'PRI = {PRI*1e6:.2f} us | Ru = {ru/1e3:.3f} km | Vu = {vu_ms:.2f} m/s | Rmin = {rank_min/1e3:.3f} km')
print(f'Resolución en rango = {res_rango:.0f} m | paso de muestreo = {rank_res:.0f} m')
print(f'CFAR: {N_REF} celdas de referencia, {N_GAP} de guarda por lado, Pfa = {PFA:g}, ganancia = {GANANCIA:.2f}')

#%% Signals

Npts = int(tmax/ts)                                  # Simulation Points
t = np.linspace(-tmax/2, tmax/2, Npts)
ranks = np.linspace(rank_res, rank_max, Npts)        # Range Vector

tx_chirp = np.exp(1j*np.pi*BW/Tp * t**2)             # Tx Linear Chirp (t)
tx_rect = np.where(np.abs(t) <= Tp/2, 1, 0)          # Rect Function
tx_chirp = tx_rect*tx_chirp                          # Tx Chirp Rectangular

# Matched Filter: h(t) = s*(-t)
matched_filter = np.conj(np.flip(tx_chirp))


def comprimir(x):
    """Compresión de un pulso: convolución con el filtro apareado, recortada para alinear el pico con el rango."""
    y = fastconv(x, matched_filter)
    i0 = (len(matched_filter) - 1)//2
    return y[i0:i0 + len(x)]


compressed = np.array([comprimir(p) for p in radar_signal])


#%% CFAR

def ventana_cfar():
    w = np.concatenate((np.ones(N_REF//2), np.zeros(2*N_GAP + 1), np.ones(N_REF//2)))
    return w/N_REF


H_CFAR = ventana_cfar()


def ruido_cfar(potencia):
    """Potencia media de las celdas de referencia. En los bordes del vector hay menos celdas, por lo que se
    normaliza por la cantidad de celdas realmente disponibles (sin esto el umbral cae en los extremos)."""
    suma = np.convolve(potencia, H_CFAR*N_REF, mode='same')
    celdas = np.convolve(np.ones_like(potencia), H_CFAR*N_REF, mode='same')
    return suma/celdas


def umbral_cfar(potencia):
    """Umbral CA-CFAR en amplitud: ganancia * sqrt(potencia media de las celdas de referencia)."""
    return np.sqrt(ALFA*ruido_cfar(potencia))


MIN_SEP = int(round(2*res_rango/rank_res))        # 10 celdas = 150 m: dentro de esto, lóbulos del mismo blanco


def detectar(amplitud, umbral, min_sep=MIN_SEP):
    """Detección por cruces por cero de (señal - umbral); devuelve el índice del máximo de cada cruce."""
    d = np.sign(amplitud - umbral)
    d[ranks < rank_min] = -1                         # celdas dentro del rango mínimo (blanqueo del receptor)
    cruces = np.diff(d)
    subidas = np.where(cruces > 0)[0] + 1
    bajadas = np.where(cruces < 0)[0] + 1
    picos = []
    for s in subidas:
        b = bajadas[bajadas > s]
        e = b[0] if len(b) else len(amplitud)
        picos.append(s + int(np.argmax(amplitud[s:e])))
    # fusiona picos separados por menos de min_sep celdas (lóbulos del mismo blanco)
    fusion = []
    for p in picos:
        if fusion and p - fusion[-1] < min_sep:
            if amplitud[p] > amplitud[fusion[-1]]:
                fusion[-1] = p
        else:
            fusion.append(p)
    return fusion, cruces


#%% Cancelers (en tiempo lento, sobre la señal comprimida)

mti_sc = compressed[1:] - compressed[:-1]                          # H(z) = 1 - z^-1
sti_sc = compressed[1:] + compressed[:-1]                          # H(z) = 1 + z^-1
mti_dc = compressed[2:] - 2*compressed[1:-1] + compressed[:-2]     # H(z) = 1 - 2 z^-1 + z^-2

resultados = dict(senal=SENAL, ganancia_cfar=GANANCIA, alfa=ALFA, pfa=PFA, n_ref=N_REF, n_gap=N_GAP)

#%% Plot 1: Received signal (un momento de muestreo)

fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
fig.suptitle(f'Señal {SENAL}: señal recibida (pulso 0)')
ax = axes[0]
ax.plot(ranks/1e3, np.real(radar_signal[0]), label='Real')
ax.plot(ranks/1e3, np.imag(radar_signal[0]), label='Imaginaria')
ax.set_ylabel('Amplitud'); ax.legend(loc='upper right'); ax.grid(True)
ax = axes[1]
ax.plot(ranks/1e3, np.abs(radar_signal[0]))
ax.set_ylabel('|Amplitud|'); ax.set_xlabel('Rango [km]'); ax.grid(True)
fig.tight_layout(); fig.savefig(f'{OUT}/01_senal_recibida.png', dpi=150); plt.close(fig)

#%% Plot 2: señal sin comprimir y comprimida

fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
fig.suptitle(f'Señal {SENAL}: compresión con filtro apareado (pulso 0)')
axes[0].plot(ranks/1e3, np.abs(radar_signal[0]))
axes[0].set_ylabel('|Señal sin comprimir|'); axes[0].grid(True)
axes[1].plot(ranks/1e3, np.abs(compressed[0]), color='tab:orange')
axes[1].set_ylabel('|Señal comprimida|'); axes[1].set_xlabel('Rango [km]'); axes[1].grid(True)
fig.tight_layout(); fig.savefig(f'{OUT}/02_compresion.png', dpi=150); plt.close(fig)

#%% Plot 3: ventana CFAR

fig, ax = plt.subplots(figsize=(7, 5))
ax.step(np.arange(len(H_CFAR)), H_CFAR, where='mid', lw=2)
ax.set_title('Ventana CFAR'); ax.set_xlabel('Muestra'); ax.set_ylabel('Valor de la ventana')
ax.text(0.05, 0.08, f'Celdas de referencia: {N_REF}\nCeldas de guarda: {N_GAP} por lado\nCelda bajo prueba: 1',
        transform=ax.transAxes, bbox=dict(boxstyle='round', fc='wheat', alpha=.5))
ax.grid(True); fig.tight_layout(); fig.savefig(f'{OUT}/03_ventana_cfar.png', dpi=150); plt.close(fig)

#%% Plot 4-6: CFAR plots de los canceladores

def cfar_plot(nombre, archivo, salida, pulsos, signos):
    """Gráfico CFAR de un cancelador usando los pulsos indicados (momento de muestreo t0, t1, ...)."""
    amp = np.abs(salida[0])
    thr = umbral_cfar(amp**2)
    det, cruces = detectar(amp, thr)
    # Detección integrada (no coherente) sobre todos los momentos de muestreo
    pot_int = np.mean(np.abs(salida)**2, axis=0)
    amp_int = np.sqrt(pot_int)
    det_int, _ = detectar(amp_int, umbral_cfar(pot_int))

    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    fig.suptitle(f'Señal {SENAL}: {nombre}')
    for k, p in enumerate(pulsos):
        axes[0].plot(ranks/1e3, np.abs(radar_signal[p]), label=f'Rx $t_{k}$')
        axes[1].plot(ranks/1e3, np.abs(compressed[p]), label=f'Comp $t_{k}$')
    axes[0].set_title('Señales recibidas sin comprimir'); axes[1].set_title('Señales comprimidas')
    axes[2].plot(ranks/1e3, amp, label=f'{nombre} ({signos})')
    axes[2].plot(ranks/1e3, thr, label=f'Umbral CFAR (ganancia {GANANCIA:.2f})')
    axes[2].set_title(f'Salida del cancelador y umbral CFAR')
    axes[3].plot(ranks[1:]/1e3, cruces, color='tab:green')
    axes[3].set_title('Cruces por cero de (salida $-$ umbral): +2 inicio, $-2$ fin de una detección')
    axes[3].set_xlabel('Rango [km]')
    for ax in axes:
        ax.grid(True); ax.axvline(rank_min/1e3, color='gray', ls=':', lw=1)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(loc='upper right', fontsize=8)
    texto = '\n'.join(f'Blanco {i+1}: {ranks[d]/1e3:.2f} km' for i, d in enumerate(det)) or 'Sin detecciones'
    axes[2].text(1.01, 1.0, texto, transform=axes[2].transAxes, va='top', fontsize=8,
                 bbox=dict(boxstyle='round', fc='wheat', alpha=.5))
    fig.tight_layout(); fig.savefig(f'{OUT}/{archivo}', dpi=150); plt.close(fig)
    return [float(ranks[d]) for d in det], [float(ranks[d]) for d in det_int], amp_int


r_mti, r_mti_int, amp_mti_int = cfar_plot('MTI simple cancelador', '04_cfar_mti_sc.png', mti_sc, [0, 1], '$x_1 - x_0$')
r_sti, r_sti_int, amp_sti_int = cfar_plot('STI simple cancelador', '05_cfar_sti_sc.png', sti_sc, [0, 1], '$x_1 + x_0$')
r_mdc, r_mdc_int, _ = cfar_plot('MTI doble cancelador', '06_cfar_mti_dc.png', mti_dc, [0, 1, 2], '$x_2 - 2x_1 + x_0$')
resultados.update(mti_sc=r_mti, sti_sc=r_sti, mti_dc=r_mdc,
                  mti_sc_integrado=r_mti_int, sti_sc_integrado=r_sti_int, mti_dc_integrado=r_mdc_int)

#%% Doppler processing: FD = exp(-j 2 pi row col / m) sobre la señal MTI SC

m = mti_sc.shape[0]
row = np.arange(m).reshape(-1, 1); col = np.arange(m).reshape(1, -1)
FD = np.exp(-1j*2*np.pi*row*col/m)                     # matriz de la DFT [m x m]
doppler = mti_sc.T @ FD                                # [rango x frecuencia Doppler]
doppler = fftshift(doppler, axes=1)/m
fd = (np.arange(m) - m//2)*PRF/m                       # frecuencias Doppler [Hz]
vel = fd*wlen/2                                        # velocidades radiales [m/s]

# Detección en el mapa rango-Doppler: CA-CFAR en rango para cada frecuencia Doppler. La integración
# coherente de los pulsos mejora la relación señal a ruido, y blancos de distinta velocidad quedan en
# columnas distintas, por lo que un blanco fuerte no enmascara a otro cercano en rango.
# Para detectar se aplica una ventana de Hamming en tiempo lento: baja los lóbulos laterales Doppler de
# -13 dB (DFT rectangular) a -43 dB, que de otro modo superarían el umbral junto a blancos de 40 dB.
doppler_w = fftshift((mti_sc*np.hamming(m)[:, None]).T @ FD, axes=1)/m
P_rd = np.abs(doppler_w)**2
det_rd = np.zeros_like(P_rd, dtype=bool)
for k in range(m):
    det_rd[:, k] = P_rd[:, k] > ALFA*ruido_cfar(P_rd[:, k])
det_rd[ranks < rank_min, :] = False
# Agrupa celdas detectadas vecinas (lóbulos en rango y en Doppler) y conserva el máximo de cada grupo
cand = sorted(zip(*np.where(det_rd)), key=lambda ik: -P_rd[ik])
blancos = []
for i, k in cand:
    dk = lambda a, b: min(abs(a - b), m - abs(a - b))          # distancia circular en Doppler
    if all(abs(i - b['_i']) > MIN_SEP or dk(k, b['_k']) > 3 for b in blancos):
        blancos.append(dict(_i=int(i), _k=int(k), rango_km=round(float(ranks[i])/1e3, 3),
                            velocidad_ms=round(float(vel[k]), 2), velocidad_kmh=round(float(vel[k])*3.6, 1),
                            snr_db=round(float(10*np.log10(P_rd[i, k]/np.median(P_rd[:, k]))), 1)))
detecciones_rd = sorted(blancos, key=lambda b: b['rango_km'])

# ---- Clasificación final de los blancos ----
# 1) Residuos: una detección en la misma celda de rango que otra más fuerte y más de 20 dB por debajo es la
#    dispersión Doppler (fluctuación de la RCS) del blanco fuerte, no un blanco distinto.
# 2) Blanco móvil: detección rango-Doppler confirmada por algún cancelador (en cualquier momento de muestreo o
#    integrado) a menos de 150 m, o con relación señal a ruido de al menos 20 dB. Las detecciones débiles y
#    aisladas se descartan como falsas alarmas.
# 3) Blanco fijo: detección del STI integrado donde la salida del STI supera a la del MTI en más de 10 dB
#    (el MTI cancela casi toda su energía, es decir, su velocidad es nula).
confirmadas = r_mti + r_sti + r_mdc + r_mti_int + r_sti_int + r_mdc_int
moviles, descartes = [], []
for b in detecciones_rd:
    vecinos = [o for o in detecciones_rd if abs(o['_i'] - b['_i']) <= MIN_SEP and o['snr_db'] > b['snr_db']]
    if any(o['snr_db'] - b['snr_db'] > 20 for o in vecinos):
        descartes.append(dict(b, motivo='residuo de un blanco más fuerte')); continue
    confirmada = any(abs(ranks[b['_i']] - r) <= 2*res_rango for r in confirmadas)
    if not (confirmada or b['snr_db'] >= 20):
        descartes.append(dict(b, motivo='falsa alarma (débil y sin confirmar)')); continue
    if abs(b['velocidad_ms']) < PRF/m*wlen/2*1.5:
        continue                                        # velocidad nula: lo clasifica el criterio de blancos fijos
    moviles.append(b)
fijos = []
for r in r_sti_int:
    i = int(np.argmin(np.abs(ranks - r)))
    rel_db = 20*np.log10(amp_sti_int[i]/amp_mti_int[i])
    if rel_db > 10:
        fijos.append(dict(rango_km=round(r/1e3, 3), sti_sobre_mti_db=round(float(rel_db), 1)))
limpiar = lambda lista: [{k: v for k, v in b.items() if not k.startswith('_')} for b in lista]
blancos = limpiar(moviles)
resultados.update(detecciones_rango_doppler=limpiar(detecciones_rd), descartes=limpiar(descartes),
                  blancos_moviles=blancos, blancos_fijos=fijos,
                  resolucion_velocidad_ms=float(PRF/m*wlen/2), velocidad_max_no_ambigua_ms=float(PRF/2*wlen/2))

# Plot 7: 3D Doppler
R, V = np.meshgrid(ranks/1e3, vel, indexing='ij')
Z = np.abs(doppler)
paso = 4                                               # submuestreo en rango para el gráfico
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection='3d')
surf = ax.plot_surface(V[::paso], R[::paso], Z[::paso], cmap='coolwarm', linewidth=0, antialiased=False)
ax.set_xlabel('Velocidad [m/s]'); ax.set_ylabel('Rango [km]'); ax.set_zlabel('|Producto Doppler|')
ax.set_title(f'Señal {SENAL}: procesamiento Doppler (MTI SC)')
fig.colorbar(surf, shrink=0.5, pad=0.1)
fig.tight_layout(); fig.savefig(f'{OUT}/07_doppler_3d.png', dpi=150); plt.close(fig)

# Plot 8: mapa rango-velocidad (vista superior) con los blancos detectados
fig, ax = plt.subplots(figsize=(9, 6))
im = ax.pcolormesh(vel, ranks/1e3, 20*np.log10(Z/Z.max() + 1e-12), cmap='viridis', vmin=-50, shading='auto')
for b in blancos:
    ax.plot(b['velocidad_ms'], b['rango_km'], 'rx', ms=10, mew=2)
    ax.annotate(f"{b['rango_km']:.2f} km\n{b['velocidad_ms']:.1f} m/s", (b['velocidad_ms'], b['rango_km']),
                textcoords='offset points', xytext=(8, 4), color='w', fontsize=8)
for b in fijos:                                         # blancos fijos (cancelados por el MTI): v = 0
    ax.plot(0, b['rango_km'], 's', mfc='none', mec='orange', ms=10, mew=2)
    ax.annotate(f"{b['rango_km']:.2f} km (fijo)", (0, b['rango_km']), textcoords='offset points',
                xytext=(8, -10), color='orange', fontsize=8)
ax.set_xlabel('Velocidad radial [m/s]'); ax.set_ylabel('Rango [km]')
ax.set_title(f'Señal {SENAL}: mapa rango-velocidad [dB]'); fig.colorbar(im, ax=ax, label='dB')
fig.tight_layout(); fig.savefig(f'{OUT}/08_mapa_rango_velocidad.png', dpi=150); plt.close(fig)

json.dump(resultados, open(f'{OUT}/resultados.json', 'w'), indent=1)
print('MTI SC (t0,t1) [km]:', [round(r/1e3, 2) for r in r_mti])
print('STI SC (t0,t1) [km]:', [round(r/1e3, 2) for r in r_sti])
print('MTI DC (t0,t1,t2) [km]:', [round(r/1e3, 2) for r in r_mdc])
print('Integrado MTI SC [km]:', [round(r/1e3, 2) for r in r_mti_int])
print('Integrado STI SC [km]:', [round(r/1e3, 2) for r in r_sti_int])
print('Integrado MTI DC [km]:', [round(r/1e3, 2) for r in r_mdc_int])
print('Blancos móviles:', blancos)
print('Blancos fijos [km]:', fijos)
