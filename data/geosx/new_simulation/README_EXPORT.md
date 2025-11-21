# 📤 Exportar Datos YMFS de GEOSX desde ResInsight a VTK

Este directorio contiene la simulación del reservorio GEOSX. Para visualizar la evolución temporal de la pluma de CO₂, necesitas exportar los datos YMFS desde ResInsight y convertirlos a formato VTK.

## 🚀 Pasos para Exportar

### 1. Preparar ResInsight

1. **Abrir ResInsight**
   ```bash
   # Asegúrate de que ResInsight esté ejecutándose
   ```

2. **Cargar el archivo EGRID**
   - Abre ResInsight
   - File → Open Case
   - Selecciona: `DEP_GAS.EGRID`
   - Ubicación: `/home/spell/Desktop/pyvista/data/geosx/new_simulation/DEP_GAS.EGRID`

### 2. Ejecutar el Script de Exportación y Conversión

```bash
cd /home/spell/Desktop/pyvista
python scripts/export_ymfs_geosx_to_vtk.py
```

El script realiza **3 pasos**:
1. ✅ Se conecta a ResInsight
2. ✅ Exporta YMFS para todos los timesteps (formato GRDECL temporal)
3. ✅ Convierte los datos a formato VTK usando PyVista
4. ✅ Guarda los archivos VTK en: `data/geosx/new_simulation/timesteps_vtk/`

### 3. Verificar la Exportación

Los archivos VTK exportados deberían estar en:
```
data/geosx/new_simulation/timesteps_vtk/
├── ymfs_ts_0000.vtk
├── ymfs_ts_0001.vtk
├── ymfs_ts_0002.vtk
└── ...
```

**Nota**: Los archivos GRDECL temporales se guardan en `timesteps_export/` pero los archivos VTK finales están en `timesteps_vtk/`.

### 4. Visualizar en GeoViz

Una vez exportados los datos:

1. Abre la aplicación Streamlit:
   ```bash
   streamlit run app.py
   ```

2. Navega a: **🔬 Propiedades** → **Pestaña: 🧊 Simulación CO₂ GEOSX**

3. Ajusta el umbral YMFS y explora la evolución temporal de la pluma de CO₂

## 📋 Requisitos

- **ResInsight** instalado y ejecutándose
- **ResInsight Python API** (`rips`) disponible
- Archivo `DEP_GAS.EGRID` en el directorio correcto

## 🔧 Solución de Problemas

### Error: "No se pudo conectar a ResInsight"
- Asegúrate de que ResInsight esté ejecutándose
- Verifica que la API esté habilitada en ResInsight

### Error: "No se pudo cargar el caso"
- Abre el archivo `DEP_GAS.EGRID` manualmente en ResInsight primero
- Luego ejecuta el script

### No se encuentran timesteps
- Verifica que la simulación tenga timesteps guardados
- Revisa que el archivo `.UNRST` esté presente

## 📊 Información del Modelo

- **Archivo EGRID**: `DEP_GAS.EGRID`
- **Simulación**: Reservorio GEOSX
- **Propiedad**: YMFS (Fracción molar de CO₂)
- **Formato de salida**: GRDECL (compatible con Eclipse)

## 🎯 Uso en la Aplicación

Los datos exportados se cargan automáticamente en la aplicación Streamlit y se visualizan con:
- Viewer 3D interactivo
- Animación temporal
- Controles de umbral
- Métricas en tiempo real

---

**Nota**: El script detecta automáticamente las dimensiones del grid basándose en los datos exportados.

