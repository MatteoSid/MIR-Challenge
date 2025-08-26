from typing import Optional

from pydantic import BaseModel, Field


class Request(BaseModel):
    user_id: str = Field(..., description="id dell'utente")
    info: Optional[str] = Field(None, description="informazioni aggiuntive")


class UserAggregatedData(BaseModel):
    """
    Modello per i dati aggregati dell'utente
    """

    user_id: int = Field(..., description="ID dell'utente")
    year: str = Field(
        ..., description="Periodo di riferimento (es. '2022' o '2018-2022')"
    )
    region: str = Field(..., description="Regione")
    travel_mode: str = Field(..., description="Modalità di trasporto")
    travel_motive: str = Field(..., description="Motivo del viaggio")
    trip_count: Optional[int] = Field(None, description="Numero di viaggi")
    km_travelled: Optional[int] = Field(None, description="Chilometri percorsi")


class ValidationResult(BaseModel):
    """
    Risultato della validazione dei dati utente
    """

    is_valid: bool = Field(..., description="Indica se i dati sono validi")
    missing_fields: list[str] = Field(
        default_factory=list, description="Campi mancanti"
    )
    message: Optional[str] = Field(None, description="Messaggio di errore o info")
    data: Optional[UserAggregatedData] = Field(
        None, description="Dati aggregati dell'utente"
    )
