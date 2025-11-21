import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import plotly.graph_objects as go

st.set_page_config(page_title="CO₂ Viewer", page_icon="🧊", layout="wide")

BASE_DIR = Path(__file__).parent
TIMESTEPS_DIR = BASE_DIR / "timesteps_export"
CACHE_DIR = BASE_DIR / "outputs" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
GEOSX_DIR = BASE_DIR / "data" / "geosx"


@st.cache_data(show_spinner=False)
def read_grdecl_property(filepath: str) -> np.ndarray:
    """Lee valores de un archivo GRDECL."""
    values: List[float] = []
    reading = False
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("--"):
                continue
            if any(key in line for key in ["YMFS", "SOIL", "SWAT", "SGAS", "PRESSURE"]):
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


@st.cache_data(show_spinner=False)
def load_all_timesteps() -> Tuple[Dict[int, np.ndarray], List[int]]:
    """Carga todos los timesteps YMFS."""
    if not TIMESTEPS_DIR.exists():
        return {}, []

    files = sorted(TIMESTEPS_DIR.glob("YMFS_ts_*.GRDECL"))
    data: Dict[int, np.ndarray] = {}
    indices: List[int] = []

    for filepath in files:
        match = re.search(r"ts_(\d+)", filepath.name)
        if not match:
            continue
        timestep = int(match.group(1))
        data[timestep] = read_grdecl_property(str(filepath))
        indices.append(timestep)

    indices.sort()
    return data, indices


@st.cache_data(show_spinner=False)
def preprocess_all_data(ymfs_dict: Dict[int, np.ndarray], ts_indices: List[int], threshold: float) -> Dict:
    """Preprocesa todos los datos para JavaScript."""
    nx, ny, nz = 100, 100, 10
    x_min, x_max = 0.0, 10000.0
    y_min, y_max = 0.0, 10000.0
    z_top, z_bottom = -2500.0, -2700.0

    cell_size_x = (x_max - x_min) / (nx - 1)
    cell_size_y = (y_max - y_min) / (ny - 1)
    cell_size_z = (z_bottom - z_top) / (nz - 1)

    # Pozos inyectores (fijos)
    wells = [
        (2500.0, 2500.0, -2500.0),
        (2500.0, 7500.0, -2500.0),
        (7500.0, 2500.0, -2500.0),
        (7438.0, 7438.0, -2500.0),
    ]
    
    cube_size = 200.0
    half = cube_size / 2.0
    
    injector_vertices = []
    injector_faces = []
    vertex_offset = 0
    
    for cx, cy, cz in wells:
        vertices = [
            [cx - half, cy - half, cz - half],
            [cx + half, cy - half, cz - half],
            [cx + half, cy + half, cz - half],
            [cx - half, cy + half, cz - half],
            [cx - half, cy - half, cz + half],
            [cx + half, cy - half, cz + half],
            [cx + half, cy + half, cz + half],
            [cx - half, cy + half, cz + half],
        ]
        injector_vertices.extend(vertices)
        
        faces = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
            [0, 3, 7], [0, 7, 4], [1, 5, 6], [1, 6, 2],
        ]
        for face in faces:
            injector_faces.append([vertex_offset + face[0], vertex_offset + face[1], vertex_offset + face[2]])
        vertex_offset += 8
    
    # Datos por timestep (solo índices y valores de celdas > threshold)
    timestep_data = {}
    
    for ts in ts_indices:
        ymfs_values = ymfs_dict[ts]
        total = nx * ny * nz
        if len(ymfs_values) < total:
            padded = np.zeros(total, dtype=float)
            padded[:len(ymfs_values)] = ymfs_values
            ymfs_values = padded
        elif len(ymfs_values) > total:
            ymfs_values = ymfs_values[:total]
        
        # Solo guardamos índices de celdas activas (> threshold)
        active_cells = []
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    idx = i + j * nx + k * nx * ny
                    value = ymfs_values[idx]
                    if value >= threshold:
                        x = x_min + i * cell_size_x
                        y = y_min + j * cell_size_y
                        z = z_top + k * cell_size_z
                        active_cells.append({
                            'x': float(x),
                            'y': float(y),
                            'z': float(z),
                            'value': float(value)
                        })
        
        timestep_data[str(ts)] = {
            'cells': active_cells,
            'count': len(active_cells)
        }
    
    return {
        'timesteps': ts_indices,
        'data': timestep_data,
        'injectors': {
            'vertices': injector_vertices,
            'faces': injector_faces
        },
        'grid': {
            'cell_size_x': float(cell_size_x),
            'cell_size_y': float(cell_size_y),
            'cell_size_z': float(cell_size_z)
        },
        'bounds': {
            'x': [float(x_min), float(x_max)],
            'y': [float(y_min), float(y_max)],
            'z': [float(z_bottom), float(z_top)]
        }
    }


@st.cache_data(show_spinner=False)
def load_npy_data(filepath: Path) -> Optional[np.ndarray]:
    """Carga datos desde un archivo .npy."""
    if not filepath.exists():
        return None
    return np.load(filepath)


