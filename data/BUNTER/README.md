# Bunter CO₂ Storage Model Dataset

Este dataset contiene datos del modelo geológico Bunter para almacenamiento de CO₂, extraídos de un modelo de simulación Eclipse E300.

## 📊 Estructura de Datos

### Archivo NPZ: `bunter_data.npz`

Archivo comprimido NumPy que contiene tres arrays 3D:

- **`facies`**: Datos de facies/regiones de roca (shape: 65, 63, 110)
  - Tipo: `int32`
  - Valores: 1, 2 (regiones SATNUM de Eclipse)
  - Orden: (k, j, i) - profundidad, Y, X

- **`permeability`**: Permeabilidad horizontal en mD (shape: 65, 63, 110)
  - Tipo: `float32`
  - Unidad: mD (millidarcies)
  - Rango: 0.0065 - 14,987.9 mD
  - Media: 179.3 mD
  - Mediana: 9.6 mD

- **`porosity`**: Porosidad como fracción (shape: 65, 63, 110)
  - Tipo: `float32`
  - Unidad: fracción (0-1)
  - Rango: 1e-5 - 0.35
  - Media: 0.137
  - Mediana: 0.15

### Dimensiones del Grid

- **NX**: 110 (dirección X/Este-Oeste)
- **NY**: 63 (dirección Y/Norte-Sur)
- **NZ**: 65 (dirección Z/Profundidad)
- **Total de celdas**: 450,450

**Nota**: El orden de los arrays es (k, j, i) siguiendo la convención de Eclipse: profundidad, Y, X.

## 💻 Cómo Cargar los Datos

### Método 1: NumPy (Recomendado)

```python
import numpy as np

# Cargar el archivo NPZ
data = np.load('bunter_data.npz')

# Acceder a cada propiedad
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

print(f"Facies shape: {facies.shape}")
print(f"Permeability shape: {permeability.shape}")
print(f"Porosity shape: {porosity.shape}")

# Acceder a un slice específico (por ejemplo, capa k=8)
layer_k = 7  # Índice 0-based
facies_slice = facies[layer_k, :, :]
permeability_slice = permeability[layer_k, :, :]
porosity_slice = porosity[layer_k, :, :]
```

### Método 2: Con Metadatos

```python
import numpy as np
import json

# Cargar datos
data = np.load('bunter_data.npz')
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

# Cargar metadatos
with open('metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Grid dimensions: {metadata['dimensions']['nx']} × {metadata['dimensions']['ny']} × {metadata['dimensions']['nz']}")
print(f"Permeability range: {metadata['properties']['permeability']['min']:.2f} - {metadata['properties']['permeability']['max']:.2f} mD")
print(f"Porosity range: {metadata['properties']['porosity']['min']:.4f} - {metadata['properties']['porosity']['max']:.4f}")
```

## 📈 Ejemplos de Código

### Visualización de un Slice 2D

```python
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos
data = np.load('bunter_data.npz')
facies = data['facies']
porosity = data['porosity']

# Seleccionar capa superior (k=8, índice 7)
layer_idx = 7
facies_slice = facies[layer_idx, :, :]
porosity_slice = porosity[layer_idx, :, :]

# Crear figura con subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot de facies
im1 = axes[0].imshow(facies_slice, cmap='Set3', origin='lower', aspect='auto')
axes[0].set_title('Facies (Capa k=8)')
axes[0].set_xlabel('X (i)')
axes[0].set_ylabel('Y (j)')
plt.colorbar(im1, ax=axes[0], label='Facies ID')

# Plot de porosidad
im2 = axes[1].imshow(porosity_slice, cmap='plasma', origin='lower', aspect='auto')
axes[1].set_title('Porosidad (Capa k=8)')
axes[1].set_xlabel('X (i)')
axes[1].set_ylabel('Y (j)')
plt.colorbar(im2, ax=axes[1], label='Porosidad (fracción)')

plt.tight_layout()
plt.savefig('bunter_slice_example.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Análisis Estadístico por Facies

```python
import numpy as np

# Cargar datos
data = np.load('bunter_data.npz')
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

# Obtener valores únicos de facies
unique_facies = np.unique(facies)
print(f"Facies únicas: {unique_facies}")

# Calcular estadísticas por facies
for facies_id in unique_facies:
    mask = facies == facies_id
    perm_values = permeability[mask]
    poro_values = porosity[mask]
    
    # Filtrar valores válidos
    perm_valid = perm_values[perm_values > 0]
    poro_valid = poro_values[~np.isnan(poro_values)]
    
    print(f"\nFacies {facies_id}:")
    print(f"  Celdas: {np.sum(mask):,}")
    if len(perm_valid) > 0:
        print(f"  Permeabilidad: μ={perm_valid.mean():.2f} mD, mediana={np.median(perm_valid):.2f} mD")
    if len(poro_valid) > 0:
        print(f"  Porosidad: μ={poro_valid.mean():.4f}, mediana={np.median(poro_valid):.4f}")
