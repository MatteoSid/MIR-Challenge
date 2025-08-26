import requests
from fastapi import APIRouter, HTTPException
from loguru import logger
from PIL import Image

from app.generation_service import generate_image_description, get_template_content
from app.mlflow_utils import log_on_mlflow
from app.models import Request
from app.prompt_service import enhance_prompt_data, validate_user_data

router = APIRouter()


@router.post("/generate-image")
async def generate_image(request: Request):
    """
    Genera un'immagine rappresentativa di un utente in base ai suoi viaggi effettuati
    """
    logger.info(f"[USER: {request.user_id}] Inizio generazione immagine per utente")
    try:
        # Prompt checker: valida i dati dell'utente
        logger.info(f"[USER: {request.user_id}] Validazione dati utente")
        validation_result = validate_user_data(request)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Dati utente incompleti",
                    "missing_fields": validation_result.missing_fields,
                    "message": validation_result.message,
                },
            )

        # Prompt enhancer: arricchisce i dati per la generazione
        logger.info(f"[USER: {request.user_id}] Arricchimento dati utente")
        enhanced_data = enhance_prompt_data(validation_result, request)

        # Genera il prompt finale per il logging
        final_prompt = get_template_content("aggregate_image_prompt.j2", enhanced_data)

        # Genera l'immagine usando OpenAI DALL-E
        logger.info(f"[USER: {request.user_id}] Generazione immagine")
        image_url = generate_image_description(enhanced_data)

        # Load image with PIL
        image = Image.open(requests.get(image_url, stream=True).raw)

        response_payload = {
            "user_id": request.user_id,
            "image_url": image_url,
            "enhanced_data": enhanced_data,
            "validation_status": "success",
        }

        # MLflow logging
        log_on_mlflow(
            "generate_image",
            request,
            response_payload,
            image_binary=image,
            final_prompt=final_prompt,
        )
        return response_payload
    except Exception as e:
        # Log errore generico
        log_on_mlflow("generate_image", request, {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
