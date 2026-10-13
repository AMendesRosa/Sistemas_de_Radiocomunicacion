# Actividad 4 - Fibra óptica

```
Actividad_4/
├── Consigna/          Enunciados de la cátedra (PDF, se suben con git add -f)
├── Parte_1/           Enlace P2P con fibra óptica (8 km, 1 Gbps) - TERMINADA
│   ├── main.tex       Documento principal (incluye parteA..D)
│   ├── parteA..D.tex  Selección, presupuesto, gráficos y preguntas
│   ├── Figuras/
│   └── Presentacion/  Presentación beamer
└── Parte_2/           Diseño de red FTTH GPON en Marcos Juárez - EN CURSO
    ├── main.tex       Documento principal
    ├── secciones/     Un archivo por punto de la consigna (00 a 11)
    ├── Figuras/       Imágenes (fotos, capturas, logos)
    └── Planos/        Planos, mapas y diagramas de la red
```

## Cómo trabajar en la Parte 2
- Cada punto de la consigna está en su propio archivo de `secciones/`. Así cada uno puede
  trabajar en una sección distinta sin pisarse en los merges.
- Lo que falta completar está marcado con `\pendiente{...}` y aparece **en rojo** en el PDF.
  Antes de entregar, buscar `\pendiente` y verificar que no quede ninguno.
- Los comentarios `%` al principio de cada sección copian lo que pide la consigna.
- Fuentes web: agregar `urldate` con la fecha de consulta (la consigna lo exige).
- Compilar desde la carpeta de cada parte: `latexmk -pdf main.tex`.
