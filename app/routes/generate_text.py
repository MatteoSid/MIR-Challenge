from fastapi import APIRouter, HTTPException
from loguru import logger

from app.generation_service import generate_text_description, get_template_content
from app.mlflow_utils import log_on_mlflow
from app.models import Request
from app.prompt_service import enhance_prompt_data, validate_user_data

router = APIRouter()


@router.post("/generate-text")
async def generate_text(request: Request):
    """
    Genera una descrizione dettagliata di un singolo utente in base ai suoi viaggi effettuati
    """
    logger.info(
        f"[USER: {request.user_id}] Inizio generazione descrizione testuale per utente"
    )
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
        final_prompt = get_template_content("aggregate_text_prompt.j2", enhanced_data)

        # Genera la descrizione testuale usando OpenAI
        logger.info(f"[USER: {request.user_id}] Generazione descrizione testuale")
        generated_text = generate_text_description(enhanced_data)

        response_payload = {
            "user_id": request.user_id,
            "text": generated_text,
            "enhanced_data": enhanced_data,
            "validation_status": "success",
        }

        # MLflow logging
        logger.info(f"[USER: {request.user_id}] Logging risultato per utente")
        log_on_mlflow(
            "generate_text", request, response_payload, final_prompt=final_prompt
        )
        return response_payload
    except Exception as e:
        # Log errore generico
        logger.error(f"[USER: {request.user_id}] Errore generico per utente: {str(e)}")
        log_on_mlflow("generate_text", request, {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
