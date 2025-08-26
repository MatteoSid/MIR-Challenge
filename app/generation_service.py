import os
from typing import Any, Dict

import openai
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# Configura OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configura Jinja2
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(template_dir))


def generate_text_description(enhanced_data: Dict[str, Any]) -> str:
    """
    Genera una descrizione testuale dell'utente usando OpenAI e template Jinja2

    Args:
        enhanced_data: Dati arricchiti dell'utente

    Returns:
        Descrizione testuale generata
    """
    try:
        # Carica il template Jinja2
        template = jinja_env.get_template("aggregate_text_prompt.j2")

        # Renderizza il prompt con i dati
        prompt = template.render(**enhanced_data)

        # Chiama OpenAI per la generazione del testo
        response = client.chat.completions.create(
            model=os.getenv("DEFAULT_TEXT_MODEL", "gpt-5-nano"),
            messages=[
                {
                    "role": "system",
                    "content": "Sei un esperto analista di mobilità specializzato nella creazione di profili utente dettagliati.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"Errore nella generazione del testo: {e}")


def generate_image_description(enhanced_data: Dict[str, Any]) -> str:
    """
    Genera un'immagine rappresentativa dell'utente usando OpenAI DALL-E

    Args:
        enhanced_data: Dati arricchiti dell'utente

    Returns:
        URL dell'immagine generata
    """
    try:
        # Carica il template Jinja2 per l'immagine
        template = jinja_env.get_template("aggregate_image_prompt.j2")

        # Renderizza il prompt per l'immagine
        image_prompt = template.render(**enhanced_data)

        # Chiama OpenAI DALL-E per la generazione dell'immagine
        response = client.images.generate(
            model=os.getenv("DEFAULT_IMAGE_MODEL", "dall-e-3"),
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        return response.data[0].url

    except Exception as e:
        raise Exception(f"Errore nella generazione dell'immagine: {e}")


def get_template_content(template_name: str, enhanced_data: Dict[str, Any]) -> str:
    """
    Utility function per ottenere il contenuto renderizzato di un template

    Args:
        template_name: Nome del template
        enhanced_data: Dati da passare al template

    Returns:
        Contenuto renderizzato del template
    """
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**enhanced_data)
    except Exception as e:
        raise Exception(f"Errore nel rendering del template {template_name}: {e}")
