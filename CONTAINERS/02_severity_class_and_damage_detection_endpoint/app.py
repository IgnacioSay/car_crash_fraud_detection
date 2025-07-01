# app.py
from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename

import numpy as np
# import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns
import os
import joblib
import io
import sys
import json
import uuid
import math


import pickle

import requests
import base64
import getpass
import sys

from PIL import Image
# from ibm_watsonx_ai import Credentials
# from ibm_watsonx_ai.foundation_models import ModelInference

import getpass

import os
import types
# from botocore.client import Config #manda error
# import ibm_boto3

import cv2
from ultralytics import YOLO
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.image as mpimg

import tensorflow as tf


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory database for simplicity
# inventory = {}


@app.route("/")
def hello():
    return "Hello, World! Damaged parts detection endpoint running"


@app.route('/damage_detection', methods=['POST'])
def handle_post():

    data = request.json

    # data es un diccionario...hay que convertirlo a json string

    json_string = json.dumps(data)

    # json_string = "[" + json_string + "]"

    # lista_resps = main_fraud_detection(json_string)

    # contenido = obten_texto(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    contenido = json_string

    image_path = crea_imagen(contenido)

    severity_clasif = main_severity_classification(image_path)

    damaged_parts_detection = main_damage_detection(image_path)

    damaged_parts_detection_img = damaged_parts_detection[0]

    damaged_parts_detection_list = damaged_parts_detection[1]

    # return "La clasificacion de severidad es: " + severity_clasif + " y la imagen de deteccion es: " + damaged_parts_detection_img

    img_base64 = image_to_base64(damaged_parts_detection_img)

    preds_list = []

    preds_list.append(severity_clasif)

    preds_list.append(img_base64)

    preds_list.append(damaged_parts_detection_list)

    # Una vez obtenida la lista con predicciones (severidad y deteccion de partes) borramos las imagenes creadas

    os.remove(image_path)

    os.remove(damaged_parts_detection_img)

    return preds_list


