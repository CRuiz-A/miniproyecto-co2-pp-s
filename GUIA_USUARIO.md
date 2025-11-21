# 📚 Guía de Usuario - GeoViz

## Bienvenido a GeoViz

GeoViz es una aplicación moderna para la visualización de datos geológicos, especialmente diseñada para el análisis de reservorios de CO₂ y propiedades geológicas.

## 🚀 Inicio Rápido

### 1. Ejecutar la Aplicación

```bash
cd /home/spell/Desktop/pyvista
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### 2. Navegación Principal

La aplicación tiene una barra lateral (sidebar) en el lado izquierdo con las siguientes secciones:

#### 🏠 Inicio
- Página de bienvenida con tarjetas informativas
- Presenta los tres tipos principales de reservorios:
  - **Reservorios de Gas Vaciado**: Campos de gas agotados
  - **Acuíferos Salinas**: Formaciones salinas profundas
  - **Otros Yacimientos (Geos)**: Otras formaciones geológicas

#### 🗺️ Bunter
Visualización completa del reservorio Bunter con dos pestañas:

**Pestaña 1: Viewer CO₂**
- Visualización 3D interactiva de la pluma de CO₂
- Control de timesteps con animación
- Métricas en tiempo real:
  - Timesteps totales
  - Celdas activas totales
  - Máximo de celdas por timestep
  - Umbral YMFS configurado

**Controles del Viewer:**
- **Slider de Timestep**: Navega entre diferentes momentos de la simulación
- **Botones de navegación**: ◀ Anterior | ▶ Siguiente | ▶ Play
- **Z Scale**: Ajusta la escala vertical para mejor visualización
- **Mostrar inyectores**: Toggle para mostrar/ocultar pozos inyectores

**Pestaña 2: Propiedades**
- Visualización 3D de propiedades geológicas
- Dos modos de visualización:
  - **Individual**: Una propiedad a la vez
  - **Paralelo**: Tres gráficos simultáneos

#### 💧 Salinas
- Sección en desarrollo para acuíferos salinas
- Próximamente disponible

#### 📊 Simulaciones
Dashboard de simulaciones avanzadas con parámetros configurables:

**Parámetros de Simulación** (en sidebar):
- **Profundidad**: 1000-4000m (paso: 100m)
- **Presión de Inyección**: 50-300 bar (paso: 10 bar)
- **Saturación de CO₂**: 0-100% (paso: 5%)
- **Escala de Tiempo**: 1-100 años (paso: 1 año)

**Visualizaciones**:
- Viewer CO₂ con configuración de parámetros
- Gráficos de evolución temporal

#### 🔬 Propiedades
Análisis detallado de propiedades geológicas:

**Propiedades Disponibles**:
1. **Permeabilidad** (`permeability.npy`)
   - Colormap: Hot (por defecto)
   - Escala logarítmica recomendada
   - Unidades: mD (milidarcys)

2. **Porosidad** (`porosity.npy`)
   - Colormap: Viridis (por defecto)
   - Escala lineal o logarítmica
   - Unidades: fracción (0-1)

3. **Facies** (`facies.npy`)
   - Colores discretos: Marrón (Shalty) y Dorado (Sand)
   - Valores: 2 (Shalty) y 3 (Sand)

## 🎮 Controles Interactivos

### Controles de Visualización 3D

**Cortes Planos**:
- **Corte X (plano YZ)**: Slider para seleccionar el índice X
- **Corte Y (plano XZ)**: Slider para seleccionar el índice Y  
- **Corte Z (plano XY)**: Slider para seleccionar el índice Z

**Configuración Visual**:
- **Mapa de colores**: Selecciona entre 12 colormaps diferentes
  - Hot, Viridis, Plasma, Cividis, Jet, Rainbow
  - Turbo, Magma, Inferno, Greys, Blues, Reds
- **Escala logarítmica**: Checkbox para aplicar log10 a los valores

### Modo de Visualización Paralelo

Cuando seleccionas "Paralelo (3 gráficos)", verás:

1. **Columna 1**: Permeabilidad
   - Configuración: Colormap independiente
   - Escala log activable

2. **Columna 2**: Porosidad
   - Configuración: Colormap independiente
   - Escala log activable

3. **Columna 3**: Facies
   - Colores fijos para Shalty y Sand
   - Estadísticas automáticas

**Ventajas del Modo Paralelo**:
- Comparación simultánea de propiedades
- Controles sincronizados (mismo corte X, Y, Z)
- Vista holística del reservorio

## 📊 Métricas y Estadísticas

### Tarjetas de Métricas (CO₂ Viewer)

Las tarjetas muestran información clave en tiempo real:

1. **Timesteps Totales**: Número de pasos temporales disponibles
2. **Celdas Activas (Total)**: Suma de celdas con CO₂ en todos los timesteps
3. **Máx. Celdas (ts)**: Mayor número de celdas activas en un timestep
4. **Umbral YMFS**: Valor mínimo de YMFS considerado (configurable)

### Estadísticas de Facies

Al visualizar facies, se muestran:
- Conteo de celdas Shalty vs Sand
- Porcentaje de distribución
- Información en caption debajo del gráfico

## ⚙️ Configuración Avanzada

### Umbral YMFS

El slider "Umbral mínimo YMFS" (en sidebar del CO₂ Viewer) controla:
- Valor mínimo de YMFS para considerar una celda "activa"
- Rango: 0.0 - 1.0
- Paso: 0.01
- Por defecto: 0.10

**Efecto**:
- Valores más altos → Menos celdas, pluma más concentrada
- Valores más bajos → Más celdas, pluma más extensa

### Cache de Datos

Los datos procesados se cachean automáticamente en:
```
outputs/cache/data_thr{threshold}.json
```

Esto acelera cargas posteriores con el mismo umbral.

## 🎨 Características de la Interfaz

### Tema Oscuro Profesional
- Diseño optimizado para reducir fatiga visual
- Alto contraste para datos importantes
- Colores vibrantes pero no excesivos

### Tarjetas Interactivas (Glass Cards)
- Efecto glassmorphism moderno
- Animaciones suaves al pasar el mouse
- Elevación visual en hover

### Indicadores de Estado
- **Punto pulsante azul**: Indica procesos activos o simulaciones en ejecución
- Texto "Simulación Activa" para claridad

### Tipografía
- Fuente: Space Grotesk (moderna y legible)
- Jerarquía clara de títulos
- Espaciado optimizado

## 🔍 Casos de Uso

### Caso 1: Análisis de Evolución Temporal de CO₂

1. Ve a **🗺️ Bunter** → **Viewer CO₂**
2. Ajusta el umbral YMFS según necesites
3. Usa el slider de timestep para navegar
4. Presiona **▶ Play** para ver la animación
5. Observa las métricas para cuantificar la dispersión

### Caso 2: Comparación de Propiedades Geológicas

1. Ve a **🔬 Propiedades**
2. Selecciona "Paralelo (3 gráficos)"
3. Ajusta los cortes X, Y, Z para explorar el volumen
4. Compara visualmente permeabilidad, porosidad y facies
5. Identifica zonas de interés

### Caso 3: Configuración de Simulación

1. Ve a **📊 Simulaciones**
2. Ajusta los parámetros en el sidebar:
   - Profundidad del reservorio
   - Presión de inyección
   - Saturación de CO₂
   - Escala temporal
3. Observa el viewer CO₂ con la configuración
4. Exporta o documenta los resultados

### Caso 4: Análisis de Facies

1. Ve a **🔬 Propiedades**
2. Selecciona `facies` de la lista
3. Visualiza la distribución de Shalty (marrón) y Sand (dorado)
4. Lee las estadísticas en la caption
5. Ajusta los cortes para encontrar zonas específicas

## 📝 Archivos de Datos Requeridos

### Estructura de Directorios

```
pyvista/
├── data/
│   └── geosx/
│       ├── permeability.npy
│       ├── porosity.npy
│       └── facies.npy
└── timesteps_export/
    ├── YMFS_ts_0000.GRDECL
    ├── YMFS_ts_0001.GRDECL
    └── ...
