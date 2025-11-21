"""
Script para exportar YMFS desde ResInsight y convertirlo a VTK para GEOSX.

Este script:
1. Exporta YMFS desde ResInsight usando la API
2. Convierte los datos GRDECL a formato VTK usando PyVista
3. Guarda archivos VTK por timestep para visualización en Streamlit
"""

import os
import sys
from pathlib import Path

# Configurar para evitar problemas de OpenGL
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
os.environ['DISPLAY'] = ''

try:
    import rips
except ImportError:
    print("Error: ResInsight Python API no está instalada")
    print("Instala ResInsight y asegúrate de que la API esté disponible")
    sys.exit(1)

try:
    import pyvista as pv
    import numpy as np
    pv.OFF_SCREEN = True
except ImportError:
    print("Error: PyVista no está instalado")
    print("Instala con: pip install pyvista")
    sys.exit(1)


def read_grdecl_property(filepath: str) -> np.ndarray:
    """Lee valores de un archivo GRDECL."""
    values = []
    reading = False
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("--"):
                continue
            if "YMFS" in line:
                reading = True
                continue
            if line == "/" or line.startswith("/"):
                break
            if reading:
                parts = line.replace("/", "").split()
                for part in parts:
                    if "*" in part:
                        count_str, value_str = part.split("*")
                        try:
                            values.extend([float(value_str)] * int(count_str))
                        except Exception:
                            continue
                    else:
                        try:
                            values.append(float(part))
                        except Exception:
                            continue
    return np.array(values, dtype=float)


