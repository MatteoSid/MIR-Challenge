# Make It Real - User Profiling API

Questo progetto è un'API di profilazione utente che utilizza la gen-ai per creare descrizioni testuali e immagini basate sui dati di viaggio degli utenti.

## Descrizione del Progetto

L'applicazione analizza i dati forniti su un utente e i suoi viaggi, li arricchisce con informazioni contestuali presenti in un database (es. livello di urbanizzazione, dati sulla popolazione) e utilizza queste informazioni per costruire un prompt. Il prompt viene poi inviato a un LLM (OpenAI) per produrre:

1.  **Un riassunto testuale**: Una descrizione narrativa dello stile di vita e delle abitudini di viaggio dell'utente.
2.  **Un'immagine rappresentativa**: Un'immagine generata con DALL-E che visualizza il profilo dell'utente.

Tutte le generazioni e i dati associati vengono tracciati e salvati utilizzando MLflow, con gli artefatti (come le immagini)

### Input

L'API accetta una richiesta JSON contenente un `user_id` e un campo `info` che conterrà eventuali campi mancati che l'utente potrà inserire in linguaggio naturale.

Esempio di richiesta:
```json
{
    "user_id": "36"
}
```

Esempio di richiesta con dati mancanti (numero di viaggi e km percorsi):
```json
{
    "user_id": "8",
    "info": "Ha viaggiato 10 volte per un totale di 500 km percorsi"
}
```

### Output

L'API restituisce una risposta JSON contenente la descrizione testuale generata e/o l'URL dell'immagine creata con dei metadati utili a capire come sono state generate.

