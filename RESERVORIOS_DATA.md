# 📊 Visualizaciones de Reservorios - BUNTER y Sleipner

## 🎉 Nuevas Características Añadidas

Se han integrado las visualizaciones de los datos de los reservorios **BUNTER** y **Sleipner** en la aplicación GeoViz.

---

## 🗺️ Reservorio BUNTER

### Ubicación en la App
**Navegación:** `🗺️ Bunter` → **Pestaña: 📊 Datos Bunter**

### Datos Disponibles

El reservorio Bunter contiene datos del modelo geológico para almacenamiento de CO₂, extraídos de un modelo de simulación Eclipse E300.

#### Dimensiones
- **NX**: 110 celdas (dirección X/Este-Oeste)
- **NY**: 63 celdas (dirección Y/Norte-Sur)
- **NZ**: 65 capas (dirección Z/Profundidad)
- **Total**: 450,450 celdas

#### Propiedades Visualizadas

1. **Permeabilidad (PERMX)**
   - Unidad: mD (millidarcies)
   - Rango: 0.0065 - 14,987.9 mD
   - Media: 179.3 mD
   - Mediana: 9.6 mD
   - Colormap: Hot (escala logarítmica)

2. **Porosidad (PORO)**
   - Unidad: Fracción (0-1)
   - Rango: 1×10⁻⁵ - 0.35
   - Media: 0.137
   - Mediana: 0.15
   - Colormap: Viridis

3. **Facies (SATNUM)**
   - Valores: 1, 2
   - Facies 1: Bunter Sandstone (reservorio principal)
   - Facies 2: Zona de reservorio secundaria
   - Colormap: Discreto (marrón/dorado)

### Características de Visualización

#### Métricas en Tiempo Real
- **Dimensiones**: Muestra X×Y×Z
- **Total de Celdas**: Cantidad total de celdas en el grid
- **Facies Únicas**: Número de tipos de facies
- **Porosidad Media**: Promedio de porosidad del reservorio

#### Modos de Visualización

**1. Modo Paralelo (Recomendado)**
- Visualiza las 3 propiedades simultáneamente
- Controles sincronizados para todos los gráficos
- Comparación lado a lado
- Ideal para análisis de correlaciones

**2. Modo Individual**
- Una propiedad a la vez
- Visualización detallada
- Estadísticas específicas por propiedad
- Panel de información expandible

#### Controles 3D
- **Corte X (plano YZ)**: Slider de 0 a 109
- **Corte Y (plano XZ)**: Slider de 0 a 62
- **Corte Z (plano XY)**: Slider de 0 a 64

---

## 💧 Reservorio Sleipner

### Ubicación en la App
**Navegación:** `💧 Sleipner`

### Datos Disponibles

El campo Sleipner es un proyecto pionero de almacenamiento de CO₂ en acuíferos salinos profundos en el Mar del Norte, operado por Equinor desde 1996.

#### Dimensiones
- **NX**: 263 celdas
- **NY**: 118 celdas
- **NZ**: 64 capas
- **Total**: 1,986,176 celdas

#### Propiedades Visualizadas

1. **Permeabilidad**
   - Unidad: mD (millidarcies)
   - Rango: 0.001 - 2,000 mD
   - Colormap: Hot (escala logarítmica)

2. **Porosidad**
   - Unidad: Fracción (0-1)
   - Rango: 0.34 - 0.36
   - Colormap: Viridis

3. **Facies**
   - Valores: 1-18 (18 tipos diferentes)
   - Colormap: Turbo (continuo para muchas categorías)
   - Distribución compleja de facies

### Características Especiales de Sleipner

#### Grid Más Grande
Con casi 2 millones de celdas, Sleipner es significativamente más grande que Bunter:
- 2.4× más celdas en X
- 1.9× más celdas en Y
- Similar número de capas en Z

#### Más Facies
Sleipner tiene 18 tipos de facies diferentes, comparado con solo 2 en Bunter, lo que refleja:
- Mayor heterogeneidad geológica
- Múltiples unidades estratigráficas
- Complejidad del acuífero salino

#### Visualización Optimizada
Para manejar el mayor tamaño:
- Caché de datos agresivo
- Renderizado optimizado
- Procesamiento por demanda

---

## 🎮 Guía de Uso

### Caso 1: Comparación de Propiedades en Bunter

