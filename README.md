# 📁 Organizador de Archivos — Mi Biblioteca Digital v2.0

Un organizador automático de archivos para Windows con interfaz gráfica moderna que clasifica tu música, PDFs, libros digitales, videos, imágenes y más.

## ✨ Características

- 🎵 **Detección automática de metadatos** — Lee géneros de canciones, temas de PDFs, fechas de fotos (EXIF), etc.
- 👁️ **Vista previa** — Ve exactamente a dónde irá cada archivo ANTES de moverlo
- ✏️ **Edición masiva** — Asigna el mismo género a múltiples archivos con un clic
- 📂 **Arrastrar y soltar** — Suelta una carpeta en la ventana para escanear automáticamente
- ↩️ **Deshacer completo** — Revierte todos los movimientos al instante
- 🤖 **Sugerencias de IA** — Clasificación heurística basada en nombres de archivo
- 👁️ **Vigilancia en tiempo real** — Monitor de carpeta para organizar archivos nuevos automáticamente
- 📅 **Programación semanal** — Ejecuta la organización cada 7 días sin intervención
- ⚙️ **Reglas personalizadas** — Crea patrones (regex o text) para clasificaciones automáticas
- 📤 **Exportar a JSON** — Descarga el catálogo de archivos para análisis

## 📋 Archivos soportados

| Tipo | Extensiones |
|------|-----------|
| 🎵 Música | `.mp3`, `.flac`, `.ogg`, `.m4a`, `.wav`, `.wma`, `.aac` |
| 📄 PDFs | `.pdf` |
| 📚 EPUBs | `.epub` |
| 🎬 Videos | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.m4v` |
| 🖼️ Imágenes | `.jpg`, `.jpeg`, `.png`, `.raw`, `.nef`, `.cr2`, `.arw`, `.dng`, `.tif`, `.tiff` |
| 📝 Word | `.doc`, `.docx` |
| 📊 Excel | `.xls`, `.xlsx`, `.xlsm` |
| 🎮 ROMs | `.nes`, `.sfc`, `.smc`, `.gba`, `.gb`, `.gbc`, `.bin`, `.iso`, `.cue`, `.rom` |

## 🚀 Instalación rápida

### 1. Descargar Python
Descarga **Python 3.8+** desde [python.org](https://www.python.org/downloads/)  
**⚠️ Importante:** Marca la casilla "Add Python to PATH" durante la instalación

### 2. Clonar o descargar este proyecto
```bash
git clone https://github.com/SolangeLisset/organizador-archivos.git
cd organizador-archivos
```

### 3. Instalar dependencias
Haz doble clic en `INSTALAR_DEPENDENCIAS.bat`  
O en terminal:
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
Haz doble clic en `EJECUTAR_APP.bat`  
O en terminal:
```bash
python organizador.py
```

## 📖 Cómo usar

1. **Selecciona una carpeta** — Usa el botón "Seleccionar" o arrastra una carpeta
2. **Haz clic en "Escanear"** — La aplicación detecta todos los archivos
3. **Edita géneros** — Doble clic para cambiar el género de un archivo
4. **Vista previa** — Revisa exactamente a dónde irá cada archivo
5. **Organiza** — Haz clic en "Organizar archivos" para empezar

### Atajos útiles
- `Ctrl+Clic` — Selección múltiple
- `Doble clic` — Editar género individual
- `Botón derecho` — Menú contextual
- `Ctrl+Shift+A` — Aceptar sugerencias de IA

## ⚙️ Configuración

### Reglas personalizadas (`reglas.json`)
Define patrones para clasificar automáticamente archivos:

```json
{
  "pattern": "factura",
  "tipo": "pdf",
  "genero": "Facturas",
  "match_type": "contains"
}
```

**match_type:**
- `contains` — Búsqueda simple (case-insensitive)
- `regex` — Expresión regular

### Configuración global (`settings.json`)
```json
{
  "force_network": false,      // Buscar en MusicBrainz/OpenLibrary
  "auto_backup": true,         // Crear backups automáticos
  "theme": "light",            // Tema de la interfaz
  "language": "es"             // Idioma (español)
}
```

## 🌐 APIs opcionales

La aplicación puede mejorar sus sugerencias consultando APIs externas (requiere activar en settings):

- **MusicBrainz** — Géneros de canciones
- **OpenLibrary** — Categorías de libros

Activar: `Sugerencias web` en la interfaz

## 📊 Estructura de carpetas generada

```
Tu carpeta/
├── Musica/
│   ├── Rock/
│   ├── Pop/
│   └── Sin categoria/
├── PDFs/
│   ├── Programacion/
│   ├── Historia/
│   └── Sin categoria/
├── EPUBs/
│   ├── Ficcion/
│   └── Sin categoria/
└── Videos/
    └── Accion/
```

## 🔄 Deshacer cambios

Después de organizar, usa el botón **"Deshacer"** para revertir todos los movimientos al instante. La app mantiene un historial completo de cada movimiento.

## 📝 Log de organisación

Un archivo `_organizador_log.txt` se crea en la carpeta base con:
- Número de archivos movidos
- Errores encontrados
- Listado detallado de cada operación

## 🛠️ Requisitos del sistema

- **Windows 7+** (o Linux/macOS con Python 3.8+)
- **Python 3.8+**
- **2 GB de RAM mínimo**

## 📦 Dependencias

Ver `requirements.txt`:
- `mutagen` — Lectura de metadatos de música
- `pypdf` — Lectura de PDFs
- `ebooklib` — Lectura de EPUBs
- `Pillow` — Procesamiento de imágenes (EXIF)
- `requests` — Consultas a APIs
- `tkinterdnd2` — Drag & Drop

## ⚖️ Licencia

MIT License — [Ver LICENSE](LICENSE)

Eres libre de usar, modificar y distribuir este software con atribución.

## 👨‍💻 Autor

**SolangeLisset** — 2026

## 🐛 Reportar problemas

Si encuentras bugs o tienes sugerencias:
1. Abre un [Issue en GitHub](https://github.com/SolangeLisset/organizador-archivos/issues)
2. Describe el problema con detalles
3. Incluye tu versión de Python (`python --version`)

## 📸 Capturas de pantalla

*(Agrega aquí imágenes de la aplicación cuando sea posible)*

## 🎓 Aprendido de este proyecto

- Procesamiento de metadatos de media (música, PDF, EXIF)
- Interfaz gráfica con Tkinter avanzado
- Patrones de IA simulada (heurísticas)
- Manejo de operaciones en threads
- Integración con APIs externas

---

**¿Te fue útil? Déjame una ⭐ en GitHub**
