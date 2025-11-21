"""
Script para exportar YMFS (propiedad de inyección) desde ResInsight para el reservorio GEOSX.
"""

import os
import sys

try:
    import rips
except ImportError:
    print("Error: ResInsight Python API no está instalada")
    sys.exit(1)


def export_ymfs_timesteps_geosx(egrid_file, output_dir=None):
    """Exporta YMFS para todos los timesteps del reservorio GEOSX."""
    
    if not os.path.exists(egrid_file):
        print(f"Error: No se encontró el archivo {egrid_file}")
        return
    
    if output_dir is None:
        # Crear directorio de salida en data/geosx/new_simulation/timesteps_export
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "data", "geosx", "new_simulation", "timesteps_export")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*60)
    print("Exportando YMFS desde ResInsight - Reservorio GEOSX")
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
        return
    
    # Cargar caso
    print(f"\nCargando caso desde: {egrid_file}")
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
    except Exception as e:
        print(f"Error al cargar caso: {e}")
        print("\nSugerencia: Abre el archivo EGRID manualmente en ResInsight primero")
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
    
    # Exportar YMFS para cada timestep
    print("\n" + "="*60)
    print("Exportando YMFS para cada timestep")
    print("="*60)
    
    exported_count = 0
    
    for i, ts in enumerate(time_steps):
        print(f"\nTimestep {i}/{len(time_steps)-1}")
        
        try:
            # Obtener valores de YMFS
            values = case.active_cell_property(
                property_type="DYNAMIC_NATIVE",
                property_name="YMFS",
                time_step=i
            )
            
            if values:
                # Escribir en formato GRDECL
                output_file = os.path.join(output_dir, f"YMFS_ts_{i:04d}.GRDECL")
                with open(output_file, 'w') as f:
                    f.write(f"-- Exported from ResInsight - GEOSX Simulation - Timestep {i}\n")
                    f.write(f"YMFS\n")
                    # Formatear valores (5 por línea como en GRDECL)
                    for j in range(0, len(values), 5):
                        line_vals = values[j:j+5]
                        f.write(" ".join(f"{v:15.6f}" for v in line_vals) + "\n")
                    f.write("/\n")
                print(f"  ✓ YMFS exportado -> {output_file} ({len(values)} valores)")
                exported_count += 1
            else:
                print(f"  ⚠ No se obtuvieron datos para timestep {i}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"✓ Exportación completada: {exported_count}/{len(time_steps)} timesteps exportados")
    print("="*60)
    print(f"\nArchivos guardados en: {output_dir}")


if __name__ == "__main__":
    # Archivo EGRID del reservorio GEOSX
    egrid_file = "/home/spell/Desktop/pyvista/data/geosx/new_simulation/DEP_GAS.EGRID"
    
    export_ymfs_timesteps_geosx(egrid_file)

