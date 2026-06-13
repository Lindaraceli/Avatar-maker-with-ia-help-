#avatar maker

import tkinter as tk
import os
from PIL import Image, ImageTk

# Compatibilidad con versiones recientes de Pillow: Image.ANTIALIAS fue removido.
try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except Exception:
    RESAMPLE_LANCZOS = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", 1))

# Las imágenes se cargan dinámicamente desde carpetas; se prescinde
# de listas estáticas y contadores antiguos para mantener el archivo más pequeño.


def load_assets(base_dir=None, exts=(".png", ".jpg", ".jpeg", ".gif")):
    """Recorre las carpetas del directorio del script y carga imágenes.

    Devuelve un dict: { carpeta: [(ruta, PIL.Image), ...], ... }
    """
    if base_dir is None:
        base_dir = os.path.dirname(__file__)
    assets = {}
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if not os.path.isdir(path):
            continue
        if entry.startswith("__"):
            continue
        # Si hay subdirectorios dentro de la carpeta de la capa, cada subdirectorio
        # representa un diseño y contendrá las variantes/colores.
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if subdirs:
            designs = {}
            for d in subdirs:
                dpath = os.path.join(path, d)
                imgs = []
                for root, _, files in os.walk(dpath):
                    for f in files:
                        if f.lower().endswith(exts):
                            fp = os.path.join(root, f)
                            try:
                                img = Image.open(fp).convert("RGBA")
                                imgs.append((fp, img))
                            except Exception as e:
                                print("Error cargando imagen:", fp, e)
                if imgs:
                    designs[d] = imgs
            if designs:
                assets[entry] = designs
        else:
            images = []
            for root, _, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(exts):
                        fp = os.path.join(root, f)
                        try:
                            img = Image.open(fp).convert("RGBA")
                            images.append((fp, img))
                        except Exception as e:
                            print("Error cargando imagen:", fp, e)
            if images:
                assets[entry] = images
    return assets


# Capas en orden de fondo -> adelante
LAYERS = [
    "pelo atras",
    "skin",
    "ropa",
    "ojos",
    "cejas",
    "boca",
    "pelo delante",
]

# Estado de índices por capa: diseño y color (o variante)
design_indices = {layer: 0 for layer in LAYERS}
color_indices = {layer: 0 for layer in LAYERS}

# Referencias para evitar que PhotoImage sea recolectado
images_refs = {layer: [] for layer in LAYERS}
# IDs de los items en el canvas por capa
image_items = {}

def prepare_layer_photos(assets, size=(450, 450)):
    """Convierte las PIL.Images cargadas en ImageTk.PhotoImage redimensionadas.

    Devuelve dict: {layer: [[PhotoImage,...], [PhotoImage,...], ...], ...}
    Cada sublista corresponde a un diseño; dentro están las variantes/colores.
    Si una capa no existe, crea una única lista con una imagen transparente.
    """
    layer_photos = {}
    for layer in LAYERS:
        designs_photos = []
        if layer in assets:
            layer_data = assets[layer]
            # Si layer_data es un dict (estructura de diseños por subcarpeta), mantener compatibilidad
            if isinstance(layer_data, dict):
                for design, imgs in layer_data.items():
                    photos = []
                    for _, img in imgs:
                        try:
                            img_resized = img.resize(size, resample=RESAMPLE_LANCZOS)
                            photo = ImageTk.PhotoImage(img_resized)
                            photos.append(photo)
                        except Exception as e:
                            print("Error al preparar foto:", e)
                    if photos:
                        designs_photos.append(photos)
            else:
                # layer_data es una lista simple de imágenes.
                # Para capas que solo tienen variantes de color (p.ej. 'skin' y 'ropa'),
                # tratamos todas las imágenes como variantes de un mismo diseño.
                if layer in ("skin", "ropa"):
                    photos = []
                    for _, img in layer_data:
                        try:
                            img_resized = img.resize(size, resample=RESAMPLE_LANCZOS)
                            photo = ImageTk.PhotoImage(img_resized)
                            photos.append(photo)
                        except Exception as e:
                            print("Error al preparar foto:", e)
                    if photos:
                        designs_photos.append(photos)
                else:
                    # Cada imagen es un diseño independiente con una sola variante
                    for _, img in layer_data:
                        try:
                            img_resized = img.resize(size, resample=RESAMPLE_LANCZOS)
                            photo = ImageTk.PhotoImage(img_resized)
                            designs_photos.append([photo])
                        except Exception as e:
                            print("Error al preparar foto:", e)
        if not designs_photos:
            empty = Image.new("RGBA", size, (0, 0, 0, 0))
            designs_photos = [[ImageTk.PhotoImage(empty)]]
        layer_photos[layer] = designs_photos
    return layer_photos

def init_canvas_layers(canvas, layer_photos):
    """Crea los items en el canvas en el orden de LAYERS y guarda referencias."""
    images_refs.clear()
    image_items.clear()
    w = int(canvas['width'])
    h = int(canvas['height'])
    cx = w // 2
    cy = h // 2
    for layer in LAYERS:
        designs = layer_photos[layer]
        d_idx = design_indices.get(layer, 0) % len(designs)
        c_idx = color_indices.get(layer, 0) % len(designs[d_idx])
        photo = designs[d_idx][c_idx]
        item = canvas.create_image(cx, cy, image=photo)
        image_items[layer] = item
        images_refs[layer] = [photo]

