import os
from typing import Any, Dict, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


def get_database_connection():
    """
    Crea connessione al database PostgreSQL
    """
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("PGPORT", "5433"),
        database=os.getenv("POSTGRES_DB", "mir_db"),
        user=os.getenv("POSTGRES_USER", "mir_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def get_user_aggregated_data(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Recupera le informazioni aggregate per un utente specifico dal database

    Args:
        user_id: ID dell'utente

    Returns:
        Dizionario con le informazioni aggregate o None se non trovate
    """
    try:
        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query per recuperare i dati aggregati dell'utente (tutte le righe aggregate)
                query = """
                SELECT 
                    t."UserId" as user_id,
                    CASE 
                        WHEN MIN(t."Periods"::int) = MAX(t."Periods"::int) 
                        THEN MIN(t."Periods"::int)::varchar
                        ELSE MIN(t."Periods"::int)::varchar || '-' || MAX(t."Periods"::int)::varchar
                    END as year,
                    (SELECT r2.region 
                     FROM trips t2 
                     LEFT JOIN region r2 ON t2."RegionCharacteristics" = r2.code 
                     WHERE t2."UserId" = t."UserId" AND r2.region IS NOT NULL
                     GROUP BY r2.region 
                     ORDER BY COUNT(*) DESC, r2.region 
                     LIMIT 1) as region,
                    (SELECT tm2.mode 
                     FROM trips t2 
                     LEFT JOIN travel_mode tm2 ON t2."TravelModes" = tm2.code 
                     WHERE t2."UserId" = t."UserId" AND tm2.mode IS NOT NULL
                     GROUP BY tm2.mode 
                     ORDER BY COUNT(*) DESC, tm2.mode 
                     LIMIT 1) as travel_mode,
                    (SELECT tmot2.motive 
                     FROM trips t2 
                     LEFT JOIN travel_motives tmot2 ON t2."TravelMotives" = tmot2.code 
                     WHERE t2."UserId" = t."UserId" AND tmot2.motive IS NOT NULL
                     GROUP BY tmot2.motive 
                     ORDER BY COUNT(*) DESC, tmot2.motive 
                     LIMIT 1) as travel_motive,
                    SUM(t."Trip in a year")::int as trip_count,
                    SUM(t."Km travelled in a year")::int as km_travelled
                FROM trips t
                LEFT JOIN region r ON t."RegionCharacteristics" = r.code
                LEFT JOIN travel_mode tm ON t."TravelModes" = tm.code
                LEFT JOIN travel_motives tmot ON t."TravelMotives" = tmot.code
                WHERE t."UserId" = %s
                GROUP BY t."UserId"
                """

                cur.execute(query, (int(user_id),))
                result = cur.fetchone()

                if result:
                    return dict(result)
                return None

    except Exception as e:
        print(f"Errore nel recupero dati aggregati: {e}")
        return None


def check_required_fields(data: Dict[str, Any]) -> list:
    """
    Controlla se tutti i campi richiesti sono presenti nei dati aggregati

    Args:
        data: Dizionario con i dati dell'utente

    Returns:
        Lista dei campi mancanti
    """
    required_fields = [
        "user_id",
        "year",
        "region",
        "travel_mode",
        "travel_motive",
        "trip_count",
        "km_travelled",
    ]

    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    return missing_fields
