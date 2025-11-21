"""
Script de depuración para entender cómo se están procesando los datos de GEOSX
"""

import numpy as np
import pyvista as pv
from pathlib import Path
import json

# Configurar PyVista
import os
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
pv.OFF_SCREEN = True

# Cargar un archivo VTK
vtk_file = Path("/home/spell/Desktop/pyvista/data/geosx/new_simulation/timesteps_vtk/ymfs_ts_0010.vtk")
grid = pv.read(str(vtk_file))

# Obtener datos
ymfs_data = np.array(grid.cell_data['YMFS'])
centers = grid.cell_centers()
z_coords = centers.points[:, 2]

print("="*60)
print("ANÁLISIS DETALLADO DE DATOS GEOSX")
print("="*60)

print(f"\n1. Información del Grid:")
print(f"   - Dimensiones: {grid.dimensions}")
print(f"   - Número de celdas: {grid.n_cells}")
print(f"   - Número de puntos: {grid.n_points}")

print(f"\n2. Datos YMFS:")
print(f"   - Total valores: {len(ymfs_data)}")
print(f"   - Min: {ymfs_data.min():.6f}, Max: {ymfs_data.max():.6f}")
print(f"   - Valores > 0.1: {np.sum(ymfs_data > 0.1)}")

print(f"\n3. Coordenadas Z:")
print(f"   - Min Z: {z_coords.min():.2f} m")
print(f"   - Max Z: {z_coords.max():.2f} m")
print(f"   - Valores únicos de Z: {len(np.unique(z_coords))}")
print(f"   - Valores únicos: {sorted(np.unique(z_coords))}")

# Dimensiones del grid
nx, ny, nz = 64, 28, 25

print(f"\n4. Dimensiones esperadas:")
print(f"   - nx={nx}, ny={ny}, nz={nz}")
print(f"   - Total esperado: {nx * ny * nz}")

# Probar diferentes órdenes de reorganización
print(f"\n5. Probando diferentes órdenes de reorganización:")

for order_name, order in [('C (row-major)', 'C'), ('F (column-major)', 'F')]:
    try:
        data_3d = ymfs_data.reshape((nx, ny, nz), order=order)
        
        # Analizar distribución por capa
        layers_info = []
        for k in range(nz):
            layer_data = data_3d[:, :, k]
            active = np.sum(layer_data > 0.1)
            z_vals = []
            for j in range(ny):
                for i in range(nx):
                    idx = i + j * nx + k * nx * ny
                    if idx < len(z_coords):
                        z_vals.append(z_coords[idx])
            
            if len(z_vals) > 0:
                z_min = min(z_vals)
                z_max = max(z_vals)
                z_avg = np.mean(z_vals)
                layers_info.append({
                    'k': k,
                    'active': active,
                    'z_min': z_min,
                    'z_max': z_max,
                    'z_avg': z_avg
                })
        
        print(f"\n   Orden {order_name}:")
        print(f"     - Capas con datos: {sum(1 for li in layers_info if li['active'] > 0)}/{nz}")
        if layers_info:
            print(f"     - Rango Z total: {min(li['z_min'] for li in layers_info):.1f} - {max(li['z_max'] for li in layers_info):.1f} m")
            print(f"     - Primeras 5 capas:")
            for li in layers_info[:5]:
                print(f"       Capa {li['k']}: Z={li['z_avg']:.1f}m, activas={li['active']}")
            if len(layers_info) > 5:
                print(f"       ...")
                print(f"     - Últimas 5 capas:")
                for li in layers_info[-5:]:
                    print(f"       Capa {li['k']}: Z={li['z_avg']:.1f}m, activas={li['active']}")
    except Exception as e:
        print(f"     - Error: {e}")

# Verificar cómo PyVista organiza los datos
print(f"\n6. Verificando orden de PyVista:")
# Los datos de cell_data en PyVista StructuredGrid están en el orden
# en que se crearon las celdas, que para un grid estructurado es:
# k (más rápido), j, i para orden C
# o i, j, k para orden F dependiendo de cómo se creó

# Probar accediendo directamente a los centros de celdas
print(f"   - Primeras 10 coordenadas Z de celdas:")
for i in range(min(10, len(z_coords))):
    idx = i
    print(f"     Celda {idx}: Z={z_coords[idx]:.1f}m, YMFS={ymfs_data[idx]:.6f}")

print(f"\n   - Últimas 10 coordenadas Z de celdas:")
for i in range(max(0, len(z_coords)-10), len(z_coords)):
    idx = i
    print(f"     Celda {idx}: Z={z_coords[idx]:.1f}m, YMFS={ymfs_data[idx]:.6f}")

# Verificar si hay un patrón en el orden
print(f"\n7. Verificando patrón de orden:")
# Para un grid estructurado, las celdas deberían estar ordenadas de manera predecible
# Si el orden es correcto, deberíamos ver patrones en las coordenadas Z

# Agrupar por coordenada Z
z_groups = {}
for idx in range(len(z_coords)):
    z = round(z_coords[idx], 1)
    if z not in z_groups:
        z_groups[z] = []
    z_groups[z].append({
        'idx': idx,
        'ymfs': ymfs_data[idx],
        'z': z_coords[idx]
    })

print(f"   - Grupos por Z (redondeado a 0.1m):")
for z in sorted(z_groups.keys())[:10]:
    group = z_groups[z]
    active = sum(1 for g in group if g['ymfs'] > 0.1)
    print(f"     Z={z:.1f}m: {len(group)} celdas, {active} activas")
    if len(group) > 0:
        print(f"       Índices ejemplo: {[g['idx'] for g in group[:5]]}")