def export_ymfs_to_vtk_geosx(egrid_file: str, output_dir: str = None):
    """
    Exporta YMFS desde ResInsight y lo convierte a VTK.
    
    Parameters
    ----------
    egrid_file : str
        Ruta al archivo .EGRID
    output_dir : str, optional
        Directorio de salida para archivos VTK
    """
    
    if not os.path.exists(egrid_file):
        print(f"Error: No se encontró el archivo {egrid_file}")
        return
    
    # Configurar directorios
    base_dir = Path(egrid_file).parent
    if output_dir is None:
        output_dir = base_dir / "timesteps_vtk"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # También crear directorio para GRDECL temporal
    grdecl_dir = base_dir / "timesteps_export"
    grdecl_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Exportando YMFS desde ResInsight y convirtiendo a VTK - GEOSX")
    print("="*60)
    print(f"\nArchivo EGRID: {egrid_file}")
    print(f"Directorio VTK: {output_dir}")
    print(f"Directorio GRDECL temporal: {grdecl_dir}")
    
    # Paso 1: Conectar a ResInsight
    print("\n[1/3] Conectando a ResInsight...")
    try:
        rips_instance = rips.Instance.find()
        if rips_instance is None:
            print("Error: No se pudo conectar a ResInsight")
            print("Asegúrate de que ResInsight esté ejecutándose")
            return
        print("✓ Conectado a ResInsight")
    except Exception as e:
        print(f"Error al conectar: {e}")
        return
    
    # Paso 2: Cargar caso y exportar YMFS
    print("\n[2/3] Cargando caso y exportando YMFS...")
    try:
        project = rips_instance.project
        cases = project.cases()
        if not cases or len(cases) == 0:
            print("Cargando archivo EGRID...")
            project.load_case(egrid_file)
            import time
            time.sleep(3)
        
        case = project.case(case_id=0)
        if case is None:
            print("Error: No se pudo cargar el caso")
            return
        print(f"✓ Caso cargado")
        
        # Obtener timesteps
        time_steps = case.time_steps()
        print(f"✓ Timesteps encontrados: {len(time_steps)}")
        
        if len(time_steps) == 0:
            print("No hay timesteps disponibles")
            return
        
    except Exception as e:
        print(f"Error al cargar caso: {e}")
        print("\nSugerencia: Abre el archivo EGRID manualmente en ResInsight primero")
        return
    
    # Obtener información del grid desde ResInsight
    print("\n[3/3] Obteniendo información del grid y convirtiendo a VTK...")
    
    # Obtener datos del primer timestep para inferir dimensiones
    try:
        first_values = case.active_cell_property(
            property_type="DYNAMIC_NATIVE",
            property_name="YMFS",
            time_step=0
        )
        if first_values:
            total_cells = len(first_values)
            print(f"✓ Total de celdas: {total_cells}")
        else:
            print("Error: No se pudieron obtener datos del primer timestep")
            return
    except Exception as e:
        print(f"Error al obtener datos del primer timestep: {e}")
        return
    
    # Intentar obtener coordenadas reales del grid desde ResInsight
    cell_centers = None
    nx, ny, nz = None, None, None
    
    try:
        # Intentar obtener centros de celdas desde ResInsight
        print("  Intentando obtener coordenadas del grid desde ResInsight...")
        if hasattr(case, 'cell_centers'):
            cell_centers = case.cell_centers()
            if cell_centers and len(cell_centers) == total_cells:
                print(f"  ✓ Coordenadas obtenidas: {len(cell_centers)} puntos")
        elif hasattr(case, 'active_cell_centers'):
            cell_centers = case.active_cell_centers()
            if cell_centers and len(cell_centers) == total_cells:
                print(f"  ✓ Coordenadas obtenidas: {len(cell_centers)} puntos")
    except Exception as e:
        print(f"  ⚠ No se pudieron obtener coordenadas directamente: {e}")
    
    # Intentar obtener dimensiones del grid desde ResInsight
    try:
        if hasattr(case, 'grid_info'):
            grid_info = case.grid_info()
            if hasattr(grid_info, 'dimensions'):
                nx, ny, nz = grid_info.dimensions
                print(f"  ✓ Dimensiones del grid: {nx} × {ny} × {nz}")
    except Exception as e:
        print(f"  ⚠ No se pudieron obtener dimensiones: {e}")
    
    # Si no se pudieron obtener dimensiones, intentar inferirlas
    if nx is None or ny is None or nz is None:
        # Intentar factorizar el número total de celdas
        # Dimensiones conocidas para GEOSX: 64 × 28 × 25 = 44800
        possible_dims = [
            (64, 28, 25),   # 64 × 28 × 25 = 44800 (CORRECTO según coordenadas reales)
            (70, 64, 10),   # 70 × 64 × 10 = 44800
            (80, 56, 10),   # 80 × 56 × 10 = 44800
            (112, 40, 10),  # 112 × 40 × 10 = 44800
        ]
        
        for test_nx, test_ny, test_nz in possible_dims:
            if test_nx * test_ny * test_nz == total_cells and test_nz > 0:
                nx, ny, nz = test_nx, test_ny, test_nz
                print(f"  ✓ Dimensiones inferidas: {nx} × {ny} × {nz}")
                break
        
        if nx is None:
            # Buscar factores más sistemáticamente
            # Intentar con 25 capas (según coordenadas reales)
            nz = 25
            product_xy = total_cells // nz
            # Buscar factores de product_xy
            for test_ny in range(int(np.sqrt(product_xy)), 0, -1):
                if product_xy % test_ny == 0:
                    test_nx = product_xy // test_ny
                    if test_nx * test_ny * nz == total_cells:
                        nx, ny, nz = test_nx, test_ny, nz
                        print(f"  ✓ Dimensiones calculadas: {nx} × {ny} × {nz}")
                        break
            
            if nx is None:
                # Usar valores por defecto razonables
                nz = 25
                ny = int(np.sqrt(total_cells / nz))
                nx = total_cells // (ny * nz)
                print(f"  ⚠ Usando dimensiones estimadas: {nx} × {ny} × {nz}")
    
    # Crear grid estructurado con proporciones reales
    coords = None
    try:
        grid_base = pv.StructuredGrid()
        
        if cell_centers and len(cell_centers) == total_cells:
            # Usar coordenadas reales del grid
            print("  Usando coordenadas reales del grid desde ResInsight")
            # Convertir a array numpy y verificar formato
            coords = np.array(cell_centers)
            
            # Verificar si es 1D (lista plana) o 2D (lista de tuplas)
            if coords.ndim == 1:
                # Si es 1D, puede ser una lista plana [x1, y1, z1, x2, y2, z2, ...]
                if len(coords) == total_cells * 3:
                    coords = coords.reshape(total_cells, 3)
                else:
                    # Si no, intentar obtener coordenadas de otra manera
                    print("  ⚠ Formato de coordenadas no reconocido, usando proporciones calculadas")
                    coords = None
            elif coords.ndim == 2 and coords.shape[1] == 3:
                # Formato correcto: array 2D con 3 columnas (x, y, z)
                pass
            else:
                print(f"  ⚠ Formato de coordenadas inesperado: shape={coords.shape}, usando proporciones calculadas")
                coords = None
            
            if coords is not None and coords.shape[0] == total_cells:
                x_coords = coords[:, 0]
                y_coords = coords[:, 1]
                z_coords = coords[:, 2]
                
                # Obtener rangos y crear grid estructurado
                x_unique = np.unique(x_coords)
                y_unique = np.unique(y_coords)
                z_unique = np.unique(z_coords)
                
                # Verificar que las dimensiones coincidan
                if len(x_unique) == nx + 1 and len(y_unique) == ny + 1 and len(z_unique) == nz + 1:
                    X, Y, Z = np.meshgrid(x_unique, y_unique, z_unique, indexing='ij')
                    grid_base.points = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
                    grid_base.dimensions = [nx + 1, ny + 1, nz + 1]
                    print(f"  ✓ Grid estructurado creado con coordenadas reales: {grid_base.n_cells} celdas")
                    print(f"    Rango X: [{x_unique.min():.1f}, {x_unique.max():.1f}] m")
                    print(f"    Rango Y: [{y_unique.min():.1f}, {y_unique.max():.1f}] m")
                    print(f"    Rango Z: [{z_unique.min():.1f}, {z_unique.max():.1f}] m")
                else:
                    # Si no coinciden exactamente, usar los valores únicos encontrados
                    print(f"  ⚠ Dimensiones de coordenadas: {len(x_unique)} × {len(y_unique)} × {len(z_unique)}")
                    print(f"  ⚠ Usando coordenadas reales con dimensiones ajustadas")
                    X, Y, Z = np.meshgrid(x_unique, y_unique, z_unique, indexing='ij')
                    grid_base.points = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
                    grid_base.dimensions = [len(x_unique), len(y_unique), len(z_unique)]
                    # Actualizar dimensiones
                    nx, ny, nz = len(x_unique) - 1, len(y_unique) - 1, len(z_unique) - 1
            else:
                # Si no pudimos procesar las coordenadas, usar proporciones calculadas
                print("  ⚠ No se pudieron procesar coordenadas, usando proporciones calculadas")
                coords = None
        if not (cell_centers and len(cell_centers) == total_cells and coords is not None):
            # Si no tenemos coordenadas reales, calcular proporciones basadas en las dimensiones
            print("  Calculando proporciones del grid basadas en dimensiones")
            
            # Calcular proporciones reales (no forzar cubo)
            # Obtener rangos aproximados de las coordenadas si están disponibles
            coords_sample = None
            if cell_centers and len(cell_centers) > 0:
                try:
                    coords_array = np.array(cell_centers[:min(1000, len(cell_centers))])  # Muestra
                    if coords_array.ndim == 1 and len(coords_array) % 3 == 0:
                        coords_sample = coords_array.reshape(-1, 3)
                    elif coords_array.ndim == 2 and coords_array.shape[1] == 3:
                        coords_sample = coords_array
                except:
                    pass
            
            if coords_sample is not None:
                x_min, x_max = coords_sample[:, 0].min(), coords_sample[:, 0].max()
                y_min, y_max = coords_sample[:, 1].min(), coords_sample[:, 1].max()
                z_min, z_max = coords_sample[:, 2].min(), coords_sample[:, 2].max()
                
                # Calcular tamaños de celda promedio
                dx_avg = (x_max - x_min) / nx if nx > 0 else 100.0
                dy_avg = (y_max - y_min) / ny if ny > 0 else 100.0
                dz_avg = (z_max - z_min) / nz if nz > 0 else 20.0
                
                # Crear grid con proporciones reales
                x = np.linspace(x_min, x_max, nx + 1)
                y = np.linspace(y_min, y_max, ny + 1)
                z = np.linspace(z_min, z_max, nz + 1)
            else:
                # Usar coordenadas reales del grid GEOSX
                # Rangos del grid: Este 0-6000, Norte 0-2800, Depth 2640-2860 (verificado desde VTK)
                x_min = 0.0    # Este mínimo
                x_max = 6000.0  # Este máximo
                y_min = 0.0    # Norte mínimo
                y_max = 2800.0  # Norte máximo
                z_min = 2640.0  # Depth mínimo (más somero, verificado desde VTK)
                z_max = 2860.0  # Depth máximo (más profundo, verificado desde VTK)
                
                # Crear grid con coordenadas reales
                x = np.linspace(x_min, x_max, nx + 1)
                y = np.linspace(y_min, y_max, ny + 1)
                z = np.linspace(z_min, z_max, nz + 1)
                
                print(f"  ✓ Usando coordenadas reales del grid GEOSX")
                print(f"    X (Este): [{x_min:.1f}, {x_max:.1f}] m")
                print(f"    Y (Norte): [{y_min:.1f}, {y_max:.1f}] m")
                print(f"    Z (Depth): [{z_min:.1f}, {z_max:.1f}] m")
            
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
            grid_base.points = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
            grid_base.dimensions = [nx + 1, ny + 1, nz + 1]
            aspect_ratio_xy = (x[-1]-x[0]) / (y[-1]-y[0]) if (y[-1]-y[0]) > 0 else 1.0
            aspect_ratio_xz = (x[-1]-x[0]) / (z[-1]-z[0]) if (z[-1]-z[0]) > 0 else 1.0
            print(f"  ✓ Grid estructurado creado: {grid_base.n_cells} celdas")
            print(f"    Dimensiones espaciales: X={x[-1]-x[0]:.1f}m, Y={y[-1]-y[0]:.1f}m, Z={z[-1]-z[0]:.1f}m")
            print(f"    Proporciones: {aspect_ratio_xy:.2f}:1 (XY), {aspect_ratio_xz:.2f}:1 (XZ)")
        
    except Exception as e:
        print(f"Error al crear grid: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Exportar YMFS para cada timestep y convertir a VTK
    print("\n" + "="*60)
    print("Exportando y convirtiendo timesteps")
    print("="*60)
    
    exported_count = 0
    
    for i, ts in enumerate(time_steps):
        print(f"\nTimestep {i}/{len(time_steps)-1}")
        
        try:
            # Exportar YMFS desde ResInsight
            values = case.active_cell_property(
                property_type="DYNAMIC_NATIVE",
                property_name="YMFS",
                time_step=i
            )
            
            if not values or len(values) == 0:
                print(f"  ⚠ No se obtuvieron datos para timestep {i}")
                continue
            
            # Guardar temporalmente en GRDECL
            grdecl_file = grdecl_dir / f"YMFS_ts_{i:04d}.GRDECL"
            with open(grdecl_file, 'w') as f:
                f.write(f"-- Exported from ResInsight - GEOSX Simulation - Timestep {i}\n")
                f.write(f"YMFS\n")
                for j in range(0, len(values), 5):
                    line_vals = values[j:j+5]
                    f.write(" ".join(f"{v:15.6f}" for v in line_vals) + "\n")
                f.write("/\n")
            
            # Crear copia del grid base
            grid_with_ymfs = grid_base.copy()
            
            # Añadir YMFS al grid
            # Asegurar que los valores coincidan con el número de celdas
            if len(values) == grid_base.n_cells:
                if hasattr(grid_with_ymfs, 'cell_data'):
                    grid_with_ymfs.cell_data['YMFS'] = np.array(values, dtype=float)
                else:
                    grid_with_ymfs.cell_arrays['YMFS'] = np.array(values, dtype=float)
            elif len(values) == grid_base.n_points:
                # Si tenemos valores por punto, necesitamos convertirlos a valores por celda
                # Por ahora, usar directamente (puede necesitar interpolación)
                if hasattr(grid_with_ymfs, 'point_data'):
                    grid_with_ymfs.point_data['YMFS'] = np.array(values, dtype=float)
                else:
                    grid_with_ymfs.point_arrays['YMFS'] = np.array(values, dtype=float)
            else:
                # Ajustar tamaño para que coincida
                print(f"  ⚠ Ajustando tamaño: {len(values)} valores vs {grid_base.n_cells} celdas")
                
                if len(values) > grid_base.n_cells:
                    # Truncar si hay más valores que celdas
                    values = values[:grid_base.n_cells]
                elif len(values) < grid_base.n_cells:
                    # Rellenar con ceros si hay menos valores
                    padded = np.zeros(grid_base.n_cells, dtype=float)
                    padded[:len(values)] = values
                    values = padded
                
                if hasattr(grid_with_ymfs, 'cell_data'):
                    grid_with_ymfs.cell_data['YMFS'] = np.array(values, dtype=float)
                else:
                    grid_with_ymfs.cell_arrays['YMFS'] = np.array(values, dtype=float)
            
            # Guardar como VTK
            vtk_file = output_dir / f"ymfs_ts_{i:04d}.vtk"
            grid_with_ymfs.save(str(vtk_file))
            
            print(f"  ✓ YMFS exportado y convertido -> {vtk_file}")
            print(f"    Valores: {len(values)}, Min: {min(values):.6f}, Max: {max(values):.6f}")
            exported_count += 1
                
        except Exception as e:
            print(f"  ✗ Error en timestep {i}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"✓ Exportación completada: {exported_count}/{len(time_steps)} timesteps")
    print("="*60)
    print(f"\nArchivos VTK guardados en: {output_dir}")
    print(f"Archivos GRDECL temporales en: {grdecl_dir}")
    print("\n💡 Los archivos VTK están listos para usar en la aplicación Streamlit")


if __name__ == "__main__":
    # Archivo EGRID del reservorio GEOSX
    egrid_file = "/home/spell/Desktop/pyvista/data/geosx/new_simulation/DEP_GAS.EGRID"
    
    export_ymfs_to_vtk_geosx(egrid_file)

