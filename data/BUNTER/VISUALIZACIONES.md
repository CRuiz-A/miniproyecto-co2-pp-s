# Visualizaciones 3D - Modelo Bunter

Este documento describe cómo crear las visualizaciones 3D interactivas del modelo Bunter usando Plotly.

## 📊 Archivos de Visualización Generados

El script `example_usage.py` genera tres visualizaciones 3D interactivas en formato HTML:

1. **`example_3d_slices.html`** - Visualización de Porosidad
2. **`example_3d_permeability.html`** - Visualización de Permeabilidad
3. **`example_3d_facies.html`** - Visualización de Facies (Saturación)

## 🚀 Cómo Generar las Visualizaciones

### Requisitos

```bash
pip install numpy plotly
```

### Ejecutar el Script

```bash
cd bunter_data
python3 example_usage.py
```

El script generará automáticamente los tres archivos HTML con las visualizaciones 3D.

## 📐 Estructura de las Visualizaciones

Cada visualización 3D muestra **tres slices ortogonales** en el mismo espacio 3D:

### 1. Slice Horizontal (Z)
- **Dirección**: Profundidad (k)
- **Posición**: k = nz/2 (capa central)
- **Orientación**: Vista desde arriba (plano XY)
- **Muestra**: Variación horizontal de la propiedad en la profundidad central

### 2. Slice Vertical Y (j)
- **Dirección**: Norte-Sur (j)
- **Posición**: j = ny/2 (posición central)
- **Orientación**: Corte vertical Norte-Sur (plano XZ)
- **Muestra**: Variación vertical en la dirección Norte-Sur

### 3. Slice Vertical X (i)
- **Dirección**: Este-Oeste (i)
- **Posición**: i = nx/2 (posición central)
- **Orientación**: Corte vertical Este-Oeste (plano YZ)
- **Muestra**: Variación vertical en la dirección Este-Oeste

## 🎨 Características de Cada Visualización

### Porosidad (`example_3d_slices.html`)

- **Colormap**: `Plasma` (púrpura-amarillo)
- **Rango**: 0.0 - 0.35 (fracción)
- **Descripción**: Muestra la distribución de porosidad en el modelo, indicando la capacidad de almacenamiento de CO₂

### Permeabilidad (`example_3d_permeability.html`)

- **Colormap**: `Hot` (rojo-amarillo)
- **Escala**: Logarítmica (log₁₀)
- **Rango**: 0.0065 - 14,987.9 mD
- **Descripción**: Muestra la distribución de permeabilidad horizontal. Se usa escala logarítmica debido al amplio rango de valores

### Facies (`example_3d_facies.html`)

- **Colormap**: Categórico personalizado
  - Verde claro (rgb(141,211,199)): Facies 1
  - Amarillo (rgb(255,255,179)): Transición
  - Morado claro (rgb(190,186,218)): Facies 2
- **Valores**: 1, 2 (regiones SATNUM)
- **Descripción**: Muestra la distribución de facies/regiones de saturación en el modelo

## 💻 Código de Ejemplo

### Cargar y Visualizar Datos

```python
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

# Cargar datos
data = np.load('bunter_data.npz')
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

# Dimensiones
nz, ny, nx = porosity.shape

# Seleccionar slices centrales
k_slice = nz // 2
j_slice = ny // 2
i_slice = nx // 2

# Crear figura
fig = go.Figure()

# Slice horizontal (Z)
x_h = np.arange(nx)
y_h = np.arange(ny)
X_h, Y_h = np.meshgrid(x_h, y_h)
Z_h = np.full_like(X_h, k_slice)

fig.add_trace(
    go.Surface(
        x=X_h, y=Y_h, z=Z_h,
        surfacecolor=porosity[k_slice, :, :],
        colorscale='Plasma',
        opacity=0.9
    )
)

# Slice vertical Y
x_v = np.arange(nx)
z_v = np.arange(nz)
X_v, Z_v = np.meshgrid(x_v, z_v)
Y_v = np.full_like(X_v, j_slice)

fig.add_trace(
    go.Surface(
        x=X_v, y=Y_v, z=Z_v,
        surfacecolor=porosity[:, j_slice, :],
        colorscale='Plasma',
        opacity=0.9
    )
)

# Slice vertical X
y_vx = np.arange(ny)
z_vx = np.arange(nz)
Y_vx, Z_vx = np.meshgrid(y_vx, z_vx)
X_vx = np.full_like(Y_vx, i_slice)

fig.add_trace(
    go.Surface(
        x=X_vx, y=Y_vx, z=Z_vx,
        surfacecolor=porosity[:, :, i_slice],
        colorscale='Plasma',
        opacity=0.9
    )
)

# Configurar layout
fig.update_layout(
    title='Modelo Bunter - Porosidad 3D',
    scene=dict(
        xaxis_title='X (i)',
        yaxis_title='Y (j)',
        zaxis_title='Profundidad (k)',
        camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        aspectmode='data'
    ),
    height=800
)

# Guardar
fig.write_html('visualizacion_3d.html')
```

## 🎯 Interactividad

Las visualizaciones HTML generadas son completamente interactivas:

- **Rotar**: Click y arrastrar para rotar la vista 3D
- **Zoom**: Scroll del mouse o botones de zoom
- **Pan**: Click derecho y arrastrar para mover la vista
- **Información**: Pasar el mouse sobre las superficies para ver valores
- **Reset**: Botón de reset para volver a la vista inicial

## 📝 Notas Técnicas

### Orden de Datos

Los arrays siguen la convención de Eclipse: **(k, j, i)** = (profundidad, Y, X)

- `porosity[k, j, i]` = porosidad en posición (i, j, k)
- `permeability[k, j, i]` = permeabilidad en posición (i, j, k)
- `facies[k, j, i]` = facies en posición (i, j, k)

### Escalas

- **Porosidad**: Escala lineal (0.0 - 0.35)
- **Permeabilidad**: Escala logarítmica (log₁₀) debido al amplio rango
- **Facies**: Escala categórica (valores discretos 1, 2)

### Opacidad

Las superficies se muestran con opacidad 0.9 para permitir ver la intersección de los slices.

## 🔧 Personalización

### Cambiar la Posición de los Slices

Modifica las variables en `example_usage.py`:

```python
k_slice = nz // 2  # Cambiar para slice horizontal diferente
j_slice = ny // 2  # Cambiar para slice vertical Y diferente
i_slice = nx // 2  # Cambiar para slice vertical X diferente
```

### Cambiar Colormaps

- **Porosidad**: `'Plasma'`, `'Viridis'`, `'Inferno'`, `'Magma'`
- **Permeabilidad**: `'Hot'`, `'Jet'`, `'Turbo'`
- **Facies**: Colormap categórico personalizado

### Añadir Más Slices

Para mostrar múltiples slices en la misma dirección, añade más trazas con diferentes posiciones:

```python
# Múltiples slices horizontales
for k in [nz//4, nz//2, 3*nz//4]:
    fig.add_trace(
        go.Surface(
            x=X_h, y=Y_h, z=np.full_like(X_h, k),
            surfacecolor=porosity[k, :, :],
            colorscale='Plasma',
            opacity=0.8
        )
    )
```

## 📚 Referencias

- [Plotly 3D Surface Documentation](https://plotly.com/python/3d-surface-plots/)
- [Plotly Color Scales](https://plotly.com/python/builtin-colorscales/)
- Modelo Eclipse E300 - Bunter CO₂ Storage

---

**Última actualización**: 2024  
**Script principal**: `example_usage.py`

