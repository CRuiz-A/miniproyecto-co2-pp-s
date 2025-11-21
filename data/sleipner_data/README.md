# Datos Sleipner Reference Model 2019

Este directorio contiene los datos extraídos del modelo de referencia Sleipner 2019, procesados y listos para generar visualizaciones 3D.

## Archivos incluidos

- **`sleipner_data.npz`**: Archivo comprimido NumPy con todos los datos 3D
- **`metadata.json`**: Metadatos sobre las dimensiones y rangos de los datos
- **`README.md`**: Este archivo con documentación

## Estructura de datos

### Dimensiones

Los arrays 3D tienen la siguiente estructura:
- **Shape**: `(z, y, x) = (64, 118, 263)`
- **X (dirección I)**: 263 celdas
- **Y (dirección J)**: 118 celdas  
- **Z (dirección K)**: 64 celdas
- **Total de celdas**: 1,986,176

### Propiedades incluidas

1. **`facies`**: Datos de facies (REGIONS)
   - Rango: 1 - 18
   - 18 tipos de facies diferentes
   - Valores enteros representando diferentes tipos de roca

2. **`permeability`**: Permeabilidad (PERMX)
   - Rango: 0.001 - 2000.0 mD
   - Unidades: milidarcies (mD)
   - Escala logarítmica recomendada para visualización

3. **`porosity`**: Porosidad (PORO)
   - Rango: 0.34 - 0.36
   - Valores adimensionales (fracción)
   - Escala lineal

## Cómo cargar los datos

### Python

```python
import numpy as np

# Cargar todos los datos
data = np.load('sleipner_data.npz')

# Acceder a cada propiedad
facies = data['facies']          # Shape: (64, 118, 263)
permeability = data['permeability']  # Shape: (64, 118, 263)
porosity = data['porosity']       # Shape: (64, 118, 263)

# Verificar dimensiones
print(f"Facies shape: {facies.shape}")
print(f"Permeability range: {permeability.min():.6f} - {permeability.max():.6f} mD")
print(f"Porosity range: {porosity.min():.6f} - {porosity.max():.6f}")
```

### Ejemplo completo de uso

```python
import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot

# Cargar datos
data = np.load('sleipner_data.npz')
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

# Obtener dimensiones
dim_z, dim_y, dim_x = facies.shape

# Crear un corte en el centro (dirección X)
slice_x = dim_x // 2
slice_data = facies[:, :, slice_x]

# Crear visualización
y_coords, z_coords = np.meshgrid(np.arange(dim_y), np.arange(dim_z))
x_coords = np.full_like(y_coords, slice_x)

fig = go.Figure(data=go.Surface(
    x=x_coords,
    y=y_coords,
    z=z_coords,
    surfacecolor=slice_data,
    colorscale='Rainbow'
))

fig.update_layout(title='Corte de Facies')
plot(fig, filename='facies_slice.html')
```

## Mapeo de Facies a Tipos de Roca

| Facies | Tipo de Roca |
|--------|--------------|
| 1 | Arenisca Utsira L1 |
| 2 | Intrashale L1-L2 |
| 3 | Arenisca Utsira L2 |
| 4 | Intrashale L2-L3 |
| 5 | Arenisca Utsira L3 |
| 6 | Intrashale L3-L4 |
| 7 | Arenisca Utsira L4 |
| 8 | Intrashale L4-L5 |
| 9 | Arenisca Utsira L5 |
| 10 | Intrashale L5-L6 |
| 11 | Arenisca Utsira L6 |
| 12 | Intrashale L6-L7 |
| 13 | Arenisca Utsira L7 |
| 14 | Intrashale L7-L8 |
| 15 | Arenisca Utsira L8 |
| 16 | Thick Shale Unit |
| 17 | Arenisca Sand Wedge L9 |
| 18 | Caprock (Lutita) |

## Generación de gráficos

### Gráfico de Facies con cortes 3D

```python
# Ver script: visualize_facies_slices.py
# Genera: facies_slices_3d.html
# Muestra: 1 corte en cada dirección (X, Y, Z)
```

### Gráfico de Permeabilidad con cortes 3D

```python
# Ver script: visualize_permeability_porosity_slices.py
# Genera: permeability_slices_3d.html
# Muestra: 1 corte en cada dirección (X, Y, Z)
# Usa escala logarítmica para mejor visualización
```

### Gráfico de Porosidad con cortes 3D

```python
# Ver script: visualize_permeability_porosity_slices.py
# Genera: porosity_slices_3d.html
# Muestra: 1 corte en cada dirección (X, Y, Z)
```

### Gráfico 3D completo de Facies

```python
# Ver script: visualize_facies_3d.py
# Genera: facies_3d_plot.html
# Muestra: Visualización 3D completa con puntos coloreados por facies
```

## Notas importantes

1. **Sistema de coordenadas**: Los arrays están en formato `(z, y, x)` donde:
   - El primer índice (0-63) corresponde a Z
   - El segundo índice (0-117) corresponde a Y
   - El tercer índice (0-262) corresponde a X

2. **Permeabilidad**: Se recomienda usar escala logarítmica para visualización debido al amplio rango (0.001 - 2000 mD):
   ```python
   permeability_log = np.log10(permeability + 0.001)
   ```

3. **Porosidad**: Los valores están en fracción (0.34 = 34%). Para convertir a porcentaje:
   ```python
   porosity_percent = porosity * 100
   ```

4. **Cortes**: Para crear cortes en diferentes direcciones:
   - **Corte X (plano YZ)**: `data[:, :, x_position]`
   - **Corte Y (plano XZ)**: `data[:, y_position, :]`
   - **Corte Z (plano XY)**: `data[z_position, :, :]`

## Dependencias

Para usar estos datos necesitarás:
- Python 3.x
- NumPy
- Plotly (para visualizaciones 3D)

Instalación:
```bash
pip install numpy plotly
```

## Fuente de datos

- **Modelo**: Sleipner 2019 Benchmark Model
- **Archivo original**: `Sleipner_Reference_Model.grdecl`
- **Formato original**: Eclipse GRDECL
- **Procesado**: Datos extraídos y reorganizados para visualización

## Licencia

Los datos provienen del Sleipner CO2 Reference Dataset bajo la SLEIPNER CO2 REFERENCE DATASET LICENSE.

## Contacto y referencias

Para más información sobre el modelo Sleipner:
- Documentación oficial del modelo Sleipner 2019
- DOI: 10.11582/2020.00004