## Prerequisiti

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)
-   Una API key di [OpenAI](https://platform.openai.com/api-keys)

## Installazione ed Esecuzione

1.  **Clonare il repository e installare le dipendenze**
    ```bash
    git clone https://github.com/MatteoSid/MIR-Challenge.git
    cd make-it-real
    poetry install --no-root
    ```

2.  **Configurare le variabili d'ambiente**
    Crea un file `.env` copiando l'esempio e inserisci la tua API key di OpenAI.
    ```bash
    cp .env.example .env
    ```
    Modifica il file `.env` e aggiungi la tua chiave:
    ```plaintext
    OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

3. **Inizializzare e popolare il database**
    ```bash
    make init-db
    ```

4.  **Avviare i servizi con Docker Compose**
    Questo comando costruirà le immagini e avvierà tutti i servizi necessari: l'API, il database PostgreSQL, MLflow e MinIO.
    ```bash
    docker compose up --build
    ```
    I servizi saranno disponibili ai seguenti indirizzi:
    -   **Swagger FastAPI**: `http://localhost:8123/docs`
    -   **MLflow UI**: `http://localhost:5001`

## Inizializzazione del Database (Caricamento Dati)

Dopo aver avviato i container, il database è vuoto. Per caricarlo con i dati CSV presenti nella cartella `/data`, il progetto utilizza un DAG di Airflow (eseguito come script una tantum).

In un nuovo terminale, esegui il seguente comando:

```bash
make init-db
```

Questo comando eseguirà lo script che crea le tabelle e popola il database. **Questo passo è fondamentale per il corretto funzionamento dell'API.**

## Prompt Checker and Enhancer

Il Prompt Checker and Enhancer viene triggerato quando mancano delle informazioni dai dati presenti nel database per un determinato utente.

Esempio con id che ha dati mancanti:

```json
{
    "user_id": "8"
}
```

Darà come risposta 400 Bad Request con i campi mancanti:

```json
{
    "user_id": "8",
    "missing_fields": ["trip_count", "km_travelled"],
    "validation_status": "error"
}
```

Il sistema si accorge che ci sono dei `missing fields` (per questo id non ci sono `trip_count` e `km_travelled`) pertanto verrà ritornato all'utente un messaggio di errore con i campi mancanti. L'utente potrà poi aggiungere queste informazioni in linguaggio naturale nel campo `info` e inviare nuovamente la richiesta.

Il campo `info` viene poi elaborato da un LLM che poi completa il json del form con i campi mancanti.

## Utilizzo degli Endpoint

Puoi interagire con l'API tramite qualsiasi client HTTP, come `curl`.

### 1. Generare una Descrizione Testuale

Questo endpoint genera una descrizione dettagliata delle abitudini di viaggio di un utente.

-   **URL**: `/generate-text`
-   **Metodo**: `POST`
-   **Header**: `Content-Type: application/json`

**Esempio di richiesta `curl`:**

```bash
curl -X 'POST' \
  'http://localhost:8123/generate-text' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "36"
    }'
```

**Esempio di risposta (200 OK):**

```json
{
    "user_id": "36",
    "text": "Dal finestrino di un tram verde-azzurro, una persona dall’aspetto rilassato, in modalità tempo libero, occupa un sedile vicino al vetro. Indossa una felpa leggera color grafite, pantaloni sportivi blu scuro e sneakers bianche; accanto, uno zainetto sportivo e una borraccia luccicante fanno capolino. Guarda fuori, ma l’occhio è calmo, in pausa tra un allenamento al parco e una corsa breve verso una palestra. All’esterno, un paesaggio olandese moderno e pianificato: condomini bassi di vetro e mattone, canali ordinati, filari di alberi e piste ciclabili",
    "enhanced_data": {
        "user_id": 36,
        "year": "2018-2022",
        "region": "Flevoland (PV)",
        "travel_mode": "Bus/tram/metro",
        "travel_motive": "Leisure, sports",
        "trip_count": 145,
        "km_travelled": 3158,
        "avg_km_per_trip": 21.78,
        "travel_frequency": "frequente",
        "travel_distance": "medie distanze"
    },
    "validation_status": "success"
}
```

### 2. Generare un'Immagine

Questo endpoint genera un'immagine rappresentativa del profilo di viaggio dell'utente.

-   **URL**: `/generate-image`
-   **Metodo**: `POST`
-   **Header**: `Content-Type: application/json`

**Esempio di richiesta `curl`:**

```bash
curl -X 'POST' \
  'http://localhost:8123/generate-image' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "8",
    "info": "Ha viaggiato 10 volte per un totale di 500 km percorsi"
}'
```

**Esempio di risposta (200 OK):**

```json
{
  "user_id": "8",
  "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/private/org-b40Jmq0HKss6NgHdr9eAUXaC/user-7WV6LHbNOID9Ps9HsQ9QieYO/img-dneuEhVyxzPVBIpS778ZGDd7.png?st=2025-08-26T20%3A41%3A15Z&se=2025-08-26T22%3A41%3A15Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=b1a0ae1f-618f-4548-84fd-8b16cacd5485&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-08-26T20%3A25%3A02Z&ske=2025-08-27T20%3A25%3A02Z&sks=b&skv=2024-08-04&sig=%2BzPOkRyoTR9duyLgQc%2B%2BeofvG72lplhveBc3zyOPbRg%3D",
  "enhanced_data": {
    "user_id": 8,
    "year": "2018-2020",
    "region": "Flevoland (PV)",
    "travel_mode": "Other",
    "travel_motive": "Shopping, groceries, funshopping.",
    "trip_count": 10,
    "km_travelled": 500,
    "avg_km_per_trip": 50,
    "travel_frequency": "occasionale",
    "travel_distance": "brevi distanze"
  },
  "validation_status": "success"
}
```

Note: 

- Sono presenti due file di .env: uno per l'ambiente locale e uno per l'ambiente dockerizzato. Differiscono solo per i puntamenti al localhost e ai container.
- Non essendoci un'immagine ufficiale di mlflow abbiamo predisposto un dockerfile ad-hoc chiamato `Dockerfile.mlflow`. Mentre il `Dockerfile.api` builda il progetto
- Riguardo la query in `database.py`: abbiamo deciso di aggregare tutti i dati di singolo utente per avere una "big-picture" di un utente in un range di anni. Per quanto riguarda region, travel_mode e travel_motive abbiamo preso i più frequenti. E' uno degli approcci possibili, ma non necessariamente quello ottimale. Altri approcci non sono stati esplorati per limiti di tempo.