def prepare_3d_data(data: np.ndarray) -> np.ndarray:
    """Prepara los datos para visualización 3D. Si son 4D, toma el primer slice temporal."""
    if len(data.shape) == 4:
        return data[0]
    elif len(data.shape) == 3:
        return data
    else:
        raise ValueError(f"Forma de datos no soportada: {data.shape}")


def create_3d_slices_facies(data_3d: np.ndarray, x_slice: Optional[int] = None,
                             y_slice: Optional[int] = None, z_slice: Optional[int] = None,
                             title: str = "Mapa de Facies 3D") -> go.Figure:
    """
    Crea visualización 3D de facies con colores discretos para shalty y sand.
    """
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
    
    # Mapear valores de facies: 2 -> shalty, 3 -> sand
    # Crear un mapa de colores discreto: shalty = marrón/beige, sand = amarillo/dorado
    facies_map = {2: 0, 3: 1}  # 2 -> índice 0 (shalty), 3 -> índice 1 (sand)
    
    # Colores personalizados: shalty (marrón) y sand (amarillo/dorado)
    facies_colorscale = [
        [0.0, 'rgb(139, 90, 43)'],   # Marrón para shalty (valor 2)
        [0.5, 'rgb(139, 90, 43)'],   # Marrón para shalty
        [0.5, 'rgb(255, 215, 0)'],   # Dorado para sand (valor 3)
        [1.0, 'rgb(255, 215, 0)']    # Dorado para sand
    ]
    
    # Normalizar datos de facies a [0, 1] para el mapa de colores
    def normalize_facies(data):
        normalized = np.zeros_like(data, dtype=float)
        normalized[data == 2] = 0.0  # shalty -> 0
        normalized[data == 3] = 1.0  # sand -> 1
        return normalized
    
    # Extraer los datos de los cortes
    slice_x_data_raw = data_3d[:, :, x_slice]  # (nz, ny) - plano YZ
    slice_x_data = np.flipud(slice_x_data_raw).T
    slice_x_norm = normalize_facies(slice_x_data)
    
    slice_y_data_raw = data_3d[:, y_slice, :]  # (nz, nx) - plano XZ
    slice_y_data = np.flipud(slice_y_data_raw).T
    slice_y_norm = normalize_facies(slice_y_data)
    
    slice_z_data = data_3d[z_slice, :, :]  # (ny, nx) - plano XY
    slice_z_norm = normalize_facies(slice_z_data)
    
    # Crear coordenadas para cada corte
    y_coords_x = np.arange(ny_array)
    z_coords_x = np.arange(nz_array)
    Y_x, Z_x_array = np.meshgrid(y_coords_x, z_coords_x, indexing='ij')
    X_x = np.full_like(Y_x, x_slice)
    Z_x = nz_array - 1 - Z_x_array
    
    x_coords_y = np.arange(nx_array)
    z_coords_y = np.arange(nz_array)
    X_y, Z_y_array = np.meshgrid(x_coords_y, z_coords_y, indexing='ij')
    Y_y = np.full_like(X_y, y_slice)
    Z_y = nz_array - 1 - Z_y_array
    
    x_coords_z = np.arange(nx_array)
    y_coords_z = np.arange(ny_array)
    X_z, Y_z = np.meshgrid(x_coords_z, y_coords_z, indexing='ij')
    Z_z = np.full_like(X_z, nz_array - 1 - z_slice)
    
    # Crear figura
    fig = go.Figure()
    
    # Agregar superficie para corte X (plano YZ)
    fig.add_trace(go.Surface(
        x=X_x, y=Y_x, z=Z_x,
        surfacecolor=slice_x_norm,
        colorscale=facies_colorscale,
        cmin=0.0,
        cmax=1.0,
        name='Corte X (YZ)',
        showscale=True,
        colorbar=dict(
            title="Facies",
            y=-0.1,
            len=0.5,
            orientation='h',
            tickmode='array',
            tickvals=[0.25, 0.75],
            ticktext=['Shalty', 'Sand']
        )
    ))
    
    # Agregar superficie para corte Y (plano XZ)
    fig.add_trace(go.Surface(
        x=X_y, y=Y_y, z=Z_y,
        surfacecolor=slice_y_norm,
        colorscale=facies_colorscale,
        cmin=0.0,
        cmax=1.0,
        name='Corte Y (XZ)',
        showscale=False
    ))
    
    # Agregar superficie para corte Z (plano XY)
    fig.add_trace(go.Surface(
        x=X_z, y=Y_z, z=Z_z,
        surfacecolor=slice_z_norm,
        colorscale=facies_colorscale,
        cmin=0.0,
        cmax=1.0,
        name='Corte Z (XY)',
        showscale=False
    ))
    
    # Configurar el layout
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data',
            camera=dict(
                eye=dict(x=2.4, y=2.4, z=2.4),  # Zoom al 50% (valores más altos = más alejado)
                up=dict(x=0, y=0, z=1)
            )
        ),
        width=1200,
        height=900,
        margin=dict(l=0, r=0, t=50, b=80)  # Aumentar margen inferior para la colorbar
    )
    
    return fig


