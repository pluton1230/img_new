import os
import uuid

from flask import Flask, render_template, request, redirect, url_for
import torch
from PIL import Image
from py_real_esrgan.model import RealESRGAN

# ---------------------------------------------------
# CONFIGURACIÓN BÁSICA
# ---------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Limitar peso de subida (ej: 5 MB)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

UPLOAD_FOLDER = os.path.join("static", "uploads")
RESULTS_FOLDER = os.path.join("static", "results")
WEIGHTS_FOLDER = os.path.join(BASE_DIR, "weights")

# Crear carpetas si no existen
os.makedirs(os.path.join(BASE_DIR, UPLOAD_FOLDER), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, RESULTS_FOLDER), exist_ok=True)
os.makedirs(WEIGHTS_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# ---------------------------------------------------
# CARGAR MODELO REAL-ESRGAN UNA SOLA VEZ
# ---------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = RealESRGAN(device, scale=4)
# Esto descarga automáticamente los pesos si no existen
weights_path = os.path.join(WEIGHTS_FOLDER, "RealESRGAN_x4.pth")
model.load_weights(weights_path, download=True)

# Tamaño máximo de entrada para no reventar la RAM
MAX_INPUT_SIDE = 512  # píxeles (lado mayor de la imagen de entrada)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def limitar_tamano(im: Image.Image) -> Image.Image:
    """
    Si la imagen es muy grande, la reduce manteniendo proporción
    para no consumir demasiada memoria en Render.
    """
    w, h = im.size
    lado_mayor = max(w, h)

    if lado_mayor <= MAX_INPUT_SIDE:
        return im

    escala = MAX_INPUT_SIDE / float(lado_mayor)
    nuevo_tamano = (int(w * escala), int(h * escala))
    return im.resize(nuevo_tamano, Image.LANCZOS)


def mejorar_imagen(input_path: str, output_path: str) -> None:
    """
    Usa py-real-esrgan para mejorar la imagen.
    Primero limita tamaño para cuidar RAM y luego aplica super-resolución x4.
    """
    image = Image.open(input_path).convert("RGB")
    image = limitar_tamano(image)
    sr_image = model.predict(image)
    sr_image.save(output_path)


# ---------------------------------------------------
# RUTA PRINCIPAL
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        if "image" not in request.files:
            return "No se envió ninguna imagen", 400

        file = request.files["image"]

        if file.filename == "":
            return "No seleccionaste ninguna imagen", 400

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"

            # Ruta completa a la original
            upload_path = os.path.join(BASE_DIR, UPLOAD_FOLDER, filename)

            # Guardar original
            file.save(upload_path)

            # Nombre para la mejorada
            result_filename = f"{uuid.uuid4().hex}_sr.png"
            result_path = os.path.join(BASE_DIR, RESULTS_FOLDER, result_filename)

            try:
                mejorar_imagen(upload_path, result_path)
            except Exception as e:
                return f"Error al procesar la imagen con Real-ESRGAN: {e}", 500

            # Rutas relativas para las plantillas (dentro de /static)
            original_rel = f"uploads/{filename}"
            result_rel = f"results/{result_filename}"

            return redirect(
                url_for(
                    "resultado",
                    original=original_rel,
                    result=result_rel,
                )
            )
        else:
            return "Formato no permitido. Usa png/jpg/jpeg.", 400

    return render_template("index.html")


# ---------------------------------------------------
# RUTA RESULTADO
# ---------------------------------------------------
@app.route("/resultado")
def resultado():
    original = request.args.get("original")
    result = request.args.get("result")

    if not original or not result:
        return redirect(url_for("index"))

    return render_template(
        "result.html",
        original_path=original,
        result_path=result,
    )


if __name__ == "__main__":
    # Para correr en local y en Render (usa el puerto que Render indica)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)