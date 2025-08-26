import os
import uuid
from typing import Any, Dict, Optional

import mlflow
from loguru import logger

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "mir-executions")


def setup_mlflow(experiment_name: str = MLFLOW_EXPERIMENT) -> bool:
    """
    Ensure MLflow is configured with tracking URI and experiment.
    Returns False if MLflow is not available, True otherwise.
    """
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(experiment_name)
        return True
    except Exception as e:
        logger.error("Errore configurazione MLflow: {}", e)
        return False


def log_request_response(
    route: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
    *,
    experiment_name: str = MLFLOW_EXPERIMENT,
    tags: Optional[Dict[str, str]] = None,
    image_binary: Optional[bytes] = None,
    final_prompt: Optional[str] = None,
) -> None:
    """
    Log request/response as JSON artifacts in MLflow under the given experiment.

    - Creates the experiment if it doesn't exist.
    - Starts a run named after the route and user_id.
    - Logs request.json, response.json, optionally an image, and final prompt as artifacts.
    """
    if not setup_mlflow(experiment_name):  # MLflow not available or misconfigured
        return

    user_id = request_payload.get("user_id")
    run_name = (
        f"{route}-user-{user_id}-{uuid.uuid4()}" if user_id is not None else route
    )

    try:
        with mlflow.start_run(run_name=run_name):
            base_tags: Dict[str, str] = {"route": route}
            base_tags["user_id"] = str(user_id)
            if tags:
                base_tags.update(tags)
            mlflow.set_tags(base_tags)

            # Log JSON artifacts
            mlflow.log_dict(request_payload, "request.json")
            mlflow.log_dict(response_payload, "response.json")

            # Optional simple metrics
            text_val = response_payload.get("text")
            if isinstance(text_val, str):
                mlflow.log_metric("text_length", len(text_val))
            if image_binary:
                mlflow.log_image(image_binary, key=f"image_{user_id}")

            # Log final prompt as text artifact
            if final_prompt:
                mlflow.log_text(final_prompt, "final_prompt.txt")

            logger.info(
                "Esecuzione loggata su MLflow (exp: {}, run: {})",
                experiment_name,
                run_name,
            )
    except Exception as e:
        logger.warning("MLflow logging skipped per errore: {}", e)


def log_on_mlflow(
    mode, request, response_payload, image_binary=None, final_prompt=None
):
    try:
        req_payload = request.model_dump()
        log_request_response(
            mode,
            req_payload,
            response_payload,
            image_binary=image_binary,
            final_prompt=final_prompt,
        )
    except Exception as e:
        logger.warning("MLflow logging skipped per errore: {}", e)
