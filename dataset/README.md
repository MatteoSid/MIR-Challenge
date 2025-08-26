# Dataset Scripts

Questo folder contiene gli script per creare le tabelle e caricare i dati CSV nel database PostgreSQL.

## Setup

1. Avvia PostgreSQL con Docker Compose:
```bash
docker-compose up -d
```

2. Installa le dipendenze Python:
```bash
poetry install
```

## Setup Completo Database

Per creare le tabelle e caricare tutti i dati in un comando:

```bash
poetry run setup-db
```

## Comandi Separati

### Solo creazione tabelle:
```bash
poetry run init-db
# oppure
python dataset/init_database.py
```

### Solo caricamento CSV:
```bash
poetry run load-csv  
# oppure
python dataset/load_csv_to_postgres.py
```

## File e Script

### Script Python:
- `init_database.py` - Crea tutte le tabelle PostgreSQL
- `load_csv_to_postgres.py` - Carica i CSV nelle tabelle
- `setup_database.py` - Esegue setup completo (tabelle + dati)

### Schema SQL:
- `create_tables.sql` - Schema completo delle tabelle con indici

## File CSV Supportati

- `population.csv` → tabella `population`
- `region.csv` → tabella `region`
- `travel_mode.csv` → tabella `travel_mode` (delimitatore: |)
- `travel_motives.csv` → tabella `travel_motives`
- `trips.csv` → tabella `trips` (tabella principale con FK)
- `urbanization_level.csv` → tabella `urbanization_level` (delimitatore: ;)

## Configurazione Database

- Host: localhost
- Port: 5433
- Database: mir_db
- User: mir_user
- Password: mir_password

## Schema Database

Le tabelle sono create con relazioni di foreign key:
- `trips` è la tabella principale (fact table)
- `population`, `region`, `travel_mode`, `travel_motives` sono tabelle di lookup
- Indici creati automaticamente per ottimizzare le query