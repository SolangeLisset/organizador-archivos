# ================================================================
# ORGANIZADOR DE ARCHIVOS — Mi Biblioteca Digital v2.0
# Autor: SolangeLisset
#
# NOVEDADES v2.0:
#   ↩️  Deshacer organización — revierte todos los movimientos
#   👁️  Vista previa         — ve a dónde irá cada archivo
#   ✏️  Edición masiva       — barra flotante para editar varios
#   📂  Arrastrar carpeta    — suelta la carpeta en la ventana
# ================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
import json
import threading
import datetime
import re

# ─── DRAG & DROP ─────────────────────────────────────────────────
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

# ─── METADATOS ───────────────────────────────────────────────────
try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False

try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

# ================================================================
# CONSTANTES
# ================================================================

EXTENSIONES = {
    'musica': {'.mp3', '.flac', '.ogg', '.m4a', '.wav', '.wma', '.aac'},
    'pdf':    {'.pdf'},
    'epub':   {'.epub'},
    'video':  {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v'},
    'imagen': {'.jpg', '.jpeg', '.png', '.raw', '.nef', '.cr2', '.arw', '.dng', '.tif', '.tiff'},
    'word':   {'.doc', '.docx'},
    'excel':  {'.xls', '.xlsx', '.xlsm'},
    'rom':    {'.nes', '.sfc', '.smc', '.gba', '.gb', '.gbc', '.bin', '.iso', '.cue', '.rom'},
}

REGLAS_FILE = os.path.join(os.path.dirname(__file__), 'reglas.json')
DEFAULT_REGLAS = [
    {'pattern': 'factura', 'tipo': 'pdf', 'genero': 'Facturas', 'match_type': 'contains'}
]

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

# global settings cache used by top-level detection functions
GLOBAL_SETTINGS = {}

def _load_global_settings():
    global GLOBAL_SETTINGS
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                GLOBAL_SETTINGS = json.load(f) or {}
        else:
            GLOBAL_SETTINGS = {}
    except Exception:
        GLOBAL_SETTINGS = {}

# load at import time
_load_global_settings()

TIPO_INFO = {
    'musica': {'icono': 'musical note', 'emoji': '🎵', 'tag': 'musica', 'carpeta': 'Musica'},
    'pdf':    {'icono': 'document',     'emoji': '📄', 'tag': 'pdf',    'carpeta': 'PDFs'},
    'epub':   {'icono': 'book',         'emoji': '📚', 'tag': 'epub',   'carpeta': 'EPUBs'},
    'video':  {'icono': 'film',         'emoji': '🎬', 'tag': 'video',  'carpeta': 'Videos'},
    'imagen': {'icono': 'photo',        'emoji': '🖼️', 'tag': 'imagen', 'carpeta': 'Imagenes'},
    'word':   {'icono': 'document',     'emoji': '📝', 'tag': 'word',   'carpeta': 'Word'},
    'excel':  {'icono': 'spreadsheet',  'emoji': '📊', 'tag': 'excel',  'carpeta': 'Excel'},
    'rom':    {'icono': 'gamepad',      'emoji': '🎮', 'tag': 'rom',    'carpeta': 'ROMs'},
    'otro':   {'icono': 'folder',       'emoji': '📁', 'tag': 'otro',   'carpeta': 'Otros'},
}

GENEROS_RAPIDOS = [
    "Rock", "Pop", "Jazz", "Clasica", "Reggaeton", "Electronica",
    "Hip-Hop", "Blues", "Metal", "Indie",
    "Ficcion", "No Ficcion", "Programacion", "Psicologia", "Historia",
    "Ciencia", "Filosofia", "Arte", "Biografia", "Economia",
    "Accion", "Comedia", "Drama", "Documental", "Terror", "Animacion",
    "Sin categoria",
]


# ================================================================
# DETECCION DE GENEROS
# ================================================================

def obtener_tipo(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    for tipo, exts in EXTENSIONES.items():
        if ext in exts:
            return tipo
    return 'otro'

def leer_genero_musica(ruta):
    if not HAS_MUTAGEN:
        return "Sin categoria"
    try:
        audio = MutagenFile(ruta, easy=True)
        if audio is None:
            return "Sin categoria"
        genero = audio.get('genre', ['Sin categoria'])
        val = genero[0] if isinstance(genero, list) and genero else str(genero)
        return val.strip() or "Sin categoria"
    except Exception:
        return "Sin categoria"
    # si no hay genero interno, intentar MusicBrainz si el usuario lo permite, o clasificador simulado
    try:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if GLOBAL_SETTINGS.get('force_network') and HAS_REQUESTS:
            mb = buscar_genero_musicbrainz(nombre)
            if mb:
                return mb
        sim = analizar_nombre_ia_simulado(nombre, tipo='musica')
        if sim:
            return sim
    except Exception:
        pass
    return "Sin categoria"

def leer_genero_pdf(ruta):
    if not HAS_PYPDF:
        return "Sin categoria"
    try:
        reader = PdfReader(ruta)
        meta = reader.metadata
        if meta:
            subject = meta.get('/Subject', '') or meta.get('/Keywords', '')
            if subject:
                return (subject.strip() if subject else "") or "Sin categoria"
        # si no hay metadata, leer primeras páginas y deducir tema
        text = ''
        for i, p in enumerate(reader.pages[:2]):
            try:
                text += p.extract_text() or ''
            except Exception:
                continue
        if text:
            tema = pdf_topic_from_text(text)
            if tema:
                return tema
        # intentar OpenLibrary por nombre de archivo solo si el usuario lo permite
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if GLOBAL_SETTINGS.get('force_network') and HAS_REQUESTS:
            ol = buscar_genero_openlibrary(nombre)
            if ol:
                return ol
        # fallback IA simulado con nombre
        sim = analizar_nombre_ia_simulado(nombre, tipo='documento')
        if sim:
            return sim
        return "Sin categoria"
    except Exception:
        return "Sin categoria"

def leer_genero_imagen(ruta):
    """Extrae la fecha de la foto desde EXIF (DateTimeOriginal) y la devuelve como YYYY-MM-DD."""
    if not HAS_PIL:
        try:
            return datetime.datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%Y-%m-%d')
        except Exception:
            return "Sin categoria"
    try:
        img = Image.open(ruta)
        exif = img._getexif() or {}
        if not exif:
            raise ValueError('no exif')
        # Buscar la etiqueta DateTimeOriginal u otras posibles
        date_tags = ('DateTimeOriginal', 'DateTime', 'DateTimeDigitized')
        tag_map = {v: k for k, v in ExifTags.TAGS.items()}
        for t in date_tags:
            if t in tag_map:
                val = exif.get(tag_map[t])
                if val:
                    # formato "YYYY:MM:DD HH:MM:SS"
                    try:
                        d = val.split(' ')[0].replace(':', '-')
                        return d
                    except Exception:
                        continue
        # fallback: usar mtime
        return datetime.datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%Y-%m-%d')
    except Exception:
        try:
            return datetime.datetime.fromtimestamp(os.path.getmtime(ruta)).strftime('%Y-%m-%d')
        except Exception:
            return "Sin categoria"

def leer_genero_word(ruta):
    return 'Word'

def leer_genero_excel(ruta):
    return 'Excel'

def leer_genero_rom(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    mapping = {
        '.nes': 'NES', '.sfc': 'SNES', '.smc': 'SNES', '.gba': 'GBA',
        '.gb': 'GameBoy', '.gbc': 'GameBoy Color', '.iso': 'ISO',
        '.bin': 'BIN', '.cue': 'CUE', '.rom': 'ROM'
    }
    return mapping.get(ext, ext.replace('.', '').upper() or 'Unknown')

def leer_genero_epub(ruta):
    if not HAS_EBOOKLIB:
        return "Sin categoria"
    try:
        libro = epub.read_epub(ruta, options={'ignore_ncx': True})
        subjects = libro.get_metadata('DC', 'subject')
        return subjects[0][0].strip() if subjects else "Sin categoria"
    except Exception:
        return "Sin categoria"

def buscar_genero_musicbrainz(titulo):
    """Consulta MusicBrainz por título y devuelve el primer tag/genre si encuentra."""
    try:
        q = requests.get('https://musicbrainz.org/ws/2/recording/', params={'query': titulo, 'fmt': 'json'}, timeout=5)
        if q.status_code != 200:
            return None
        data = q.json()
        recs = data.get('recordings') or []
        for r in recs:
            tags = r.get('tags') or []
            if tags:
                tags_sorted = sorted(tags, key=lambda x: x.get('count',0), reverse=True)
                return tags_sorted[0].get('name')
        return None
    except Exception:
        return None

def buscar_genero_openlibrary(titulo):
    """Consulta OpenLibrary por título y devuelve subjects si encuentra."""
    try:
        q = requests.get('https://openlibrary.org/search.json', params={'q': titulo}, timeout=5)
        if q.status_code != 200:
            return None
        data = q.json()
        docs = data.get('docs') or []
        for d in docs:
            subjects = d.get('subject') or d.get('subjects') or []
            if subjects:
                return subjects[0]
        return None
    except Exception:
        return None

KEYWORD_GENRES = {
    'musica': {
        'rock': ['rock', 'live', 'guitar'],
        'pop': ['pop', 'single'],
        'jazz': ['jazz', 'sax', 'trumpet'],
        'clasica': ['symphony', 'concerto', 'classical', 'mozart', 'beethoven'],
    },
    'documento': {
        'Facturas': ['factura', 'invoice', 'recibo'],
        'Programacion': ['codigo', 'python', 'java', 'programacion', 'programming'],
        'Historia': ['historia', 'siglo', 'guerra', 'imperio'],
        'Ciencia': ['investigacion', 'estudio', 'estudios', 'ciencia', 'scientific'],
    }
}

def analizar_nombre_ia_simulado(nombre, tipo='documento'):
    """Clasificador IA simulado: heurísticas por palabras clave para sugerir genero."""
    n = nombre.lower()
    n = os.path.splitext(n)[0]
    tokens = re.split(r'[^a-z0-9]+', n)
    mapa = KEYWORD_GENRES.get(tipo, KEYWORD_GENRES['documento'])
    scores = {}
    for cat, keys in mapa.items():
        for k in keys:
            if k in n or k in tokens:
                scores[cat] = scores.get(cat, 0) + 1
    if not scores:
        return None
    best = max(scores.items(), key=lambda x: x[1])[0]
    return best

def pdf_topic_from_text(text):
    """Analiza texto y devuelve un tema sugerido (simulado)."""
    txt = text.lower()
    mapa = KEYWORD_GENRES['documento']
    for cat, keys in mapa.items():
        for k in keys:
            if k in txt:
                return cat
    snippet = ' '.join(txt.split()[:50])
    return analizar_nombre_ia_simulado(snippet, tipo='documento')

def leer_genero_video(ruta):
    carpeta = os.path.basename(os.path.dirname(ruta))
    return carpeta if carpeta else "Sin categoria"

def detectar_genero(ruta):
    tipo = obtener_tipo(ruta)
    if tipo == 'musica': return leer_genero_musica(ruta)
    if tipo == 'pdf':    return leer_genero_pdf(ruta)
    if tipo == 'epub':   return leer_genero_epub(ruta)
    if tipo == 'video':  return leer_genero_video(ruta)
    if tipo == 'imagen': return leer_genero_imagen(ruta)
    if tipo == 'word':   return leer_genero_word(ruta)
    if tipo == 'excel':  return leer_genero_excel(ruta)
    if tipo == 'rom':    return leer_genero_rom(ruta)
    return "Sin categoria"

def limpiar_carpeta(nombre):
    """Elimina caracteres invalidos para nombres de carpeta en Windows."""
    for c in r'\/:*?"<>|':
        nombre = nombre.replace(c, '_')
    return nombre.strip() or "Sin categoria"

def fmt_tamanio(bytes_):
    for u in ('B', 'KB', 'MB', 'GB'):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {u}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


# ================================================================
# VENTANA: VISTA PREVIA
# ================================================================

class VentanaVistaPrevia(tk.Toplevel):
    """
    Muestra exactamente a donde ira cada archivo ANTES de moverlo.
    El usuario puede confirmar o cancelar desde aqui.
    """
    def __init__(self, parent, archivos, carpeta_base, colores, on_confirmar):
        super().__init__(parent)
        self.title("Vista previa de organizacion")
        self.geometry("860x600")
        self.minsize(600, 400)
        self.configure(bg=colores['bg'])
        self.transient(parent)
        self.grab_set()
        self.colores      = colores
        self.on_confirmar = on_confirmar

        c = colores
        self.resizable(True, True)

        # Header
        hdr = tk.Frame(self, bg=c['surface'], pady=14, padx=20)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Vista previa — donde ira cada archivo",
                 bg=c['surface'], fg=c['text'],
                 font=('Segoe UI', 13, 'bold')).pack(side='left')
        tk.Label(hdr, text=f"{len(archivos)} archivos",
                 bg=c['surface'], fg=c['text_muted'],
                 font=('Segoe UI', 10)).pack(side='right')

        # Info
        tk.Label(self,
            text=f"  Carpeta base: {carpeta_base}\n"
                 "  Revisa la estructura. Los archivos marcados con (!) ya existen en destino.",
            bg=c['bg'], fg=c['text_muted'],
            font=('Segoe UI', 9), justify='left', anchor='w'
        ).pack(fill='x', padx=16, pady=(10, 4))

        # Arbol
        tree_frame = tk.Frame(self, bg=c['bg'])
        tree_frame.pack(fill='both', expand=True, padx=16, pady=4)

        st = ttk.Style()
        st.configure('Prev.Treeview',
            background=c['surface'], foreground=c['text'],
            fieldbackground=c['surface'],
            rowheight=22, font=('Segoe UI', 9), borderwidth=0)
        st.configure('Prev.Treeview.Heading',
            background=c['surface2'], foreground=c['text_muted'],
            font=('Segoe UI', 9, 'bold'), relief='flat')
        st.map('Prev.Treeview',
            background=[('selected', c['accent'])],
            foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(tree_frame,
            columns=('destino', 'estado'), style='Prev.Treeview')
        self.tree.heading('#0',      text='Archivo / Carpeta destino')
        self.tree.heading('destino', text='Ruta relativa')
        self.tree.heading('estado',  text='Estado')
        self.tree.column('#0',      width=300)
        self.tree.column('destino', width=360)
        self.tree.column('estado',  width=80, anchor='center')

        self.tree.tag_configure('tipo',   foreground=c['accent'],   font=('Segoe UI', 9, 'bold'))
        self.tree.tag_configure('genero', foreground=c['text_muted'],font=('Segoe UI', 9, 'italic'))
        self.tree.tag_configure('ok',     foreground=c['success'])
        self.tree.tag_configure('warn',   foreground=c['warning'])

        sby = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        sbx = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
        sby.pack(side='right', fill='y')
        sbx.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        self._poblar(archivos, carpeta_base)

        # Resumen
        sin_cat    = sum(1 for a in archivos if a['genero'] == 'Sin categoria')
        conflictos = self._conflictos(archivos, carpeta_base)
        tk.Label(self,
            text=(f"  Archivos con categoria: {len(archivos)-sin_cat}   "
                  f"Sin categoria: {sin_cat}   "
                  f"{'Conflictos de nombre: ' + str(conflictos) if conflictos else 'Sin conflictos'}"),
            bg=c['surface2'], fg=c['text'],
            font=('Segoe UI', 9), anchor='w', pady=6, padx=14
        ).pack(fill='x')

        # Botones
        bf = tk.Frame(self, bg=c['bg'], pady=12, padx=16)
        bf.pack(fill='x')
        tk.Button(bf, text="  Confirmar y organizar  ",
            bg='#4a9e4a', fg='white', activebackground='#3a8a3a',
            font=('Segoe UI', 10, 'bold'), relief='flat',
            padx=8, pady=8, cursor='hand2',
            command=self._confirmar).pack(side='right', padx=(6, 0))
        tk.Button(bf, text="Cancelar",
            bg=c['surface2'], fg=c['text_muted'],
            activebackground=c['surface'],
            font=('Segoe UI', 10), relief='flat',
            padx=12, pady=8, cursor='hand2',
            command=self.destroy).pack(side='right')

    def _poblar(self, archivos, carpeta_base):
        """Arma el arbol Tipo > Genero > archivo."""
        grupos = {}
        for a in archivos:
            carp = TIPO_INFO.get(a['tipo'], TIPO_INFO['otro'])['carpeta']
            gen  = a['genero'] or 'Sin categoria'
            grupos.setdefault(carp, {}).setdefault(gen, []).append(a)

        for carp_tipo, generos in sorted(grupos.items()):
            total = sum(len(v) for v in generos.values())
            n_tipo = self.tree.insert('', 'end',
                text=f"[+] {carp_tipo}  ({total} archivos)",
                values=('', ''), tags=('tipo',), open=True)

            for gen, lista in sorted(generos.items()):
                gen_limpio = limpiar_carpeta(gen)
                n_gen = self.tree.insert(n_tipo, 'end',
                    text=f"    [{gen}]  ({len(lista)})",
                    values=(f"{carp_tipo}/{gen_limpio}/", ''),
                    tags=('genero',), open=False)

                for a in lista:
                    dst = os.path.join(carpeta_base, carp_tipo, gen_limpio, a['nombre'])
                    conflicto = os.path.exists(dst) and dst != a['ruta']
                    tag    = 'warn' if conflicto else 'ok'
                    estado = '(!) existe' if conflicto else 'libre'
                    self.tree.insert(n_gen, 'end',
                        text=f"        {a['nombre']}",
                        values=(f"{carp_tipo}/{gen_limpio}/{a['nombre']}", estado),
                        tags=(tag,))

    def _conflictos(self, archivos, carpeta_base):
        count = 0
        for a in archivos:
            carp = TIPO_INFO.get(a['tipo'], TIPO_INFO['otro'])['carpeta']
            dst  = os.path.join(carpeta_base, carp, limpiar_carpeta(a['genero']), a['nombre'])
            if os.path.exists(dst) and dst != a['ruta']:
                count += 1
        return count

    def _confirmar(self):
        self.on_confirmar()
        self.destroy()


# ================================================================
# VENTANA: EDICION MASIVA
# ================================================================

class VentanaEdicionMasiva(tk.Toplevel):
    """
    Ventana dedicada para asignar el mismo genero a muchos archivos.
    Muestra la lista completa de seleccionados + un selector de genero.
    """
    def __init__(self, parent, archivos_sel, colores, on_aplicar):
        super().__init__(parent)
        n = len(archivos_sel)
        self.title(f"Edicion masiva — {n} archivos")
        self.geometry("620x480")
        self.resizable(False, False)
        self.configure(bg=colores['bg'])
        self.transient(parent)
        self.grab_set()
        self.colores    = colores
        self.on_aplicar = on_aplicar
        self.archivos   = archivos_sel

        c = colores

        # Header
        hdr = tk.Frame(self, bg=c['surface'], pady=14, padx=20)
        hdr.pack(fill='x')
        tk.Label(hdr,
            text=f"Edicion masiva — {n} archivo{'s' if n != 1 else ''}",
            bg=c['surface'], fg=c['text'],
            font=('Segoe UI', 13, 'bold')).pack(side='left')

        # Lista de archivos afectados
        tk.Label(self, text="  Archivos que se modificaran:",
                 bg=c['bg'], fg=c['text_muted'],
                 font=('Segoe UI', 9, 'bold'), anchor='w'
                 ).pack(fill='x', padx=16, pady=(12, 2))

        lf = tk.Frame(self, bg=c['bg'])
        lf.pack(fill='both', expand=True, padx=16, pady=(0, 8))

        sb = tk.Scrollbar(lf)
        sb.pack(side='right', fill='y')

        lb = tk.Listbox(lf, yscrollcommand=sb.set,
            bg=c['surface'], fg=c['text'],
            selectbackground=c['accent'],
            font=('Segoe UI', 9),
            relief='flat', bd=0, highlightthickness=0)
        lb.pack(fill='both', expand=True)
        sb.config(command=lb.yview)

        for a in archivos_sel:
            em = TIPO_INFO.get(a['tipo'], TIPO_INFO['otro'])['emoji']
            lb.insert('end', f"  {em}  {a['nombre']}   (actual: {a.get('genero', '?')})")

        # Panel selector
        pf = tk.Frame(self, bg=c['surface2'], pady=14, padx=20)
        pf.pack(fill='x')

        tk.Label(pf, text="Nuevo genero para TODOS los archivos anteriores:",
                 bg=c['surface2'], fg=c['text'],
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        self.var_genero = tk.StringVar()
        cb = ttk.Combobox(pf, textvariable=self.var_genero,
            values=GENEROS_RAPIDOS, font=('Segoe UI', 11), state='normal')
        cb.pack(fill='x', pady=(8, 0))
        cb.focus_set()

        # Botones
        bf = tk.Frame(self, bg=c['bg'], pady=12, padx=16)
        bf.pack(fill='x')

        tk.Label(bf, text="Puedes escribir un genero nuevo en el campo de arriba",
                 bg=c['bg'], fg=c['text_muted'],
                 font=('Segoe UI', 8)).pack(side='left')

        tk.Button(bf, text=f"  Aplicar a {n} archivos  ",
            bg=c['accent'], fg='white', activebackground='#6a5aaa',
            font=('Segoe UI', 10, 'bold'), relief='flat',
            padx=8, pady=8, cursor='hand2',
            command=self._aplicar).pack(side='right')

        tk.Button(bf, text="Cancelar",
            bg=c['surface2'], fg=c['text_muted'],
            activebackground=c['surface'],
            font=('Segoe UI', 10), relief='flat',
            padx=12, pady=8, cursor='hand2',
            command=self.destroy).pack(side='right', padx=(0, 6))

    def _aplicar(self):
        gen = self.var_genero.get().strip()
        if not gen:
            messagebox.showwarning("Sin genero",
                "Escribe o elige un genero primero.", parent=self)
            return
        self.on_aplicar([a['ruta'] for a in self.archivos], gen)
        self.destroy()


# ================================================================
# WIDGET: ZONA DRAG & DROP
# ================================================================

class ZonaDrop(tk.Label):
    """
    Area visual que acepta carpetas arrastradas desde el Explorador.
    Requiere tkinterdnd2. Si no esta instalado, muestra un aviso.
    """
    def __init__(self, parent, colores, on_drop, **kw):
        c = colores
        if HAS_DND:
            texto = "Arrastra una carpeta aqui\no usa el boton Seleccionar"
            color_fg = c['text_muted']
        else:
            texto = "Drag & Drop no disponible\nInstala tkinterdnd2 para activarlo"
            color_fg = c['danger']

        super().__init__(parent,
            text=texto, bg=c['surface2'], fg=color_fg,
            font=('Segoe UI', 9), relief='flat',
            pady=14, padx=10, justify='center',
            cursor='hand2' if HAS_DND else 'arrow', **kw)

        self.colores = c
        self.on_drop = on_drop

        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>',      self._drop)
            self.dnd_bind('<<DragEnter>>', self._enter)
            self.dnd_bind('<<DragLeave>>', self._leave)

    def _drop(self, e):
        ruta = e.data.strip().strip('{}')
        self._leave(e)
        if os.path.isdir(ruta):
            self.on_drop(ruta)
        else:
            self.config(text="Solo se aceptan carpetas", fg=self.colores['danger'])
            self.after(2000, self._reset)

    def _enter(self, e):
        self.config(bg=self.colores['accent'], fg='white',
                    text="Suelta la carpeta aqui")

    def _leave(self, e):
        self.config(bg=self.colores['surface2'], fg=self.colores['text_muted'])
        self._reset()

    def _reset(self):
        self.config(text="Arrastra una carpeta aqui\no usa el boton Seleccionar")


# ================================================================
# APLICACION PRINCIPAL
# ================================================================

class OrganizadorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Archivos v2.0")
        self.root.geometry("1100x700")
        self.root.minsize(820, 520)

        self.C = {
            'bg':         '#1e1e2e',
            'surface':    '#2a2a3e',
            'surface2':   '#313149',
            'accent':     '#7c6bc2',
            'text':       '#cdd6f4',
            'text_muted': '#6c7086',
            'success':    '#a6e3a1',
            'warning':    '#f9e2af',
            'danger':     '#f38ba8',
            'musica':     '#89b4fa',
            'pdf':        '#f38ba8',
            'epub':       '#a6e3a1',
            'video':      '#fab387',
            'imagen':     '#f5c2e7',
            'word':       '#9bbefc',
            'excel':      '#9be79a',
            'rom':        '#ffb86c',
        }

        # Estado
        self.archivos           = []
        self.carpeta_origen     = tk.StringVar()
        self.texto_busqueda     = tk.StringVar()
        self.filtro_tipo        = tk.StringVar(value='Todos')
        self.historial          = []   # [(ruta_src, ruta_dst), ...]  para deshacer
        self.watching = False
        self._watch_thread = None
        self._seen_files = set()
        self.scheduled = False
        self._schedule_thread = None

        self.reglas = self._cargar_reglas()

        # Cargar settings y definir toggles
        self.settings = self._cargar_settings()
        self.var_sugerencias = tk.BooleanVar(value=self.settings.get('sugerencias_ia', True))
        self.var_force_network = tk.BooleanVar(value=self.settings.get('force_network', False))
        # guardar cambios cuando el usuario cambia los checkboxes
        try:
            self.var_sugerencias.trace('w', lambda *a: self._guardar_settings())
            self.var_force_network.trace('w', lambda *a: self._guardar_settings())
        except Exception:
            pass

        self.texto_busqueda.trace('w', lambda *a: self._filtrar())

        self._tema()
        self._ui()
        # Atajo para aplicar sugerencias: Ctrl+Shift+A
        try:
            self.root.bind('<Control-Shift-A>', lambda e: self._aceptar_sugerencias_selection())
            self.root.bind('<Control-Shift-a>', lambda e: self._aceptar_sugerencias_selection())
        except Exception:
            pass
        self._check_libs()

    # ─── REGLAS: cargar/guardar ─────────────────────────────────
    def _cargar_reglas(self):
        reglas = []
        if os.path.exists(REGLAS_FILE):
            try:
                with open(REGLAS_FILE, 'r', encoding='utf-8') as f:
                    reglas = json.load(f) or []
            except Exception:
                reglas = []
        # Ensure DEFAULT_REGLAS are present (merge, avoid duplicates)
        existing_keys = {(r.get('pattern','').lower(), r.get('match_type','contains')) for r in reglas}
        for dr in DEFAULT_REGLAS:
            key = (dr.get('pattern','').lower(), dr.get('match_type','contains'))
            if key not in existing_keys:
                reglas.insert(0, dr)
        # persist merged rules
        try:
            with open(REGLAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(reglas, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        # store default keys for UI protection
        self._default_keys = {(r.get('pattern','').lower(), r.get('match_type','contains')) for r in DEFAULT_REGLAS}
        return reglas

    def _guardar_reglas(self):
        try:
            with open(REGLAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.reglas, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ─── SETTINGS ───────────────────────────────────────────────
    def _cargar_settings(self):
        settings = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f) or {}
            except Exception:
                settings = {}
        return settings

    def _guardar_settings(self):
        try:
            s = {
                'sugerencias_ia': bool(self.var_sugerencias.get()),
                'force_network': bool(self.var_force_network.get())
            }
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(s, f, ensure_ascii=False, indent=2)
            # update global cache used by top-level functions
            try:
                GLOBAL_SETTINGS.update(s)
            except Exception:
                pass
        except Exception:
            pass

    # ─── TEMA ────────────────────────────────────────────────────
    def _tema(self):
        c = self.C
        self.root.configure(bg=c['bg'])
        s = ttk.Style()
        s.theme_use('clam')

        s.configure('S.TFrame',  background=c['surface'])
        s.configure('S2.TFrame', background=c['surface2'])
        s.configure('BG.TFrame', background=c['bg'])

        for nombre, bg, fg, font_ in [
            ('Accent',  c['accent'],  'white', ('Segoe UI', 9, 'bold')),
            ('Success', '#4a9e4a',    'white', ('Segoe UI', 9, 'bold')),
            ('Ghost',   c['surface2'],c['text'],('Segoe UI', 9)),
        ]:
            s.configure(f'{nombre}.TButton',
                background=bg, foreground=fg, font=font_,
                padding=(12, 7), relief='flat', borderwidth=0)
            s.map(f'{nombre}.TButton',
                background=[('active', c['surface']), ('pressed', c['bg'])])

        s.configure('Dark.TEntry',
            fieldbackground=c['surface2'], foreground=c['text'],
            insertcolor=c['text'], relief='flat', padding=6)

        s.configure('T.Treeview',
            background=c['surface'], foreground=c['text'],
            fieldbackground=c['surface'], rowheight=36,
            font=('Segoe UI', 10), borderwidth=0, relief='flat')
        s.configure('T.Treeview.Heading',
            background=c['surface2'], foreground=c['text_muted'],
            font=('Segoe UI', 9, 'bold'), relief='flat', padding=(8, 6))
        s.map('T.Treeview',
            background=[('selected', c['accent'])],
            foreground=[('selected', 'white')])

        s.configure('V.Vertical.TScrollbar',
            background=c['surface2'], troughcolor=c['bg'],
            arrowcolor=c['text_muted'], relief='flat')

    # ─── UI ──────────────────────────────────────────────────────
    def _ui(self):
        c = self.C

        # HEADER
        hdr = tk.Frame(self.root, bg=c['surface'], pady=12, padx=20)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Organizador de Archivos v2.0",
                 bg=c['surface'], fg=c['text'],
                 font=('Segoe UI', 14, 'bold')).pack(side='left')
        self.lbl_total = tk.Label(hdr, text="0 archivos",
            bg=c['surface'], fg=c['text_muted'], font=('Segoe UI', 10))
        self.lbl_total.pack(side='right', padx=8)

        # TOOLBAR
        tb = tk.Frame(self.root, bg=c['bg'], pady=10, padx=16)
        tb.pack(fill='x')

        # --- izquierda: carpeta + escanear
        iz = tk.Frame(tb, bg=c['bg'])
        iz.pack(side='left', fill='x', expand=True)
        tk.Label(iz, text="Carpeta:", bg=c['bg'], fg=c['text_muted'],
                 font=('Segoe UI', 9)).pack(side='left')
        ttk.Entry(iz, textvariable=self.carpeta_origen, style='Dark.TEntry',
                  width=38, state='readonly').pack(side='left', padx=(6, 4))
        ttk.Button(iz, text="Seleccionar", style='Ghost.TButton',
                   command=self._sel_carpeta).pack(side='left', padx=2)
        ttk.Button(iz, text="Escanear", style='Accent.TButton',
                   command=self._escanear).pack(side='left', padx=(8, 0))

        # --- derecha: acciones
        der = tk.Frame(tb, bg=c['bg'])
        der.pack(side='right')

        # Boton Deshacer (deshabilitado hasta que haya historial)
        self.btn_deshacer = ttk.Button(der, text="Deshacer", style='Ghost.TButton',
                                        command=self._deshacer, state='disabled')
        self.btn_deshacer.pack(side='left', padx=2)

        ttk.Button(der, text="Exportar", style='Ghost.TButton',
                   command=self._exportar).pack(side='left', padx=2)

        # Boton Vista Previa
        ttk.Button(der, text="Vista previa", style='Ghost.TButton',
                   command=self._vista_previa).pack(side='left', padx=2)

        # Boton Aceptar sugerencias (aplica la sugerencia IA a la selección)
        ttk.Button(der, text="Aceptar sugerencias  Ctrl+Shift+A", style='Ghost.TButton',
               command=self._aceptar_sugerencias_selection).pack(side='left', padx=2)

        # Boton Organizar
        ttk.Button(der, text="Organizar archivos", style='Success.TButton',
                   command=self._organizar).pack(side='left', padx=(4, 0))

        # Boton Vigilancia (toggle)
        self.btn_vig = ttk.Button(der, text="Vigilancia: OFF", style='Ghost.TButton',
               command=self._toggle_vigilancia)
        self.btn_vig.pack(side='left', padx=4)

        # Boton Reglas
        ttk.Button(der, text="Reglas", style='Ghost.TButton',
               command=self._abrir_reglas).pack(side='left', padx=2)

        # Boton Restaurar reglas por defecto
        ttk.Button(der, text="Restaurar reglas", style='Ghost.TButton',
                   command=self._restore_rules_main).pack(side='left', padx=2)

        # Boton Programar semanal (toggle)
        self.btn_sched = ttk.Button(der, text="Programar semanal: OFF", style='Ghost.TButton',
               command=self._toggle_schedule)
        self.btn_sched.pack(side='left', padx=4)

        # Checkbutton para activar/desactivar sugerencias IA
        cb = tk.Checkbutton(der, text='Sugerencias IA', variable=self.var_sugerencias,
                    bg=c['bg'], fg=c['text'], selectcolor=c['surface2'],
                    activebackground=c['bg'], activeforeground=c['accent'],
                    font=('Segoe UI', 9), cursor='hand2')
        cb.pack(side='left', padx=6)
        # Checkbutton para forzar búsquedas en la red (opt-in)
        cb_net = tk.Checkbutton(der, text='Forzar búsquedas web', variable=self.var_force_network,
                    bg=c['bg'], fg=c['text'], selectcolor=c['surface2'],
                    activebackground=c['bg'], activeforeground=c['accent'],
                    font=('Segoe UI', 9), cursor='hand2')
        cb_net.pack(side='left', padx=6)
        # tooltip in status bar on hover
        def _suger_tip_enter(e=None):
            try:
                self._prev_status = self.status.cget('text')
            except Exception:
                self._prev_status = ''
            self._status('Sugerencias IA: muestra sugerencias heurísticas (persistente).')
        def _suger_tip_leave(e=None):
            try:
                self._status(self._prev_status)
            except Exception:
                self._status('')
        cb.bind('<Enter>', _suger_tip_enter)
        cb.bind('<Leave>', _suger_tip_leave)

        # BODY
        body = tk.Frame(self.root, bg=c['bg'])
        body.pack(fill='both', expand=True, padx=12, pady=(0, 0))
        self._sidebar(body)
        self._tabla_area(body)

        # BARRA MASIVA (oculta inicialmente)
        self._construir_barra_masiva()

        # STATUS
        self.status = tk.Label(self.root,
            text="  Selecciona o arrastra una carpeta para comenzar.",
            bg=c['surface2'], fg=c['text_muted'],
            font=('Segoe UI', 9), anchor='w', pady=5, padx=10)
        self.status.pack(fill='x', side='bottom')

    def _sidebar(self, parent):
        c = self.C
        sb = tk.Frame(parent, bg=c['surface'], width=210)
        sb.pack(side='left', fill='y', padx=(0, 8), pady=8)
        sb.pack_propagate(False)

        # ZONA DROP
        self.zona_drop = ZonaDrop(sb, c, on_drop=self._on_drop)
        self.zona_drop.pack(fill='x', padx=10, pady=(12, 4))

        self._sep(sb)

        # BUSCADOR
        self._sec(sb, "BUSCAR")
        ttk.Entry(sb, textvariable=self.texto_busqueda,
                  style='Dark.TEntry').pack(fill='x', padx=12, pady=(4, 8))

        self._sep(sb)

        # FILTROS
        self._sec(sb, "TIPO DE ARCHIVO")
        for txt, val in [('Todos','Todos'),('Musica','musica'),
                          ('PDFs','pdf'),('EPUBs','epub'),('Videos','video'),
                          ('Imagenes','imagen'),('Word','word'),('Excel','excel'),('ROMs','rom')]:
            tk.Radiobutton(sb, text=txt, variable=self.filtro_tipo, value=val,
                command=self._filtrar,
                bg=c['surface'], fg=c['text'], selectcolor=c['surface2'],
                activebackground=c['surface'], activeforeground=c['accent'],
                font=('Segoe UI', 9), cursor='hand2'
            ).pack(anchor='w', padx=14, pady=2)

        self._sep(sb)

        # STATS
        self._sec(sb, "ESTADISTICAS")
        self.stats = {}
        for tipo in ['musica','pdf','epub','video','imagen','word','excel','rom']:
            f = tk.Frame(sb, bg=c['surface'])
            f.pack(fill='x', padx=14, pady=2)
            tk.Label(f, text=TIPO_INFO[tipo]['emoji'],
                     bg=c['surface'], font=('Segoe UI', 10)).pack(side='left')
            lbl = tk.Label(f, text="0 archivos",
                bg=c['surface'], fg=c['text_muted'], font=('Segoe UI', 9))
            lbl.pack(side='left', padx=6)
            self.stats[tipo] = lbl

        self._sep(sb)

        # LIBRERIAS
        self._sec(sb, "LIBRERIAS")
        for nombre, ok in [('mutagen', HAS_MUTAGEN), ('pypdf', HAS_PYPDF),
                            ('ebooklib', HAS_EBOOKLIB), ('tkinterdnd2', HAS_DND)]:
            f = tk.Frame(sb, bg=c['surface'])
            f.pack(fill='x', padx=14, pady=1)
            tk.Label(f, text='[OK]' if ok else '[--]',
                bg=c['surface'],
                fg=c['success'] if ok else c['danger'],
                font=('Segoe UI', 8, 'bold')).pack(side='left')
            tk.Label(f, text=nombre, bg=c['surface'],
                fg=c['text_muted'], font=('Segoe UI', 8)).pack(side='left', padx=4)

    def _tabla_area(self, parent):
        c = self.C
        area = tk.Frame(parent, bg=c['bg'])
        area.pack(side='left', fill='both', expand=True, pady=8)

        # Cabecera de la tabla
        cab = tk.Frame(area, bg=c['bg'])
        cab.pack(fill='x', pady=(0, 6))
        self.lbl_mostrando = tk.Label(cab, text="Todos los archivos",
            bg=c['bg'], fg=c['text_muted'], font=('Segoe UI', 10, 'italic'))
        self.lbl_mostrando.pack(side='left')

        # Boton edicion masiva (se activa con la seleccion)
        self.btn_masivo = ttk.Button(cab,
            text="Editar seleccionados (0)", style='Ghost.TButton',
            command=self._abrir_masivo, state='disabled')
        self.btn_masivo.pack(side='right')

        # Treeview (tabla)
        tf = tk.Frame(area, bg=c['bg'])
        tf.pack(fill='both', expand=True)

        cols = ('tipo','nombre','genero','tamanio','ruta')
        self.tabla = ttk.Treeview(tf, columns=cols,
            show='headings', style='T.Treeview', selectmode='extended')

        for col, titulo, ancho, stretch in [
            ('tipo',    'Tipo',   60,  False),
            ('nombre',  'Nombre', 280, True),
            ('genero',  'Genero', 180, True),
            ('tamanio', 'Tamano', 80,  False),
            ('ruta',    'Ruta',   300, True),
        ]:
            self.tabla.heading(col, text=titulo,
                anchor='center' if col in ('tipo','tamanio') else 'w')
            self.tabla.column(col, width=ancho, stretch=stretch,
                anchor='center' if col in ('tipo','tamanio') else 'w',
                minwidth=50)

        for tipo, color in [('musica',c['musica']),('pdf',c['pdf']),
                     ('epub',c['epub']),('video',c['video']),
                     ('imagen',c['imagen']),('word',c['word']),('excel',c['excel']),('rom',c['rom']),
                     ('otro',c['text_muted'])]:
            self.tabla.tag_configure(tipo, foreground=color)
        self.tabla.tag_configure('sincat', foreground=c['text_muted'])

        sby = ttk.Scrollbar(tf, orient='vertical',
            command=self.tabla.yview, style='V.Vertical.TScrollbar')
        sbx = ttk.Scrollbar(tf, orient='horizontal', command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
        sby.pack(side='right', fill='y')
        sbx.pack(side='bottom', fill='x')
        self.tabla.pack(fill='both', expand=True)

        self.tabla.bind('<Double-1>', self._editar_uno)
        self.tabla.bind('<Button-3>', self._menu_ctx)
        self.tabla.bind('<<TreeviewSelect>>', self._on_sel)

        tk.Label(area,
            text="Doble clic para editar genero   |   "
                 "Ctrl+clic para seleccion multiple   |   "
                 "Clic derecho para mas opciones",
            bg=c['bg'], fg=c['text_muted'], font=('Segoe UI', 8)
        ).pack(pady=(4, 0))

    def _construir_barra_masiva(self):
        """
        Barra flotante de edicion rapida.
        Aparece automaticamente cuando hay 2+ archivos seleccionados.
        """
        c = self.C
        self.barra = tk.Frame(self.root, bg=c['accent'], pady=8, padx=16)
        # No se empaqueta aun — se muestra/oculta en _on_sel

        tk.Label(self.barra, text="Edicion rapida:",
                 bg=c['accent'], fg='white',
                 font=('Segoe UI', 9, 'bold')).pack(side='left')

        self.var_rapido = tk.StringVar()
        ttk.Combobox(self.barra, textvariable=self.var_rapido,
            values=GENEROS_RAPIDOS, font=('Segoe UI', 10),
            width=22).pack(side='left', padx=(10, 6))

        self.lbl_barra_n = tk.Label(self.barra, text="",
            bg=c['accent'], fg='white', font=('Segoe UI', 9))
        self.lbl_barra_n.pack(side='left', padx=6)

        tk.Button(self.barra, text="Aplicar",
            bg='white', fg=c['accent'], activebackground='#eeeeee',
            font=('Segoe UI', 9, 'bold'), relief='flat',
            padx=12, pady=4, cursor='hand2',
            command=self._aplicar_rapido).pack(side='left', padx=4)

        tk.Button(self.barra, text="X",
            bg=c['accent'], fg='white',
            font=('Segoe UI', 11), relief='flat', cursor='hand2',
            command=self._ocultar_barra).pack(side='right')

    # ─── DRAG & DROP ─────────────────────────────────────────────
    def _on_drop(self, ruta):
        """Recibe la carpeta arrastrada y lanza el escaneo automaticamente."""
        self.carpeta_origen.set(ruta)
        self._status(f"Carpeta recibida: {ruta} — Escaneando...")
        self.root.after(250, self._escanear)

    # ─── SELECCION → BARRA MASIVA ────────────────────────────────
    def _on_sel(self, event=None):
        """Muestra/oculta la barra flotante segun cuantos hay seleccionados."""
        n = len(self.tabla.selection())
        self.btn_masivo.config(
            text=f"Editar seleccionados ({n})",
            state='normal' if n > 0 else 'disabled')

        if n >= 2:
            self.lbl_barra_n.config(text=f"{n} archivos seleccionados")
            if not self.barra.winfo_ismapped():
                self.barra.pack(fill='x', side='bottom', before=self.status)
        else:
            self._ocultar_barra()

    def _ocultar_barra(self):
        if self.barra.winfo_ismapped():
            self.barra.pack_forget()

    # ─── ESCANEO ─────────────────────────────────────────────────
    def _sel_carpeta(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta")
        if ruta:
            self.carpeta_origen.set(ruta)

    def _escanear(self):
        carpeta = self.carpeta_origen.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning("Sin carpeta", "Selecciona una carpeta primero.")
            return
        self.archivos.clear()
        self._limpiar()
        self._status("Escaneando... espera.")
        threading.Thread(target=self._scan_worker, args=(carpeta,), daemon=True).start()

    def _scan_worker(self, carpeta):
        found = []
        for raiz, dirs, files in os.walk(carpeta):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for nombre in files:
                if nombre.startswith('.'): continue
                ruta = os.path.join(raiz, nombre)
                tipo = obtener_tipo(ruta)
                if tipo == 'otro': continue
                genero = detectar_genero(ruta)
                try:
                    tam = fmt_tamanio(os.path.getsize(ruta))
                except OSError:
                    tam = "?"
                found.append({'ruta': ruta, 'nombre': nombre,
                              'tipo': tipo, 'genero': genero, 'tamanio': tam})
                if len(found) % 10 == 0:
                    self.root.after(0, self._status, f"Escaneando... {len(found)} archivos")
        self.archivos = found
        self.root.after(0, self._poblar_tabla)

    # ─── VIGILANCIA / MONITOREO ──────────────────────────────────
    def _toggle_vigilancia(self):
        if not self.carpeta_origen.get():
            messagebox.showwarning("Sin carpeta", "Selecciona una carpeta primero.")
            return
        if self.watching:
            self.watching = False
            self.btn_vig.config(text="Vigilancia: OFF")
        else:
            self.watching = True
            self._seen_files = set()
            # seed seen set with current files
            for raiz, dirs, files in os.walk(self.carpeta_origen.get()):
                for f in files:
                    self._seen_files.add(os.path.join(raiz, f))
            self._watch_thread = threading.Thread(target=self._watch_worker, daemon=True)
            self._watch_thread.start()
            self.btn_vig.config(text="Vigilancia: ON")
            self._status("Modo vigilancia activado.")

    def _watch_worker(self):
        base = self.carpeta_origen.get()
        while self.watching:
            try:
                for raiz, dirs, files in os.walk(base):
                    for nombre in files:
                        ruta = os.path.join(raiz, nombre)
                        if ruta in self._seen_files: continue
                        self._seen_files.add(ruta)
                        # pequeño delay para que archivo termine de copiar
                        self.root.after(100, lambda r=ruta: threading.Thread(target=self._handle_new_file, args=(r,), daemon=True).start())
                # esperar 5 segundos
                for _ in range(5):
                    if not self.watching: break
                    threading.Event().wait(1)
            except Exception:
                threading.Event().wait(5)

    def _handle_new_file(self, ruta):
        # Detectar tipo y aplicar reglas
        tipo = obtener_tipo(ruta)
        genero = detectar_genero(ruta)
        regla = self._match_reglas(os.path.basename(ruta))
        if regla:
            tipo = regla.get('tipo', tipo)
            genero = regla.get('genero', genero)
        # mover inmediatamente
        try:
            carp_tipo = TIPO_INFO.get(tipo, TIPO_INFO['otro'])['carpeta']
            gen_clean = limpiar_carpeta(genero)
            dst_dir = os.path.join(self.carpeta_origen.get(), carp_tipo, gen_clean)
            os.makedirs(dst_dir, exist_ok=True)
            base2, ext = os.path.splitext(os.path.basename(ruta))
            dst = os.path.join(dst_dir, os.path.basename(ruta))
            k = 1
            while os.path.exists(dst) and dst != ruta:
                dst = os.path.join(dst_dir, f"{base2} ({k}){ext}"); k += 1
            shutil.move(ruta, dst)
            self.historial.append((ruta, dst))
            self._status(f"Vigilancia: movido {os.path.basename(ruta)} -> {carp_tipo}/{gen_clean}/")
            # refrescar lista
            self.root.after(0, self._escanear)
        except Exception as ex:
            self._status(f"Vigilancia: error moviendo {os.path.basename(ruta)}: {ex}")

    def _match_reglas(self, nombre):
        nombre_l = nombre.lower()
        for r in self.reglas:
            mt = r.get('match_type', 'contains')
            pat = r.get('pattern', '')
            if not pat: continue
            if mt == 'contains' and pat.lower() in nombre_l:
                return r
            if mt == 'regex':
                try:
                    if re.search(pat, nombre, re.IGNORECASE):
                        return r
                except Exception:
                    continue
        return None

    def _poblar_tabla(self):
        self._limpiar()
        conteo = {t: 0 for t in ['musica','pdf','epub','video','imagen','word','excel','rom']}
        for a in self.archivos:
            t = a['tipo']
            em = TIPO_INFO.get(t, TIPO_INFO['otro'])['emoji']
            tag = TIPO_INFO.get(t, TIPO_INFO['otro'])['tag']
            tags = (tag, 'sincat') if a['genero'] == 'Sin categoria' else (tag,)
            # compute simulated IA suggestion and show it alongside genero
            sugerido = None
            try:
                if getattr(self, 'var_sugerencias', None) and self.var_sugerencias.get():
                    sim_tipo = 'musica' if t == 'musica' else 'documento'
                    sugerido = analizar_nombre_ia_simulado(a['nombre'], tipo=sim_tipo)
            except Exception:
                sugerido = None
            genero_display = a['genero']
            if sugerido and sugerido != a['genero']:
                genero_display = f"{a['genero']} — Sugerido: {sugerido}"
            self.tabla.insert('', 'end',
                values=(em, a['nombre'], genero_display, a['tamanio'], a['ruta']),
                tags=tags)
            if t in conteo: conteo[t] += 1
        for t, lbl in self.stats.items():
            lbl.config(text=f"{conteo[t]} archivos")
        self.lbl_total.config(text=f"{len(self.archivos)} archivos")
        self._status(f"{len(self.archivos)} archivos encontrados. Doble clic para editar genero.")

    # ─── FILTROS ─────────────────────────────────────────────────
    def _filtrar(self, *args):
        self._limpiar()
        ft = self.filtro_tipo.get()
        fb = self.texto_busqueda.get().lower().strip()
        n = 0
        for a in self.archivos:
            if ft != 'Todos' and a['tipo'] != ft: continue
            if fb and fb not in (a['nombre'] + a['genero']).lower(): continue
            t   = a['tipo']
            em  = TIPO_INFO.get(t, TIPO_INFO['otro'])['emoji']
            tag = TIPO_INFO.get(t, TIPO_INFO['otro'])['tag']
            tags = (tag, 'sincat') if a['genero'] == 'Sin categoria' else (tag,)
            # compute IA suggestion to display inline with genero
            sugerido = None
            try:
                if getattr(self, 'var_sugerencias', None) and self.var_sugerencias.get():
                    sim_tipo = 'musica' if t == 'musica' else 'documento'
                    sugerido = analizar_nombre_ia_simulado(a['nombre'], tipo=sim_tipo)
            except Exception:
                sugerido = None
            genero_display = a['genero']
            if sugerido and sugerido != a['genero']:
                genero_display = f"{a['genero']} — Sugerido: {sugerido}"
            self.tabla.insert('', 'end',
                values=(em, a['nombre'], genero_display, a['tamanio'], a['ruta']),
                tags=tags)
            n += 1
        self.lbl_total.config(text=f"{n} archivos")
        self.lbl_mostrando.config(
            text=f"Mostrando {n} de {len(self.archivos)}"
                 if n != len(self.archivos) else "Todos los archivos")

    def _limpiar(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)

    # ─── EDITAR GENERO ────────────────────────────────────────────
    def _editar_uno(self, event=None):
        sel = self.tabla.selection()
        if not sel: return
        item = sel[0]
        vals = self.tabla.item(item, 'values')
        if not vals: return
        nuevo = simpledialog.askstring(
            "Editar genero", f"Archivo: {vals[1]}\n\nNuevo genero:",
            initialvalue=vals[2], parent=self.root)
        if nuevo is not None:
            nuevo = nuevo.strip() or "Sin categoria"
            nv = list(vals); nv[2] = nuevo
            self.tabla.item(item, values=nv)
            for a in self.archivos:
                if a['ruta'] == vals[4]:
                    a['genero'] = nuevo
                    break
            self._status(f"'{vals[1]}' — genero: {nuevo}")

    def _abrir_masivo(self):
        """Abre la ventana de edicion masiva con los seleccionados."""
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Sin seleccion", "Selecciona archivos con Ctrl+clic.")
            return
        sel_arch = []
        for item in sel:
            vals = self.tabla.item(item, 'values')
            if vals:
                for a in self.archivos:
                    if a['ruta'] == vals[4]:
                        sel_arch.append(a); break
        VentanaEdicionMasiva(self.root, sel_arch, self.C,
                             on_aplicar=self._aplicar_masivo)

    def _aplicar_masivo(self, rutas, genero):
        """Aplica el genero a los archivos y actualiza la tabla."""
        rs = set(rutas)
        n = 0
        for item in self.tabla.get_children():
            vals = self.tabla.item(item, 'values')
            if vals and vals[4] in rs:
                nv = list(vals); nv[2] = genero
                self.tabla.item(item, values=nv); n += 1
        for a in self.archivos:
            if a['ruta'] in rs: a['genero'] = genero
        self._status(f"Genero '{genero}' aplicado a {n} archivos.")

    def _aplicar_rapido(self):
        """Aplica el genero de la barra flotante a los seleccionados."""
        gen = self.var_rapido.get().strip()
        if not gen:
            self._status("Escribe un genero en la barra antes de aplicar.")
            return
        rutas = [self.tabla.item(i, 'values')[4]
                 for i in self.tabla.selection()
                 if self.tabla.item(i, 'values')]
        self._aplicar_masivo(rutas, gen)
        self.var_rapido.set('')

    # ─── MENU CONTEXTUAL ─────────────────────────────────────────
    def _menu_ctx(self, event):
        item = self.tabla.identify_row(event.y)
        if not item: return
        if item not in self.tabla.selection():
            self.tabla.selection_set(item)
        c = self.C
        n = len(self.tabla.selection())
        menu = tk.Menu(self.root, tearoff=0,
            bg=c['surface2'], fg=c['text'],
            activebackground=c['accent'], activeforeground='white',
            font=('Segoe UI', 9))
        menu.add_command(
            label=f"Editar genero ({n} archivo{'s' if n>1 else ''})",
            command=self._abrir_masivo if n > 1 else self._editar_uno)
        menu.add_command(label=f"Aceptar sugerencia ({n})\tCtrl+Shift+A", command=self._aceptar_sugerencias_selection)
        sub = tk.Menu(menu, tearoff=0, bg=c['surface2'], fg=c['text'],
            activebackground=c['accent'], activeforeground='white',
            font=('Segoe UI', 9))
        for g in GENEROS_RAPIDOS:
            sub.add_command(label=g, command=lambda gen=g: self._set_rapido(gen))
        menu.add_cascade(label="Genero rapido", menu=sub)
        menu.add_separator()
        menu.add_command(label="Abrir en Explorador", command=self._abrir_expl)
        menu.post(event.x_root, event.y_root)

    def _set_rapido(self, gen):
        rutas = [self.tabla.item(i,'values')[4]
                 for i in self.tabla.selection()
                 if self.tabla.item(i,'values')]
        self._aplicar_masivo(rutas, gen)

    def _aceptar_sugerencias_selection(self):
        sel = self.tabla.selection()
        if not sel:
            self._status('Selecciona archivos primero.')
            return
        # primero, recopilar las sugerencias que serían aplicadas
        pendientes = []  # list of (item, ruta, nombre, sugerido)
        for item in sel:
            vals = self.tabla.item(item, 'values')
            if not vals: continue
            nombre = vals[1]
            ruta = vals[4]
            tipo = None
            for a in self.archivos:
                if a['ruta'] == ruta:
                    tipo = a['tipo']; break
            if not tipo:
                continue
            sim_tipo = 'musica' if tipo == 'musica' else 'documento'
            try:
                sugerido = analizar_nombre_ia_simulado(nombre, tipo=sim_tipo)
            except Exception:
                sugerido = None
            if sugerido and sugerido != vals[2]:
                pendientes.append((item, ruta, nombre, sugerido))
        if not pendientes:
            self._status('No hay sugerencias distintas para aplicar.')
            return
        # pedir confirmación al usuario con el número de cambios
        if not messagebox.askyesno('Confirmar sugerencias',
                                   f"Se aplicarán {len(pendientes)} sugerencia{'s' if len(pendientes)!=1 else ''}.\n¿Continuar?"):
            self._status('Operación cancelada.')
            return
        aplicadas = 0
        for item, ruta, nombre, sugerido in pendientes:
            vals = self.tabla.item(item, 'values')
            if not vals: continue
            nv = list(vals); nv[2] = sugerido
            self.tabla.item(item, values=nv)
            for a in self.archivos:
                if a['ruta'] == ruta:
                    a['genero'] = sugerido; break
            aplicadas += 1
        self._status(f"Sugerencias aplicadas a {aplicadas} archivo{'s' if aplicadas!=1 else ''}.")

    def _abrir_expl(self):
        import subprocess
        sel = self.tabla.selection()
        if not sel: return
        ruta = self.tabla.item(sel[0], 'values')[4]
        subprocess.Popen(f'explorer /select,"{ruta}"')

    # ─── VISTA PREVIA ────────────────────────────────────────────
    def _vista_previa(self):
        if not self.archivos:
            messagebox.showwarning("Sin archivos", "Escanea una carpeta primero.")
            return
        VentanaVistaPrevia(self.root, self.archivos,
                           self.carpeta_origen.get(), self.C,
                           on_confirmar=self._ejecutar_org)

    # ─── REGLAS UI ──────────────────────────────────────────────
    def _abrir_reglas(self):
        win = tk.Toplevel(self.root)
        win.title('Reglas personalizadas')
        win.geometry('520x360')
        tk.Label(win, text='Reglas (patrón -> tipo + genero)').pack(anchor='w', padx=8, pady=6)

        lb = tk.Listbox(win)
        lb.pack(fill='both', expand=True, padx=8, pady=6)

        def refrescar():
            lb.delete(0, 'end')
            for r in self.reglas:
                mt = r.get('match_type','contains')
                key = (r.get('pattern','').lower(), mt)
                suffix = ' (default)' if hasattr(self, '_default_keys') and key in self._default_keys else ''
                lb.insert('end', f"[{mt}] '{r.get('pattern','')}' -> {r.get('tipo','?')}/{r.get('genero','?')}{suffix}")

        def agregar():
            p = simpledialog.askstring('Patrón', 'Patrón (texto o regex):', parent=win)
            if not p: return
            tipo = simpledialog.askstring('Tipo', 'Tipo (musica/pdf/epub/video/imagen/word/excel/rom):', parent=win, initialvalue='pdf')
            genero = simpledialog.askstring('Genero', 'Genero / subcarpeta (p.ej. Facturas):', parent=win, initialvalue='')
            mt = simpledialog.askstring('Match type', 'Tipo de coincidencia: contains o regex', parent=win, initialvalue='contains')
            if tipo and p:
                self.reglas.append({'pattern': p, 'tipo': tipo, 'genero': genero or 'Sin categoria', 'match_type': mt or 'contains'})
                self._guardar_reglas(); refrescar()

        def eliminar():
            sel = lb.curselection()
            if not sel: return
            idx = sel[0]
            r = self.reglas[idx]
            key = (r.get('pattern','').lower(), r.get('match_type','contains'))
            if hasattr(self, '_default_keys') and key in self._default_keys:
                messagebox.showwarning('No permitido', 'No puedes eliminar una regla por defecto.', parent=win)
                return
            del self.reglas[idx]
            self._guardar_reglas(); refrescar()

        def editar():
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo('Editar', 'Selecciona una regla para editar.', parent=win)
                return
            idx = sel[0]
            r = self.reglas[idx]
            key = (r.get('pattern','').lower(), r.get('match_type','contains'))
            if hasattr(self, '_default_keys') and key in self._default_keys:
                messagebox.showwarning('No permitido', 'No puedes editar una regla por defecto.', parent=win)
                return
            p = simpledialog.askstring('Patrón', 'Patrón (texto o regex):', parent=win, initialvalue=r.get('pattern',''))
            if not p: return
            tipo = simpledialog.askstring('Tipo', 'Tipo (musica/pdf/epub/video/imagen/word/excel/rom):', parent=win, initialvalue=r.get('tipo','pdf'))
            genero = simpledialog.askstring('Genero', 'Genero / subcarpeta (p.ej. Facturas):', parent=win, initialvalue=r.get('genero',''))
            mt = simpledialog.askstring('Match type', 'Tipo de coincidencia: contains o regex', parent=win, initialvalue=r.get('match_type','contains'))
            self.reglas[idx] = {'pattern': p, 'tipo': tipo or r.get('tipo','pdf'), 'genero': genero or r.get('genero','Sin categoria'), 'match_type': mt or 'contains'}
            self._guardar_reglas(); refrescar()

        def _restore_confirm():
            if not messagebox.askyesno('Restaurar', 'Restaurar reglas por defecto? Se sobrescribirá el archivo de reglas.', parent=win):
                return
            try:
                self.reglas = DEFAULT_REGLAS.copy()
                self._guardar_reglas(); refrescar()
                messagebox.showinfo('Restaurado', 'Reglas por defecto restauradas.', parent=win)
            except Exception as ex:
                messagebox.showerror('Error', f'No se pudo restaurar: {ex}', parent=win)

        btnf = tk.Frame(win)
        btnf.pack(fill='x', padx=8, pady=(0,8))
        tk.Button(btnf, text='Agregar', command=agregar).pack(side='left', padx=4)
        tk.Button(btnf, text='Editar', command=editar).pack(side='left', padx=4)
        tk.Button(btnf, text='Eliminar', command=eliminar).pack(side='left', padx=4)
        tk.Button(btnf, text='Restaurar por defecto', command=_restore_confirm).pack(side='left', padx=4)
        # Checkbox para controlar sugerencias IA desde la ventana de reglas
        cb = tk.Checkbutton(btnf, text='Mostrar sugerencias IA', variable=self.var_sugerencias,
                            bg=self.C['surface'], fg=self.C['text'], selectcolor=self.C['surface2'],
                            activebackground=self.C['surface'], activeforeground=self.C['accent'],
                            font=('Segoe UI', 9))
        cb.pack(side='right', padx=6)
        # tooltip for rules window checkbox
        def _rules_tip_enter(e=None):
            try:
                self._prev_status = self.status.cget('text')
            except Exception:
                self._prev_status = ''
            self._status('Mostrar sugerencias IA: activa/desactiva las sugerencias heurísticas.')
        def _rules_tip_leave(e=None):
            try:
                self._status(self._prev_status)
            except Exception:
                self._status('')
        cb.bind('<Enter>', _rules_tip_enter)
        cb.bind('<Leave>', _rules_tip_leave)
        tk.Button(btnf, text='Cerrar', command=win.destroy).pack(side='right', padx=4)

        refrescar()

    def _restore_rules_main(self):
        if not messagebox.askyesno('Restaurar reglas',
            'Restaurar reglas por defecto? Se sobrescribirá el archivo de reglas.\n\nContinuar?'):
            return
        try:
            self.reglas = DEFAULT_REGLAS.copy()
            self._guardar_reglas()
            self._status('Reglas por defecto restauradas.')
            messagebox.showinfo('Restaurado', 'Reglas por defecto restauradas.')
        except Exception as ex:
            messagebox.showerror('Error', f'No se pudo restaurar: {ex}')

    # ─── PROGRAMAR SEMANAL ─────────────────────────────────────
    def _toggle_schedule(self):
        if self.scheduled:
            self.scheduled = False
            self.btn_sched.config(text='Programar semanal: OFF')
            self._status('Programación semanal desactivada.')
        else:
            # programar primera ejecución a 7 días desde ahora
            self.scheduled = True
            self._schedule_thread = threading.Thread(target=self._schedule_worker, daemon=True)
            self._schedule_thread.start()
            self.btn_sched.config(text='Programar semanal: ON')
            self._status('Programación semanal activada (ejecutará en 7 días).')

    def _schedule_worker(self):
        # ejecuta cada 7 días mientras self.scheduled True
        while self.scheduled:
            # esperar 7 días (inicial espera)
            wait_seconds = 7 * 24 * 3600
            # pero dormir en intervalos para poder reaccionar a cancelación
            slept = 0
            while self.scheduled and slept < wait_seconds:
                threading.Event().wait(1)
                slept += 1
            if not self.scheduled: break
            # ejecutar organización completa
            try:
                self.root.after(0, lambda: messagebox.showinfo('Programado', 'Ejecutando organización semanal.'))
                self._ejecutar_org()
            except Exception:
                pass

    # ─── ORGANIZAR ───────────────────────────────────────────────
    def _organizar(self):
        if not self.archivos:
            messagebox.showwarning("Sin archivos", "Escanea una carpeta primero.")
            return
        n   = len(self.archivos)
        sc  = sum(1 for a in self.archivos if a['genero'] == 'Sin categoria')
        if not messagebox.askyesno("Confirmar",
            f"Se moveran {n} archivos ({sc} sin categoria).\n"
            "Usa 'Vista previa' para ver exactamente que pasara.\n\n"
            "Continuar?"):
            return
        self._ejecutar_org()

    def _ejecutar_org(self):
        self.historial.clear()
        self.btn_deshacer.config(state='disabled')
        self._status("Moviendo archivos...")
        threading.Thread(target=self._org_worker,
                          args=(self.carpeta_origen.get(),), daemon=True).start()

    def _org_worker(self, base):
        movidos = errores = 0
        log = []
        for a in self.archivos:
            carp_tipo = TIPO_INFO.get(a['tipo'], TIPO_INFO['otro'])['carpeta']
            gen_clean = limpiar_carpeta(a['genero'])
            dst_dir   = os.path.join(base, carp_tipo, gen_clean)
            try:
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, a['nombre'])
                if os.path.exists(dst) and dst != a['ruta']:
                    base2, ext = os.path.splitext(a['nombre'])
                    k = 1
                    while os.path.exists(dst):
                        dst = os.path.join(dst_dir, f"{base2} ({k}){ext}"); k += 1
                src = a['ruta']
                shutil.move(src, dst)
                self.historial.append((src, dst))   # guardar para deshacer
                a['ruta'] = dst
                movidos += 1
                log.append(f"OK: {a['nombre']} -> {carp_tipo}/{gen_clean}/")
            except Exception as ex:
                errores += 1
                log.append(f"ERR: {a['nombre']}: {ex}")
            if (movidos + errores) % 5 == 0:
                self.root.after(0, self._status, f"Moviendo... {movidos} listos")
        ruta_log = os.path.join(base, '_organizador_log.txt')
        with open(ruta_log, 'w', encoding='utf-8') as f:
            f.write(f"Movidos: {movidos}  Errores: {errores}\n\n" + '\n'.join(log))
        self.root.after(0, self._fin_org, movidos, errores, ruta_log)

    def _fin_org(self, movidos, errores, ruta_log):
        if self.historial:
            self.btn_deshacer.config(state='normal')
        self._status(
            f"{movidos} archivos organizados. "
            f"{'❌ ' + str(errores) + ' errores. ' if errores else ''}"
            "Puedes deshacer con el boton 'Deshacer'.")
        messagebox.showinfo("Listo",
            f"{movidos} archivos organizados\n"
            f"{errores} errores\n\nLog: {ruta_log}\n\n"
            "Usa 'Deshacer' si quieres revertir.")

    # ─── DESHACER ────────────────────────────────────────────────
    def _deshacer(self):
        if not self.historial:
            messagebox.showinfo("Nada que deshacer", "No hay organizacion reciente.")
            return
        n = len(self.historial)
        if not messagebox.askyesno("Deshacer organizacion",
            f"Se revertiran {n} movimientos.\n"
            "Cada archivo volvera a su ubicacion original.\n\nContinuar?"):
            return
        self._status("Revirtiendo...")
        self.btn_deshacer.config(state='disabled')
        threading.Thread(target=self._deshacer_worker, daemon=True).start()

    def _deshacer_worker(self):
        revertidos = errores = 0
        for src_orig, dst_actual in reversed(self.historial):
            try:
                os.makedirs(os.path.dirname(src_orig), exist_ok=True)
                if os.path.exists(dst_actual):
                    shutil.move(dst_actual, src_orig)
                    for a in self.archivos:
                        if a['ruta'] == dst_actual:
                            a['ruta'] = src_orig; break
                    revertidos += 1
                else:
                    errores += 1
            except Exception:
                errores += 1
            if revertidos % 5 == 0:
                self.root.after(0, self._status,
                    f"Revirtiendo... {revertidos} restaurados")
        self.historial.clear()
        self.root.after(0, self._fin_deshacer, revertidos, errores)

    def _fin_deshacer(self, revertidos, errores):
        self._status(
            f"{revertidos} archivos restaurados. "
            f"{'❌ ' + str(errores) + ' errores.' if errores else ''}")
        messagebox.showinfo("Deshacer completado",
            f"{revertidos} archivos restaurados\n{errores} errores")
        if self.carpeta_origen.get():
            self._escanear()

    # ─── EXPORTAR ────────────────────────────────────────────────
    def _exportar(self):
        if not self.archivos:
            messagebox.showwarning("Sin datos", "No hay archivos escaneados.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON', '*.json')],
            initialfile='mi_biblioteca.json')
        if not ruta: return
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(self.archivos, f, ensure_ascii=False, indent=2)
        self._status(f"Lista exportada: {ruta}")

    # ─── HELPERS ─────────────────────────────────────────────────
    def _status(self, msg):
        self.status.config(text=f"  {msg}")

    def _sep(self, parent):
        f = tk.Frame(parent, bg=self.C['surface'], pady=4)
        f.pack(fill='x')
        tk.Frame(f, bg=self.C['surface2'], height=1).pack(fill='x', padx=10)

    def _sec(self, parent, titulo):
        tk.Label(parent, text=titulo, bg=self.C['surface'],
                 fg=self.C['text_muted'],
                 font=('Segoe UI', 8, 'bold')).pack(
                     anchor='w', padx=14, pady=(8, 2))

    def _check_libs(self):
        faltantes = [n for n, ok in [
            ('mutagen', HAS_MUTAGEN), ('pypdf', HAS_PYPDF),
            ('ebooklib', HAS_EBOOKLIB), ('tkinterdnd2', HAS_DND), ('Pillow', HAS_PIL)] if not ok]
        if faltantes:
            self._status(
                f"Librerias no instaladas: {', '.join(faltantes)} — "
                "Ejecuta INSTALAR_DEPENDENCIAS.bat")


# ================================================================
# PUNTO DE ENTRADA
# ================================================================

if __name__ == '__main__':
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    try:
        root.iconbitmap('icono.ico')
    except Exception:
        pass
    OrganizadorApp(root)
    root.mainloop()
