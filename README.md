# Visualización de Archivos GRDECL con PyVista

Este proyecto contiene scripts para visualizar archivos GRDECL exportados desde ResInsight utilizando PyVista.

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

# miniproyecto-co2-pp-s
