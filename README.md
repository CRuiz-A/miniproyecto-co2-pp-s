# 🌍 Proyecto de Visualización Geológica - CO₂ Reservoirs

Este proyecto incluye herramientas avanzadas para la visualización de datos geológicos, con enfoque en el almacenamiento de CO₂ en reservorios. Cuenta con dos interfaces principales:

1. **🎨 GeoViz App (Streamlit)** - Interfaz web moderna e interactiva ⭐ **NUEVO v2.0**
2. **📊 Scripts PyVista/GRDECL** - Herramientas de línea de comandos

---

## 🚀 GeoViz - Aplicación Web (Recomendado)

### Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501` con una interfaz moderna y profesional.

### ✨ Características GeoViz v2.1

- **Tema Oscuro Profesional** con diseño glassmorphism
- **Viewer CO₂ 3D Interactivo** con animación temporal
- **Propiedades Geológicas** (permeabilidad, porosidad, facies)
- **Simulaciones Configurables** con parámetros ajustables
- **Navegación Intuitiva** por diferentes reservorios
- **Métricas en Tiempo Real** con tarjetas interactivas
- **🆕 Datos BUNTER**: Visualización completa del reservorio (450K celdas)
- **🆕 Datos Sleipner**: Acuífero salino pionero (2M celdas, 18 facies)

### 📚 Documentación GeoViz

- **[GEOVIZ_README.md](GEOVIZ_README.md)** - Documentación completa de GeoViz
- **[GEOVIZ_DESIGN.md](GEOVIZ_DESIGN.md)** - Sistema de diseño y componentes
- **[GUIA_USUARIO.md](GUIA_USUARIO.md)** - Manual de usuario paso a paso
- **[RESERVORIOS_DATA.md](RESERVORIOS_DATA.md)** - 🆕 Guía de visualizaciones BUNTER y Sleipner
- **[INSTRUCCIONES_STREAMLIT.md](INSTRUCCIONES_STREAMLIT.md)** - Instrucciones específicas

### 🎯 Casos de Uso GeoViz

| Caso de Uso | Descripción | Acceso Rápido |
|------------|-------------|---------------|
| 📊 Análisis CO₂ | Evolución temporal de la pluma | `Bunter → Viewer CO₂` |
| 🔬 Propiedades | Análisis geológico comparativo | `Propiedades → Modo Paralelo` |
| ⚙️ Simulaciones | Configurar escenarios de inyección | `Simulaciones → Ajustar parámetros` |
| 🗺️ Datos BUNTER | Visualizar reservorio completo | `Bunter → Datos Bunter` |
| 💧 Datos Sleipner | Acuífero con 18 facies | `Sleipner` |

---

## 📊 Scripts PyVista/GRDECL (Línea de Comandos)

Esta sección contiene scripts para trabajar directamente con archivos GRDECL desde la terminal.

## Archivos Disponibles

- `GRID.GRDECL` - Estructura de la grilla (100x100x6 celdas)
- `PORO.GRDECL` - Porosidad
- `PERMX.GRDECL` - Permeabilidad en X
- `PERMY.GRDECL` - Permeabilidad en Y
- `PERMZ.GRDECL` - Permeabilidad en Z
- `NTG.GRDECL` - Net-to-Gross
- `BORDNUM.GRDECL` - Números de borde
- `OPERNUM.GRDECL` - Números de operación
- `FAULTS.GRDECL` - Fallas

## Requisitos

```bash
pip install pyvista numpy
```

## Uso Básico

### Opción 1: Cargar Datos (Sin Visualización)

```bash
python load_grdecl.py
```

Este script:
- Carga la grilla desde `GRID.GRDECL`
- Carga automáticamente todas las propiedades disponibles
- Muestra estadísticas de cada propiedad
- **No requiere display gráfico** - funciona en servidores sin GUI

### Opción 2: Script Simple

```bash
python ejemplo_simple.py
```

Este script carga la grilla y la visualiza directamente (requiere display gráfico).

### Opción 3: Guardar como VTK para Visualización Posterior

```bash
python save_vtk.py
```

Este script:
- Carga la grilla y todas las propiedades
- Guarda todo en un archivo VTK (`grid_with_properties.vtk`)
- **No requiere display gráfico** - solo carga y guarda datos
- El archivo VTK se puede visualizar después con ParaView o PyVista

### Opción 4: Visualizar Archivo VTK con PyVista

```bash
python visualize_vtk.py [propiedad]
```

Ejemplos:
```bash
python visualize_vtk.py          # Visualiza con la primera propiedad
python visualize_vtk.py PORO     # Visualiza porosidad
python visualize_vtk.py PERMX    # Visualiza permeabilidad X
```

