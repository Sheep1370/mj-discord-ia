import json
import logging
import os

from google import genai
from google.genai import types
from pydantic import BaseModel


client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def chat_with_gemini(message: str) -> str:
    """
    Envoie un message à Gemini et retourne la réponse.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY n'est pas définie. Veuillez configurer cette clé dans les Secrets de Replit.")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=message
        )
        
        return response.text or "Désolé, je n'ai pas pu générer une réponse."
    
    except Exception as e:
        logging.error(f"Erreur lors de l'appel à Gemini: {e}")
        raise


def summarize_article(text: str) -> str:
    prompt = f"Résume le texte suivant de manière concise tout en gardant les points clés:\n\n{text}"

    response = client.models.generate_content(model="gemini-2.0-flash-exp",
                                              contents=prompt)

    return response.text or "ERREUR: Impossible de résumer"


class Sentiment(BaseModel):
    rating: int
    confidence: float


def analyze_sentiment(text: str) -> Sentiment:
    try:
        system_prompt = (
            "Tu es un expert en analyse de sentiment. "
            "Analyse le sentiment du texte et fournis une note "
            "de 1 à 5 étoiles et un score de confiance entre 0 et 1. "
            "Réponds avec du JSON dans ce format: "
            "{'rating': number, 'confidence': number}")

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Content(role="user", parts=[types.Part(text=text)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=Sentiment,
            ),
        )

        raw_json = response.text
        logging.info(f"Raw JSON: {raw_json}")

        if raw_json:
            data = json.loads(raw_json)
            return Sentiment(**data)
        else:
            raise ValueError("Réponse vide du modèle")

    except Exception as e:
        raise Exception(f"Échec de l'analyse de sentiment: {e}")
