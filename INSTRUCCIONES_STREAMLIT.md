# 🌍 Visualizador CO2 - Instrucciones de Uso

## 🚀 Acceso a la Aplicación

La aplicación está corriendo en:
- **Local:** http://localhost:8503
- **Network:** http://192.168.0.15:8503
- **External:** http://181.51.221.25:8503

## ✨ Características Principales

### 1. **Carga Inteligente con Caché**
- ✅ Todos los timesteps se cargan en memoria al inicio (solo una vez)
- ✅ Las visualizaciones se cachean por combinación de parámetros
- ✅ Navegación instantánea entre timesteps sin recarga

### 2. **Controles de Animación** 🎬
- **▶️ Play:** Reproduce automáticamente todos los timesteps
- **⏸️ Pause:** Pausa la animación
- **⏹️ Reset:** Vuelve al timestep inicial
- **Velocidad:** Ajusta de 0.5x a 3.0x (más lento a más rápido)

### 3. **Controles de Visualización** ⚙️

#### 🕐 Timestep (Manual)
- Slider para navegar manualmente entre timesteps
- Se actualiza automáticamente durante la animación

#### 🔍 Threshold YMFS Mínimo
- Rango: 0.01 - 0.50
- Default: 0.10
- Define el valor mínimo de CO2 para mostrar (Property Filter)

#### 📏 Escala Visual Eje Z
- Rango: 1 - 25
- Default: 10
- Ajusta la altura visual sin alterar los valores reales
- Útil para ver mejor la distribución vertical

### 4. **Opciones de Vista** 📊
- ✅ **Mostrar pozos inyectores:** Cubos azules en las 4 ubicaciones
- ✅ **Mostrar contorno del grid:** Wireframe del bounding box

### 5. **Información en Tiempo Real** ℹ️
El panel lateral muestra estadísticas del timestep actual:
- Min/Max/Promedio de YMFS
- Número de celdas visibles (≥ threshold)
- Bounds del modelo

## 🎮 Controles de Vista 3D (Plotly WebGL)

| Control | Descripción |
|---------|-------------|
| **Clic + Arrastrar** | Rotar vista en 3D |
| **Scroll** | Zoom in/out |
| **Shift + Clic + Arrastrar** | Pan (mover vista) |
| **Doble clic** | Reset vista |
| **Hover sobre voxels** | Ver valor exacto de YMFS |

## 🔧 Optimizaciones Implementadas

### Patrón de Diseño: Cache-Aside Pattern
```python
@st.cache_data
def load_all_timesteps_data(timesteps):
    # Carga todos los datos una sola vez
    
@st.cache_data(show_spinner=False)
def create_plotly_figure_cached(timestep_idx, ymfs_tuple, threshold, ...):
    # Cachea figuras por combinación de parámetros
```

### Estrategia de Caché en Capas
1. **Nivel 1:** Datos crudos (YMFS arrays) - Cargados al inicio
2. **Nivel 2:** Geometría de voxels - Cacheados por (timestep, threshold)
3. **Nivel 3:** Figuras Plotly completas - Cacheadas por todos los parámetros

### Beneficios
- ✅ **Primera carga:** ~10-15 segundos (carga todos los timesteps)
- ✅ **Navegación posterior:** Instantánea (< 0.1 segundos)
- ✅ **Cambio de parámetros:** Rápida si la combinación ya fue vista
- ✅ **Animación fluida:** Sin interrupciones ni recargas

## 📊 Modelo del Tutorial DEP_GAS

### Especificaciones
- **Grid:** 100×100×10 (100,000 celdas)
- **Área:** 10 km × 10 km
- **Profundidad:** 2500-2700 m (200 m de espesor)

### Fases de Simulación
1. **2010-2025:** Depleción con 4 pozos productores
2. **2025-2040:** Inyección de CO2 con 4 pozos inyectores
3. **2040-2060:** Soak (difusión sin inyección)

### Comportamiento del CO2
- El CO2 es más pesado que el gas del yacimiento
- Se mueve hacia el fondo de la capa
- Con el tiempo se aplana por difusión en fase vapor

## 🐛 Solución de Problemas

### La aplicación no responde
```bash
# Reiniciar Streamlit
pkill -f "streamlit run streamlit_co2_plotly.py"
cd /home/spell/Desktop/pyvista
streamlit run streamlit_co2_plotly.py --server.port 8503 --server.headless true &
```

### La animación es muy lenta
- Ajusta el slider de "Velocidad de Animación" a 2.0x o 3.0x

### Los voxels no se ven
- Reduce el threshold YMFS (prueba con 0.05 o 0.01)
- Verifica que estés en un timestep con CO2 inyectado (> timestep 5)

### El eje Z se ve muy comprimido
- Aumenta la "Escala Visual Eje Z" a 15 o 20

## 💡 Consejos de Uso

1. **Primera vez:** Espera a que se carguen todos los timesteps (~15 seg)
2. **Exploración rápida:** Usa el slider manual para saltar entre timesteps
3. **Análisis detallado:** Ajusta threshold para ver diferentes concentraciones
4. **Presentación:** Usa Play a velocidad 1.0x con escala Z = 15
5. **Comparación:** Abre múltiples pestañas con diferentes parámetros

## 📝 Notas Técnicas

### Tecnologías
- **Streamlit:** Framework web interactivo
- **Plotly:** Visualización 3D con WebGL
- **NumPy:** Procesamiento de datos
- **Cache:** Streamlit's `@st.cache_data` decorator

### Rendimiento
- Memoria: ~500 MB (todos los timesteps cargados)
- CPU: Baja (solo durante generación inicial de voxels)
- GPU: No requerida (WebGL en navegador)

### Arquitectura
```
Usuario → Streamlit UI → Cache Layer → Data Layer → GRDECL Files
                ↓
           Plotly WebGL → Navegador (Renderizado)
```

## 🎯 Mejoras Futuras Posibles

- [ ] Exportar frames específicos como PNG
- [ ] Comparación lado a lado de timesteps
- [ ] Gráficos 2D adicionales (cortes, perfiles)
- [ ] Anotaciones personalizadas en el 3D
- [ ] Exportar animación como video

---

**Desarrollado con** 🔬 Plotly WebGL + Streamlit | Visualización de yacimientos