def create_3d_slices_plotly(data_3d: np.ndarray, x_slice: Optional[int] = None, 
                            y_slice: Optional[int] = None, z_slice: Optional[int] = None,
                            colormap: str = 'Hot', log_scale: bool = True, 
                            title: str = "Mapa de Calor 3D", colorbar_title: str = None) -> go.Figure:
    """
    Crea visualización 3D con 3 cortes planos usando Plotly.
    Basado en los scripts de visualize_permeability_3d_plotly.py y visualize_porosity_3d_plotly.py
    """
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
    
    # Aplicar escala logarítmica si es necesario
    if log_scale:
        data_viz = np.log10(data_3d + 1e-20)
        if colorbar_title is None:
            colorbar_title = 'log10(Valor)'
    else:
        data_viz = data_3d
        if colorbar_title is None:
            colorbar_title = 'Valor'
    
    # Crear figura
    fig = go.Figure()
    
    # Extraer los datos de los cortes
    slice_x_data_raw = data_viz[:, :, x_slice]  # (nz, ny) - plano YZ
    slice_x_data = np.flipud(slice_x_data_raw).T
    
    slice_y_data_raw = data_viz[:, y_slice, :]  # (nz, nx) - plano XZ
    slice_y_data = np.flipud(slice_y_data_raw).T
    
    slice_z_data = data_viz[z_slice, :, :]  # (ny, nx) - plano XY
    
    # Crear coordenadas para cada corte
    y_coords_x = np.arange(ny_array)
    z_coords_x = np.arange(nz_array)
    Y_x, Z_x_array = np.meshgrid(y_coords_x, z_coords_x, indexing='ij')
    X_x = np.full_like(Y_x, x_slice)
    Z_x = nz_array - 1 - Z_x_array
    
    x_coords_y = np.arange(nx_array)
    z_coords_y = np.arange(nz_array)
    X_y, Z_y_array = np.meshgrid(x_coords_y, z_coords_y, indexing='ij')
    Y_y = np.full_like(X_y, y_slice)
    Z_y = nz_array - 1 - Z_y_array
    
    x_coords_z = np.arange(nx_array)
    y_coords_z = np.arange(ny_array)
    X_z, Y_z = np.meshgrid(x_coords_z, y_coords_z, indexing='ij')
    Z_z = np.full_like(X_z, nz_array - 1 - z_slice)
    
    # Encontrar el rango de colores común
    vmin = min(slice_x_data.min(), slice_y_data.min(), slice_z_data.min())
    vmax = max(slice_x_data.max(), slice_y_data.max(), slice_z_data.max())
    
    # Agregar superficie para corte X (plano YZ)
    fig.add_trace(go.Surface(
        x=X_x, y=Y_x, z=Z_x,
        surfacecolor=slice_x_data,
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte X (YZ)',
        showscale=True,
        colorbar=dict(
            title=colorbar_title,
            y=-0.1,
            len=0.5,
            orientation='h'
        )
    ))
    
    # Agregar superficie para corte Y (plano XZ)
    fig.add_trace(go.Surface(
        x=X_y, y=Y_y, z=Z_y,
        surfacecolor=slice_y_data,
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte Y (XZ)',
        showscale=False
    ))
    
    # Agregar superficie para corte Z (plano XY)
    fig.add_trace(go.Surface(
        x=X_z, y=Y_z, z=Z_z,
        surfacecolor=slice_z_data,
        colorscale=colormap,
        cmin=vmin,
        cmax=vmax,
        name='Corte Z (XY)',
        showscale=False
    ))
    
    # Configurar el layout
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data',
            camera=dict(
                eye=dict(x=2.4, y=2.4, z=2.4),  # Zoom al 50% (valores más altos = más alejado)
                up=dict(x=0, y=0, z=1)
            )
        ),
        width=1200,
        height=900,
        margin=dict(l=0, r=0, t=50, b=80)  # Aumentar margen inferior para la colorbar
    )
    
    return fig


