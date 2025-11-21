#!/usr/bin/env python3
"""
Script de ejemplo para cargar y visualizar los datos de Bunter
Visualizaciones 3D: una para permeabilidad y otra para facies (saturación)
"""
import numpy as np
import plotly.graph_objects as go
import json
from pathlib import Path

# Configuración
DATA_DIR = Path(__file__).parent

def load_data():
    """Carga los datos del archivo NPZ"""
    print("📂 Cargando datos desde bunter_data.npz...")
    data = np.load(DATA_DIR / "bunter_data.npz")
    
    facies = data['facies']
    permeability = data['permeability']
    porosity = data['porosity']
    
    print(f"✅ Datos cargados:")
    print(f"   • Facies: shape {facies.shape}")
    print(f"   • Permeabilidad: shape {permeability.shape}")
    print(f"   • Porosidad: shape {porosity.shape}")
    
    return facies, permeability, porosity

def create_3d_permeability_plot(permeability):
    """
    Crea visualización 3D única para permeabilidad con slices en X, Y, Z
    """
    print("\n🎨 Generando visualización 3D para Permeabilidad...")
    
    nz, ny, nx = permeability.shape
    
    # Seleccionar slices centrales para cada dirección
    k_slice = nz // 2  # Slice horizontal (profundidad)
    j_slice = ny // 2  # Slice vertical Y (Norte-Sur)
    i_slice = nx // 2  # Slice vertical X (Este-Oeste)
    
    fig = go.Figure()
    
    # Usar escala logarítmica para permeabilidad
    perm_log = np.log10(np.maximum(permeability, 0.001))
    
    # ========================================================================
    # SLICE HORIZONTAL (Z) - Vista desde arriba
    # ========================================================================
    x_h = np.arange(nx)
    y_h = np.arange(ny)
    X_h, Y_h = np.meshgrid(x_h, y_h)
    Z_h = np.full_like(X_h, k_slice)
    
    # Permeabilidad - Horizontal
    fig.add_trace(
        go.Surface(
            x=X_h, y=Y_h, z=Z_h,
            surfacecolor=perm_log[k_slice, :, :],
            colorscale='Hot',
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="log₁₀(Permeabilidad) mD"),
            name='Slice Horizontal (Z)',
            showscale=True,
            opacity=0.9
        )
    )
    
    # ========================================================================
    # SLICE VERTICAL Y (j) - Corte Norte-Sur
    # ========================================================================
    x_v = np.arange(nx)
    z_v = np.arange(nz)
    X_v, Z_v = np.meshgrid(x_v, z_v)
    Y_v = np.full_like(X_v, j_slice)
    
    # Permeabilidad - Vertical Y
    fig.add_trace(
        go.Surface(
            x=X_v, y=Y_v, z=Z_v,
            surfacecolor=perm_log[:, j_slice, :],
            colorscale='Hot',
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="log₁₀(Permeabilidad) mD"),
            name='Slice Vertical Y',
            showscale=False,
            opacity=0.9
        )
    )
    
    # ========================================================================
    # SLICE VERTICAL X (i) - Corte Este-Oeste
    # ========================================================================
    y_vx = np.arange(ny)
    z_vx = np.arange(nz)
    Y_vx, Z_vx = np.meshgrid(y_vx, z_vx)
    X_vx = np.full_like(Y_vx, i_slice)
    
    # Permeabilidad - Vertical X
    fig.add_trace(
        go.Surface(
            x=X_vx, y=Y_vx, z=Z_vx,
            surfacecolor=perm_log[:, :, i_slice],
            colorscale='Hot',
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="log₁₀(Permeabilidad) mD"),
            name='Slice Vertical X',
            showscale=False,
            opacity=0.9
        )
    )
    
    # Actualizar layout
    fig.update_layout(
        title=dict(
            text='Modelo Bunter - Permeabilidad 3D<br><sub>Slice Horizontal (Z), Vertical Y (j), Vertical X (i) - Escala logarítmica</sub>',
            x=0.5,
            font=dict(size=18)
        ),
        scene=dict(
            xaxis_title='X (i)',
            yaxis_title='Y (j)',
            zaxis_title='Profundidad (k)',
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
            aspectmode='data'
        ),
        height=800
    )
    
    # Guardar como HTML
    output_path = DATA_DIR / "example_3d_permeability.html"
    fig.write_html(str(output_path))
    print(f"✅ Visualización 3D de Permeabilidad guardada: {output_path}")
    
    return fig

