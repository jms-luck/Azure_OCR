import streamlit as st
import requests
import json
import time

# Azure API details
AZURE_KEY = "Azure ai service key"  # Replace with your Azure key
AZURE_ENDPOINT_TRANSLATOR = "https://api.cognitive.microsofttranslator.com"
AZURE_ENDPOINT_VISION = "https://servicename.cognitiveservices.azure.com/" #replace with your service name
AZURE_REGION = "eastus"  # Example: "eastus"

# Function to translate text
def translate_text(text, target_lang):
    url = f"{AZURE_ENDPOINT_TRANSLATOR}/translate?api-version=3.0&to={target_lang}"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_REGION,
        "Content-Type": "application/json",
    }
    body = [{"text": text}]
    
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        translation = response.json()
        return translation[0]["translations"][0]["text"]
    else:
        return "Error: Unable to translate text. Check API credentials."

# Function to recognize handwritten text using Azure Computer Vision
def recognize_handwritten_text(image):
    url = f"{AZURE_ENDPOINT_VISION}/vision/v3.2/read/analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/octet-stream"
    }
    response = requests.post(url, headers=headers, data=image)
    if response.status_code == 202:
        operation_url = response.headers["Operation-Location"]
        return operation_url
    else:
        st.error(f"Error recognizing text: {response.status_code}, {response.text}")
        return None

def get_recognized_text(operation_url):
    headers = {"Ocp-Apim-Subscription-Key": AZURE_KEY}
    # Add delay and retry logic
    max_retries = 10
    retry_delay = 1
    
    for _ in range(max_retries):
        response = requests.get(operation_url, headers=headers)
        result = response.json()
        
        if "status" in result:
            if result["status"] == "succeeded":
                text = ""
                if "analyzeResult" in result and "readResults" in result["analyzeResult"]:
                    for read_result in result["analyzeResult"]["readResults"]:
                        if "lines" in read_result:
                            for line in read_result["lines"]:
                                text += line["text"] + " "
                return text.strip()
            elif result["status"] == "failed":
                return "Error: Failed to recognize text."
            else:
                # Still processing, wait and retry
                time.sleep(retry_delay)
        else:
            st.error(f"Unexpected response format: {json.dumps(result)}")
            return "Error: Unexpected response format."
    
    return "Error: Operation timed out after multiple retries."

# Streamlit UI
st.title("Azure Translator & Handwritten Text Recognition")

# Image upload for handwritten text recognition
uploaded_image = st.file_uploader("Upload a handwritten text image", type=["jpg", "png", "jpeg"])
if uploaded_image is not None:
    st.image(uploaded_image, caption="Uploaded Image", width=300)
    with st.spinner("Processing image..."):
        operation_url = recognize_handwritten_text(uploaded_image.read())
        if operation_url:
            recognized_text = get_recognized_text(operation_url)
            st.write("Recognized Text:", recognized_text)
        else:
            st.error("Error: Unable to process the image.")

# User input for translation
text_to_translate = st.text_input("Enter text to translate:")
target_language = st.selectbox("Select target language:", ["fr", "es", "de", "zh", "hi", "ta", "te", "ar", "ru", "ja"])

if st.button("Translate"):
    translated_text = translate_text(text_to_translate, target_language)
    st.success(f"Translated Text: {translated_text}")