def render_geological_properties_tab():
    """Renderiza la pestaña de propiedades geológicas (permeabilidad y porosidad)."""
    st.header("🔬 Propiedades Geológicas")
    st.caption("Visualización 3D de permeabilidad y porosidad")
    
    # Buscar archivos .npy en data/geosx
    npy_files = list(GEOSX_DIR.glob("*.npy")) if GEOSX_DIR.exists() else []
    
    if not npy_files:
        st.warning(f"⚠️ No se encontraron archivos .npy en {GEOSX_DIR}")
        st.info("Por favor, coloca los archivos `permeability.npy` y `porosity.npy` en la carpeta `data/geosx/`")
        return
    
    # Modo de visualización
    view_mode = st.radio(
        "Modo de visualización",
        options=["Individual", "Paralelo (3 gráficos)"],
        horizontal=True,
        help="Vista individual: un gráfico a la vez | Vista paralela: 3 gráficos simultáneos"
    )
    
    property_files = {f.stem: f for f in npy_files}
    
    if view_mode == "Paralelo (3 gráficos)":
        # Vista paralela: cargar los 3 gráficos principales
        required_files = ["permeability", "porosity", "facies"]
        available_files = {}
        
        for prop in required_files:
            if prop in property_files:
                available_files[prop] = property_files[prop]
            else:
                st.warning(f"⚠️ No se encontró el archivo `{prop}.npy`")
        
        if len(available_files) == 0:
            st.error("❌ No se encontraron archivos para la vista paralela")
            return
        
        # Cargar todos los datos
        all_data = {}
        all_data_3d = {}
        shapes = {}
        
        with st.spinner("Cargando datos de todas las propiedades..."):
            for prop_name, filepath in available_files.items():
                data = load_npy_data(filepath)
                if data is not None:
                    try:
                        data_3d = prepare_3d_data(data)
                        all_data[prop_name] = data
                        all_data_3d[prop_name] = data_3d
                        shapes[prop_name] = data_3d.shape
                    except Exception as e:
                        st.error(f"❌ Error al preparar datos de {prop_name}: {e}")
        
        if not all_data_3d:
            st.error("❌ No se pudieron cargar los datos")
            return
        
        # Verificar que todas las propiedades tengan las mismas dimensiones
        first_shape = list(shapes.values())[0]
        if not all(s == first_shape for s in shapes.values()):
            st.warning("⚠️ Las propiedades tienen dimensiones diferentes. Usando las dimensiones de la primera propiedad.")
        
        nz, ny, nx = first_shape
        
        # Controles en sidebar (sincronizados para todos)
        st.sidebar.header("Controles de Visualización")
        st.sidebar.info("Los controles se aplican a los 3 gráficos simultáneamente")
        
        x_slice = st.sidebar.slider(
            "Corte X (plano YZ)",
            min_value=0,
            max_value=nx - 1,
            value=nx // 2,
            help="Índice para el corte en dirección X"
        )
        
        y_slice = st.sidebar.slider(
            "Corte Y (plano XZ)",
            min_value=0,
            max_value=ny - 1,
            value=ny // 2,
            help="Índice para el corte en dirección Y"
        )
        
        z_slice = st.sidebar.slider(
            "Corte Z (plano XY)",
            min_value=0,
            max_value=nz - 1,
            value=nz // 2,
            help="Índice para el corte en dirección Z"
        )
        
        # Controles adicionales para propiedades no-facies
        colormaps = ['Hot', 'Viridis', 'Plasma', 'Cividis', 'Jet', 'Rainbow', 'Turbo', 'Magma', 'Inferno']
        permeability_colormap = st.sidebar.selectbox(
            "Colormap - Permeabilidad",
            options=colormaps,
            index=0,
            help="Mapa de colores para permeabilidad"
        )
        
        porosity_colormap = st.sidebar.selectbox(
            "Colormap - Porosidad",
            options=colormaps,
            index=1,
            help="Mapa de colores para porosidad"
        )
        
        log_scale_perm = st.sidebar.checkbox(
            "Escala log - Permeabilidad",
            value=True,
            help="Escala logarítmica para permeabilidad"
        )
        
        log_scale_poro = st.sidebar.checkbox(
            "Escala log - Porosidad",
            value=False,
            help="Escala logarítmica para porosidad"
        )
        
        # Crear 3 columnas
        cols = st.columns(3)
        
        # Gráfico 1: Permeabilidad
        if "permeability" in all_data_3d:
            with cols[0]:
                st.subheader("🔴 Permeabilidad")
                with st.spinner("Generando gráfico de permeabilidad..."):
                    fig_perm = create_3d_slices_plotly(
                        all_data_3d["permeability"],
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        colormap=permeability_colormap,
                        log_scale=log_scale_perm,
                        title="Permeabilidad",
                        colorbar_title="log10(Permeabilidad)" if log_scale_perm else "Permeabilidad"
                    )
                    st.plotly_chart(fig_perm, use_container_width=True)
        
        # Gráfico 2: Porosidad
        if "porosity" in all_data_3d:
            with cols[1]:
                st.subheader("🟢 Porosidad")
                with st.spinner("Generando gráfico de porosidad..."):
                    fig_poro = create_3d_slices_plotly(
                        all_data_3d["porosity"],
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        colormap=porosity_colormap,
                        log_scale=log_scale_poro,
                        title="Porosidad",
                        colorbar_title="log10(Porosidad)" if log_scale_poro else "Porosidad"
                    )
                    st.plotly_chart(fig_poro, use_container_width=True)
        
        # Gráfico 3: Facies
        if "facies" in all_data_3d:
            with cols[2]:
                st.subheader("🟡 Facies")
                with st.spinner("Generando gráfico de facies..."):
                    fig_facies = create_3d_slices_facies(
                        all_data_3d["facies"],
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        title="Facies"
                    )
                    st.plotly_chart(fig_facies, use_container_width=True)
                    
                    # Estadísticas de facies
                    facies_data = all_data_3d["facies"]
                    shalty_count = np.sum(facies_data == 2)
                    sand_count = np.sum(facies_data == 3)
                    st.caption(f"Shalty: {shalty_count:,} ({100*shalty_count/facies_data.size:.1f}%) | Sand: {sand_count:,} ({100*sand_count/facies_data.size:.1f}%)")
        
        return
    
    # Vista individual (código original)
    selected_property = st.selectbox(
        "Seleccionar propiedad",
        options=list(property_files.keys()),
        index=0 if "permeability" in property_files else (0 if property_files else None)
    )
    
    if selected_property is None:
        return
    
    filepath = property_files[selected_property]
    
    # Cargar datos
    with st.spinner(f"Cargando {selected_property}..."):
        data = load_npy_data(filepath)
    
    if data is None:
        st.error(f"❌ No se pudo cargar el archivo: {filepath}")
        return
    
    # Preparar datos 3D
    try:
        data_3d = prepare_3d_data(data)
        nz, ny, nx = data_3d.shape
        unique_vals = np.unique(data_3d)
        st.success(f"✅ Datos cargados: Shape {data_3d.shape} | Rango: [{data_3d.min():.4e}, {data_3d.max():.4e}] | Valores únicos: {unique_vals}")
    except Exception as e:
        st.error(f"❌ Error al preparar datos: {e}")
        return
    
    # Detectar si es facies (valores discretos 2 y 3)
    is_facies = selected_property.lower() == "facies" or (len(np.unique(data_3d)) <= 2 and np.all(np.isin(np.unique(data_3d), [2, 3])))
    
    # Controles en sidebar
    st.sidebar.header("Controles de Visualización")
    
    # Slice X
    x_slice = st.sidebar.slider(
        "Corte X (plano YZ)",
        min_value=0,
        max_value=nx - 1,
        value=nx // 2,
        help="Índice para el corte en dirección X"
    )
    
    # Slice Y
    y_slice = st.sidebar.slider(
        "Corte Y (plano XZ)",
        min_value=0,
        max_value=ny - 1,
        value=ny // 2,
        help="Índice para el corte en dirección Y"
    )
    
    # Slice Z
    z_slice = st.sidebar.slider(
        "Corte Z (plano XY)",
        min_value=0,
        max_value=nz - 1,
        value=nz // 2,
        help="Índice para el corte en dirección Z"
    )
    
    # Inicializar variables para información
    colormap = None
    log_scale = False
    
    # Crear visualización según el tipo de dato
    if is_facies:
        # Visualización especial para facies
        property_title = selected_property.replace("_", " ").title()
        title = f"Mapa de Facies 3D - {property_title}<br>3 Cortes Planos (Shalty y Sand)"
        
        with st.spinner("Generando visualización 3D de facies..."):
            fig = create_3d_slices_facies(
                data_3d,
                x_slice=x_slice,
                y_slice=y_slice,
                z_slice=z_slice,
                title=title
            )
        
        # Información sobre facies
        shalty_count = np.sum(data_3d == 2)
        sand_count = np.sum(data_3d == 3)
        st.info(f"📊 Distribución de facies: Shalty = {shalty_count:,} celdas ({100*shalty_count/data_3d.size:.1f}%) | Sand = {sand_count:,} celdas ({100*sand_count/data_3d.size:.1f}%)")
    else:
        # Visualización normal para otras propiedades
        colormaps = [
            'Hot', 'Viridis', 'Plasma', 'Cividis', 'Jet', 'Rainbow',
            'Turbo', 'Magma', 'Inferno', 'Greys', 'Blues', 'Reds'
        ]
        colormap = st.sidebar.selectbox(
            "Mapa de colores",
            options=colormaps,
            index=0 if selected_property.lower() == "permeability" else 1
        )
        
        # Escala logarítmica
        log_scale = st.sidebar.checkbox(
            "Escala logarítmica",
            value=selected_property.lower() == "permeability",
            help="Aplicar transformación log10 a los valores"
        )
        
        # Títulos
        property_title = selected_property.replace("_", " ").title()
        title = f"Mapa de Calor 3D - {property_title}<br>3 Cortes Planos"
        colorbar_title = f"log10({property_title})" if log_scale else property_title
        
        # Crear visualización
        with st.spinner("Generando visualización 3D..."):
            fig = create_3d_slices_plotly(
                data_3d,
                x_slice=x_slice,
                y_slice=y_slice,
                z_slice=z_slice,
                colormap=colormap,
                log_scale=log_scale,
                title=title,
                colorbar_title=colorbar_title
            )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    with st.expander("ℹ️ Información"):
        if is_facies:
            st.write(f"""
            **Datos de Facies:**
            - Archivo: `{filepath.name}`
            - Dimensiones: {nz} × {ny} × {nx} (Z × Y × X)
            - Valores: 2 (Shalty) y 3 (Sand)
            - Corte X (plano YZ): Índice {x_slice}/{nx-1}
            - Corte Y (plano XZ): Índice {y_slice}/{ny-1}
            - Corte Z (plano XY): Índice {z_slice}/{nz-1}
            - Colores: Marrón (Shalty) y Dorado (Sand)
            """)
        else:
            st.write(f"""
            **Datos cargados:**
            - Archivo: `{filepath.name}`
            - Dimensiones: {nz} × {ny} × {nx} (Z × Y × X)
            - Rango de valores: [{data_3d.min():.4e}, {data_3d.max():.4e}]
            - Corte X (plano YZ): Índice {x_slice}/{nx-1}
            - Corte Y (plano XZ): Índice {y_slice}/{ny-1}
            - Corte Z (plano XY): Índice {z_slice}/{nz-1}
            - Colormap: {colormap}
            - Escala: {'Logarítmica' if log_scale else 'Lineal'}
            """)


