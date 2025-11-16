## 📂 Estructura del proyecto

```text
superres-flask/
│
├── app.py
├── requirements.txt
│
├── static/
│   ├── uploads/      # imágenes originales subidas por el usuario
│   └── results/      # imágenes mejoradas generadas por el modelo
│
├── templates/
│   ├── index.html    # formulario para subir imágenes
│   └── result.html   # muestra original vs mejorada
│
├── weights/          # aquí se guardan los pesos del modelo (descarga automática)
│
└── README.md

Instalación

En Windows
python -m venv venv
venv\Scripts\activate

En Linux / MacOS
python3 -m venv venv
source venv/bin/activate

Instalar dependencias
pip install -r requirements.txt

RUN:
Windows
python app.py

Linux / MacOS
python3 app.py

