"""
Script para cargar archivos GRDECL y mostrar información sin visualización.

Este script carga los datos sin intentar renderizar, útil cuando no hay display gráfico.
"""

import os
import numpy as np

# Configurar para evitar inicialización de OpenGL
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
os.environ['DISPLAY'] = ''

try:
    import pyvista as pv
    # Forzar offscreen
    pv.OFF_SCREEN = True
except ImportError:
    print("Error: PyVista no está instalado")
    exit(1)


def read_grdecl_property(filename):
    """
    Lee una propiedad desde un archivo GRDECL.
    """
    values = []
    property_name_found = False
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith('--'):
                continue
            
            # Detectar el final de los datos
            if line == '/':
                break
            
            # Buscar el nombre de la propiedad
            if not property_name_found:
                if not any(char.isdigit() for char in line):
                    property_name_found = True
                    continue
            
            # Después del nombre, empezar a leer datos numéricos
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
    """Función principal para cargar los archivos GRDECL."""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    grid_file = os.path.join(base_dir, 'GRID.GRDECL')
    
    print("="*60)
    print("Cargando archivos GRDECL")
    print("="*60)
    print(f"\nCargando grilla desde: {grid_file}")
    
    try:
        # Intentar cargar sin inicializar renderer
        # Usar try/except para manejar problemas de OpenGL
        try:
            grid = pv.read_grdecl(grid_file)
        except Exception as e:
            print(f"Error al cargar con read_grdecl: {e}")
            print("\nIntentando método alternativo...")
            # Si falla, al menos mostrar información del archivo
            print("No se pudo cargar la grilla debido a problemas con OpenGL.")
            print("Instala OSMesa para renderizado sin display:")
            print("  sudo apt-get install libosmesa6-dev")
            return None
        
        print(f"✓ Grilla cargada exitosamente")
        print(f"  Tipo: {type(grid)}")
        if hasattr(grid, 'dimensions'):
            print(f"  Dimensiones: {grid.dimensions}")
        print(f"  Número de celdas: {grid.n_cells}")
        print(f"  Número de puntos: {grid.n_points}")
        print(f"  Bounds: {grid.bounds}")
        
    except Exception as e:
        print(f"Error al cargar la grilla: {e}")
        return None
    
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
    
    print("\n" + "="*60)
    print("Cargando propiedades")
    print("="*60)
    
    loaded_properties = {}
    
    for prop_name, filename in property_files.items():
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            try:
                prop_values = read_grdecl_property(filepath)
                print(f"\n{prop_name}:")
                print(f"  Valores cargados: {len(prop_values)}")
                print(f"  Min: {prop_values.min():.6f}")
                print(f"  Max: {prop_values.max():.6f}")
                print(f"  Media: {prop_values.mean():.6f}")
                
                if grid is not None:
                    if len(prop_values) == grid.n_cells:
                        # Usar cell_data en lugar de cell_arrays (PyVista >= 0.32)
                        if hasattr(grid, 'cell_data'):
                            grid.cell_data[prop_name] = prop_values
                        else:
                            grid.cell_arrays[prop_name] = prop_values
                        loaded_properties[prop_name] = prop_values
                        print(f"  ✓ Agregado a celdas")
                    elif len(prop_values) == grid.n_points:
                        # Usar point_data en lugar de point_arrays (PyVista >= 0.32)
                        if hasattr(grid, 'point_data'):
                            grid.point_data[prop_name] = prop_values
                        else:
                            grid.point_arrays[prop_name] = prop_values
                        loaded_properties[prop_name] = prop_values
                        print(f"  ✓ Agregado a puntos")
                    else:
                        print(f"  ⚠ Tamaño no coincide (celdas: {grid.n_cells}, puntos: {grid.n_points})")
                else:
                    loaded_properties[prop_name] = prop_values
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)
    print("Resumen")
    print("="*60)
    print(f"Grilla: {'✓ Cargada' if grid is not None else '✗ No cargada'}")
    print(f"Propiedades cargadas: {len(loaded_properties)}")
    for prop in loaded_properties.keys():
        print(f"  - {prop}")
    
    if grid is not None and loaded_properties:
        print("\nPara visualizar, ejecuta:")
        print("  python visualize_grdecl.py")
        print("\nO instala OSMesa para renderizado sin display:")
        print("  sudo apt-get install libosmesa6-dev")
    
    return grid, loaded_properties


if __name__ == "__main__":
    grid, properties = main()