@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        base64_string = data['image']

        # Decode the base64 string
        image_bytes = base64.b64decode(base64_string)

        # Save the image (example)
        filename = "uploaded_image.png"
        with open(filename, "wb") as fh:
            fh.write(image_bytes)

        return jsonify({'message': 'Image uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return 'File uploaded successfully'
            contenido = obten_texto(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            image_path = crea_imagen(contenido)
            # lista_resps = main_fraud_detection(contenido)

            severity_clasif = main_severity_classification(image_path)
            # return "La clasificacion de severidad es: " + severity_clasif

            damaged_parts_detection_img_list = main_damage_detection(
                image_path)

            damaged_parts_detection_img = damaged_parts_detection_img_list[0]

            damaged_parts_detection_list = damaged_parts_detection_img_list[1]

            txt_list = create_list(damaged_parts_detection_list)

            return "La clasificacion de severidad es: " + severity_clasif + ", la lista de partes dañadas es: " + txt_list + ", y la imagen de deteccion es: " + damaged_parts_detection_img

    return render_template('upload.html')


def image_to_base64(image_path):
    """
    Reads an image from the given path and converts it to a Base64 string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The Base64 encoded string of the image, or None if an error occurs.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(
                image_file.read()).decode("utf-8")
            return encoded_string
    except FileNotFoundError:
        print(f"Error: Image not found at path: {image_path}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")
        return None


def obten_texto(nombre_archivo):
    with open(nombre_archivo, "r") as file:
        content = file.read()
        return content


def crea_imagen(texto_json):
    try:
        myuuid = uuid.uuid4()

        # print('Your UUID is: ' + str(myuuid))
        data = json.loads(texto_json)
        base64_string = data['image_base64']

        # Decode the base64 string
        image_bytes = base64.b64decode(base64_string)

        # Save the image (example)
        filename = "uploaded_image_"+str(myuuid)+".jpg"

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, "wb") as fh:
            fh.write(image_bytes)

        # return jsonify({'message': 'Image uploaded successfully'})

        # se hace el resize de la imagen si es necesario (para que sea de 640 x 640 minimo)

        resized_image_path = resize_image(file_path)

        # return file_path

        return resized_image_path

    except Exception as e:
        return jsonify({'error': str(e)}), 400


def resize_image(path):
    # Load the image
    image = cv2.imread(path)

    # Get the original size
    height, width = image.shape[:2]

    height_factor = 640 / height

    width_factor = 640 / width

    factor = 1

    if height_factor > 1.0 or width_factor > 1.0:

        factor = find_greater(height_factor, width_factor)

        # Convertimos el factor a entero (redondeado hacia arriba)

        factor = math.ceil(factor)

    # Define the new size (e.g., double the size)
    new_width = width * factor
    new_height = height * factor
    new_size = (new_width, new_height)

    # Resize the image
    resized_image = cv2.resize(image, new_size)

    # Save the resized image

    myuuid = uuid.uuid4()

    filename = "resized_image_"+str(myuuid)+".jpg"

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    cv2.imwrite(file_path, resized_image)

    os.remove(path)

    return file_path


def find_greater(num1, num2):
    """Compares two numbers and returns the greater one.

    Args:
      num1: The first number.
      num2: The second number.

    Returns:
      The greater of the two numbers.
    """
    if num1 > num2:
        return num1
    else:
        return num2

# Función para descargar el modelo de clasificación de severidad desde cloud object storage y guardarlo en la instancia


def retrive_yolo_severity_classif_model():
    object_key = 'best_severity_classification_yolo_11.pt'
    return object_key

# Funcion para descargar el modelo desde cloud-object-storage y guardarlo en la instancia


def retrive_yolo_model():
    object_key = 'yolo11x-best_46_classes.pt'
    return object_key


# Función para definir el modelo Yolo de clasificación de severidad

def yolo_severity_classif_model():
    model_path = retrive_yolo_severity_classif_model()
    model = YOLO(model_path)
    return model

# Función para definir el modelo Yolo de detección de partes dañadas


def yolo_model():
    model_path = retrive_yolo_model()
    model = YOLO(model_path)
    return model


# Definimos la función para convertir la respuesta de imagen con anotaciones de Yolo a JPEG
def convert_result_to_jpeg(res_plotted):
    img = res_plotted
    image_rgb_01 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    myuuid = uuid.uuid4()

    # img_name = 'jpg_image.jpg'

    # cv2.imwrite('jpg_image.jpg', cv2.cvtColor(image_rgb_01, cv2.COLOR_RGB2BGR))
    # return img_name

    img_name = "analyzed_image_"+str(myuuid)+".jpg"
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_name)
    cv2.imwrite(img_path, cv2.cvtColor(image_rgb_01, cv2.COLOR_RGB2BGR))
    return img_path


# Definimos una función para confirmar si el argumento es un string que contenga el resultado de la clasificación de severidad

def check_string(txt):
    if txt == "01-minor" or txt == "02-moderate" or txt == "03-severe":
        return True
    else:
        return False


def create_list(my_list):
    numbered_list_str = ""
    for i, item in enumerate(my_list):
        numbered_list_str += f"{i+1}. {item}"
        if i < len(my_list) - 1:
            numbered_list_str += ", "

    if len(my_list) == 0:
        numbered_list_str = "No damaged parts detected on image"

    return numbered_list_str


def get_categories(results):

    category_names = results[0].names
    categories = []
    for result in results:
        boxes = result.boxes  # Boxes object for bounding box outputs

    cls = boxes.cls

    for category in cls:
        item = category.item()
        int_item = int(item)
        categories.append(category_names[int_item])

    return categories


def main_damage_detection(image_path):
    model = yolo_model()
    # image_path = get_image()
    results = model(image_path, conf=0.1)
    res_plotted = results[0].plot()
    categories = get_categories(results)
    # result = augment_api_request_body(model_name, res_plotted, severity_classification)
    # display_results(result, 'jpg_image.jpg')

    result = convert_result_to_jpeg(res_plotted)
    return result, categories


def main_severity_classification(image_path):
    model = yolo_severity_classif_model()
    # image_path = get_image()
    result = model(image_path)
    probs = result[0].probs
    max_index = tf.argmax(probs.data).numpy().item()
    clasif_names = result[0].names
    resp = clasif_names[max_index]
    return resp


# if __name__ == '__main__':
#    app.run(debug=True)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# NOTA: USAR IMAGENES DEL DATASET DE DETECCION DE AUTOPARTES DAÑADAS DE ROBOFLOW PORQUE EL DE GITHUB TIENE MUY BAJA RESOLUCION
