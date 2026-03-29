================================================================
  ORGANIZADOR DE ARCHIVOS - INSTRUCCIONES
  Mi Biblioteca Digital para Windows
================================================================

Autor: SolangeLisset

¿QUÉ HACE ESTE PROGRAMA?
─────────────────────────
  Escanea una carpeta de tu PC y organiza automáticamente:
    🎵 Música  (mp3, flac, ogg, m4a, wav, wma, aac)
    📄 PDFs
    📚 Libros digitales (epub)
    🎬 Videos  (mp4, mkv, avi, mov, wmv)

  Los organiza en subcarpetas así:
    📁 Tu carpeta/
      📁 Música/
        📁 Rock/
        📁 Pop/
        📁 Sin categoría/
      📁 PDFs/
        📁 Programación/
        📁 Historia/
      📁 EPUBs/
        📁 Ficción/
      📁 Videos/
        📁 Acción/


INSTALACIÓN (solo una vez)
──────────────────────────
  PASO 1: Instala Python desde https://www.python.org/downloads/
          ⚠️ IMPORTANTE: Marca la opción "Add Python to PATH"
             durante la instalación.

  PASO 2: Haz doble clic en "INSTALAR_DEPENDENCIAS.bat"
          Esto instala las librerías para leer los archivos.
          (Necesitas internet para este paso)

  PASO 3: ¡Listo! Ya puedes usar la app.


CÓMO USAR
──────────
  1. Haz doble clic en "EJECUTAR_APP.bat"

  2. Haz clic en "📂 Seleccionar" y elige la carpeta que quieres
     organizar (por ejemplo: D:\Mis Archivos)

  3. Haz clic en "🔍 Escanear"
     El programa leerá los metadatos de cada archivo.

  4. Revisa la lista. Si algún archivo tiene un género incorrecto:
     → Haz DOBLE CLIC en la fila para editarlo
     → O haz clic derecho para opciones rápidas

  5. Cuando estés conforme, haz clic en "✅ Organizar archivos"
     Los archivos se moverán a sus subcarpetas correspondientes.


CÓMO FUNCIONA LA DETECCIÓN DE GÉNERO
──────────────────────────────────────
  🎵 MÚSICA: Lee los metadatos ID3 que ya trae el archivo
     (el mismo que ves en el Windows Media Player o iTunes).
     Si tu canción no tiene género en sus metadatos, dirá
     "Sin categoría" y podrás editarlo manualmente.

  📄 PDFs: Lee el campo "Asunto" de los metadatos del documento.
     La mayoría de PDFs no tienen este campo, así que probablemente
     necesites asignarles el género manualmente.

  📚 EPUBs: Lee el campo "subject" del libro digital.
     Los libros descargados de tiendas suelen tenerlo.

  🎬 Videos: Usa el nombre de la carpeta donde está el video.
     Si tu video está en una carpeta llamada "Acción", lo detectará.


CONSEJOS
────────
  • Puedes seleccionar varios archivos (Ctrl+clic) y asignarles
    el mismo género con clic derecho → "Asignar género rápido".

  • Usa el buscador para encontrar archivos específicos.

  • Filtra por tipo (Música, PDF, EPUB, Video) con los botones
    de la izquierda.

  • El botón "💾 Exportar lista" guarda un archivo JSON con toda
    tu biblioteca catalogada.

  • Después de organizar, se crea un archivo "_organizador_log.txt"
    en tu carpeta con el detalle de todo lo que se movió.

NUEVA OPCIÓN: SUGERENCIAS IA (SIMULADO)
──────────────────────────────────────
  El programa ahora puede mostrar sugerencias automáticas de
  categoría usando un clasificador ligero simulado. Esto es solo
  una ayuda: las sugerencias no cambian archivos por sí solas.

  • "Mostrar sugerencias IA": checkbox en la barra de herramientas
    y en la ventana de `Reglas`. Cuando está activado, la columna
    "Género" mostrará algo como: "Sin categoria — Sugerido: Programacion".
  • Para desactivar las sugerencias (persistente), desmarca el
    checkbox; el estado se guarda en `settings.json`.
  • Las sugerencias usan heurísticas simples por palabras clave
    y pueden fallar — revísalas antes de organizar.


SOLUCIÓN DE PROBLEMAS
─────────────────────
  ❌ "Python no está instalado"
     → Descarga Python desde python.org y reinstálalo marcando
       "Add Python to PATH"

  ❌ "La ventana se abre y cierra rápido"
     → Abre el archivo con botón derecho → "Editar" y luego
       ejecuta con "python organizador.py" desde CMD

  ❌ Los géneros de música salen vacíos
     → Significa que tus archivos no tienen metadatos.
       Puedes editarlos con MusicBrainz Picard (gratis).

  ❌ Error de permisos al mover archivos
     → Asegúrate de que los archivos no estén abiertos en otro
       programa, y que tienes permisos de escritura en la carpeta.


ARCHIVOS DEL PROGRAMA
─────────────────────
  organizador.py           → El programa principal
  INSTALAR_DEPENDENCIAS.bat → Instala las librerías (solo 1 vez)
  EJECUTAR_APP.bat         → Abre la aplicación
  README.txt               → Este archivo


================================================================
  Hecho con Python + Tkinter
================================================================
