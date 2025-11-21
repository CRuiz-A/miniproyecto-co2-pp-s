"""
Script para inspeccionar los archivos VTK de GEOSX y verificar
cuántas capas de profundidad tienen y en qué rango están.
"""

import numpy as np
import pyvista as pv
from pathlib import Path

# Configurar PyVista
import os
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
pv.OFF_SCREEN = True

# Directorio de archivos VTK
vtk_dir = Path("/home/spell/Desktop/pyvista/data/geosx/new_simulation/timesteps_vtk")

# Buscar archivos VTK
vtk_files = sorted(vtk_dir.glob("ymfs_ts_*.vtk"))

if not vtk_files:
    print("❌ No se encontraron archivos VTK")
    exit(1)

print(f"📁 Encontrados {len(vtk_files)} archivos VTK\n")

# Inspeccionar el primer archivo en detalle
first_file = vtk_files[0]
print(f"🔍 Inspeccionando: {first_file.name}\n")

try:
    grid = pv.read(str(first_file))
    
    print(f"Grid Info:")
    print(f"  - Tipo: {type(grid)}")
    print(f"  - Dimensiones: {grid.dimensions if hasattr(grid, 'dimensions') else 'N/A'}")
    print(f"  - Número de puntos: {grid.n_points}")
    print(f"  - Número de celdas: {grid.n_cells}")
    
    # Obtener datos YMFS
    ymfs_data = None
    if hasattr(grid, 'cell_data') and 'YMFS' in grid.cell_data:
        ymfs_data = np.array(grid.cell_data['YMFS'])
        print(f"  - YMFS en cell_data: {len(ymfs_data)} valores")
    elif hasattr(grid, 'cell_arrays') and 'YMFS' in grid.cell_arrays:
        ymfs_data = np.array(grid.cell_arrays['YMFS'])
        print(f"  - YMFS en cell_arrays: {len(ymfs_data)} valores")
    elif hasattr(grid, 'point_data') and 'YMFS' in grid.point_data:
        ymfs_data = np.array(grid.point_data['YMFS'])
        print(f"  - YMFS en point_data: {len(ymfs_data)} valores")
    else:
        print("  - ⚠ No se encontró YMFS en el grid")
        print(f"  - Arrays disponibles en cell_data: {list(grid.cell_data.keys()) if hasattr(grid, 'cell_data') else 'N/A'}")
        print(f"  - Arrays disponibles en point_data: {list(grid.point_data.keys()) if hasattr(grid, 'point_data') else 'N/A'}")
    
    if ymfs_data is not None:
        print(f"\n📊 Estadísticas YMFS:")
        print(f"  - Min: {ymfs_data.min():.6f}")
        print(f"  - Max: {ymfs_data.max():.6f}")
        print(f"  - Media: {ymfs_data.mean():.6f}")
        print(f"  - Valores > 0: {np.sum(ymfs_data > 0)}")
        print(f"  - Valores > 0.1: {np.sum(ymfs_data > 0.1)}")
        
        # Obtener coordenadas de las celdas
        if hasattr(grid, 'cell_centers'):
            centers = grid.cell_centers()
            z_coords = centers.points[:, 2]  # Coordenada Z (depth)
        else:
            # Obtener desde los puntos del grid
            z_coords = grid.points[:, 2]
            # Si son puntos, necesitamos calcular centros de celdas
            if len(z_coords) == grid.n_points:
                # Para un grid estructurado, los puntos están en orden
                # Necesitamos calcular los centros
                print("\n  ⚠ Calculando centros de celdas desde puntos...")
                # Esto es aproximado, mejor usar cell_centers si está disponible
                z_coords = z_coords  # Usar directamente por ahora
        
        print(f"\n📍 Coordenadas Z (Depth):")
        print(f"  - Min Z: {z_coords.min():.2f} m")
        print(f"  - Max Z: {z_coords.max():.2f} m")
        print(f"  - Rango Z: {z_coords.max() - z_coords.min():.2f} m")
        
        # Analizar distribución por capas
        if hasattr(grid, 'dimensions') and len(grid.dimensions) == 3:
            nx, ny, nz = grid.dimensions[0] - 1, grid.dimensions[1] - 1, grid.dimensions[2] - 1
            print(f"\n📐 Dimensiones del grid (celdas):")
            print(f"  - nx (X): {nx}")
            print(f"  - ny (Y): {ny}")
            print(f"  - nz (Z): {nz}")
            print(f"  - Total esperado: {nx * ny * nz}")
            print(f"  - Total real: {len(ymfs_data)}")
            
            # Intentar reorganizar los datos y ver distribución por capa
            if len(ymfs_data) == nx * ny * nz:
                print(f"\n🔬 Analizando distribución por capas Z:")
                
                # Probar diferentes órdenes
                for order_name, order in [('C (row-major)', 'C'), ('F (column-major)', 'F')]:
                    try:
                        data_3d = ymfs_data.reshape((nx, ny, nz), order=order)
                        cells_per_layer = []
                        for k in range(nz):
                            layer_data = data_3d[:, :, k]
                            active_cells = np.sum(layer_data > 0.1)
                            cells_per_layer.append(active_cells)
                        
                        layers_with_data = sum(1 for count in cells_per_layer if count > 0)
                        print(f"\n  Orden {order_name}:")
                        print(f"    - Capas con datos (>0.1): {layers_with_data}/{nz}")
                        if layers_with_data > 0:
                            print(f"    - Primera capa con datos: capa {next(i for i, c in enumerate(cells_per_layer) if c > 0)}")
                            print(f"    - Última capa con datos: capa {next(i for i in range(nz-1, -1, -1) if cells_per_layer[i] > 0)}")
                            print(f"    - Distribución: {[c for c in cells_per_layer if c > 0][:5]}... (primeras 5 capas con datos)")
                    except Exception as e:
                        print(f"    - Error con orden {order_name}: {e}")
        
        # Analizar valores únicos de Z para ver cuántas capas reales hay
        unique_z = np.unique(z_coords)
        print(f"\n📊 Análisis de profundidades únicas:")
        print(f"  - Valores únicos de Z: {len(unique_z)}")
        if len(unique_z) <= 30:
            print(f"  - Valores: {unique_z}")
        else:
            print(f"  - Primeros 10: {unique_z[:10]}")
            print(f"  - Últimos 10: {unique_z[-10:]}")
        
        # Verificar si hay datos en diferentes rangos de Z
        if len(unique_z) > 1:
            z_min, z_max = unique_z.min(), unique_z.max()
            z_range = z_max - z_min
            z_step = z_range / (len(unique_z) - 1) if len(unique_z) > 1 else 0
            print(f"\n📏 Rango de profundidad:")
            print(f"  - Z mínimo: {z_min:.2f} m")
            print(f"  - Z máximo: {z_max:.2f} m")
            print(f"  - Espesor total: {z_range:.2f} m")
            print(f"  - Paso promedio: {z_step:.2f} m")
            print(f"  - Número de niveles: {len(unique_z)}")
            
            # Contar celdas activas por nivel de Z
            if len(z_coords) == len(ymfs_data):
                z_levels = {}
                for z_val, ymfs_val in zip(z_coords, ymfs_data):
                    z_rounded = round(z_val, 1)  # Redondear a 0.1 m
                    if z_rounded not in z_levels:
                        z_levels[z_rounded] = {'total': 0, 'active': 0}
                    z_levels[z_rounded]['total'] += 1
                    if ymfs_val > 0.1:
                        z_levels[z_rounded]['active'] += 1
                
                print(f"\n📈 Celdas por nivel Z (redondeado a 0.1m):")
                sorted_levels = sorted(z_levels.keys())
                print(f"  - Total de niveles: {len(sorted_levels)}")
                active_levels = [z for z in sorted_levels if z_levels[z]['active'] > 0]
                print(f"  - Niveles con datos activos (>0.1): {len(active_levels)}")
                if len(active_levels) <= 30:
                    for z in sorted_levels[:10]:
                        info = z_levels[z]
                        print(f"    Z={z:.1f}m: {info['active']}/{info['total']} activas")
                    if len(sorted_levels) > 10:
                        print(f"    ... ({len(sorted_levels) - 10} más)")
    
except Exception as e:
    print(f"❌ Error al leer el archivo: {e}")
    import traceback
    traceback.print_exc()

