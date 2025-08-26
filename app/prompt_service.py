import json
import os
from typing import Any, Dict, Optional

import openai
from jinja2 import Environment, FileSystemLoader

from .database import check_required_fields, get_user_aggregated_data
from .models import Request, UserAggregatedData, ValidationResult


def extract_info_from_request(
    info: Optional[str], missing_fields: list[str]
) -> Dict[str, Any]:
    """
    Estrae informazioni aggiuntive dal campo info della request, usando un LLM.

    Args:
        info: Campo info della request contenente informazioni aggiuntive.
        missing_fields: Lista di campi che l'LLM dovrebbe cercare di estrarre.

    Returns:
        Dizionario con le informazioni estratte.
    """
    if not info or not missing_fields:
        return {}

    # Prova a parsare come JSON
    try:
        extracted_info = json.loads(info)
        return extracted_info
    except json.JSONDecodeError:
        pass

    try:
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("extract_info_prompt.j2")

        # Render the prompt
        prompt = template.render(missing_fields=missing_fields, info=info)

        # La chiave API di OpenAI deve essere impostata come variabile d'ambiente OPENAI_API_KEY
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "Sei un assistente che estrae informazioni strutturate dal testo in formato JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        if response.choices and response.choices[0].message.content:
            extracted_info = json.loads(response.choices[0].message.content)

            # Post-processing per tentare di convertire i tipi
            processed_info = {}
            for key, value in extracted_info.items():
                if key not in missing_fields:
                    continue  # Ignora chiavi non richieste
                try:
                    if isinstance(value, str):
                        if "." in value:
                            processed_info[key] = float(value)
                        else:
                            processed_info[key] = int(value)
                    else:
                        processed_info[key] = value
                except (ValueError, TypeError):
                    processed_info[key] = value
            return processed_info

    except Exception as e:
        print(f"Errore durante la chiamata all'LLM per l'estrazione delle info: {e}")
        # Fallback al parsing semplice in caso di errore dell'LLM
        extracted_info = {}
        try:
            lines = info.replace(",", "\n").split("\n")
            for line in lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().lower().replace(" ", "_")
                    if key in missing_fields:
                        value = value.strip()
                        try:
                            if "." in value:
                                extracted_info[key] = float(value)
                            else:
                                extracted_info[key] = int(value)
                        except ValueError:
                            extracted_info[key] = value
        except Exception:
            pass
        return extracted_info

    return {}


def validate_user_data(request: Request) -> ValidationResult:
    """
    Prompt checker: valida se abbiamo tutte le informazioni aggregate per l'utente

    Args:
        request: Request dell'utente

    Returns:
        Risultato della validazione con informazioni sui campi mancanti
    """
    try:
        # Recupera i dati aggregati dal database
        user_data = get_user_aggregated_data(request.user_id)

        if not user_data:
            return ValidationResult(
                is_valid=False,
                missing_fields=[
                    "user_id",
                    "year",
                    "region",
                    "travel_mode",
                    "travel_motive",
                    "trip_count",
                    "km_travelled",
                ],
                message=f"Nessun dato trovato per l'utente {request.user_id}",
            )

        # Controlla i campi mancanti
        missing_fields = check_required_fields(user_data)

        if missing_fields:
            # Prova a recuperare informazioni mancanti dal campo info
            additional_info = extract_info_from_request(request.info, missing_fields)

            # Aggiorna i dati con le informazioni aggiuntive
            for field in missing_fields.copy():
                if field in additional_info:
                    # Make sure the key exists before assigning
                    if additional_info.get(field) is not None:
                        user_data[field] = additional_info[field]
                        missing_fields.remove(field)

            # Controlla di nuovo i campi mancanti
            if missing_fields:
                return ValidationResult(
                    is_valid=False,
                    missing_fields=missing_fields,
                    message=f"Campi mancanti per l'utente {request.user_id}: {', '.join(missing_fields)}",
                )

        # Tutti i dati sono presenti, crea il modello UserAggregatedData
        try:
            aggregated_data = UserAggregatedData(**user_data)
            return ValidationResult(
                is_valid=True,
                missing_fields=[],
                message="Dati dell'utente completi",
                data=aggregated_data,
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                missing_fields=["validation_error"],
                message=f"Errore nella validazione dei dati: {e}",
            )

    except Exception as e:
        return ValidationResult(
            is_valid=False,
            missing_fields=["database_error"],
            message=f"Errore nel recupero dei dati: {e}",
        )


def enhance_prompt_data(
    validation_result: ValidationResult, request: Request
) -> Dict[str, Any]:
    """
    Prompt enhancer: arricchisce i dati per la generazione del prompt

    Args:
        validation_result: Risultato della validazione contenente i dati dell'utente

    Returns:
        Dizionario con i dati arricchiti per la generazione del prompt
    """
    if not validation_result.is_valid or not validation_result.data:
        return {}

    data = validation_result.data

    # Calcola metriche aggiuntive
    if (
        data.trip_count is not None
        and data.km_travelled is not None
        and data.trip_count > 0
    ):
        avg_km_per_trip = data.km_travelled / data.trip_count
    else:
        avg_km_per_trip = None

    # Categorizza l'utente in base ai suoi viaggi
    if data.trip_count is None:
        travel_frequency = "dati non disponibili"
    elif data.trip_count > 200:
        travel_frequency = "molto frequente"
    elif data.trip_count > 100:
        travel_frequency = "frequente"
    elif data.trip_count > 50:
        travel_frequency = "moderata"
    else:
        travel_frequency = "occasionale"

    # Categorizza in base ai km percorsi
    if data.km_travelled is None:
        travel_distance = "dati non disponibili"
    elif data.km_travelled > 5000:
        travel_distance = "lunghe distanze"
    elif data.km_travelled > 2000:
        travel_distance = "medie distanze"
    else:
        travel_distance = "brevi distanze"

    enhanced_data = {
        "user_id": data.user_id,
        "year": data.year,
        "region": data.region,
        "travel_mode": data.travel_mode,
        "travel_motive": data.travel_motive,
        "trip_count": data.trip_count,
        "km_travelled": data.km_travelled,
        "avg_km_per_trip": (
            round(avg_km_per_trip, 2) if avg_km_per_trip is not None else None
        ),
        "travel_frequency": travel_frequency,
        "travel_distance": travel_distance,
    }

    return enhanced_data
