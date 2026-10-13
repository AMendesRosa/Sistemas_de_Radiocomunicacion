"""Parámetros de la región a diseñar. Uso: REG=E python design.py  (o REG=O para la Región Oeste)."""
import os
REG = os.environ.get('REG', 'E')
SUF = '' if REG == 'E' else '_O'          # sufijo de los archivos de salida
PC = 'C' if REG == 'E' else 'O'           # prefijo de cluster: C1... / O1...
PS = '' if REG == 'E' else 'O'            # prefijo de sector: 28 / O28
PD = 'D' if REG == 'E' else 'DO'          # prefijo de las derivaciones del troncal
NOMBRE = 'Este' if REG == 'E' else 'Oeste'
# Sectores desarrollados en detalle (índices desde 0)
DETALLE = [int(x) for x in os.environ.get('DETALLE', '27,89' if REG == 'E' else '').split(',') if x]


def fn(nombre):
    base, ext = nombre.rsplit('.', 1)
    return f'{base}{SUF}.{ext}'
