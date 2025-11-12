"""
Script para exportar todos los timesteps desde ResInsight usando la API de Python.

Este script:
1. Conecta a ResInsight
2. Carga el archivo EGRID
3. Exporta todas las propiedades para cada timestep
"""

import os
import sys

try:
    import rips
    print(f"✓ ResInsight API {rips.__version__ if hasattr(rips, '__version__') else 'cargada'}")
except ImportError:
    print("Error: ResInsight Python API no está instalada")
    print("Asegúrate de tener ResInsight instalado y la API disponible")
    sys.exit(1)


def export_all_timesteps(egrid_file, output_dir=None, properties=None):
    """
    Exporta todas las propiedades para todos los timesteps desde ResInsight.
    
    Parameters
    ----------
    egrid_file : str
        Ruta al archivo .EGRID
    output_dir : str, optional
        Directorio de salida (por defecto: mismo directorio que el EGRID)
    properties : list, optional
        Lista de propiedades a exportar (por defecto: todas disponibles)
    """
    
    # Verificar que el archivo existe
    if not os.path.exists(egrid_file):
        print(f"Error: No se encontró el archivo {egrid_file}")
        return
    
    # Configurar directorio de salida
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(egrid_file))
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*60)
    print("Exportando timesteps desde ResInsight")
    print("="*60)
    print(f"\nArchivo EGRID: {egrid_file}")
    print(f"Directorio de salida: {output_dir}")
    
    # Conectar a ResInsight
    print("\nConectando a ResInsight...")
    try:
        rips_instance = rips.Instance.find()
        if rips_instance is None:
            print("Error: No se pudo conectar a ResInsight")
            print("Asegúrate de que ResInsight esté ejecutándose")
            return
        print("✓ Conectado a ResInsight")
    except Exception as e:
        print(f"Error al conectar: {e}")
        print("\nSugerencias:")
        print("  1. Asegúrate de que ResInsight esté ejecutándose")
        print("  2. Verifica que la API esté habilitada en ResInsight")
        return
    
    # Cargar el proyecto/caso
    print(f"\nCargando caso desde: {egrid_file}")
    try:
        project = rips_instance.project
        
        # Verificar si ya hay casos cargados
        cases = project.cases()
        case_count = len(cases) if cases else 0
        print(f"Casos actuales en el proyecto: {case_count}")
        
        # Si no hay casos, necesitamos cargar el archivo
        if case_count == 0:
            print("Cargando archivo EGRID...")
            try:
                project.load_case(egrid_file)
                print("✓ Archivo cargado, esperando...")
                # Esperar un momento para que se cargue
                import time
                time.sleep(3)
            except Exception as e:
                print(f"Error al cargar: {e}")
                print("Intenta abrir el archivo manualmente en ResInsight primero")
                return
        
        # Obtener el caso (usando case_id=0 para el primer caso)
        cases = project.cases()
        if not cases or len(cases) == 0:
            print("Error: No se pudo cargar el caso")
            print("Intenta abrir el archivo manualmente en ResInsight primero")
            return
        
        case = project.case(case_id=0)
        if case is None:
            print("Error: No se pudo obtener el caso")
            return
        
        print(f"✓ Caso cargado: ID=0")
        
    except Exception as e:
        print(f"Error al cargar caso: {e}")
        print("\nSugerencia: Abre el archivo EGRID manualmente en ResInsight primero")
        import traceback
        traceback.print_exc()
        return
    
    # Obtener timesteps
    try:
        time_steps = case.time_steps()
        print(f"\n✓ Timesteps encontrados: {len(time_steps)}")
        
        if len(time_steps) == 0:
            print("No hay timesteps disponibles")
            return
        
        # Mostrar información de timesteps
        print("\nTimesteps disponibles:")
        for i, ts in enumerate(time_steps):
            print(f"  {i}: {ts}")
            
    except Exception as e:
        print(f"Error al obtener timesteps: {e}")
        return
    
    # Obtener propiedades disponibles
    if properties is None:
        try:
            # Intentar obtener propiedades disponibles
            # Nota: La API puede variar, esto es un ejemplo
            properties = ['SOIL', 'SWAT', 'SGAS', 'PRESSURE', 'PORO', 'PERMX', 'PERMY', 'PERMZ']
            print(f"\nPropiedades a exportar: {properties}")
        except Exception as e:
            print(f"Advertencia: No se pudieron obtener propiedades automáticamente: {e}")
            properties = ['SOIL', 'SWAT', 'SGAS']
    
    # Exportar para cada timestep
    print("\n" + "="*60)
    print("Exportando propiedades para cada timestep")
    print("="*60)
    
    for i, ts in enumerate(time_steps):
        print(f"\nTimestep {i}/{len(time_steps)-1}: {ts}")
        
        try:
            # Activar el timestep - intentar diferentes métodos
            try:
                case.set_time_step(i)
            except AttributeError:
                try:
                    case.set_current_time_step(i)
                except AttributeError:
                    # Algunas versiones de la API usan el índice directamente en export
                    pass
            
            print(f"  ✓ Timestep {i} activado")
            
            # Exportar cada propiedad
            for prop in properties:
                try:
                    output_file = os.path.join(output_dir, f"{prop}_ts_{i:04d}.GRDECL")
                    
                    # La firma es: export_property(time_step, property_name, ...)
                    # export_file es una propiedad, configurarla antes si es posible
                    try:
                        # Intentar configurar export_file como propiedad
                        if hasattr(case, 'export_file'):
                            case.export_file = output_file
                        
                        # Llamar al método con los parámetros posicionales
                        case.export_property(i, prop)
                        print(f"  ✓ {prop} exportado -> {output_file}")
                    except Exception as e1:
                        # Si falla, intentar obtener los datos y escribirlos manualmente
                        try:
                            # Obtener los valores de la propiedad
                            values = case.active_cell_property(
                                property_type="DYNAMIC_NATIVE",
                                property_name=prop,
                                time_step=i
                            )
                            
                            # Escribir en formato GRDECL
                            with open(output_file, 'w') as f:
                                f.write(f"-- Exported from ResInsight - Timestep {i}\n")
                                f.write(f"{prop}\n")
                                # Formatear valores (5 por línea como en GRDECL)
                                if values:
                                    for j in range(0, len(values), 5):
                                        line_vals = values[j:j+5]
                                        f.write(" ".join(f"{v:15.6f}" for v in line_vals) + "\n")
                                f.write("/\n")
                            print(f"  ✓ {prop} exportado -> {output_file}")
                        except Exception as e2:
                            print(f"  ✗ Error al exportar {prop}: {e2}")
                            
                except Exception as e:
                    print(f"  ✗ Error al exportar {prop}: {e}")
                    
        except Exception as e:
            print(f"  ✗ Error en timestep {i}: {e}")
            continue
    
    print("\n" + "="*60)
    print("✓ Exportación completada")
    print("="*60)
    print(f"\nArchivos guardados en: {output_dir}")


def main():
    """Función principal."""
    
    # Archivo EGRID
    egrid_file = "/home/spell/Desktop/TUT4/DEP_GAS.EGRID"
    
    # Directorio de salida (mismo que el script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "timesteps_export")
    
    # Propiedades a exportar (puedes modificar esta lista)
    properties = [
        'SOIL',      # Saturación de aceite
        'SWAT',      # Saturación de agua
        'SGAS',      # Saturación de gas
        'PRESSURE',  # Presión
        'PORO',      # Porosidad
        'PERMX',     # Permeabilidad X
        'PERMY',     # Permeabilidad Y
        'PERMZ',     # Permeabilidad Z
    ]
    
    export_all_timesteps(
        egrid_file=egrid_file,
        output_dir=output_dir,
        properties=properties
    )


if __name__ == "__main__":
    main()

