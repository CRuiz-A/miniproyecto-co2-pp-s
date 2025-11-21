#!/usr/bin/env python3
"""
Script para extraer datos YMFS del periodo de inyección usando ResInsight API
y generar un gráfico 3D con Plotly mostrando solo celdas con YMFS > 0.1
"""

import sys
import os
import time
sys.path.insert(0, '/home/spell/ResInsight_Install/bin')

try:
    import rips
except ImportError:
    print("Error: No se pudo importar rips. Verifica que ResInsight esté instalado.")
    sys.exit(1)

import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Configuración
project_path = '/home/spell/Desktop/reservorio_forzado/new_simulation'
egrid_file = os.path.join(project_path, 'DEP_GAS.EGRID')
unrst_file = os.path.join(project_path, 'DEP_GAS.UNRST')
output_html = os.path.join(project_path, 'ymfs_3d_plot.html')

# Dimensiones de la grilla (del grid.grdecl)
nx, ny, nz = 64, 28, 25

# Periodo de inyección: 2025-2040 (días desde 2010: 5475 a 10950)
injection_start_days = 5475  # 1 JAN 2025
injection_end_days = 10950   # 1 JAN 2040

print("Conectando a ResInsight...")
try:
    # Configurar el ejecutable de ResInsight
    resinsight_exe = '/home/spell/ResInsight_Install/bin/ResInsight'
    
    # Intentar conectar a instancia existente primero
    print("Buscando instancia existente de ResInsight...")
    resinsight = rips.Instance.find()
    
    if resinsight is None:
        print("No hay instancia existente. Lanzando ResInsight (modo consola)...")
        resinsight = rips.Instance.launch(
            resinsight_executable=resinsight_exe,
            console=True,
            init_timeout=60
        )
        time.sleep(5)  # Dar tiempo para que se inicie
    
    if resinsight is None:
        print("Error: No se pudo conectar a ResInsight.")
        print("Asegúrate de que ResInsight esté instalado en:", resinsight_exe)
        sys.exit(1)
    
    print("✓ Conectado a ResInsight")
    project = resinsight.project
    
    print("Cargando caso Eclipse...")
    # Cargar el caso usando loadCase
    case = project.load_case(egrid_file)
    
    if case is None:
        print("Error: No se pudo cargar el caso.")
        sys.exit(1)
    
    print(f"✓ Caso cargado: {case.name}")
    
    # Obtener las fechas disponibles
    time_steps = case.time_steps()
    print(f"Pasos de tiempo disponibles: {len(time_steps)}")
    
    if len(time_steps) == 0:
        print("Error: No se encontraron pasos de tiempo.")
        sys.exit(1)
    
    # Mostrar información de los pasos de tiempo
    print("\nInformación de pasos de tiempo:")
    for i, ts in enumerate(time_steps):
        print(f"  Paso {i}: {ts}")
    
    # Filtrar pasos de tiempo del periodo de inyección (2025-2040)
    injection_time_steps = []
    for i, ts in enumerate(time_steps):
        year = ts.year
        if 2025 <= year <= 2040:
            injection_time_steps.append((i, ts, year))
            print(f"  Paso {i}: {year}-{ts.month:02d}-{ts.day:02d}")
    
    if len(injection_time_steps) == 0:
        print("Error: No se encontraron pasos de tiempo en el periodo de inyección (2025-2040).")
        sys.exit(1)
    
    # Usar el último paso del periodo de inyección (más representativo)
    target_step, time_step, year = injection_time_steps[-1]
    print(f"\nUsando paso de tiempo {target_step} ({year}-{time_step.month:02d}-{time_step.day:02d})")
    
    # Obtener los nombres de propiedades disponibles
    print("\nBuscando variable YMFS...")
    # property_type puede ser 'DYNAMIC_NATIVE', 'STATIC_NATIVE', 'GENERATED', etc.
    try:
        all_props = case.available_properties('DYNAMIC_NATIVE')
    except:
        try:
            all_props = case.available_properties('STATIC_NATIVE')
        except:
            all_props = []
    
    # Buscar variable YMFS específicamente
    y_var_name = None
    for prop in all_props:
        if prop == 'YMFS':
            y_var_name = prop
            print(f"✓ Variable encontrada: {prop}")
            break
    
    if y_var_name is None:
        print("\nVariables disponibles:")
        for prop in all_props:
            print(f"  - {prop}")
        print("\nBuscando variables con 'YMF'...")
        for prop in all_props:
            if 'YMF' in prop.upper():
                print(f"  Encontrada: {prop}")
                if 'S' in prop.upper() and 'G' not in prop.upper():  # YMFS pero no YMFG
                    y_var_name = prop
                    print(f"✓ Usando variable: {prop}")
                    break
    
    if y_var_name is None:
        print("\nError: No se pudo encontrar la variable YMFS.")
        print("Por favor, verifica manualmente las variables disponibles en ResInsight.")
        sys.exit(1)
    
    # Usar el último paso del periodo de inyección (más representativo)
    step_idx, time_step_obj, year = injection_time_steps[-1]
    print(f"\nExtrayendo datos del paso {step_idx} ({year}-{time_step_obj.month:02d}-{time_step_obj.day:02d})...")
    
    # Obtener valores de YMFS
    print("Leyendo valores de YMFS...")
    ymfs_values = case.selected_cell_property(y_var_name, time_step_obj)
    
    if ymfs_values is None or len(ymfs_values) == 0:
        print("Error: No se pudieron leer los valores de YMFS.")
        sys.exit(1)
    
    print(f"Valores leídos: {len(ymfs_values)}")
    
    # Obtener coordenadas de las celdas
    print("Obteniendo coordenadas de las celdas...")
    cell_centers = case.cell_centers()
    
    if cell_centers is None or len(cell_centers) == 0:
        print("Error: No se pudieron obtener las coordenadas de las celdas.")
        sys.exit(1)
    
    print(f"Coordenadas obtenidas: {len(cell_centers)}")
    
    # Convertir a arrays numpy
    ymfs_array = np.array(ymfs_values)
    centers_array = np.array(cell_centers)
    
    # Filtrar celdas con YMFS > 0.1
    mask = ymfs_array > 0.1
    
    if np.sum(mask) == 0:
        print("Error: No hay celdas con YMFS > 0.1 en este paso de tiempo.")
        print(f"Rango de YMFS: {ymfs_array.min():.6f} - {ymfs_array.max():.6f}")
        sys.exit(1)
    
    filtered_centers = centers_array[mask]
    filtered_values = ymfs_array[mask]
    
    print(f"\nCeldas con YMFS > 0.1: {np.sum(mask)}")
    print(f"Rango de YMFS (filtrado): {filtered_values.min():.4f} - {filtered_values.max():.4f}")
    
    # Crear gráfico 3D con Plotly
    print("\nGenerando gráfico 3D...")
    fig = go.Figure(data=go.Scatter3d(
        x=filtered_centers[:, 0],
        y=filtered_centers[:, 1],
        z=filtered_centers[:, 2],
        mode='markers',
        marker=dict(
            size=4,
            color=filtered_values,
            colorscale='Viridis',
            colorbar=dict(title='YMFS'),
            cmin=0.1,
            cmax=filtered_values.max(),
            showscale=True
        ),
        text=[f'YMFS: {v:.3f}' for v in filtered_values],
        hovertemplate='X: %{x:.1f} m<br>Y: %{y:.1f} m<br>Z: %{z:.1f} m<br>YMFS: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Distribución 3D de YMFS > 0.1 - Periodo de Inyección<br>{year}-{time_step_obj.month:02d}-{time_step_obj.day:02d} (Paso {step_idx})',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='data'
        ),
        width=1400,
        height=900
    )
    
    # Guardar como HTML
    print(f"\nGuardando gráfico en: {output_html}")
    fig.write_html(output_html)
    print("✓ Gráfico guardado exitosamente!")
    print(f"\nAbre el archivo en tu navegador: {output_html}")
    
    # No cerrar ResInsight para que el usuario pueda seguir usándolo
    # resinsight.exit()

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
