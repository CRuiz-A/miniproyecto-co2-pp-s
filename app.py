import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import plotly.graph_objects as go

st.set_page_config(
    page_title="GeoViz - Visualizador Geológico",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).parent
TIMESTEPS_DIR = BASE_DIR / "timesteps_export"
GEOSX_TIMESTEPS_DIR = BASE_DIR / "data" / "geosx" / "new_simulation" / "timesteps_export"
GEOSX_TIMESTEPS_DIR.mkdir(parents=True, exist_ok=True)
GEOSX_VTK_DIR = BASE_DIR / "data" / "geosx" / "new_simulation" / "timesteps_vtk"
GEOSX_VTK_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "outputs" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
GEOSX_DIR = BASE_DIR / "data" / "geosx"
BUNTER_DIR = BASE_DIR / "data" / "BUNTER"
SLEIPNER_DIR = BASE_DIR / "data" / "sleipner_data"


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
def load_vtk_ymfs(filepath: Path) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Carga datos YMFS y coordenadas desde un archivo VTK.
    
    Returns:
        Tuple de (ymfs_data, z_coords) o (None, None) si hay error
    """
    try:
        import pyvista as pv
        # Configurar para evitar problemas de OpenGL
        import os
        os.environ['PYVISTA_OFF_SCREEN'] = 'true'
        pv.OFF_SCREEN = True
        
        grid = pv.read(str(filepath))
        
        # Intentar obtener YMFS de cell_data o cell_arrays
        ymfs_data = None
        if hasattr(grid, 'cell_data') and 'YMFS' in grid.cell_data:
            ymfs_data = np.array(grid.cell_data['YMFS'])
        elif hasattr(grid, 'cell_arrays') and 'YMFS' in grid.cell_arrays:
            ymfs_data = np.array(grid.cell_arrays['YMFS'])
        elif hasattr(grid, 'point_data') and 'YMFS' in grid.point_data:
            ymfs_data = np.array(grid.point_data['YMFS'])
        elif hasattr(grid, 'point_arrays') and 'YMFS' in grid.point_arrays:
            ymfs_data = np.array(grid.point_arrays['YMFS'])
        
        # Obtener coordenadas Z reales de las celdas
        z_coords = None
        try:
            centers = grid.cell_centers()
            z_coords = centers.points[:, 2]  # Coordenada Z (depth)
        except:
            # Fallback: usar puntos del grid
            if hasattr(grid, 'points'):
                z_coords = grid.points[:, 2]
        
        if ymfs_data is not None and z_coords is not None:
            return ymfs_data, z_coords
        
        return None, None
    except Exception as e:
        print(f"Error al cargar VTK {filepath}: {e}")
        return None, None


@st.cache_data(show_spinner=False)
def load_all_timesteps_geosx() -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray], List[int]]:
    """Carga todos los timesteps YMFS y coordenadas Z del reservorio GEOSX desde VTK o GRDECL.
    
    Returns:
        Tuple de (ymfs_dict, z_coords_dict, timestep_indices)
    """
    data: Dict[int, np.ndarray] = {}
    z_coords_dict: Dict[int, np.ndarray] = {}
    indices: List[int] = []
    
    # Primero intentar cargar desde VTK (preferido)
    if GEOSX_VTK_DIR.exists():
        vtk_files = sorted(GEOSX_VTK_DIR.glob("ymfs_ts_*.vtk"))
        if vtk_files:
            for filepath in vtk_files:
                match = re.search(r"ts_(\d+)", filepath.name)
                if not match:
                    continue
                timestep = int(match.group(1))
                ymfs_data, z_coords = load_vtk_ymfs(filepath)
                if ymfs_data is not None and z_coords is not None:
                    data[timestep] = ymfs_data
                    z_coords_dict[timestep] = z_coords
                    indices.append(timestep)
            
            if indices:
                indices.sort()
                return data, z_coords_dict, indices
    
    # Si no hay VTK, intentar cargar desde GRDECL
    if GEOSX_TIMESTEPS_DIR.exists():
        grdecl_files = sorted(GEOSX_TIMESTEPS_DIR.glob("YMFS_ts_*.GRDECL"))
        for filepath in grdecl_files:
            match = re.search(r"ts_(\d+)", filepath.name)
            if not match:
                continue
            timestep = int(match.group(1))
            data[timestep] = read_grdecl_property(str(filepath))
            # Para GRDECL, no tenemos coordenadas Z, así que usamos None
            z_coords_dict[timestep] = None
            indices.append(timestep)
    
    indices.sort()
    return data, z_coords_dict, indices


@st.cache_data(show_spinner=False)
def preprocess_all_data_geosx(ymfs_dict: Dict[int, np.ndarray], z_coords_dict: Dict[int, np.ndarray], ts_indices: List[int], threshold: float) -> Dict:
    """Preprocesa todos los datos de GEOSX para JavaScript usando coordenadas reales del VTK."""
    if not ts_indices or not ymfs_dict:
        return {'timesteps': [], 'data': {}, 'injectors': {'vertices': [], 'faces': []}, 'grid': {}, 'bounds': {}}
    
    # Obtener dimensiones del primer timestep
    first_ts = ts_indices[0]
    first_data = ymfs_dict[first_ts]
    first_z_coords = z_coords_dict.get(first_ts)
    
    # Calcular dimensiones del grid basándose en el número total de celdas
    total_cells = len(first_data)
    
    # Intentar detectar dimensiones comunes o usar valores por defecto
    # Para GEOSX, vamos a usar dimensiones típicas o detectarlas
    # Si el número de celdas es un cubo perfecto o tiene factores comunes, usarlos
    # Por ahora, usaremos valores razonables basados en grids típicos
    # nx * ny * nz = total_cells
    
    # Dimensiones reales del grid GEOSX: 64 × 28 × 25 = 44800
    # Coordenadas reales basadas en las esquinas del grid:
    # Celda [1, 1, 1]: E: 27.03, N: 0.00, Depth: 2512.89
    # Celda [64, 1, 25]: E: 6308.94, N: 0.00, Depth: 2995.50
    # Celda [64, 28, 25]: E: 6400.00, N: 2741.59, Depth: 2991.94
    
    if total_cells == 44800:  # GEOSX: 64 × 28 × 25
        nx, ny, nz = 64, 28, 25
        # Coordenadas reales del grid GEOSX (verificadas desde archivos VTK)
        x_min, x_max = 0.0, 6000.0     # Este (E)
        y_min, y_max = 0.0, 2800.0     # Norte (N)
        
        # Usar coordenadas Z reales del VTK si están disponibles
        if first_z_coords is not None and len(first_z_coords) == total_cells:
            z_min_real = float(first_z_coords.min())
            z_max_real = float(first_z_coords.max())
            z_top, z_bottom = z_min_real, z_max_real
            use_real_z = True
        else:
            # Fallback a valores por defecto
            z_top, z_bottom = 2700.0, 2800.0  # Rango aproximado desde análisis
            use_real_z = False
    elif total_cells == 100000:  # 100x100x10
        nx, ny, nz = 100, 100, 10
        x_min, x_max = 0.0, float(nx * 100)
        y_min, y_max = 0.0, float(ny * 100)
        z_top, z_bottom = -2500.0, -2500.0 - float(nz * 20)
    elif total_cells == 450450:  # Bunter
        nx, ny, nz = 110, 63, 65
        x_min, x_max = 0.0, float(nx * 100)
        y_min, y_max = 0.0, float(ny * 100)
        z_top, z_bottom = -2500.0, -2500.0 - float(nz * 20)
    elif total_cells == 1986176:  # Sleipner
        nx, ny, nz = 263, 118, 64
        x_min, x_max = 0.0, float(nx * 100)
        y_min, y_max = 0.0, float(ny * 100)
        z_top, z_bottom = -2500.0, -2500.0 - float(nz * 20)
    else:
        # Intentar factorizar para encontrar dimensiones razonables
        # Por defecto, usar valores comunes
        nx, ny, nz = 100, 100, total_cells // (100 * 100) if total_cells >= 10000 else 10
        if nx * ny * nz != total_cells:
            # Ajustar para que coincida
            nz = max(1, total_cells // (nx * ny))
        x_min, x_max = 0.0, float(nx * 100)
        y_min, y_max = 0.0, float(ny * 100)
        z_top, z_bottom = -2500.0, -2500.0 - float(nz * 20)
    
    # Calcular tamaño de celdas (para nx celdas, necesitamos nx+1 puntos)
    # El tamaño de cada celda es el rango total dividido por el número de celdas
    cell_size_x = (x_max - x_min) / nx if nx > 0 else 100.0
    cell_size_y = (y_max - y_min) / ny if ny > 0 else 100.0
    cell_size_z = (z_bottom - z_top) / nz if nz > 0 else 20.0
    
    # Pozos inyectores (ajustar según el caso de GEOSX)
    # Por ahora, usar valores por defecto en el centro
    wells = [
        (x_min + (x_max - x_min) * 0.25, y_min + (y_max - y_min) * 0.25, z_top),
        (x_min + (x_max - x_min) * 0.75, y_min + (y_max - y_min) * 0.25, z_top),
        (x_min + (x_max - x_min) * 0.25, y_min + (y_max - y_min) * 0.75, z_top),
        (x_min + (x_max - x_min) * 0.75, y_min + (y_max - y_min) * 0.75, z_top),
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
    
    # Crear grilla completa una sola vez (usando el primer timestep como referencia)
    first_ts = ts_indices[0]
    first_z_coords_ts = z_coords_dict.get(first_ts)
    
    # Intentar obtener coordenadas completas (X, Y, Z) del VTK
    grid_cells = []  # Para visualizar toda la grilla (una sola vez, muy transparente)
    
    # Si tenemos coordenadas Z del VTK, intentar obtener también X e Y
    if first_z_coords_ts is not None and len(first_z_coords_ts) == total_cells:
        # Cargar el VTK para obtener todas las coordenadas
        try:
            import pyvista as pv
            import os
            os.environ['PYVISTA_OFF_SCREEN'] = 'true'
            pv.OFF_SCREEN = True
            
            vtk_file = GEOSX_VTK_DIR / f"ymfs_ts_{first_ts:04d}.vtk"
            if vtk_file.exists():
                grid_vtk = pv.read(str(vtk_file))
                centers = grid_vtk.cell_centers()
                coords_all = centers.points  # Array de (n_cells, 3) con [x, y, z]
                
                # Usar coordenadas reales del VTK directamente
                for idx in range(min(total_cells, len(coords_all))):
                    grid_cells.append({
                        'x': float(coords_all[idx, 0]),
                        'y': float(coords_all[idx, 1]),
                        'z': float(coords_all[idx, 2]),
                        'value': 0.0
                    })
                
                # Si faltan celdas, completar con cálculo
                if len(grid_cells) < total_cells:
                    for idx in range(len(grid_cells), total_cells):
                        k = idx // (nx * ny)
                        j = (idx % (nx * ny)) // nx
                        i = idx % nx
                        x = x_min + (i + 0.5) * cell_size_x
                        y = y_min + (j + 0.5) * cell_size_y
                        z = z_top + (k + 0.5) * cell_size_z
                        grid_cells.append({
                            'x': float(x),
                            'y': float(y),
                            'z': float(z),
                            'value': 0.0
                        })
            else:
                raise FileNotFoundError(f"VTK file not found: {vtk_file}")
        except Exception as e:
            print(f"⚠️ No se pudieron cargar coordenadas completas del VTK: {e}")
            # Fallback: calcular coordenadas
            use_real_coords_grid = False
    else:
        use_real_coords_grid = False
    
    # Si no se pudieron cargar coordenadas del VTK, calcularlas
    if len(grid_cells) == 0:
        # Calcular coordenadas para todas las celdas
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    idx = i + j * nx + k * nx * ny
                    if idx >= total_cells:
                        continue
                    
                    x = x_min + (i + 0.5) * cell_size_x
                    y = y_min + (j + 0.5) * cell_size_y
                    
                    # Usar coordenada Z real si está disponible
                    if first_z_coords_ts is not None and idx < len(first_z_coords_ts):
                        z = float(first_z_coords_ts[idx])
                    else:
                        z = z_top + (k + 0.5) * cell_size_z
                    
                    grid_cells.append({
                        'x': float(x),
                        'y': float(y),
                        'z': float(z),
                        'value': 0.0
                    })
    
    # Datos por timestep (solo índices y valores de celdas > threshold)
    timestep_data = {}
    
    for ts in ts_indices:
        ymfs_values = ymfs_dict[ts]
        z_coords_ts = z_coords_dict.get(ts)
        use_real_coords_ts = (z_coords_ts is not None and len(z_coords_ts) == len(ymfs_values))
        
        total = nx * ny * nz
        if len(ymfs_values) < total:
            padded = np.zeros(total, dtype=float)
            padded[:len(ymfs_values)] = ymfs_values
            ymfs_values = padded
        elif len(ymfs_values) > total:
            ymfs_values = ymfs_values[:total]
        
        # Solo guardamos índices de celdas activas (> threshold)
        active_cells = []
        
        # Procesar todas las celdas usando las coordenadas de la grilla
        for idx in range(len(ymfs_values)):
            value = ymfs_values[idx]
            
            # Usar coordenadas de la grilla ya calculadas
            grid_cell = grid_cells[idx]
            x = grid_cell['x']
            y = grid_cell['y']
            
            # Si tenemos coordenadas Z reales para este timestep, usarlas
            if use_real_coords_ts:
                z = float(z_coords_ts[idx])
            else:
                z = grid_cell['z']
            
            # Guardar solo celdas activas (> threshold)
            if value >= threshold:
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
    
    # Calcular bounds reales desde las coordenadas Z
    if first_z_coords is not None and len(first_z_coords) > 0:
        z_min_real = float(first_z_coords.min())
        z_max_real = float(first_z_coords.max())
    else:
        z_min_real = z_top
        z_max_real = z_bottom
    
    return {
        'timesteps': ts_indices,
        'data': timestep_data,
        'grid_cells': grid_cells,  # Todas las celdas de la grilla para visualización transparente
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
            'z': [float(z_min_real), float(z_max_real)]
        }
    }


@st.cache_data(show_spinner=False)
def preprocess_all_data(ymfs_dict: Dict[int, np.ndarray], ts_indices: List[int], threshold: float) -> Dict:
    """Preprocesa todos los datos para JavaScript (Bunter)."""
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


@st.cache_data(show_spinner=False)
def load_bunter_data() -> Optional[Dict[str, np.ndarray]]:
    """Carga los datos del reservorio BUNTER desde archivo NPZ."""
    npz_file = BUNTER_DIR / "bunter_data.npz"
    if not npz_file.exists():
        return None
    
    data = np.load(npz_file)
    return {
        'facies': data['facies'],
        'permeability': data['permeability'],
        'porosity': data['porosity']
    }


@st.cache_data(show_spinner=False)
def load_sleipner_data() -> Optional[Dict[str, np.ndarray]]:
    """Carga los datos del reservorio Sleipner desde archivo NPZ."""
    npz_file = SLEIPNER_DIR / "sleipner_data.npz"
    if not npz_file.exists():
        return None
    
    data = np.load(npz_file)
    return {
        'facies': data['facies'],
        'permeability': data['permeability'],
        'porosity': data['porosity']
    }


def prepare_3d_data(data: np.ndarray) -> np.ndarray:
    """Prepara los datos para visualización 3D. Si son 4D, toma el primer slice temporal."""
    if len(data.shape) == 4:
        return data[0]
    elif len(data.shape) == 3:
        return data
    else:
        raise ValueError(f"Forma de datos no soportada: {data.shape}")


def render_reservoir_data_tab(reservoir_name: str, data_dict: Dict[str, np.ndarray]):
    """Renderiza visualizaciones para un reservorio específico (BUNTER o Sleipner)."""
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            Datos del Reservorio {reservoir_name}
        </h2>
        <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
            Visualización 3D de propiedades geológicas
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener dimensiones
    facies_shape = data_dict['facies'].shape
    nz, ny, nx = facies_shape
    
    # Métricas del reservorio
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Dimensiones (X×Y×Z)</div>
            <div class="metric-value" style="font-size: 1.2rem;">{nx}×{ny}×{nz}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_cells = nx * ny * nz
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total de Celdas</div>
            <div class="metric-value" style="font-size: 1.2rem;">{total_cells:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_facies = len(np.unique(data_dict['facies']))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Facies Únicas</div>
            <div class="metric-value" style="font-size: 1.2rem;">{unique_facies}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        poro_mean = np.mean(data_dict['porosity'][data_dict['porosity'] > 0])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Porosidad Media</div>
            <div class="metric-value" style="font-size: 1.2rem;">{poro_mean:.3f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Modo de visualización
    view_mode = st.radio(
        "Modo de visualización",
        options=["Paralelo (3 propiedades)", "Individual"],
        horizontal=True,
        help="Vista paralela: 3 gráficos simultáneos | Vista individual: una propiedad a la vez"
    )
    
    # Controles de cortes en sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 🎮 Controles - {reservoir_name}")
        
        x_slice = st.slider(
            "Corte X (plano YZ)",
            min_value=0,
            max_value=nx - 1,
            value=nx // 2,
            help="Índice para el corte en dirección X"
        )
        
        y_slice = st.slider(
            "Corte Y (plano XZ)",
            min_value=0,
            max_value=ny - 1,
            value=ny // 2,
            help="Índice para el corte en dirección Y"
        )
        
        z_slice = st.slider(
            "Corte Z (plano XY)",
            min_value=0,
            max_value=nz - 1,
            value=nz // 2,
            help="Índice para el corte en dirección Z"
        )
    
    if view_mode == "Paralelo (3 propiedades)":
        # Vista paralela
        col1, col2, col3 = st.columns(3)
        
        # Permeabilidad
        with col1:
            st.markdown("#### 🔴 Permeabilidad")
            with st.spinner("Generando..."):
                fig_perm = create_3d_slices_plotly(
                    data_dict['permeability'],
                    x_slice=x_slice,
                    y_slice=y_slice,
                    z_slice=z_slice,
                    colormap='Hot',
                    log_scale=True,
                    title="Permeabilidad",
                    colorbar_title="log10(Permeabilidad mD)"
                )
                st.plotly_chart(fig_perm, use_container_width=True)
        
        # Porosidad
        with col2:
            st.markdown("#### 🟢 Porosidad")
            with st.spinner("Generando..."):
                fig_poro = create_3d_slices_plotly(
                    data_dict['porosity'],
                    x_slice=x_slice,
                    y_slice=y_slice,
                    z_slice=z_slice,
                    colormap='Viridis',
                    log_scale=False,
                    title="Porosidad",
                    colorbar_title="Porosidad (fracción)"
                )
                st.plotly_chart(fig_poro, use_container_width=True)
        
        # Facies
        with col3:
            st.markdown("#### 🟡 Facies")
            with st.spinner("Generando..."):
                # Para facies, usar visualización especial
                if unique_facies <= 3:
                    fig_facies = create_3d_slices_facies(
                        data_dict['facies'],
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        title="Facies"
                    )
                else:
                    # Para muchas facies, usar colormap continuo
                    fig_facies = create_3d_slices_plotly(
                        data_dict['facies'].astype(float),
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        colormap='Turbo',
                        log_scale=False,
                        title="Facies",
                        colorbar_title="Facies ID"
                    )
                st.plotly_chart(fig_facies, use_container_width=True)
                
                # Estadísticas de facies
                facies_unique, facies_counts = np.unique(data_dict['facies'], return_counts=True)
                facies_info = " | ".join([f"Facies {fid}: {count:,} ({100*count/facies_shape[0]/facies_shape[1]/facies_shape[2]:.1f}%)" 
                                         for fid, count in zip(facies_unique, facies_counts)])
                st.caption(facies_info)
    
    else:
        # Vista individual
        selected_property = st.selectbox(
            "Seleccionar propiedad",
            options=['permeability', 'porosity', 'facies'],
            format_func=lambda x: x.title()
        )
        
        data_3d = data_dict[selected_property]
        
        if selected_property == 'permeability':
            with st.spinner("Generando visualización..."):
                fig = create_3d_slices_plotly(
                    data_3d,
                    x_slice=x_slice,
                    y_slice=y_slice,
                    z_slice=z_slice,
                    colormap='Hot',
                    log_scale=True,
                    title=f"{reservoir_name} - Permeabilidad",
                    colorbar_title="log10(Permeabilidad mD)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif selected_property == 'porosity':
            with st.spinner("Generando visualización..."):
                fig = create_3d_slices_plotly(
                    data_3d,
                    x_slice=x_slice,
                    y_slice=y_slice,
                    z_slice=z_slice,
                    colormap='Viridis',
                    log_scale=False,
                    title=f"{reservoir_name} - Porosidad",
                    colorbar_title="Porosidad (fracción)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:  # facies
            unique_facies_count = len(np.unique(data_3d))
            with st.spinner("Generando visualización..."):
                if unique_facies_count <= 3:
                    fig = create_3d_slices_facies(
                        data_3d,
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        title=f"{reservoir_name} - Facies"
                    )
                else:
                    fig = create_3d_slices_plotly(
                        data_3d.astype(float),
                        x_slice=x_slice,
                        y_slice=y_slice,
                        z_slice=z_slice,
                        colormap='Turbo',
                        log_scale=False,
                        title=f"{reservoir_name} - Facies",
                        colorbar_title="Facies ID"
                    )
                st.plotly_chart(fig, use_container_width=True)
        
        # Información adicional
        with st.expander("ℹ️ Información"):
            st.write(f"""
            **Datos del reservorio {reservoir_name}:**
            - Dimensiones: {nz} × {ny} × {nx} (Z × Y × X)
            - Total de celdas: {nx * ny * nz:,}
            - Propiedad: {selected_property.title()}
            - Corte X (plano YZ): Índice {x_slice}/{nx-1}
            - Corte Y (plano XZ): Índice {y_slice}/{ny-1}
            - Corte Z (plano XY): Índice {z_slice}/{nz-1}
            """)
            
            if selected_property == 'permeability':
                perm_data = data_dict['permeability']
                perm_valid = perm_data[perm_data > 0]
                st.write(f"""
                **Estadísticas de Permeabilidad:**
                - Mínimo: {perm_valid.min():.4f} mD
                - Máximo: {perm_valid.max():.4f} mD
                - Media: {perm_valid.mean():.4f} mD
                - Mediana: {np.median(perm_valid):.4f} mD
                """)
            
            elif selected_property == 'porosity':
                poro_data = data_dict['porosity']
                poro_valid = poro_data[poro_data > 0]
                st.write(f"""
                **Estadísticas de Porosidad:**
                - Mínimo: {poro_valid.min():.6f}
                - Máximo: {poro_valid.max():.6f}
                - Media: {poro_valid.mean():.6f}
                - Mediana: {np.median(poro_valid):.6f}
                """)
            
            elif selected_property == 'facies':
                facies_unique, facies_counts = np.unique(data_dict['facies'], return_counts=True)
                st.write("**Distribución de Facies:**")
                for fid, count in zip(facies_unique, facies_counts):
                    percentage = 100 * count / (nx * ny * nz)
                    st.write(f"- Facies {int(fid)}: {count:,} celdas ({percentage:.2f}%)")


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
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            Propiedades Geológicas
        </h2>
        <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
            Visualización 3D de permeabilidad, porosidad y facies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
            
            // SIEMPRE agregar grilla completa transparente (debe cubrir toda la dimensión)
            if (DATA.grid_cells && DATA.grid_cells.length > 0) {{
                const gridMesh = buildMesh(DATA.grid_cells, {{
                    x: cellSize.cell_size_x,
                    y: cellSize.cell_size_y,
                    z: cellSize.cell_size_z
                }});
                
                // Renderizar la grilla SIEMPRE, sin importar si hay YMFS o no
                if (gridMesh.x.length > 0) {{
                    traces.push({{
                        type: 'mesh3d',
                        x: gridMesh.x, y: gridMesh.y, z: gridMesh.z,
                        i: gridMesh.i, j: gridMesh.j, k: gridMesh.k,
                        color: '#3984c6',  // Azul sólido
                        opacity: 0.08,  // Muy transparente pero visible
                        flatshading: true,
                        showscale: false,
                        lighting: {{
                            ambient: 1.0,
                            diffuse: 0.1,
                            specular: 0.0
                        }},
                        name: 'Grid',
                        hovertemplate: 'Grid Cell<extra></extra>',
                        visible: true  // Siempre visible
                    }});
                }}
            }}
            
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
            
            // Calcular proporciones reales basadas en los bounds
            const xRange = DATA.bounds.x[1] - DATA.bounds.x[0];
            const yRange = DATA.bounds.y[1] - DATA.bounds.y[0];
            const zRange = DATA.bounds.z[1] - DATA.bounds.z[0];
            
            // Normalizar usando el rango máximo para mantener proporciones reales
            const maxRange = Math.max(xRange, yRange, zRange);
            const aspectX = xRange / maxRange;
            const aspectY = yRange / maxRange;
            const aspectZ = (zRange / maxRange) * zScale;
            
            const layout = {{
                title: `CO₂ (YMFS) - Timestep ${{ts}}`,
                scene: {{
                    xaxis: {{ title: 'X (m)', range: DATA.bounds.x }},
                    yaxis: {{ title: 'Y (m)', range: DATA.bounds.y }},
                    zaxis: {{ title: 'Z (m)', range: DATA.bounds.z }},
                    aspectmode: 'manual',
                    aspectratio: {{ x: aspectX, y: aspectY, z: aspectZ }},
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


def render_co2_viewer_tab_geosx():
    """Renderiza la pestaña del viewer de CO₂ para GEOSX."""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            Visualizador CO₂ - Reservorio GEOSX
        </h2>
        <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
            Simulación interactiva de la pluma de CO₂ en el reservorio GEOSX
        </p>
    </div>
    """, unsafe_allow_html=True)

    threshold = st.sidebar.slider("Umbral mínimo YMFS", 0.0, 1.0, 0.10, 0.01, key="geosx_threshold")

    # Cargar datos
    with st.spinner("Cargando timesteps de GEOSX..."):
        ymfs_by_ts, z_coords_dict, ts_indices = load_all_timesteps_geosx()

    if not ts_indices:
        st.error("❌ No se encontraron archivos YMFS de GEOSX")
        st.info(f"Buscando en:")
        st.info(f"  • VTK: {GEOSX_VTK_DIR}")
        st.info(f"  • GRDECL: {GEOSX_TIMESTEPS_DIR}")
        st.markdown("""
        <div style="background: rgba(57, 132, 198, 0.1); border: 1px solid rgba(57, 132, 198, 0.3); 
                    border-radius: 0.5rem; padding: 1rem; margin-top: 1rem;">
            <h4 style="color: var(--primary); margin-bottom: 0.5rem;">💡 Pasos para exportar datos:</h4>
            <ol style="color: var(--text-secondary-dark); margin-left: 1.5rem;">
                <li>Abre ResInsight y carga el archivo <code>DEP_GAS.EGRID</code></li>
                <li>Ejecuta el script de exportación:
                    <pre style="background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 0.25rem; margin-top: 0.5rem;">
python scripts/export_ymfs_geosx_to_vtk.py</pre>
                </li>
                <li>El script exportará YMFS desde ResInsight y lo convertirá a VTK</li>
                <li>Los archivos VTK se guardarán en: <code>data/geosx/new_simulation/timesteps_vtk/</code></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    st.success(f"✅ {len(ts_indices)} timesteps de GEOSX cargados")

    # Preprocesar datos
    cache_file = CACHE_DIR / f"geosx_data_thr{threshold:.2f}.json"
    
    if cache_file.exists():
        with st.spinner("Cargando datos preprocesados..."):
            with open(cache_file, "r") as f:
                processed_data = json.load(f)
    else:
        with st.spinner("Preprocesando datos de GEOSX (solo la primera vez)..."):
            processed_data = preprocess_all_data_geosx(ymfs_by_ts, z_coords_dict, ts_indices, threshold)
            with open(cache_file, "w") as f:
                json.dump(processed_data, f)

    # Métricas en tarjetas
    total_cells = sum(processed_data['data'][str(ts)]['count'] for ts in ts_indices)
    max_cells = max(processed_data['data'][str(ts)]['count'] for ts in ts_indices)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Timesteps Totales</div>
            <div class="metric-value">{len(ts_indices)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Celdas Activas (Total)</div>
            <div class="metric-value">{total_cells:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Máx. Celdas (ts)</div>
            <div class="metric-value">{max_cells:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Umbral YMFS</div>
            <div class="metric-value">{threshold:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Crear HTML
    html_content = create_viewer_html(json.dumps(processed_data))
    
    # Mostrar
    components.html(html_content, height=900, scrolling=False)


def render_co2_viewer_tab():
    """Renderiza la pestaña del viewer de CO₂."""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            Visualizador CO₂
        </h2>
        <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
            Simulación interactiva de la pluma de CO₂ en el reservorio
        </p>
    </div>
    """, unsafe_allow_html=True)

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

    # Métricas en tarjetas
    total_cells = sum(processed_data['data'][str(ts)]['count'] for ts in ts_indices)
    max_cells = max(processed_data['data'][str(ts)]['count'] for ts in ts_indices)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Timesteps Totales</div>
            <div class="metric-value">{len(ts_indices)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Celdas Activas (Total)</div>
            <div class="metric-value">{total_cells:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Máx. Celdas (ts)</div>
            <div class="metric-value">{max_cells:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Umbral YMFS</div>
            <div class="metric-value">{threshold:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Crear HTML
    html_content = create_viewer_html(json.dumps(processed_data))
    
    # Mostrar
    components.html(html_content, height=900, scrolling=False)


def apply_geoviz_theme():
    """Aplica el tema GeoViz personalizado."""
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    
    <style>
        /* Import Space Grotesk */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        
        /* Material Symbols */
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            font-size: 24px;
            vertical-align: middle;
        }
        
        /* GeoViz Color Palette */
        :root {
            --primary: #3984c6;
            --background-light: #f6f7f8;
            --background-dark: #13191f;
            --surface-light: #ffffff;
            --surface-dark: #1b232b;
            --text-primary-light: #18181b;
            --text-primary-dark: #f8fafc;
            --text-secondary-light: #64748b;
            --text-secondary-dark: #9bafbf;
            --border-light: #e2e8f0;
            --border-dark: #3c4e5d;
        }
        
        /* Global Styles */
        * {
            font-family: 'Space Grotesk', sans-serif !important;
        }
        
        .stApp {
            background-color: var(--background-dark) !important;
            color: var(--text-primary-dark) !important;
        }
        
        /* Main Content Area */
        .main .block-container {
            padding: 2rem 3rem !important;
            max-width: 100% !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-primary-dark) !important;
            font-weight: 700 !important;
        }
        
        h1 {
            font-size: 2.5rem !important;
            font-weight: 900 !important;
            letter-spacing: -0.033em !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--surface-dark) !important;
            border-right: 1px solid var(--border-dark) !important;
        }
        
        section[data-testid="stSidebar"] > div {
            padding: 1.5rem !important;
        }
        
        /* Sidebar Text */
        section[data-testid="stSidebar"] .element-container,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: var(--text-primary-dark) !important;
        }
        
        /* Glass Card Effect */
        .glass-card {
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 1rem !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            transition: all 0.3s ease !important;
        }
        
        .glass-card:hover {
            border-color: rgba(57, 132, 198, 0.5) !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Tarjetas clickeables */
        .glass-card.clickable {
            cursor: pointer !important;
        }
        
        .glass-card.clickable:hover {
            border-color: rgba(57, 132, 198, 0.8) !important;
            box-shadow: 0 20px 50px rgba(57, 132, 198, 0.4) !important;
        }
        
        .glass-card.clickable:active {
            transform: translateY(0px) !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: var(--primary) !important;
            color: white !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.625rem 1rem !important;
            font-weight: 700 !important;
            font-size: 0.875rem !important;
            letter-spacing: 0.015em !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #2d6ba0 !important;
            box-shadow: 0 4px 12px rgba(57, 132, 198, 0.4) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Radio Buttons */
        .stRadio > label {
            color: var(--text-primary-dark) !important;
            font-weight: 500 !important;
        }
        
        .stRadio > div {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border-radius: 0.5rem !important;
            padding: 0.5rem !important;
        }
        
        /* Sliders */
        .stSlider > label {
            color: var(--text-primary-dark) !important;
            font-weight: 500 !important;
            font-size: 1rem !important;
        }
        
        .stSlider [data-baseweb="slider"] {
            background-color: var(--border-dark) !important;
        }
        
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background-color: var(--primary) !important;
            border: 4px solid var(--surface-dark) !important;
            box-shadow: 0 0 0 1px var(--primary) !important;
        }
        
        .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
            background-color: var(--primary) !important;
            color: white !important;
            font-weight: 600 !important;
        }
        
        /* Selectbox */
        .stSelectbox > label {
            color: var(--text-primary-dark) !important;
            font-weight: 500 !important;
        }
        
        .stSelectbox > div > div {
            background-color: var(--surface-dark) !important;
            border: 1px solid var(--border-dark) !important;
            color: var(--text-primary-dark) !important;
        }
        
        /* Checkbox */
        .stCheckbox > label {
            color: var(--text-primary-dark) !important;
        }
        
        .stCheckbox input[type="checkbox"]:checked {
            background-color: var(--primary) !important;
            border-color: var(--primary) !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background-color: transparent !important;
            border-bottom: 2px solid var(--border-dark) !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            background-color: transparent !important;
            border-radius: 0.5rem 0.5rem 0 0 !important;
            color: var(--text-secondary-dark) !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0 1.5rem !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(57, 132, 198, 0.1) !important;
            color: var(--primary) !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: rgba(57, 132, 198, 0.2) !important;
            color: var(--primary) !important;
            border-bottom: 2px solid var(--primary) !important;
        }
        
        /* Info/Success/Warning/Error boxes */
        .stAlert {
            background-color: rgba(57, 132, 198, 0.1) !important;
            border: 1px solid rgba(57, 132, 198, 0.3) !important;
            border-radius: 0.5rem !important;
            color: var(--text-primary-dark) !important;
        }
        
        /* Captions */
        .stCaption {
            color: var(--text-secondary-dark) !important;
            font-size: 0.875rem !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 0.5rem !important;
            color: var(--text-primary-dark) !important;
            font-weight: 500 !important;
        }
        
        .streamlit-expanderHeader:hover {
            background-color: rgba(57, 132, 198, 0.1) !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: var(--primary) !important;
        }
        
        /* Plotly charts background */
        .js-plotly-plot {
            background-color: transparent !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--background-dark);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-dark);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
        }
        
        /* Custom Card Component */
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            border-color: rgba(57, 132, 198, 0.5);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transform: translateY(-2px);
        }
        
        .metric-title {
            color: var(--text-secondary-dark);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: var(--text-primary-dark);
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }
        
        /* Status indicator */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--primary);
            font-weight: 500;
            font-size: 1rem;
        }
        
        .status-dot {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background-color: var(--primary);
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
    </style>
    <script>
        // Esperar a que el DOM esté listo
        function setupClickableCards() {
            // Tarjeta 1: Gas Vaciado -> Bunter
            const card1 = document.getElementById('card-gas-vaciado');
            if (card1 && !card1.hasAttribute('data-listener-attached')) {
                card1.setAttribute('data-listener-attached', 'true');
                card1.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Buscar el botón por data attribute
                    const button = document.querySelector('button[data-nav-target="bunter"]');
                    if (button) {
                        button.click();
                } else {
                        // Fallback: buscar por texto
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if ((btn.textContent || '').trim() === 'Ir a Bunter') {
                                btn.click();
                                break;
                            }
                        }
                    }
                });
            }
            
            // Tarjeta 2: Sleipner -> Sleipner
            const card2 = document.getElementById('card-sleipner');
            if (card2 && !card2.hasAttribute('data-listener-attached')) {
                card2.setAttribute('data-listener-attached', 'true');
                card2.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Buscar el botón por data attribute
                    const button = document.querySelector('button[data-nav-target="sleipner"]');
                    if (button) {
                        button.click();
                    } else {
                        // Fallback: buscar por texto
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if ((btn.textContent || '').trim() === 'Ir a Sleipner') {
                                btn.click();
                                break;
                            }
                        }
                    }
                });
            }
            
            // Tarjeta 3: Geos -> Propiedades
            const card3 = document.getElementById('card-geos');
            if (card3 && !card3.hasAttribute('data-listener-attached')) {
                card3.setAttribute('data-listener-attached', 'true');
                card3.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Buscar el botón por data attribute
                    const button = document.querySelector('button[data-nav-target="propiedades"]');
                    if (button) {
                        button.click();
                    } else {
                        // Fallback: buscar por texto
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if ((btn.textContent || '').trim() === 'Ir a Propiedades') {
                                btn.click();
                                break;
                            }
                        }
                    }
                });
            }
        }
        
        // Ejecutar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupClickableCards);
        } else {
            setupClickableCards();
        }
        
        // También ejecutar después de que Streamlit cargue
        setTimeout(setupClickableCards, 100);
        setTimeout(setupClickableCards, 500);
        setTimeout(setupClickableCards, 1000);
        setTimeout(setupClickableCards, 2000);
        setTimeout(setupClickableCards, 3000);
        
        // Observar cambios en el DOM
        const observer = new MutationObserver(function(mutations) {
            setupClickableCards();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    </script>
    """, unsafe_allow_html=True)
    

def render_sidebar():
    """Renderiza el sidebar con navegación y controles."""
    with st.sidebar:
        # Logo y título
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #3984c6 0%, #2d6ba0 100%); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 20px; font-weight: 700;">G</span>
            </div>
            <div>
                <h1 style="margin: 0; font-size: 1rem; font-weight: 700;">GeoViz</h1>
                <p style="margin: 0; font-size: 0.875rem; color: var(--text-secondary-dark);">CO₂ Reservoirs</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navegación
        st.markdown("### 📍 Navegación")
        
        # Determinar índice inicial basado en session_state
        options = ["🏠 Inicio", "🗺️ Bunter", "💧 Sleipner", "📊 Simulaciones", "🔬 Propiedades", "📚 Referencias"]
        default_index = 0
        
        if 'navigate_to' in st.session_state and st.session_state.navigate_to:
            if st.session_state.navigate_to in options:
                default_index = options.index(st.session_state.navigate_to)
        
        page = st.radio(
            "Seleccionar vista",
            options=options,
            index=default_index,
            label_visibility="collapsed",
            key="main_navigation"
        )
        
        # Limpiar navigate_to después de usar
        if 'navigate_to' in st.session_state:
            st.session_state.navigate_to = None
        
        st.divider()
        
        return page


def render_references_page():
    """Renderiza la página de referencias."""
    st.markdown("""
    <h1 style="color: var(--text-primary-dark); font-size: 2.5rem; font-weight: 900; 
               letter-spacing: -0.033em; margin-bottom: 0.5rem;">
        📚 Referencias
    </h1>
    <p style="color: var(--text-secondary-dark); font-size: 1rem; margin-bottom: 3rem;">
        Bibliografía y recursos relacionados con el almacenamiento de CO₂ y visualización geológica.
    </p>
    """, unsafe_allow_html=True)
    
    # Bibliografía
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); 
                border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; 
                padding: 2rem; margin-bottom: 2rem;">
        <h2 style="color: var(--text-primary-dark); font-size: 1.5rem; font-weight: 700; 
                   margin-bottom: 1.5rem;">Bibliografía</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Almacenamiento de CO₂
    st.markdown("#### Almacenamiento de CO₂ en Reservorios")
    st.markdown("""
    **Bachu, S.** (2008). CO₂ storage in geological media: Role, means, status and barriers to deployment. 
    *Progress in Energy and Combustion Science*, 34(2), 254-273.
    """)
    st.markdown("""
    **IPCC** (2005). *IPCC Special Report on Carbon Dioxide Capture and Storage*. 
    Cambridge University Press, Cambridge, United Kingdom and New York, NY, USA.
    """)
    
    st.markdown("---")
    
    # Proyecto Sleipner
    st.markdown("#### Proyecto Sleipner")
    st.markdown("""
    **Chadwick, R. A., et al.** (2010). Quantitative analysis of time-lapse seismic monitoring data at the Sleipner CO₂ storage operation. 
    *The Leading Edge*, 29(2), 170-177.
    """)
    st.markdown("""
    **Hansen, O., et al.** (2005). Snøhvit: The history of injecting and storing 1 Mt CO₂ in the fluvial Tubåen Fm. 
    *Energy Procedia*, 1(1), 2557-2564.
    """)
    st.markdown("""
    **Sleipner 2019 Benchmark Model** - Dataset de referencia del sitio de almacenamiento de CO₂ Sleipner. 
    Disponible en: [CO2DataShare - Sleipner 2019 Benchmark Model](https://co2datashare.org/dataset/sleipner-2019-benchmark-model)
    """)
    
    st.markdown("---")
    
    # Visualización y Modelado
    st.markdown("#### Visualización y Modelado Geológico")
    st.markdown("""
    **PyVista** - Herramienta de visualización 3D para Python. 
    Disponible en: [https://docs.pyvista.org/](https://docs.pyvista.org/)
    """)
    st.markdown("""
    **Plotly** - Biblioteca de visualización interactiva. 
    Disponible en: [https://plotly.com/python/](https://plotly.com/python/)
    """)
    st.markdown("""
    **Streamlit** - Framework para aplicaciones web en Python. 
    Disponible en: [https://streamlit.io/](https://streamlit.io/)
    """)
    st.markdown("""
    **ResInsight** - Herramienta de visualización para simulaciones de reservorios. 
    Disponible en: [https://resinsight.org/](https://resinsight.org/)
    """)
    st.markdown("""
    **3DFNO_GCS** - Repositorio de código para modelado rápido de almacenamiento de carbono geológico a gran escala usando FNO (Fourier Neural Operator). 
    Disponible en: [GitHub - 3DFNO_GCS](https://github.com/qingkaikong/3DFNO_GCS)
    """)
    st.markdown("""
    **clastic_shelf_GEOS** - Repositorio relacionado con modelado geológico usando GEOS. 
    Disponible en: [GitHub - clastic_shelf_GEOS](https://github.com/tang39/clastic_shelf_GEOS)
    """)
    
    st.markdown("---")
    
    # Recursos Adicionales
    st.markdown("#### Recursos Adicionales")
    st.markdown("""
    - Global CCS Institute - [https://www.globalccsinstitute.com/](https://www.globalccsinstitute.com/)
    - IEA Greenhouse Gas R&D Programme - [https://ieaghg.org/](https://ieaghg.org/)
    - Carbon Capture and Storage Association - [https://www.ccsassociation.org/](https://www.ccsassociation.org/)
    - BGS National Geoscience Data Centre - [https://webapps.bgs.ac.uk/services/ngdc/accessions/index.html#](https://webapps.bgs.ac.uk/services/ngdc/accessions/index.html#)
    """)


def render_home_page():
    """Renderiza la página de inicio."""
    st.markdown("""
    <h1 style="color: var(--text-primary-dark); font-size: 2.5rem; font-weight: 900; 
               letter-spacing: -0.033em; margin-bottom: 0.5rem;">
        Bienvenido al Visualizador Geológico
    </h1>
    <p style="color: var(--text-secondary-dark); font-size: 1rem; margin-bottom: 3rem;">
        Seleccione un tipo de reservorio para comenzar a explorar los datos.
    </p>
    """, unsafe_allow_html=True)
    
    # Inicializar session_state para navegación
    if 'navigate_to' not in st.session_state:
        st.session_state.navigate_to = None
    
    # Crear 3 columnas para las tarjetas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div id="card-gas-vaciado" class="glass-card clickable" title="Click para ir a Reservorio Bunter">
            <div style="margin-bottom: 1.5rem;">
                <span class="material-symbols-outlined" style="font-size: 3rem; color: var(--primary); 
                      font-variation-settings: 'FILL' 1, 'wght' 300;">gas_meter</span>
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 700; margin-bottom: 0.5rem;">
                Reservorios de Gas Vaciado
            </h3>
            <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
                Análisis de campos de gas agotados para el almacenamiento de CO₂.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div id="card-sleipner" class="glass-card clickable" title="Click para ir a Reservorio Sleipner">
            <div style="margin-bottom: 1.5rem;">
                <span class="material-symbols-outlined" style="font-size: 3rem; color: var(--primary); 
                      font-variation-settings: 'FILL' 1, 'wght' 300;">waves</span>
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 700; margin-bottom: 0.5rem;">
                Sleipner (Acuífero Salino)
            </h3>
            <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
                Proyecto pionero de almacenamiento de CO₂ en el Mar del Norte desde 1996.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div id="card-geos" class="glass-card clickable" title="Click para ir a Propiedades Geológicas">
            <div style="margin-bottom: 1.5rem;">
                <span class="material-symbols-outlined" style="font-size: 3rem; color: var(--primary); 
                      font-variation-settings: 'FILL' 1, 'wght' 300;">layers</span>
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 700; margin-bottom: 0.5rem;">
                Otros Yacimientos (Geos)
            </h3>
            <p style="color: var(--text-secondary-dark); font-size: 0.875rem;">
                Evaluación de otras formaciones geológicas para la captura de carbono.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Botones invisibles para navegación (se activan con JavaScript)
    button_col1, button_col2, button_col3 = st.columns(3)
    
    with button_col1:
        if st.button("Ir a Bunter", key="nav_bunter", help="Navegar a Reservorio Bunter"):
            st.session_state.navigate_to = "🗺️ Bunter"
            st.rerun()
    
    with button_col2:
        if st.button("Ir a Sleipner", key="nav_sleipner", help="Navegar a Reservorio Sleipner"):
            st.session_state.navigate_to = "💧 Sleipner"
            st.rerun()
    
    with button_col3:
        if st.button("Ir a Propiedades", key="nav_propiedades", help="Navegar a Propiedades Geológicas"):
            st.session_state.navigate_to = "🔬 Propiedades"
            st.rerun()
    
    # Ocultar los botones con CSS y añadir data attributes con JavaScript
    st.markdown("""
    <style>
        button[key="nav_bunter"],
        button[key="nav_sleipner"],
        button[key="nav_propiedades"] {
            display: none !important;
            visibility: hidden !important;
            position: absolute !important;
            left: -9999px !important;
        }
    </style>
    <script>
        // Añadir data attributes a los botones para identificarlos fácilmente
        function markNavigationButtons() {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => {
                const text = (btn.textContent || btn.innerText || '').trim();
                if (text === 'Ir a Bunter') {
                    btn.setAttribute('data-nav-target', 'bunter');
                } else if (text === 'Ir a Sleipner') {
                    btn.setAttribute('data-nav-target', 'sleipner');
                } else if (text === 'Ir a Propiedades') {
                    btn.setAttribute('data-nav-target', 'propiedades');
                }
            });
        }
        
        // Ejecutar inmediatamente y después de delays
        markNavigationButtons();
        setTimeout(markNavigationButtons, 100);
        setTimeout(markNavigationButtons, 500);
        setTimeout(markNavigationButtons, 1000);
        
        // Observar cambios
        const btnObserver = new MutationObserver(markNavigationButtons);
        btnObserver.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)


def main() -> None:
    # Aplicar tema GeoViz
    apply_geoviz_theme()
    
    # Renderizar sidebar y obtener la página seleccionada
    page = render_sidebar()
    
    # Renderizar contenido según la página seleccionada
    if page == "🏠 Inicio":
        render_home_page()
    
    elif page == "🗺️ Bunter":
        st.markdown("""
        <h1>🗺️ Reservorio Bunter</h1>
        <p class="status-indicator">
            <span class="status-dot"></span>
            Simulación Activa
        </p>
        """, unsafe_allow_html=True)
        
        # Pestañas para Bunter
        tab1, tab2 = st.tabs(["🔬 Propiedades GEOSX", "📊 Datos Bunter"])
        
        with tab1:
            render_geological_properties_tab()
        
        with tab2:
            # Cargar y mostrar datos de BUNTER
            with st.spinner("Cargando datos del reservorio Bunter..."):
                bunter_data = load_bunter_data()
            
            if bunter_data is None:
                st.error("❌ No se encontró el archivo de datos de Bunter (bunter_data.npz)")
                st.info(f"Buscando en: {BUNTER_DIR / 'bunter_data.npz'}")
            else:
                st.success("✅ Datos de Bunter cargados correctamente")
                render_reservoir_data_tab("Bunter", bunter_data)
    
    elif page == "💧 Sleipner":
        st.markdown("""
        <h1>💧 Reservorio Sleipner</h1>
        <p class="status-indicator">
            <span class="status-dot"></span>
            Datos Disponibles
        </p>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <p style="color: var(--text-secondary-dark); margin-bottom: 2rem;">
            El campo Sleipner es un proyecto pionero de almacenamiento de CO₂ en acuíferos salinos 
            profundos en el Mar del Norte, operado por Equinor desde 1996.
        </p>
        """, unsafe_allow_html=True)
        
        # Mapa de ubicación de Sleipner
        st.markdown("### 📍 Ubicación del Reservorio")
        
        # Coordenadas del centro
        lat_center = 58.36
        lon_center = 1.91
        
        # Dimensiones del modelo (en grados aproximados)
        # 3.2 km ≈ 0.029 grados, 5.9 km ≈ 0.053 grados (a esta latitud)
        width_deg = 0.029  # ~3.2 km
        height_deg = 0.053  # ~5.9 km
        
        # Crear rectángulo que representa el área del modelo
        rect_lats = [
            lat_center - height_deg/2,
            lat_center + height_deg/2,
            lat_center + height_deg/2,
            lat_center - height_deg/2,
            lat_center - height_deg/2
        ]
        rect_lons = [
            lon_center - width_deg/2,
            lon_center - width_deg/2,
            lon_center + width_deg/2,
            lon_center + width_deg/2,
            lon_center - width_deg/2
        ]
        
        # Crear mapa con Plotly
        fig_map = go.Figure()
        
        # Añadir rectángulo del área del modelo
        fig_map.add_trace(go.Scattermapbox(
            mode="lines",
            lon=rect_lons,
            lat=rect_lats,
            marker=dict(size=10, color='#3984c6'),
            line=dict(width=3, color='#3984c6'),
            fill='toself',
            fillcolor='rgba(57, 132, 198, 0.2)',
            name='Área del Modelo',
            hovertemplate='<b>Área del Modelo Sleipner</b><br>' +
                         'Dimensiones: 3.2 km × 5.9 km<extra></extra>'
        ))
        
        # Añadir marcador del centro
        fig_map.add_trace(go.Scattermapbox(
            mode="markers",
            lon=[lon_center],
            lat=[lat_center],
            marker=dict(size=15, color='#3984c6', symbol='circle'),
            name='Centro del Reservorio',
            hovertemplate='<b>Centro del Reservorio</b><br>' +
                         f'Latitud: {lat_center}°<br>' +
                         f'Longitud: {lon_center}°<br>' +
                         'WGS 84<extra></extra>'
        ))
        
        # Configurar el layout del mapa
        fig_map.update_layout(
            mapbox=dict(
                style="open-street-map",  # Usar OpenStreetMap (gratis, no requiere API key)
                center=dict(lat=lat_center, lon=lon_center),
                zoom=8,  # Zoom reducido para ver más área
                bearing=0,
                pitch=0
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=500,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(27, 35, 43, 0.8)",
                bordercolor="rgba(57, 132, 198, 0.5)",
                borderwidth=1,
                font=dict(color="#f8fafc", size=12)
            )
        )
        
        # Mostrar el mapa
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Información adicional sobre la ubicación
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Coordenadas (WGS 84)</div>
                <div class="metric-value" style="font-size: 1rem;">
                    {lat_center}°N, {lon_center}°E
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Extensión Lateral</div>
                <div class="metric-value" style="font-size: 1rem;">
                    3.2 × 5.9 km
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Espesor Máximo</div>
                <div class="metric-value" style="font-size: 1rem;">
                    ~300 m
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Cargar y mostrar datos de Sleipner
        with st.spinner("Cargando datos del reservorio Sleipner..."):
            sleipner_data = load_sleipner_data()
        
        if sleipner_data is None:
            st.error("❌ No se encontró el archivo de datos de Sleipner (sleipner_data.npz)")
            st.info(f"Buscando en: {SLEIPNER_DIR / 'sleipner_data.npz'}")
            st.info("🚧 Por favor, asegúrate de que el archivo sleipner_data.npz esté en la carpeta data/sleipner_data/")
        else:
            st.success("✅ Datos de Sleipner cargados correctamente")
            render_reservoir_data_tab("Sleipner", sleipner_data)
    
    elif page == "📊 Simulaciones":
        st.markdown("""
        <h1>📊 Simulaciones Avanzadas</h1>
        <p class="status-indicator">
            <span class="status-dot"></span>
            Reservorio Alpha-3
        </p>
        """, unsafe_allow_html=True)
        
        # Parámetros de simulación en el sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### ⚙️ Parámetros de Simulación")
            
            depth = st.slider("Profundidad", 1000, 4000, 2500, 100, format="%d m")
            pressure = st.slider("Presión de Inyección", 50, 300, 150, 10, format="%d bar")
            saturation = st.slider("Saturación de CO₂", 0, 100, 85, 5, format="%d%%")
            time_scale = st.slider("Escala de Tiempo", 1, 100, 50, 1, format="%d Años")
        
        # Contenido principal de simulaciones
        render_co2_viewer_tab()
    
    elif page == "🔬 Propiedades":
        st.markdown("""
        <h1>🔬 Propiedades Geológicas</h1>
        <p class="status-indicator">
            <span class="status-dot"></span>
            Análisis Geológico Completo
        </p>
        """, unsafe_allow_html=True)
        
        # Pestañas para Propiedades
        tab1, tab2 = st.tabs(["📊 Propiedades Estáticas", "🧊 Simulación CO₂ GEOSX"])
        
        with tab1:
            render_geological_properties_tab()
        
        with tab2:
            render_co2_viewer_tab_geosx()
    
    elif page == "📚 Referencias":
        render_references_page()


if __name__ == "__main__":
    main()