def create_viewer_html(data_json: str) -> str:
    """Crea el HTML del viewer con Plotly."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }}
        #plot {{ width: 100vw; height: 100vh; }}
        #controls {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            z-index: 1000;
            max-width: 250px;
        }}
        .control-group {{
            margin-bottom: 12px;
        }}
        label {{
            display: block;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 4px;
            color: #333;
        }}
        input[type="range"] {{
            width: 100%;
        }}
        button {{
            padding: 8px 16px;
            margin: 4px 2px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        button:hover {{
            background: #0056b3;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .info {{
            font-size: 11px;
            color: #666;
            margin-top: 8px;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 20px;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div id="loading">Cargando datos...</div>
    <div id="controls" style="display:none;">
        <div class="control-group">
            <label>Timestep: <span id="ts-label">0</span></label>
            <input type="range" id="ts-slider" min="0" max="0" value="0" step="1">
        </div>
        <div style="text-align: center;">
            <button id="play-btn" onclick="togglePlay()">▶ Play</button>
            <button onclick="previousTimestep()">◀</button>
            <button onclick="nextTimestep()">▶</button>
        </div>
        <div class="control-group">
            <label>Z Scale: <span id="zscale-label">1</span></label>
            <input type="range" id="zscale-slider" min="1" max="20" value="1" step="1">
        </div>
        <div class="control-group">
            <label>
                <input type="checkbox" id="injectors-check" checked onchange="toggleInjectors()">
                Mostrar inyectores
            </label>
        </div>
        <div class="info">
            <div>Celdas activas: <span id="cell-count">0</span></div>
            <div>FPS: <span id="fps">0</span></div>
        </div>
    </div>
    <div id="plot"></div>

    <script>
        const DATA = {data_json};
        let currentTimestepIndex = 0;
        let isPlaying = false;
        let playInterval = null;
        let showInjectors = true;
        let lastFrameTime = Date.now();
        let frameCount = 0;
        let fps = 0;

        function updateFPS() {{
            frameCount++;
            const now = Date.now();
            if (now - lastFrameTime >= 1000) {{
                fps = frameCount;
                document.getElementById('fps').textContent = fps;
                frameCount = 0;
                lastFrameTime = now;
            }}
        }}

        function buildMesh(cells, cellSize) {{
            if (!cells || cells.length === 0) {{
                return {{
                    x: [], y: [], z: [],
                    i: [], j: [], k: [],
                    intensity: []
                }};
            }}

            const x = [], y = [], z = [];
            const i = [], j = [], k = [];
            const intensity = [];
            
            const dx = cellSize.x;
            const dy = cellSize.y;
            const dz = cellSize.z;

            let vertexIndex = 0;
            
            cells.forEach(cell => {{
                const x0 = cell.x, y0 = cell.y, z0 = cell.z;
                
                // 8 vértices del cubo
                x.push(x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0);
                y.push(y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy);
                z.push(z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz);
                
                // 12 triángulos (6 caras × 2 triángulos)
                const faces = [
                    [0,1,2],[0,2,3], [4,6,5],[4,7,6],
                    [0,4,5],[0,5,1], [2,6,7],[2,7,3],
                    [0,3,7],[0,7,4], [1,5,6],[1,6,2]
                ];
                
                faces.forEach(face => {{
                    i.push(vertexIndex + face[0]);
                    j.push(vertexIndex + face[1]);
                    k.push(vertexIndex + face[2]);
                    intensity.push(cell.value);
                }});
                
                vertexIndex += 8;
            }});

            return {{ x, y, z, i, j, k, intensity }};
        }}

        function buildInjectorMesh() {{
            const vertices = DATA.injectors.vertices;
            const faces = DATA.injectors.faces;
            
            const x = vertices.map(v => v[0]);
            const y = vertices.map(v => v[1]);
            const z = vertices.map(v => v[2]);
            
            const i = [], j = [], k = [];
            faces.forEach(face => {{
                i.push(face[0]);
                j.push(face[1]);
                k.push(face[2]);
            }});
            
            return {{ x, y, z, i, j, k }};
        }}

        function updatePlot() {{
            const ts = DATA.timesteps[currentTimestepIndex];
            const tsData = DATA.data[ts];
            const zScale = parseInt(document.getElementById('zscale-slider').value);
            
            document.getElementById('ts-label').textContent = ts;
            document.getElementById('cell-count').textContent = tsData.count;
            
            const cellSize = DATA.grid;
            const mesh = buildMesh(tsData.cells, {{
                x: cellSize.cell_size_x,
                y: cellSize.cell_size_y,
                z: cellSize.cell_size_z
            }});
            
            const traces = [];
            
            if (mesh.x.length > 0) {{
                traces.push({{
                    type: 'mesh3d',
                    x: mesh.x, y: mesh.y, z: mesh.z,
                    i: mesh.i, j: mesh.j, k: mesh.k,
                    intensity: mesh.intensity,
                    colorscale: 'Hot',
                    cmin: 0.1,
                    cmax: 1.0,
                    showscale: true,
                    flatshading: false,
                    lighting: {{
                        ambient: 0.6,
                        diffuse: 0.7,
                        specular: 0.2
                    }},
                    name: 'YMFS'
                }});
            }}
            
            if (showInjectors) {{
                const injMesh = buildInjectorMesh();
                traces.push({{
                    type: 'mesh3d',
                    x: injMesh.x, y: injMesh.y, z: injMesh.z,
                    i: injMesh.i, j: injMesh.j, k: injMesh.k,
                    color: 'blue',
                    opacity: 0.9,
                    flatshading: true,
                    showscale: false,
                    name: 'Inyectores'
                }});
            }}
            
            const layout = {{
                title: `CO₂ (YMFS) - Timestep ${{ts}}`,
                scene: {{
                    xaxis: {{ title: 'X (m)', range: DATA.bounds.x }},
                    yaxis: {{ title: 'Y (m)', range: DATA.bounds.y }},
                    zaxis: {{ title: 'Z (m)', range: DATA.bounds.z }},
                    aspectmode: 'manual',
                    aspectratio: {{ x: 1, y: 1, z: zScale }},
                    camera: {{
                        eye: {{ x: 1.5, y: 1.5, z: 1.2 }}
                    }}
                }},
                margin: {{ l: 0, r: 0, t: 40, b: 0 }},
                paper_bgcolor: '#f8f9fa'
            }};
            
            Plotly.react('plot', traces, layout, {{ responsive: true }});
            updateFPS();
        }}

        function nextTimestep() {{
            if (currentTimestepIndex < DATA.timesteps.length - 1) {{
                currentTimestepIndex++;
                document.getElementById('ts-slider').value = currentTimestepIndex;
                updatePlot();
            }}
        }}

        function previousTimestep() {{
            if (currentTimestepIndex > 0) {{
                currentTimestepIndex--;
                document.getElementById('ts-slider').value = currentTimestepIndex;
                updatePlot();
            }}
        }}

        function togglePlay() {{
            isPlaying = !isPlaying;
            const btn = document.getElementById('play-btn');
            
            if (isPlaying) {{
                btn.textContent = '⏸ Pause';
                playInterval = setInterval(() => {{
                    if (currentTimestepIndex < DATA.timesteps.length - 1) {{
                        nextTimestep();
                    }} else {{
                        currentTimestepIndex = 0;
                        document.getElementById('ts-slider').value = 0;
                        updatePlot();
                    }}
                }}, 500);
            }} else {{
                btn.textContent = '▶ Play';
                if (playInterval) {{
                    clearInterval(playInterval);
                    playInterval = null;
                }}
            }}
        }}

        function toggleInjectors() {{
            showInjectors = document.getElementById('injectors-check').checked;
            updatePlot();
        }}

        // Event listeners
        document.getElementById('ts-slider').addEventListener('input', (e) => {{
            currentTimestepIndex = parseInt(e.target.value);
            updatePlot();
        }});

        document.getElementById('zscale-slider').addEventListener('input', (e) => {{
            document.getElementById('zscale-label').textContent = e.target.value;
            updatePlot();
        }});

        // Inicializar
        window.addEventListener('load', () => {{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('controls').style.display = 'block';
            
            const slider = document.getElementById('ts-slider');
            slider.max = DATA.timesteps.length - 1;
            
            updatePlot();
        }});
    </script>
</body>
</html>
"""


