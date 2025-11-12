# Estructura del Proyecto

## Archivos Principales
- `app.py` - Aplicación Streamlit principal (para despliegue)
- `requirements.txt` - Dependencias Python
- `README.md` - Documentación del proyecto
- `INSTRUCCIONES_STREAMLIT.md` - Instrucciones de uso

## Carpetas

### `scripts/`
Scripts de utilidad para exportar y procesar datos:
- `export_ymfs.py` - Exporta YMFS desde ResInsight
- `export_timesteps_resinsight.py` - Exporta múltiples propiedades
- `load_grdecl.py` - Carga archivos GRDECL
- `save_vtk.py` - Convierte GRDECL a VTK

### `data/`
Archivos GRDECL de entrada (grid y propiedades estáticas):
- `GRID.GRDECL` - Definición de la grilla
- `PORO.GRDECL` - Porosidad
- `PERMX.GRDECL`, `PERMY.GRDECL`, `PERMZ.GRDECL` - Permeabilidades
- `NTG.GRDECL`, `BORDNUM.GRDECL`, `FAULTS.GRDECL`, `OPERNUM.GRDECL` - Otras propiedades

### `timesteps_export/`
Datos dinámicos exportados desde ResInsight (necesarios para `app.py`):
- `YMFS_ts_*.GRDECL` - Fracción molar de CO2 por timestep
- `SOIL_ts_*.GRDECL`, `SWAT_ts_*.GRDECL`, `SGAS_ts_*.GRDECL` - Otras propiedades dinámicas
- `PRESSURE_ts_*.GRDECL` - Presión por timestep

### `outputs/`
Resultados generados (visualizaciones HTML y archivos VTK):
- `outputs/html/` - Visualizaciones HTML estáticas
- `outputs/vtk/` - Archivos VTK consolidados

## Para Despliegue en Streamlit Cloud

Los archivos necesarios en la raíz:
- `app.py` ✓
- `requirements.txt` ✓
- `timesteps_export/` ✓ (debe estar en la raíz para que app.py lo encuentre)