```

### Extraer Perfil Vertical

```python
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos
data = np.load('bunter_data.npz')
porosity = data['porosity']
permeability = data['permeability']

# Seleccionar ubicación (i, j)
i_pos, j_pos = 79, 25  # Ubicación de pozo I1

# Extraer perfil vertical
poro_profile = porosity[:, j_pos, i_pos]
perm_profile = permeability[:, j_pos, i_pos]

# Crear gráfico
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))

# Perfil de porosidad
ax1.plot(poro_profile, range(len(poro_profile)), 'b-', linewidth=2)
ax1.set_xlabel('Porosidad (fracción)')
ax1.set_ylabel('Profundidad (k)')
ax1.set_title('Perfil Vertical de Porosidad')
ax1.invert_yaxis()
ax1.grid(True, alpha=0.3)

# Perfil de permeabilidad
ax2.semilogx(perm_profile, range(len(perm_profile)), 'r-', linewidth=2)
ax2.set_xlabel('Permeabilidad (mD) - escala log')
ax2.set_ylabel('Profundidad (k)')
ax2.set_title('Perfil Vertical de Permeabilidad')
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bunter_vertical_profile.png', dpi=150, bbox_inches='tight')
plt.show()
```

## 🗺️ Mapeo de Facies a Tipos de Roca

Según los metadatos del modelo Eclipse:

- **Facies 1**: Bunter Sandstone (reservorio principal)
- **Facies 2**: Zona de reservorio secundaria
- **Facies 3**: Zona de baja permeabilidad
- **Facies 4**: Sello/Caprock
- **Facies 5**: Celdas inactivas

**Nota**: En este dataset, solo se encuentran las facies 1 y 2, que corresponden a las regiones SATNUM activas del modelo.

## 📝 Notas sobre Visualización

### Escalas Recomendadas

- **Porosidad**: Usar colormap `plasma` o `viridis` para valores 0-0.35
- **Permeabilidad**: Usar escala logarítmica debido al amplio rango (0.0065 - 14,987 mD)
  - Colormap: `hot` o `inferno` para escala log
- **Facies**: Usar colormap categórico como `Set3`, `tab10`, o `Pastel1`

### Visualización 3D

Para visualizaciones 3D, se recomienda usar:
- **PyVista**: Para visualizaciones interactivas
- **matplotlib 3D**: Para visualizaciones estáticas
- **Mayavi**: Para visualizaciones avanzadas

Ejemplo con PyVista:
```python
import numpy as np
import pyvista as pv

data = np.load('bunter_data.npz')
porosity = data['porosity']

# Crear grid estructurado
grid = pv.StructuredGrid()
grid.dimensions = porosity.shape[::-1]  # Invertir para (x, y, z)
grid.point_data['porosity'] = porosity.flatten(order='F')

# Visualizar
grid.plot(show_edges=False, cmap='plasma')
```

## 📦 Dependencias

Para usar este dataset, necesitarás:

```bash
pip install numpy matplotlib
```

Para visualizaciones 3D adicionales:
```bash
pip install pyvista  # Visualización 3D interactiva
pip install plotly   # Visualizaciones web interactivas
```

## 📚 Referencias

- **Modelo Original**: Eclipse E300 simulation model
- **Formación**: Bunter Sandstone (almacenamiento geológico de CO₂)
- **Grid**: 110 × 63 × 65 celdas
- **Propiedades**: Porosidad (PORO), Permeabilidad (PERMX), Regiones (SATNUM)

## 🔗 Archivos Relacionados

- `bunter_data.npz`: Archivo comprimido con los datos
- `metadata.json`: Metadatos detallados sobre el dataset
- `example_usage.py`: Script para generar visualizaciones 3D
- `VISUALIZACIONES.md`: Documentación completa sobre las visualizaciones 3D

### Visualizaciones 3D Generadas

Ejecuta `python3 example_usage.py` para generar:

- `example_3d_slices.html`: Visualización 3D de Porosidad
- `example_3d_permeability.html`: Visualización 3D de Permeabilidad
- `example_3d_facies.html`: Visualización 3D de Facies (Saturación)

Ver `VISUALIZACIONES.md` para más detalles sobre cómo crear y personalizar las visualizaciones.

## 📄 Licencia

Uso educativo / investigación

---

**Creado por**: Script automatizado de conversión Eclipse → NPZ  
**Fecha**: 2024

