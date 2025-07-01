import streamlit as st
import re
import os
import requests
from authenticator.controller.authentication_controller import AuthenticationController
from authenticator.controller.cookie_controller import CookieController
import authenticator.params as params
import extra_streamlit_components as stx
import time
from collections import defaultdict
from PIL import Image
import io
import streamlit as st
import requests
from llm_utils import analyze_image_with_llm, image_to_base64
import base64
from io import BytesIO


def daños(user: str, logo):
    print("Enter")
    st.sidebar.image(logo, caption="CAR ACCIDENTS", use_container_width=True)
    st.title("🛠️ Visual Analysis of Vehicle Damage")

    # Selector de modelo LLM
    modelos_llm = ["Pixtral(mistralai/pixtral-12b)",
                   "Granite(ibm/granite-vision-3-2-2b)",
                   "Llama(meta-llama/llama-3-2-11b-vision-instruct)",
                   "GPT4o-mini(openai/gpt-4o-mini)",
                   "Qwen(qwen/qwen2.5-vl-72b-instruct:free)",
                   "Gemma(google/gemma-3-27b-it:free)",
                   "Gemini(google/gemini-2.0-flash-exp:free)",
                   "Grok(x-ai/grok-vision-beta)"]
    modelo_seleccionado = st.selectbox(
        "Select the LLM model for analysis:", modelos_llm)
    st.markdown(
        """
    <hr style="border: 2px solid #888; margin-top: 30px; margin-bottom: 30px;">
    """,
        unsafe_allow_html=True
    )
    # Vistas del vehículo a cargar
    vistas = {
        "Front": "frontal",
        "Right": "right",
        "Left": "left",
        "Rear": "rear"
    }

    for titulo, clave in vistas.items():
        with st.expander(f"📷 Load {titulo} image"):
            archivo = st.file_uploader(f"Upload {titulo.lower()} image", type=[
                                       "jpg", "jpeg", "png"], key=clave)

            encoded_image = ""

            if archivo:
                try:
                    imagen_original = Image.open(archivo)

                    bytes_data = archivo.getvalue()

                    st.markdown(
                        f"<p style='text-align:center; font-size:18px; font-weight:bold;'>Original image - {titulo}</p>",
                        unsafe_allow_html=True
                    )
                    st.image(imagen_original)

                except Exception as e:
                    st.error(
                        "Error processing image. Make sure you upload a valid file.")
                st.markdown(
                    f"<p style='text-align:center; font-size:18px; font-weight:bold;'>Damage detection image - {titulo}</p>",
                    unsafe_allow_html=True
                )

                # encoded_image = image_to_base64(imagen_original)

                encoded_image = base64.b64encode(bytes_data).decode('utf-8')

                try:
                    response = requests.post(
                        url="https://damage-detection-endpoint-url-here/damage_detection",
                        json={"image_base64": encoded_image},
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code == 200:
                        resultado = response.json()
                        clasificacion = resultado[0]
                        imagen_partes = resultado[1]
                        partes_danadas = resultado[2]
                        imagen_bytes = base64.b64decode(imagen_partes)
                        imagen_dañada = Image.open(BytesIO(imagen_bytes))
                        st.image(imagen_dañada,
                                 caption=f"Damage detection - {titulo}")

                        st.success("📝 LLM model description :")
                        response = analyze_image_with_llm(
                            modelo_seleccionado, imagen_original, clasificacion, partes_danadas)
                        st.write(response)
                    else:
                        st.error(
                            f"❌ Response error: {response.status_code}")

                except Exception as e:
                    st.error(
                        f"❌ Unable to connect to server\n\n{str(e)}")


def image_to_base64_json(base64_encoded):

    # output_file = "image_base64.txt"

    json_data = {
        "image_base64": base64_encoded
    }

    # with open(output_file, 'w') as outfile:
    #    json.dump(json_data, outfile, indent=4)
    # print(f"Image converted to base64 and saved to {output_file}")

    return json_data


def levantamiento_proyectos_page(user: str, logo):
    st.sidebar.image(logo, caption="CAR ACCIDENTS", use_container_width=True)

    # Diccionarios para traducir de español a inglés
    translate = {
        "fault": {
            "Third Party": "Third Party",
            "Policy Holder": "Policy Holder"
        },
        "vehicle_category": {
            "Sedan": "Sedan",
            "Sport": "Sport",
            "Utility": "Utility"
        },
        "vehicle_price": {
            "less than 20000": "less than 20000",
            "20000 to 29000": "20000 to 29000",
            "30000 to 39000": "30000 to 39000",
            "40000 to 59000": "40000 to 59000",
            "more than 69000": "more than 69000"
        },
        "past_claims": {
            "none": "none",
            "1": "1",
            "2 a 4": "2 to 4",
            "more than 4": "more than 4"
        },
        "base_policy": {
            "Collision": "Collision",
            "Liability civil": "Liability",
            "All Perils": "All Perils"
        },
        "Sex": {
            "Male": "Male",
            "Female": "Female"
        }
    }

    st.title("Claims Assessment Form 🚗")

    with st.form("fraud_form"):
        st.subheader("Accident information")

        category_es = st.selectbox("Vehicle category", list(
            translate["vehicle_category"].keys()))
        price_es = st.selectbox("Vehicle price", list(
            translate["vehicle_price"].keys()))
        claims_es = st.selectbox("Number of past claims", list(
            translate["past_claims"].keys()))
        fault_es = st.selectbox("Whose fault was it?",
                                list(translate["fault"].keys()))
        policy_es = st.selectbox("Base policy type", list(
            translate["base_policy"].keys()))
        sex_es = st.selectbox("Driver's gender:",
                              list(translate["Sex"].keys()))

        submit = st.form_submit_button("Assess")

    if submit:
        # Limpiar contenedores anteriores
        status_placeholder = st.empty()
        result_placeholder = st.empty()

        # Traducción al inglés
        input_data = {
            "VehicleCategory": translate["vehicle_category"][category_es],
            "VehiclePrice": translate["vehicle_price"][price_es],
            "PastNumberOfClaims": translate["past_claims"][claims_es],
            "Fault": translate["fault"][fault_es],
            "Sex": translate["Sex"][sex_es],
            "BasePolicy": translate["base_policy"][policy_es]
        }

        status_placeholder.info("⏳ Sending data to the model...")

        try:
            response = requests.post(
                url="https://fraud-detection-endpoint-url-here/fraud_detection",
                json=input_data,
                headers={"Content-Type": "application/json"}
            )
            print(input_data)
            if response.status_code == 200:
                resultado = response.json()
                print(resultado)
                status_placeholder.success("✅ Result received")
                with result_placeholder.container():
                    st.subheader("Model result")
                    st.markdown(f"**🔍 {resultado[0]}**")
            else:
                status_placeholder.error(
                    f"❌ Response error: {response.status_code}")
                result_placeholder.text(response.text)

        except Exception as e:
            status_placeholder.error(
                f"❌ Unable to connect to the server\n\n{str(e)}")


def sub_main(cookie_controller):
    logo_path = r"media/logo1.png"  # Reemplaza con la ruta de tu archivo de imagen
    logo = Image.open(logo_path)
    if "area" not in st.session_state:
        st.session_state.area = None
    if "last_AI" not in st.query_params:
        st.query_params["last_AI"] = False
    if "nuevo_HU" not in st.session_state:
        st.session_state.nuevo_HU = False
    # Mostrar el contenido de la página activa
    if st.query_params["page"] == "Daños":
        daños(st.session_state["name"], logo)
    elif st.query_params["page"] == "Pro_fraude":
        levantamiento_proyectos_page(st.session_state["name"], logo)
    # Navegación entre ventanas
    with st.sidebar:
        # Usar Markdown y CSS para darle forma circular a la imagen en el sidebar
        st.title("Process")

        # Obtener la página actual
        current_page = st.query_params.get("page", "")

        # Configurar botones con estilos dinámicos
        buttons = [
            ("1)📝  Fraud probability assessment 🚗", "Pro_fraude"),
            ("2)🖼️   Severity and damaged parts analysis 🚗", "Daños")
        ]

        for label, page in buttons:
            button_type = "primary" if current_page == page else "secondary"

            if st.button(label, use_container_width=True, type=button_type):
                if current_page != page:
                    st.session_state.messages = []
                    st.session_state.nuevo_HU = False
                    st.session_state.nuevo_p = False
                    st.query_params["last_AI"] = True
                    st.query_params["page"] = page
                    st.rerun()

        st.divider()
        with st.expander("SESSION"):
            st.subheader(st.session_state["name"])
            st.caption(st.session_state["roles"])
            if st.button('Close session'):
                st.session_state['authentication_status'] = None
                st.session_state.messages = []
                cookie_controller.delete_cookie()
            st.divider()


# Configuración de la app
st.set_page_config(page_title="CAR ACCIDENTS", page_icon="🤖")

if "page" not in st.query_params:
    # st.query_params.page=""
    st.query_params["page"] = "Pro_fraude"
# Obtener nombres de los archivos en la carpeta "chats"
nombres_archivos = []

if "messages" not in st.session_state:
    st.session_state.messages = []


def main():
    # Cargar el logo del cohete
    logo_path = r"media/logo1.png"  # Reemplaza con la ruta de tu archivo de imagen
    logo = Image.open(logo_path)
    col2, col3 = st.columns(2)
    cookie_controller = CookieController(
        "Siniestros", "Siniestros", 1)  # 0.000694444
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
        token = cookie_controller.get_cookie()
        if token:
            st.session_state['email'] = token['email']
            st.session_state['name'] = token['name']
            st.session_state['roles'] = token['roles']
            st.session_state['authentication_status'] = True
            st.session_state['username'] = token['username']
            # self.credentials['usernames'][token['username']]['logged_in'] = True
        time.sleep(params.PRE_LOGIN_SLEEP_TIME)
        # Obtener el token de la cookie si existe

    try:
        with col2:
            # Título del formulario
            if st.session_state['authentication_status'] != True:
                st.header("Access your account")

                # Campos del formulario de login
                username = st.text_input("Username:", max_chars=50)
                password = st.text_input(
                    "Password:", type="password", max_chars=50)

                # Botón de login
                login = st.button("Login")
                if login:
                    respuesta, verificacion = Autentificar(username, password)
                    if verificacion == True:
                        if "area" not in st.session_state:
                            st.session_state.area = None
                        resultado = "Pro_fraude"
                        if resultado:
                            st.session_state.area = resultado
                        else:
                            st.session_state.area = None
                        credentials = {"usernames": {
                            'username': username,
                            'password': password,
                            'email': "juan.jo98@hotmail.com",
                            'roles': "User",
                            "failed_login_attempts": "0",  # Will be managed automatically
                            "logged_in": "False",  # Will be managed automatically
                            'name': respuesta}
                        }
                        # Inicializar el objeto AuthenticationController con los parámetros deseados
                        auth_controller = AuthenticationController(
                            credentials=credentials,    # Credenciales del usuario
                            # Establecer si los passwords deben ser automáticamente hasheados
                            auto_hash=True,
                        )
                    # Realizar el intento de inicio de sesión
                        if auth_controller.login(respuesta, password, 3, 3, single_session=True):
                            cookie_controller.set_cookie()
                            st.rerun()

                    else:
                        st.session_state['authentication_status'] = False

        if st.session_state['authentication_status']:
            sub_main(cookie_controller)
        elif st.session_state['authentication_status'] is False:
            with col3:
                st.image(logo, width=300)
            st.error('Wrong username or password')
        elif st.session_state['authentication_status'] is None:
            with col3:
                st.image(logo, width=300)
            st.warning('Please enter your Username and Password')
    except Exception as e:
        st.error(e)


def Autentificar(username, password):
    return "Juan Jose Hurtado", True


# Ejecutar la aplicación principal
if __name__ == "__main__":
    main()