```
1. Ir a: 🗺️ Bunter → 📊 Datos Bunter
2. Seleccionar: "Paralelo (3 propiedades)"
3. Ajustar cortes con los sliders en el sidebar
4. Observar correlaciones entre permeabilidad y porosidad
5. Identificar zonas de facies y su relación con propiedades
```

### Caso 2: Análisis Detallado de Sleipner

```
1. Ir a: 💧 Sleipner
2. Seleccionar: "Individual"
3. Elegir: "facies"
4. Navegar con los cortes X, Y, Z
5. Expandir "ℹ️ Información" para ver estadísticas
6. Observar la distribución de 18 tipos de facies
```

### Caso 3: Análisis Vertical (Corte Z)

```
1. Seleccionar cualquier reservorio
2. Ajustar corte Z para explorar diferentes profundidades
3. Observar cómo varían las propiedades con la profundidad
4. Identificar capas con alta/baja permeabilidad
```

### Caso 4: Análisis Horizontal (Cortes X e Y)

```
1. Modo paralelo para ver 3 propiedades
2. Fijar Z en una capa de interés
3. Mover X e Y para explorar lateralmente
4. Identificar continuidad lateral de facies
```

---

## 📊 Comparación BUNTER vs Sleipner

| Característica | BUNTER | Sleipner |
|---------------|--------|----------|
| **Dimensiones** | 110×63×65 | 263×118×64 |
| **Total Celdas** | 450,450 | 1,986,176 |
| **Facies** | 2 tipos | 18 tipos |
| **Permeabilidad (rango)** | 0.007-15,000 mD | 0.001-2,000 mD |
| **Porosidad (rango)** | 0.00001-0.35 | 0.34-0.36 |
| **Tipo de Reservorio** | Gas vaciado | Acuífero salino |
| **Complejidad** | Moderada | Alta |
| **Heterogeneidad** | Baja (2 facies) | Alta (18 facies) |

---

## 🎨 Estilos de Visualización

### Colormaps Utilizados

**Permeabilidad:**
- Colormap: `Hot`
- Escala: Logarítmica
- Razón: Amplio rango de valores (4-5 órdenes de magnitud)

**Porosidad:**
- Colormap: `Viridis`
- Escala: Lineal
- Razón: Rango más estrecho, variación suave

**Facies (2-3 tipos):**
- Colormap: Discreto personalizado
- Colores: Marrón (Shalty) y Dorado (Sand)
- Razón: Categorías discretas claras

**Facies (>3 tipos):**
- Colormap: `Turbo`
- Escala: Continua
- Razón: Muchas categorías, necesita espectro amplio

---

## 💡 Tips de Visualización

### Para Análisis de Permeabilidad
1. Usa escala logarítmica siempre
2. Observa las zonas rojas (alta permeabilidad)
3. Identifica barreras (azul/negro)
4. Compara con facies para entender control geológico

### Para Análisis de Porosidad
1. Escala lineal es adecuada
2. Busca zonas amarillas/blancas (alta porosidad)
3. Correlaciona con permeabilidad (suelen ir juntas)
4. Identifica capas productivas

### Para Análisis de Facies
1. En Bunter: 2 colores claros (marrón vs dorado)
2. En Sleipner: Gradiente de colores (18 tipos)
3. Observa la distribución espacial
4. Identifica patrones estratigráficos

### Navegación Eficiente
1. **Modo Paralelo**: Usa para exploración inicial
2. **Modo Individual**: Usa para análisis detallado
3. **Corte Z medio**: Empieza aquí (capa media)
4. **Luego explora verticalmente**: Arriba y abajo
5. **Finalmente horizontal**: X e Y

---

## 🔧 Configuración Técnica

### Archivos de Datos

**BUNTER:**
```
data/BUNTER/bunter_data.npz
  ├── facies: (65, 63, 110) int32
  ├── permeability: (65, 63, 110) float32
  └── porosity: (65, 63, 110) float32
```

**Sleipner:**
```
data/sleipner_data/sleipner_data.npz
  ├── facies: (64, 118, 263) float64
  ├── permeability: (64, 118, 263) float64
  └── porosity: (64, 118, 263) float64
```

### Caché de Datos
- Los archivos .npz se cargan con `@st.cache_data`
- Primera carga: Lenta (segundos)
- Cargas posteriores: Instantáneas (caché)
- Caché automático por Streamlit