def update_canvas_layers(canvas, layer_photos):
    """Actualiza cada item del canvas según índices de diseño/colour y mantiene referencias."""
    for layer in LAYERS:
        photos = layer_photos.get(layer)
        if not photos:
            continue
        designs = photos
        d_idx = design_indices.get(layer, 0) % len(designs)
        c_idx = color_indices.get(layer, 0) % len(designs[d_idx])
        photo = designs[d_idx][c_idx]
        item = image_items.get(layer)
        if item is None:
            # crear si faltara
            w = int(canvas['width'])
            h = int(canvas['height'])
            cx = w // 2
            cy = h // 2
            item = canvas.create_image(cx, cy, image=photo)
            image_items[layer] = item
        else:
            canvas.itemconfig(item, image=photo)
        # mantener referencia
        images_refs[layer] = [photo]

# Variables antiguas eliminadas: ahora usamos `design_indices` y `color_indices`.

# Helpers para navegar diseños y colores usando la estructura efectivamente cargada
def _next_design(layer):
    designs = layer_photos.get(layer) if 'layer_photos' in globals() else None
    if not designs:
        return
    d_idx = design_indices.get(layer, 0)
    d_idx = (d_idx + 1) % len(designs)
    design_indices[layer] = d_idx
    try:
        update_canvas_layers(canvas, layer_photos)
    except Exception:
        pass

def _next_color(layer):
    designs = layer_photos.get(layer) if 'layer_photos' in globals() else None
    if not designs:
        return
    d_idx = design_indices.get(layer, 0) % len(designs)
    variants = len(designs[d_idx]) if designs[d_idx] else 1
    c_idx = color_indices.get(layer, 0)
    c_idx = (c_idx + 1) % variants
    color_indices[layer] = c_idx
    try:
        update_canvas_layers(canvas, layer_photos)
    except Exception:
        pass

# Wrappers usados por los botones
def color_piel():
    _next_color('skin')

def color_ropa():
    _next_color('ropa')

def diseno_ceja():
    _next_design('cejas')

def diseno_boca():
    _next_design('boca')

def diseno_ojos():
    _next_design('ojos')

def color_ojos():
    _next_color('ojos')

def diseno_bp():
    _next_design('pelo atras')

def color_bp():
    _next_color('pelo atras')

def diseno_chas():
    _next_design('pelo delante')

def color_chas():
    _next_color('pelo delante')

#ventana 
ventana = tk.Tk()
ventana.title("Avatar maker")
ventana.geometry("500x650")

canvas = tk.Canvas(ventana, width = "450", height= "450", bg="beige")
canvas.pack()
# Botones organizados en filas; agrupar `skin`+`ropa` y `cejas`+`boca` para que quepan en pantalla.

# Skin + Ropa (colores)
row_skin_ropa = tk.Frame(ventana)
row_skin_ropa.pack(fill="x", padx=8, pady=2)
boton_piel = tk.Button(row_skin_ropa, text="Skin colour", command=color_piel)
boton_piel.pack(side=tk.LEFT)
boton_ropa = tk.Button(row_skin_ropa, text="Clothes colour", command=color_ropa)
boton_ropa.pack(side=tk.LEFT, padx=6)

# Cejas + Boca (diseños)
row_cejas_boca = tk.Frame(ventana)
row_cejas_boca.pack(fill="x", padx=8, pady=2)
boton_cejas = tk.Button(row_cejas_boca, text="Eyebrow", command=diseno_ceja)
boton_cejas.pack(side=tk.LEFT)
boton_boca = tk.Button(row_cejas_boca, text="Mouth", command=diseno_boca)
boton_boca.pack(side=tk.LEFT, padx=6)

# Ojos (diseño + color)
row_ojos = tk.Frame(ventana)
row_ojos.pack(fill="x", padx=8, pady=2)
boton_ojos = tk.Button(row_ojos, text="Eyes", command=diseno_ojos)
boton_ojos.pack(side=tk.LEFT)
boton_colojos = tk.Button(row_ojos, text="Eyes colour", command=color_ojos)
boton_colojos.pack(side=tk.LEFT, padx=6)

# Pelo atras (diseño + color)
row_bp = tk.Frame(ventana)
row_bp.pack(fill="x", padx=8, pady=2)
boton_bp = tk.Button(row_bp, text="Back hair", command=diseno_bp)
boton_bp.pack(side=tk.LEFT)
boton_colbp = tk.Button(row_bp, text="Back hair colour", command=color_bp)
boton_colbp.pack(side=tk.LEFT, padx=6)

# Pelo delante / chasquilla (diseño + color)
row_chas = tk.Frame(ventana)
row_chas.pack(fill="x", padx=8, pady=2)
boton_chas = tk.Button(row_chas, text="Front hair", command=diseno_chas)
boton_chas.pack(side=tk.LEFT)
boton_colchas = tk.Button(row_chas, text="Front hair colour", command=color_chas)
boton_colchas.pack(side=tk.LEFT, padx=6)

# Inicializar assets y capas
assets = load_assets()
layer_photos = prepare_layer_photos(assets, size=(450, 450))
init_canvas_layers(canvas, layer_photos)

ventana.mainloop()



ventana.mainloop()


