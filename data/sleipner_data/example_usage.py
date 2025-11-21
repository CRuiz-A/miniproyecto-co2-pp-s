#!/usr/bin/env python3
"""
Ejemplo de uso de los datos Sleipner
Muestra cómo cargar y visualizar los datos del archivo NPZ
"""

import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot

# Cargar datos
print("Cargando datos desde sleipner_data.npz...")
data = np.load('sleipner_data.npz')

# Acceder a cada propiedad
facies = data['facies']
permeability = data['permeability']
porosity = data['porosity']

# Mostrar información
print(f"\nDimensiones:")
print(f"  Facies: {facies.shape}")
print(f"  Permeabilidad: {permeability.shape}")
print(f"  Porosidad: {porosity.shape}")

print(f"\nRangos:")
print(f"  Facies: {facies.min():.0f} - {facies.max():.0f}")
print(f"  Permeabilidad: {permeability.min():.6f} - {permeability.max():.6f} mD")
print(f"  Porosidad: {porosity.min():.6f} - {porosity.max():.6f}")

# Obtener dimensiones
dim_z, dim_y, dim_x = facies.shape

# Crear un ejemplo de visualización: corte de facies en dirección X
print(f"\nCreando ejemplo de visualización...")
slice_x = dim_x // 2  # Corte en el centro
slice_data = facies[:, :, slice_x]

# Crear coordenadas para el plano YZ
y_coords, z_coords = np.meshgrid(np.arange(dim_y), np.arange(dim_z))
x_coords = np.full_like(y_coords, slice_x)

# Crear figura
fig = go.Figure(data=go.Surface(
    x=x_coords,
    y=y_coords,
    z=z_coords,
    surfacecolor=slice_data,
    colorscale='Rainbow',
    colorbar=dict(title="Facies"),
    hovertemplate='X: %{x:.0f}<br>Y: %{y:.0f}<br>Z: %{z:.0f}<br>Facies: %{surfacecolor:.0f}<extra></extra>'
))

fig.update_layout(
    title=f'Corte de Facies - Plano YZ en X={slice_x}',
    scene=dict(
        xaxis_title='X',
        yaxis_title='Y',
        zaxis_title='Z',
        aspectmode='data'
    ),
    width=1000,
    height=800
)

# Guardar
output_file = 'example_facies_slice.html'
plot(fig, filename=output_file, auto_open=False)
print(f"✅ Gráfico de ejemplo guardado en: {output_file}")

print("\n✅ Ejemplo completado exitosamente!")