def render_co2_viewer_tab():
    """Renderiza la pestaña del viewer de CO₂."""
    st.header("🧊 CO₂ Optimized Viewer")
    st.caption("Viewer optimizado con un solo HTML y datos en JavaScript")

    threshold = st.sidebar.slider("Umbral mínimo YMFS", 0.0, 1.0, 0.10, 0.01)

    # Cargar datos
    with st.spinner("Cargando timesteps..."):
        ymfs_by_ts, ts_indices = load_all_timesteps()

    if not ts_indices:
        st.error("❌ No se encontraron archivos YMFS en timesteps_export/")
        return

    st.success(f"✅ {len(ts_indices)} timesteps cargados")

    # Preprocesar datos
    cache_file = CACHE_DIR / f"data_thr{threshold:.2f}.json"
    
    if cache_file.exists():
        with st.spinner("Cargando datos preprocesados..."):
            with open(cache_file, "r") as f:
                processed_data = json.load(f)
    else:
        with st.spinner("Preprocesando datos (solo la primera vez)..."):
            processed_data = preprocess_all_data(ymfs_by_ts, ts_indices, threshold)
            with open(cache_file, "w") as f:
                json.dump(processed_data, f)

    st.info(f"📊 Total de celdas activas en todos los timesteps: {sum(processed_data['data'][str(ts)]['count'] for ts in ts_indices)}")

    # Crear HTML
    html_content = create_viewer_html(json.dumps(processed_data))
    
    # Mostrar
    components.html(html_content, height=900, scrolling=False)


