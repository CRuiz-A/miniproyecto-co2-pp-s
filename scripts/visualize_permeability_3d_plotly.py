#!/usr/bin/env python3
"""
Script para visualizar mapas de calor 3D de permeabilidad usando Plotly.
Muestra 3 cortes planos (slices) en las direcciones X, Y, Z.
Usa WebGL en el navegador, no requiere OpenGL en el sistema.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import argparse
import sys

def load_permeability(filepath):
    """Carga el archivo de permeabilidad."""
    data = np.load(filepath)
    print(f"Shape del array: {data.shape}")
    print(f"Rango de valores: [{data.min():.2e}, {data.max():.2e}]")
    return data

def prepare_3d_data(data):
    """
    Prepara los datos para visualización 3D.
    Si los datos son 4D, toma el primer slice temporal.
    """
    if len(data.shape) == 4:
        print("Datos 4D detectados. Usando el primer slice temporal.")
        data_3d = data[0]
    elif len(data.shape) == 3:
        data_3d = data
    else:
        raise ValueError(f"Forma de datos no soportada: {data.shape}")
    
    print(f"Shape 3D final: {data_3d.shape}")
    return data_3d

def create_3d_slices_plotly(data_3d, x_slice=None, y_slice=None, z_slice=None, 
                            colormap='Hot', log_scale=True):
    """
    Crea visualización 3D con 3 cortes planos usando Plotly.
    
    Args:
        data_3d: Array 3D de permeabilidad
        x_slice: Índice para el corte en dirección X (plano YZ)
        y_slice: Índice para el corte en dirección Y (plano XZ)
        z_slice: Índice para el corte en dirección Z (plano XY)
        colormap: Mapa de colores de Plotly
        log_scale: Si True, usa escala logarítmica para los valores
    """
    # El array tiene shape (nz, ny, nx) donde:
    # - Primera dimensión (índice 0) = Z
    # - Segunda dimensión (índice 1) = Y  
    # - Tercera dimensión (índice 2) = X
    nz_array, ny_array, nx_array = data_3d.shape
    
    # Valores por defecto (mitad del dominio)
    if x_slice is None:
        x_slice = nx_array // 2
    if y_slice is None:
        y_slice = ny_array // 2
    if z_slice is None:
        z_slice = nz_array // 2
    
    # Asegurar que los índices estén dentro del rango
    x_slice = max(0, min(nx_array - 1, x_slice))
    y_slice = max(0, min(ny_array - 1, y_slice))
    z_slice = max(0, min(nz_array - 1, z_slice))
    
    print(f"\nCortes seleccionados:")
    print(f"  - Corte X (plano YZ) en índice: {x_slice}/{nx_array-1}")
    print(f"  - Corte Y (plano XZ) en índice: {y_slice}/{ny_array-1}")
    print(f"  - Corte Z (plano XY) en índice: {z_slice}/{nz_array-1}")
    
    # Aplicar escala logarítmica si es necesario
    if log_scale:
        # Evitar log(0) agregando un pequeño valor
        data_viz = np.log10(data_3d + 1e-20)
        colorbar_title = 'log10(Permeabilidad)'
    else:
        data_viz = data_3d
        colorbar_title = 'Permeabilidad'
    
    # Crear figura
    fig = go.Figure()
    
    # Extraer los datos de los cortes
    # Corte X: fijar la tercera dimensión (X), variar Z y Y
    slice_x_data_raw = data_viz[:, :, x_slice]  # (nz, ny) - plano YZ
    # Invertir en la dimensión Z para que coincida con coordenadas invertidas
    slice_x_data = np.flipud(slice_x_data_raw)  # Invertir primera dimensión (Z)
    # Transponer para que coincida con las coordenadas (ny, nz)
    slice_x_data = slice_x_data.T

    # Corte Y: fijar la segunda dimensión (Y), variar Z y X
    slice_y_data_raw = data_viz[:, y_slice, :]  # (nz, nx) - plano XZ
    # Invertir en la dimensión Z para que coincida con coordenadas invertidas
    slice_y_data = np.flipud(slice_y_data_raw)  # Invertir primera dimensión (Z)
    # Transponer para que coincida con las coordenadas (nx, nz)
    slice_y_data = slice_y_data.T

    # Corte Z: fijar la primera dimensión (Z), variar Y y X
    slice_z_data = data_viz[z_slice, :, :]  # (ny, nx) - plano XY
    # No necesita inversión porque Z es constante
    # Ya está en la forma correcta (ny, nx) que coincide con las coordenadas
    
    # Crear coordenadas para cada corte en el espacio 3D
    # En Plotly: x=horizontal, y=horizontal perpendicular, z=vertical
    # Array: (nz, ny, nx) donde nz es la dimensión vertical
    
    # Corte X (plano YZ) - perpendicular al eje X, fijar X
    # En este plano, Y y Z varían, X es constante
    y_coords_x = np.arange(ny_array)
    z_coords_x = np.arange(nz_array)
    Y_x, Z_x_array = np.meshgrid(y_coords_x, z_coords_x, indexing='ij')
    X_x = np.full_like(Y_x, x_slice)
    # Invertir Z para que índice 0 esté abajo y mayor índice arriba
    Z_x = nz_array - 1 - Z_x_array
    
    # Corte Y (plano XZ) - perpendicular al eje Y, fijar Y
    # En este plano, X y Z varían, Y es constante
    x_coords_y = np.arange(nx_array)
    z_coords_y = np.arange(nz_array)
    X_y, Z_y_array = np.meshgrid(x_coords_y, z_coords_y, indexing='ij')
    Y_y = np.full_like(X_y, y_slice)
    # Invertir Z para que índice 0 esté abajo y mayor índice arriba
    Z_y = nz_array - 1 - Z_y_array
    
    # Corte Z (plano XY) - perpendicular al eje Z, fijar Z
    # En este plano, X y Y varían, Z es constante
    x_coords_z = np.arange(nx_array)
    y_coords_z = np.arange(ny_array)
    X_z, Y_z = np.meshgrid(x_coords_z, y_coords_z, indexing='ij')
    # Invertir Z para que índice 0 esté abajo y mayor índice arriba
    Z_z = np.full_like(X_z, nz_array - 1 - z_slice)
    
    # Encontrar el rango de colores común
    vmin = min(slice_x_data.min(), slice_y_data.min(), slice_z_data.min())
    vmax = max(slice_x_data.max(), slice_y_data.max(), slice_z_data.max())
    
    # Agregar superficie para corte X (plano YZ) - perpendicular al eje X
    # En este plano: X=constante, Y varía horizontalmente, Z varía verticalmente
    fig.add_trace(go.Surface(
        x=X_x,  # X constante
        y=Y_x,  # Y varía
        z=Z_x,  # Z varía (vertical)
        surfacecolor=slice_x_data,  # Datos del plano YZ
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte X (YZ)',
        showscale=True,
        colorbar=dict(
            title=colorbar_title,
            x=1.02,
            len=0.7
        )
    ))

    # Agregar superficie para corte Y (plano XZ) - perpendicular al eje Y
    # En este plano: Y=constante, X varía horizontalmente, Z varía verticalmente
    fig.add_trace(go.Surface(
        x=X_y,  # X varía
        y=Y_y,  # Y constante
        z=Z_y,  # Z varía (vertical)
        surfacecolor=slice_y_data,  # Datos del plano XZ
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte Y (XZ)',
        showscale=False
    ))

    # Agregar superficie para corte Z (plano XY) - perpendicular al eje Z
    # En este plano: Z=constante, X varía horizontalmente, Y varía horizontalmente
    fig.add_trace(go.Surface(
        x=X_z,  # X varía
        y=Y_z,  # Y varía
        z=Z_z,  # Z constante
        surfacecolor=slice_z_data,  # Datos del plano XY
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte Z (XY)',
        showscale=False
    ))
    
    # Configurar el layout
    fig.update_layout(
        title='Mapa de Calor 3D - Permeabilidad<br>3 Cortes Planos',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.2, y=1.2, z=1.2),
                up=dict(x=0, y=0, z=1)  # Z apunta hacia arriba
            )
        ),
        width=1200,
        height=900,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def main():
    parser = argparse.ArgumentParser(
        description='Visualiza mapas de calor 3D de permeabilidad con Plotly (WebGL)'
    )
    parser.add_argument(
        'filepath',
        type=str,
        default='permeability.npy',
        nargs='?',
        help='Ruta al archivo .npy de permeabilidad'
    )
    parser.add_argument(
        '--x-slice',
        type=int,
        default=None,
        help='Índice para el corte en dirección X (plano YZ)'
    )
    parser.add_argument(
        '--y-slice',
        type=int,
        default=None,
        help='Índice para el corte en dirección Y (plano XZ)'
    )
    parser.add_argument(
        '--z-slice',
        type=int,
        default=None,
        help='Índice para el corte en dirección Z (plano XY)'
    )
    parser.add_argument(
        '--colormap',
        type=str,
        default='Hot',
        help='Mapa de colores de Plotly (Hot, Viridis, Plasma, Jet, etc.)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='permeability_3d.html',
        help='Nombre del archivo HTML de salida'
    )
    parser.add_argument(
        '--no-log',
        action='store_true',
        help='No usar escala logarítmica'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Abrir automáticamente en el navegador'
    )
    
    args = parser.parse_args()
    
    try:
        # Cargar datos
        print("Cargando datos de permeabilidad...")
        data = load_permeability(args.filepath)
        
        # Preparar datos 3D
        data_3d = prepare_3d_data(data)
        
        # Crear visualización
        print("\nCreando visualización 3D...")
        fig = create_3d_slices_plotly(
            data_3d,
            x_slice=args.x_slice,
            y_slice=args.y_slice,
            z_slice=args.z_slice,
            colormap=args.colormap,
            log_scale=not args.no_log
        )
        
        # Guardar archivo HTML
        print(f"\n✓ Guardando visualización en {args.output}...")
        fig.write_html(args.output)
        print(f"✓ Archivo HTML generado exitosamente: {args.output}")
        
        import os
        print(f"  Ruta completa: {os.path.abspath(args.output)}")
        print(f"  Abre el archivo en tu navegador web para ver la visualización interactiva.")
        
        # Opcionalmente abrir en el navegador
        if args.show:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(args.output))
            print(f"\n✓ Abriendo en el navegador...")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