```

### Formato de Datos

**Archivos .npy**:
- Arrays NumPy 3D o 4D
- Shape: (nz, ny, nx) o (nt, nz, ny, nx)
- Dtype: float32 o float64

**Archivos GRDECL**:
- Formato Eclipse estándar
- Propiedades: YMFS, PRESSURE, SGAS, SOIL, SWAT
- Un archivo por timestep

## 🐛 Resolución de Problemas

### Problema: "No se encontraron archivos .npy"

**Solución**:
1. Verifica que los archivos estén en `data/geosx/`
2. Nombres correctos: `permeability.npy`, `porosity.npy`, `facies.npy`
3. Formato NumPy válido

### Problema: "No se encontraron archivos YMFS"

**Solución**:
1. Verifica que los archivos estén en `timesteps_export/`
2. Patrón de nombre: `YMFS_ts_####.GRDECL`
3. Al menos un archivo debe existir

### Problema: Viewer CO₂ no carga

**Solución**:
1. Espera a que se complete el preprocesamiento (primera vez)
2. Verifica el cache en `outputs/cache/`
3. Prueba con un umbral diferente

### Problema: Gráficos 3D no se ven

**Solución**:
1. Refresca la página del navegador
2. Verifica la consola de JavaScript (F12)
3. Asegúrate de que Plotly está cargando correctamente

## 💡 Consejos y Trucos

1. **Performance**: Usa umbrales más altos (>0.4) para cargas más rápidas
2. **Visualización**: Ajusta Z Scale en el viewer CO₂ para mejor perspectiva
3. **Exploración**: Usa el modo paralelo para análisis rápido de correlaciones
4. **Comparación**: Toma screenshots de diferentes timesteps para comparar
5. **Exportación**: Los gráficos Plotly tienen botón de descarga integrado

## 🆘 Soporte

Para más información o reportar issues:
- Revisa la documentación en `GEOVIZ_DESIGN.md`
- Verifica la estructura del proyecto en `STRUCTURE.md`
- Consulta las instrucciones de Streamlit en `INSTRUCCIONES_STREAMLIT.md`

---

**¡Feliz exploración geológica! 🌍**