Este script:
- Carga el archivo VTK guardado
- Crea visualizaciones interactivas
- **Requiere display gráfico** o OSMesa configurado

**Nota**: Si no tienes display gráfico, puedes usar ParaView:
```bash
paraview grid_with_properties.vtk
```

## Uso Programático

### Leer la Grilla

```python
import pyvista as pv

# Cargar el archivo GRDECL
grid = pv.read_grdecl('GRID.GRDECL')

# Ajustar la interpretación de elevación (opcional)
# grid = pv.read_grdecl('GRID.GRDECL', elevation=False)
```

### Agregar Propiedades

Si tienes arrays de propiedades, puedes agregarlos así:

```python
import numpy as np

# Cargar propiedad desde archivo de texto
prop = np.loadtxt('porosidad.txt')
grid.point_arrays['POROSIDAD'] = prop

# O cargar desde archivo GRDECL usando el script helper
from visualize_grdecl import read_grdecl_property
poro = read_grdecl_property('PORO.GRDECL')
grid.cell_arrays['PORO'] = poro
```

### Visualizar

```python
# Visualización básica
grid.plot()

# Visualizar con propiedad
grid.plot(scalars='PORO', cmap='viridis')

# Visualización interactiva avanzada
plotter = pv.Plotter()
plotter.add_mesh(grid, scalars='PORO', show_edges=False)
plotter.show()
```

## Notas

- PyVista lee directamente los archivos GRDECL sin necesidad de conversión previa a VTK
- Las propiedades se pueden asignar a `point_arrays` (puntos) o `cell_arrays` (celdas)
- El parámetro `elevation` en `read_grdecl` controla si se convierten profundidades a elevaciones (por defecto `True`)

## Alternativas

Si necesitas convertir a VTK/VTU para otros programas:

- **PyGRDECL**: https://github.com/BinWang0213/PyGRDECL
- **meshio**: Para conversión genérica entre formatos

## Resumen de Scripts

| Script | Descripción | Requiere Display |
|--------|-------------|------------------|
| `load_grdecl.py` | Carga datos y muestra estadísticas | ❌ No |
| `save_vtk.py` | Carga y guarda en formato VTK | ❌ No |
| `visualize_vtk.py` | Visualiza archivo VTK | ✅ Sí |
| `visualize_grdecl.py` | Carga y visualiza directamente | ✅ Sí |
| `ejemplo_simple.py` | Ejemplo básico | ✅ Sí |

## Flujo de Trabajo Recomendado

1. **Sin display gráfico**: Usa `load_grdecl.py` o `save_vtk.py`
2. **Con display gráfico**: Usa `visualize_vtk.py` o `visualize_grdecl.py`
3. **Para análisis avanzado**: Usa ParaView con el archivo VTK generado

## Referencias

