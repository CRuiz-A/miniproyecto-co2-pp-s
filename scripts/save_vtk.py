"""
Script para cargar archivos GRDECL y guardarlos en formato VTK.

Esto permite visualizar los datos en ParaView u otros visualizadores VTK
sin problemas de OpenGL/display.
"""

import os
import numpy as np

# Configurar para solucionar problema de OpenGL
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['GALLIUM_DRIVER'] = 'llvmpipe'
os.environ['LP_NUM_THREADS'] = '1'
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
os.environ['DISPLAY'] = ''

try:
    import pyvista as pv
    pv.OFF_SCREEN = True
except ImportError:
    print("Error: PyVista no está instalado")
    exit(1)


def read_grdecl_property(filename):
    """Lee una propiedad desde un archivo GRDECL."""
    values = []
    property_name_found = False
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            if not line or line.startswith('--'):
                continue
            
            if line == '/':
                break
            
            if not property_name_found:
                if not any(char.isdigit() for char in line):
                    property_name_found = True
                    continue
            
            if property_name_found:
                parts = line.split()
                for part in parts:
                    try:
                        val = float(part)
                        values.append(val)
                    except ValueError:
                        continue
                            
    return np.array(values)


def main():
    """Función principal."""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    grid_file = os.path.join(base_dir, 'GRID.GRDECL')
    
    print("="*60)
    print("Cargando y guardando archivos GRDECL como VTK")
    print("="*60)
    
    # Cargar grilla
    print(f"\nCargando grilla desde: {grid_file}")
    try:
        grid = pv.read_grdecl(grid_file)
        print(f"✓ Grilla cargada: {grid.n_cells} celdas")
    except Exception as e:
        print(f"✗ Error al cargar grilla: {e}")
        print("\nUsa 'python load_grdecl.py' para cargar datos sin visualización")
        return
    
    # Cargar propiedades
    property_files = {
        'PORO': 'PORO.GRDECL',
        'PERMX': 'PERMX.GRDECL',
        'PERMY': 'PERMY.GRDECL',
        'PERMZ': 'PERMZ.GRDECL',
        'NTG': 'NTG.GRDECL',
        'BORDNUM': 'BORDNUM.GRDECL',
        'OPERNUM': 'OPERNUM.GRDECL',
    }
    
    print("\nCargando propiedades...")
    for prop_name, filename in property_files.items():
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            try:
                prop_values = read_grdecl_property(filepath)
                if len(prop_values) == grid.n_cells:
                    if hasattr(grid, 'cell_data'):
                        grid.cell_data[prop_name] = prop_values
                    else:
                        grid.cell_arrays[prop_name] = prop_values
                    print(f"  ✓ {prop_name}")
                elif len(prop_values) == grid.n_points:
                    if hasattr(grid, 'point_data'):
                        grid.point_data[prop_name] = prop_values
                    else:
                        grid.point_arrays[prop_name] = prop_values
                    print(f"  ✓ {prop_name} (puntos)")
            except Exception as e:
                print(f"  ✗ {prop_name}: {e}")
    
    # Guardar en formato VTK
    output_file = os.path.join(base_dir, 'grid_with_properties.vtk')
    print(f"\nGuardando grilla en: {output_file}")
    try:
        grid.save(output_file)
        print(f"✓ Archivo VTK guardado exitosamente")
        print(f"\nPuedes visualizar este archivo con:")
        print(f"  - ParaView: paraview {output_file}")
        print(f"  - PyVista (con display): grid = pv.read('{output_file}'); grid.plot()")
    except Exception as e:
        print(f"✗ Error al guardar: {e}")


if __name__ == "__main__":
    main()