def create_3d_facies_plot(facies):
    """
    Crea visualización 3D única para facies (saturación) con slices en X, Y, Z
    """
    print("\n🎨 Generando visualización 3D para Facies (Saturación)...")
    
    nz, ny, nx = facies.shape
    
    # Seleccionar slices centrales para cada dirección
    k_slice = nz // 2  # Slice horizontal (profundidad)
    j_slice = ny // 2  # Slice vertical Y (Norte-Sur)
    i_slice = nx // 2  # Slice vertical X (Este-Oeste)
    
    fig = go.Figure()
    
    # Colorescale categórico para facies
    colorscale_facies = [
        [0.0, 'rgb(141,211,199)'],  # Verde claro para facies 1
        [0.5, 'rgb(255,255,179)'],  # Amarillo para transición
        [1.0, 'rgb(190,186,218)']  # Morado claro para facies 2
    ]
    
    # ========================================================================
    # SLICE HORIZONTAL (Z) - Vista desde arriba
    # ========================================================================
    x_h = np.arange(nx)
    y_h = np.arange(ny)
    X_h, Y_h = np.meshgrid(x_h, y_h)
    Z_h = np.full_like(X_h, k_slice)
    
    # Facies - Horizontal
    fig.add_trace(
        go.Surface(
            x=X_h, y=Y_h, z=Z_h,
            surfacecolor=facies[k_slice, :, :],
            colorscale=colorscale_facies,
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="Facies ID"),
            name='Slice Horizontal (Z)',
            showscale=True,
            opacity=0.9
        )
    )
    
    # ========================================================================
    # SLICE VERTICAL Y (j) - Corte Norte-Sur
    # ========================================================================
    x_v = np.arange(nx)
    z_v = np.arange(nz)
    X_v, Z_v = np.meshgrid(x_v, z_v)
    Y_v = np.full_like(X_v, j_slice)
    
    # Facies - Vertical Y
    fig.add_trace(
        go.Surface(
            x=X_v, y=Y_v, z=Z_v,
            surfacecolor=facies[:, j_slice, :],
            colorscale=colorscale_facies,
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="Facies ID"),
            name='Slice Vertical Y',
            showscale=False,
            opacity=0.9
        )
    )
    
    # ========================================================================
    # SLICE VERTICAL X (i) - Corte Este-Oeste
    # ========================================================================
    y_vx = np.arange(ny)
    z_vx = np.arange(nz)
    Y_vx, Z_vx = np.meshgrid(y_vx, z_vx)
    X_vx = np.full_like(Y_vx, i_slice)
    
    # Facies - Vertical X
    fig.add_trace(
        go.Surface(
            x=X_vx, y=Y_vx, z=Z_vx,
            surfacecolor=facies[:, :, i_slice],
            colorscale=colorscale_facies,
            colorbar=dict(x=0.1, y=0.5, len=0.3, title="Facies ID"),
            name='Slice Vertical X',
            showscale=False,
            opacity=0.9
        )
    )
    
    # Actualizar layout
    fig.update_layout(
        title=dict(
            text='Modelo Bunter - Facies (Saturación) 3D<br><sub>Slice Horizontal (Z), Vertical Y (j), Vertical X (i)</sub>',
            x=0.5,
            font=dict(size=18)
        ),
        scene=dict(
            xaxis_title='X (i)',
            yaxis_title='Y (j)',
            zaxis_title='Profundidad (k)',
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
            aspectmode='data'
        ),
        height=800
    )
    
    # Guardar como HTML
    output_path = DATA_DIR / "example_3d_facies.html"
    fig.write_html(str(output_path))
    print(f"✅ Visualización 3D de Facies guardada: {output_path}")
    
    return fig

def main():
    print("=" * 70)
    print("🌍 EJEMPLO DE USO - DATOS BUNTER")
    print("=" * 70)
    print()
    
    # Cargar datos
    facies, permeability, porosity = load_data()
    
    # Crear visualización 3D para permeabilidad
    create_3d_permeability_plot(permeability)
    
    # Crear visualización 3D para facies (saturación)
    create_3d_facies_plot(facies)
    
    print("\n" + "=" * 70)
    print("✅ VISUALIZACIONES 3D GENERADAS EXITOSAMENTE")
    print("=" * 70)
    print("\n📁 Archivos HTML generados:")
    print(f"   • {DATA_DIR / 'example_3d_permeability.html'} (Permeabilidad)")
    print(f"   • {DATA_DIR / 'example_3d_facies.html'} (Facies/Saturación)")
    print("\n💡 Abre los archivos HTML en tu navegador para visualizaciones interactivas 3D")
    print("   Cada gráfico muestra un slice horizontal (Z) y dos slices verticales (X, Y)")

if __name__ == "__main__":
    main()