- [Documentación de PyVista](https://docs.pyvista.org/)
- [ResInsight](https://resinsight.org/)
- [ParaView](https://www.paraview.org/)
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/python/)

---

## 🗂️ Estructura del Proyecto

```
pyvista/
├── app.py                      # ⭐ Aplicación GeoViz Streamlit (PRINCIPAL)
├── requirements.txt            # Dependencias del proyecto
│
├── 📚 Documentación GeoViz
├── GEOVIZ_README.md           # Documentación completa de GeoViz
├── GEOVIZ_DESIGN.md           # Sistema de diseño
├── GUIA_USUARIO.md            # Manual de usuario
├── INSTRUCCIONES_STREAMLIT.md # Instrucciones Streamlit
│
├── 📁 data/                   # Datos de entrada
│   ├── geosx/                 # Propiedades geológicas (.npy)
│   │   ├── permeability.npy
│   │   ├── porosity.npy
│   │   └── facies.npy
│   ├── BUNTER/                # Datos del reservorio Bunter
│   ├── sleipner_data/         # Datos de Sleipner
│   └── *.GRDECL               # Archivos GRDECL estáticos
│
├── 📁 timesteps_export/       # Timesteps de simulación
│   ├── YMFS_ts_*.GRDECL      # CO₂ por timestep
│   ├── PRESSURE_ts_*.GRDECL  # Presión
│   └── SGAS_ts_*.GRDECL      # Saturación de gas
│
├── 📁 outputs/                # Salidas generadas
│   ├── cache/                 # Caché de datos procesados
│   ├── html/                  # Visualizaciones HTML
│   └── vtk/                   # Archivos VTK
│
└── 📁 scripts/                # Scripts de línea de comandos
    ├── load_grdecl.py
    ├── save_vtk.py
    └── visualize_*.py
```

## 🎯 ¿Qué Herramienta Usar?

### Usa **GeoViz App** (Streamlit) si quieres:
✅ Interfaz web moderna e interactiva  
✅ Visualización 3D en tiempo real  
✅ Comparación de múltiples propiedades  
✅ Animaciones temporales de CO₂  
✅ No requiere conocimientos de programación  
✅ Ideal para presentaciones y análisis exploratorio

```bash
streamlit run app.py
```

### Usa **Scripts PyVista** si necesitas:
✅ Automatización de procesos  
✅ Procesamiento batch  
✅ Integración con otros pipelines  
✅ Ejecución en servidores sin GUI  
✅ Conversión de formatos  
✅ Control programático total

```bash
python scripts/load_grdecl.py
```

## 🚀 Getting Started

### Para Usuarios Nuevos (Recomendado)

1. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Inicia GeoViz:**
   ```bash
   streamlit run app.py
   ```

3. **Explora la aplicación:**
   - Ve a `🏠 Inicio` para conocer las funcionalidades
   - Selecciona `🗺️ Bunter` para ver visualizaciones reales
   - Lee la `GUIA_USUARIO.md` para casos de uso detallados

### Para Desarrolladores

1. **Revisa la documentación técnica:**
   - `GEOVIZ_DESIGN.md` - Sistema de diseño y componentes
   - `STRUCTURE.md` - Arquitectura del proyecto
   - `app.py` - Código fuente principal

2. **Ejecuta en modo desarrollo:**
   ```bash
   streamlit run app.py --server.runOnSave true
   ```

3. **Contribuye:**
   - Sigue las guías de estilo en `GEOVIZ_DESIGN.md`
   - Mantén la consistencia visual
   - Documenta nuevas características

## 📊 Datos de Ejemplo

El proyecto incluye datos de ejemplo de:

- **Bunter Sandstone Formation**: Reservorio de gas en el Mar del Norte
- **Simulaciones de CO₂**: 11 timesteps (ts_0000 a ts_0010)
- **Propiedades Geológicas**: Permeabilidad, porosidad, facies

## 🆘 Soporte y Ayuda

| Necesitas... | Ve a... |
|-------------|---------|
| Aprender a usar la app | `GUIA_USUARIO.md` |
| Entender el diseño | `GEOVIZ_DESIGN.md` |
| Documentación completa | `GEOVIZ_README.md` |
| Instrucciones de Streamlit | `INSTRUCCIONES_STREAMLIT.md` |
| Estructura del proyecto | `STRUCTURE.md` |
| Problemas comunes | `GUIA_USUARIO.md` → Resolución de Problemas |

## 🎨 Capturas de Pantalla

### GeoViz Dashboard
- **Tema oscuro profesional** con efecto glassmorphism
- **Navegación intuitiva** en sidebar
- **Visualizaciones 3D interactivas** con Plotly
- **Métricas en tiempo real** con tarjetas animadas

### Características Destacadas
- ✨ Glass cards con backdrop blur
- 📊 Gráficos 3D interactivos
- 🎯 Controles sincronizados
- ⚡ Caché inteligente
- 🎨 Diseño responsive

## 📈 Versiones

### v2.0 (2025-11-21) - GeoViz Launch ⭐
- **Nuevo:** Interfaz GeoViz completamente rediseñada
- **Nuevo:** Sistema de diseño moderno con glassmorphism
- **Nuevo:** Navegación por páginas
- **Nuevo:** Métricas interactivas con tarjetas
- **Nuevo:** Modo paralelo para propiedades
- **Mejorado:** UI/UX completamente renovado
- **Mejorado:** Documentación exhaustiva

### v1.x (Anterior)
- Scripts PyVista/GRDECL
- Viewer CO₂ básico
- Visualización de propiedades

## 🎓 Recursos Adicionales

- **[Streamlit Docs](https://docs.streamlit.io/)** - Documentación oficial de Streamlit
- **[Plotly Docs](https://plotly.com/python/)** - Gráficos 3D interactivos
- **[Material Symbols](https://fonts.google.com/icons)** - Iconografía usada
- **[Space Grotesk Font](https://fonts.google.com/specimen/Space+Grotesk)** - Tipografía

---

<div align="center">

## 🌟 Proyecto GeoViz

**Visualización Moderna de Datos Geológicos para Almacenamiento de CO₂**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)

**[Documentación](GEOVIZ_README.md)** • 
**[Guía de Usuario](GUIA_USUARIO.md)** • 
**[Sistema de Diseño](GEOVIZ_DESIGN.md)**

Desarrollado con ❤️ para la visualización de datos geológicos

</div>
