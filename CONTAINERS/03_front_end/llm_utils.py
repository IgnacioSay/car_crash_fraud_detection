import base64
import requests
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
import io
from PIL import Image


def image_to_base64(image: Image.Image) -> str:
    # Detectar el formato original o usar PNG como predeterminado si no está disponible
    formato = image.format if image.format else "PNG"

    # Crear un buffer en memoria
    buffered = io.BytesIO()

    # Guardar la imagen en el buffer con su formato original (o forzar PNG)
    image.save(buffered, format=formato)

    # Obtener el contenido en base64
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_string
# --- Funciones auxiliares ---


def get_credentials():
    return Credentials(
        url="https://us-south.ml.cloud.ibm.com",
        api_key="your_api_key_here"
    )


def get_project_id():
    return "your_project_id_here"


def check_string(txt):
    return txt in ["01-minor", "02-moderate", "03-severe"]


def formulate_question(severity_classification, categories):

    categories_txt_list = create_list(categories)

    if check_string(severity_classification):
        third_question = (
            f"The insurance agent classified the overall severity damage as: {severity_classification}. "
            "Given that the severity damage classification options are only 01-minor, 02-moderate, or 03-severe. "
            "Do you agree with the agent's classification? or, would you choose a different option?"
        )
    else:
        third_question = (
            "In one short sentence, can you classify the overall severity damage using only "
            "01-minor, 02-moderate, or 03-severe options?"
        )

    question = (
        "You are a helpful ai assistant for an insurance agent specialized on car parts damaged and their associated repair costs. "
        "Insurance agent has received an image from a claim for a vehicle damage with annotaded boxes indicating the damaged car parts. "
        "Based on the image, I need you to answer 3 questions. First question: can you describe the car model and color? "
        "Second question: Can you make a main list of the possibly damaged parts whether they are annotated with a box in the image or not? "
        "The list should contain at least one damaged car part but no more than seven damaged car parts. For each damaged car part create a sublist answering the following bullets: "
        "1. Damaged Car part, 2. Description of the damage, 3. Is the damaged part annotated on image? (yes or no), 4. Estimated damage severity of the part (01-minor, 02-moderate, or 03-severe). "
        "If there are no visible damaged car parts then omit the main list and just say so. Make sure the main list does not contain repeated items. "
        "Please note that the image has already the following damaged parts annotated within a box: " + categories_txt_list +
        "Third question: " + third_question
    )

    return question

# --- Modelos Watsonx ---


def llm_model(model_name):
    credentials = get_credentials()
    project_id = get_project_id()

    models = {
        "Pixtral": "mistralai/pixtral-12b",
        "Granite": "ibm/granite-vision-3-2-2b",
        "Llama": "meta-llama/llama-3-2-11b-vision-instruct",
        "Tiny": "ibm/granite-13b-instruct-v2",
        "Mixtral": "mistralai/mixtral-8x7b-instruct-v01",
    }

    # model_id = models.get(model_name, "mistralai/pixtral-12b")
    # model_id = models.get(model_name, model_name)

    if model_name == "Pixtral":
        model_id = "mistralai/pixtral-12b"

    if model_name == "Granite":
        model_id = "ibm/granite-vision-3-2-2b"

    if model_name == "Llama":
        model_id = "meta-llama/llama-3-2-11b-vision-instruct"

    if model_name == "Tiny":
        model_id = "ibm/granite-13b-instruct-v2"

    if model_name == "Mixtral":
        model_id = "mistralai/mixtral-8x7b-instruct-v01"

    return ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=project_id,
        params={"max_tokens": 800, "temperature": 0, "seed": 123}
    )


# --- Función principal unificada ---

def create_list(my_list):
    numbered_list_str = ""
    for i, item in enumerate(my_list):
        numbered_list_str += f"{i+1}. {item}"
        if i < len(my_list) - 1:
            numbered_list_str += ", "

    if len(my_list) == 0:
        numbered_list_str = "No damaged parts detected on image"

    return numbered_list_str


def analyze_image_with_llm(model_name, image, severity_classification, partes_danadas):
    encoded_string = image_to_base64(image)
    question = formulate_question(severity_classification, partes_danadas)

    # Extraer identificador real del modelo (lo que está dentro de paréntesis)
    if "(" in model_name and ")" in model_name:
        model_id = model_name.split("(")[1].replace(")", "").strip()
    else:
        return "❌ Modelo inválido. Debe tener formato Nombre(identificador)."

    # --- Modelos OpenRouter ---
    if any(prefix in model_id for prefix in ["openai", "google", "qwen", "x-ai"]):
        API_KEY = "your_open_ai_api_key_here"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://tusitio.com",
            "X-Title": "Análisis de imagen con modelo vision",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]
                }
            ]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            response_result = response.json(
            )["choices"][0]["message"]["content"]
        else:
            response_result = f"Error {response.status_code}: {response.text}"

    # --- Modelos Watsonx ---
    else:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_string}"}}
                ]
            }
        ]

        model_prefix = model_name.split("(")[0]
        model = llm_model(model_prefix)
        result = model.chat(messages=messages)
        response_result = result["choices"][0]["message"]["content"]

    response_result = " The severity classification from the vision model is: " + severity_classification + "\n\n The answer from the " + \
        model_name + " LLM is : \n\n\n" + response_result

    return response_result