### Performance
- **BUNTER**: ~450K celdas → Muy rápido
- **Sleipner**: ~2M celdas → Rápido con caché
- Visualización 3D optimizada con Plotly

---

## 📚 Integración con Otras Secciones

### Relación con Viewer CO₂ (Bunter)

El Viewer CO₂ muestra la **evolución temporal** de la pluma de CO₂:
- Datos dinámicos (timesteps 0-10)
- Variable: YMFS (fracción molar de CO₂)
- Animación temporal

Los **Datos Bunter** muestran las **propiedades estáticas** del reservorio:
- Datos estáticos (no cambian con el tiempo)
- Variables: Permeabilidad, Porosidad, Facies
- Propiedades geológicas base

**Juntos** permiten entender:
1. **Dónde** se almacena el CO₂ (propiedades del reservorio)
2. **Cómo** se mueve el CO₂ en el tiempo (simulación dinámica)
3. **Por qué** se mueve así (permeabilidad y facies controlan el flujo)

### Relación con Propiedades GEOSX (Bunter)

**Propiedades GEOSX:**
- Datos de otro modelo (GEOSX)
- Shape: (nz, ny, nx) diferente
- Mismo tipo de propiedades

**Datos Bunter:**
- Datos del modelo Eclipse
- Shape: (65, 63, 110)
- Mismo tipo de propiedades

Ambos conjuntos de datos muestran propiedades geológicas pero de diferentes:
- Modelos numéricos
- Grids/resoluciones
- Fuentes de datos

---

## 🎯 Casos de Uso Avanzados

### 1. Validación de Modelos
```
Compara GEOSX vs Bunter en la página de Bunter:
- Tab 2: Propiedades GEOSX
- Tab 3: Datos Bunter
- Observa diferencias en distribución espacial
- Valida consistencia geológica
```

### 2. Análisis Multi-Reservorio
```
Compara Bunter vs Sleipner:
- Bunter: Reservorio de gas (2 facies, homogéneo)
- Sleipner: Acuífero salino (18 facies, heterogéneo)
- Identifica diferencias en almacenamiento de CO₂
- Evalúa capacidad y riesgos
```

### 3. Caracterización de Facies
```
En Sleipner (18 facies):
- Modo individual → Facies
- Explorar con cortes X, Y, Z
- Identificar arquitectura estratigráfica
- Correlacionar facies entre pozos virtuales
```

### 4. Análisis de Permeabilidad-Porosidad
```
Modo paralelo:
- Gráfico izquierdo: Permeabilidad (log)
- Gráfico centro: Porosidad (lineal)
- Observar correlación positiva
- Identificar anomalías (alta φ, baja k → arcillas)
```

---

## 🐛 Solución de Problemas

### Problema: "No se encontró el archivo de datos"

**Solución:**
1. Verifica que los archivos .npz estén en:
   - `data/BUNTER/bunter_data.npz`
   - `data/sleipner_data/sleipner_data.npz`
2. Verifica permisos de lectura
3. Recarga la página (Ctrl+R)

### Problema: Carga lenta

**Solución:**
1. Primera carga es normal (carga de datos)
2. Segunda carga debe ser instantánea (caché)
3. Si persiste, limpia caché de Streamlit:
   ```bash
   streamlit cache clear
   ```

### Problema: Gráficos no se ven

**Solución:**
1. Refresca el navegador (F5)
2. Verifica consola JavaScript (F12)
3. Asegúrate de que Plotly esté instalado:
   ```bash
   pip install plotly
   ```

---

## 📖 Referencias

### BUNTER
- **Fuente**: Eclipse E300 simulation model
- **Formación**: Bunter Sandstone
- **Ubicación**: Mar del Norte
- **Uso**: Almacenamiento geológico de CO₂

### Sleipner
- **Fuente**: Sleipner Reference Model
- **Operador**: Equinor
- **Ubicación**: Mar del Norte (offshore Noruega)
- **Proyecto**: Almacenamiento de CO₂ desde 1996
- **Tipo**: Acuífero salino (formación Utsira)

---

<div align="center">

## 🎉 Nuevas Visualizaciones Disponibles

**2 Reservorios × 3 Propiedades × 2 Modos = 12 Visualizaciones**

📊 BUNTER • 💧 Sleipner • 🔬 Permeabilidad • 🌊 Porosidad • 🗺️ Facies

---

**Añadido a GeoViz v2.1**

*Noviembre 2025*

</div>