def main() -> None:
    # CSS y JavaScript para ocultar/mostrar sidebar
    st.markdown("""
    <style>
        /* Variables de color personalizadas */
        :root {
            --text: #eceef0;
            --background: #050606;
            --primary: #1d96e2;
            --secondary: #234b7c;
            --accent: #b83232;
        }
        
        /* Aplicar colores a la página principal */
        .stApp {
            background-color: var(--background) !important;
            color: var(--text) !important;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #080d12 !important;
            color: var(--text) !important;
        }
        
        /* Texto principal */
        .main .block-container,
        .main h1,
        .main h2,
        .main h3,
        .main p,
        .main div,
        .main span,
        .main label {
            color: var(--text) !important;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text) !important;
        }
        
        /* Botones */
        .stButton > button {
            background-color: var(--primary) !important;
            color: var(--text) !important;
            border: 1px solid var(--primary) !important;
        }
        
        .stButton > button:hover {
            background-color: var(--secondary) !important;
            border-color: var(--secondary) !important;
        }
        
        /* Sliders */
        .stSlider > div > div > div {
            background-color: var(--primary) !important;
        }
        
        /* Checkboxes */
        .stCheckbox > label {
            color: var(--text) !important;
        }
        
        /* Selectboxes */
        .stSelectbox > label {
            color: var(--text) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: var(--background) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: var(--text) !important;
        }
        
        .stTabs [aria-selected="true"] {
            color: var(--primary) !important;
        }
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background-color: var(--background) !important;
            color: var(--text) !important;
            border-color: var(--secondary) !important;
        }
        
        /* Captions y info boxes */
        .stCaption,
        .stInfo,
        .stSuccess,
        .stWarning,
        .stError {
            color: var(--text) !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-color: var(--primary) !important;
        }
        
        /* Botón para ocultar/mostrar sidebar */
        .sidebar-toggle {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 999;
            background-color: var(--secondary) !important;
            color: var(--text) !important;
            border: 1px solid var(--primary) !important;
            border-radius: 4px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .sidebar-toggle:hover {
            background-color: var(--primary) !important;
            border-color: var(--accent) !important;
        }
        
        /* Ocultar sidebar cuando tiene la clase 'hidden' */
        section[data-testid="stSidebar"][class*="hidden"] {
            display: none !important;
        }
        
        /* Ajustar el contenido principal cuando el sidebar está oculto */
        section[data-testid="stSidebar"][class*="hidden"] ~ div[data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
        }
        
        /* Estilo para el estado oculto */
        .sidebar-hidden section[data-testid="stSidebar"] {
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }
        
        /* Scrollbar personalizado */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--background);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--secondary);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
        }
    </style>
    
    <script>
        function toggleSidebar() {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const appContainer = document.querySelector('div[data-testid="stAppViewContainer"]');
            const mainContent = document.querySelector('div[data-testid="stAppViewContainer"] > div');
            const button = document.getElementById('sidebar-toggle-btn');
            
            if (sidebar) {
                const isHidden = sidebar.style.display === 'none' || sidebar.style.visibility === 'hidden';
                
                if (isHidden) {
                    // Mostrar sidebar
                    sidebar.style.display = '';
                    sidebar.style.visibility = '';
                    sidebar.style.transform = '';
                    if (appContainer) {
                        appContainer.style.marginLeft = '';
                    }
                    if (mainContent) {
                        mainContent.style.marginLeft = '';
                    }
                    if (button) {
                        button.textContent = '◀ Ocultar';
                        button.title = 'Ocultar Sidebar';
                    }
                } else {
                    // Ocultar sidebar
                    sidebar.style.display = 'none';
                    sidebar.style.visibility = 'hidden';
                    if (appContainer) {
                        appContainer.style.marginLeft = '0';
                    }
                    if (mainContent) {
                        mainContent.style.marginLeft = '0';
                    }
                    if (button) {
                        button.textContent = '▶ Mostrar';
                        button.title = 'Mostrar Sidebar';
                    }
                }
            }
        }
        
        // Crear botón flotante si no existe
        function createToggleButton() {
            if (!document.getElementById('sidebar-toggle-btn')) {
                const button = document.createElement('button');
                button.id = 'sidebar-toggle-btn';
                button.className = 'sidebar-toggle';
                button.textContent = '◀ Ocultar';
                button.title = 'Ocultar Sidebar';
                button.onclick = toggleSidebar;
                document.body.appendChild(button);
            }
        }
        
        // Intentar crear el botón cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createToggleButton);
        } else {
            createToggleButton();
        }
        
        // También intentar después de un pequeño delay para asegurar que Streamlit haya cargado
        setTimeout(createToggleButton, 500);
    </script>
    """, unsafe_allow_html=True)
    
    st.title("🌍 Visualizador 3D - CO₂ y Propiedades Geológicas")
    
    # Crear pestañas
    tab1, tab2 = st.tabs(["🧊 CO₂ Viewer", "🔬 Propiedades Geológicas"])
    
    with tab1:
        render_co2_viewer_tab()
    
    with tab2:
        render_geological_properties_tab()


if __name__ == "__main__":
    main()
