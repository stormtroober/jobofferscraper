# Guida Docker per JobOfferScraper

Questa guida spiega come eseguire lo scraper all'interno di un container Docker.

## Prerequisiti

- Docker installato
- Docker Compose (solitamente incluso in Docker Desktop)

## File Inclusi

- `Dockerfile`: Definisce l'immagine Docker con Python e Firefox.
- `docker-compose.yml`: Configura il container e i volumi.
- `.dockerignore`: Esclude file non necessari.
- `requirements.txt`: Elenco delle dipendenze Python.

## Come Usare

1.  **Costruire l'immagine**:
    ```bash
    docker compose build
    ```

2.  **Eseguire lo scraper**:
    ```bash
    docker compose up
    ```
    Questo eseguirà il comando predefinito (`python main.py`), che scaricherà le offerte dai link nel file `links`.

3.  **Eseguire comandi specifici**:
    Se vuoi eseguire lo scraper con opzioni specifiche (es. solo organizzazione), usa:
    ```bash
    docker compose run --rm scraper python main.py --organize-only
    ```

## Note sui Volumi

Il file `docker-compose.yml` è configurato per "montare" (collegare) i seguenti file dal tuo sistema locale al container:
- `links`: Così puoi modificare i link senza dover ricostruire l'immagine.
- `token.json` e `credentials.json`: Per mantenere l'autenticazione Google persistente.

Se modifichi il codice Python (es. `main.py` o le strategie), dovrai ricostruire l'immagine con `docker compose build` oppure decommentare le righe dei volumi nel `docker-compose.yml` per lo sviluppo.
