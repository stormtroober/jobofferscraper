# Guida al Cloud Deployment (GCP + GHCR)

Questa guida spiega come configurare Google Cloud Run per eseguire lo scraper utilizzando l'immagine ospitata su GitHub Container Registry (GHCR) e gestendo le credenziali in modo sicuro tramite Google Secret Manager.

## 1. Preparazione

1.  **Push su GitHub**:
    Il progetto ora include una GitHub Action (`.github/workflows/docker-publish.yml`). 
    Semplicemente facendo un push sul branch `main`, GitHub costruirà l'immagine e la caricherà su `ghcr.io/tuo-username/tuo-repo:latest`.
    *Nota: Assicurati che nelle impostazioni del repo su GitHub, sotto "Actions" -> "General", i permessi "Workflow permissions" siano su "Read and write permissions".*

2.  **Verifica Immagine**:
    Dopo il push, vai sul profilo GitHub -> Packages e dovresti vedere la tua immagine.
    *Importante*: Imposta la visibilità del pacchetto su **Public** (se non hai dati sensibili nel codice) per semplificare il pull da GCP. Se vuoi tenerla Private, dovrai configurare l'autenticazione Docker su GCP (opzione più avanzata).

---

## 2. Configurazione Google Secret Manager

Invece di mettere i file `.json` nell'immagine, li carichiamo come "Secret" su GCP.

1.  Vai su [Google Cloud Console](https://console.cloud.google.com/) -> **Security** -> **Secret Manager**.
2.  Crea un nuovo Secret chiamato `job-scraper-credentials`.
    - Carica il contenuto del tuo file locale `credentials.json`.
3.  Crea un altro Secret chiamato `job-scraper-token`.
    - Carica il contenuto del tuo file locale `token.json` (quello generato dopo il primo login).

---

## 3. Creazione del Cloud Run Job

Usiamo "Cloud Run Jobs" perché lo scraper è un processo che inizia, lavora e finisce (non è un server web sempre acceso).

1.  Vai su **Cloud Run** -> Tab **JOBS** -> **Crea Job**.
2.  **Immagine Container**: Inserisci l'URL della tua immagine GHCR (es. `ghcr.io/tuo-user/jobofferscraper:latest`).
3.  **Nome Job**: `job-scraper`.
4.  **Regione**: `europe-west1` (o quella che preferisci).

### Configurazione Volumi e Secrets

Nella sezione configurazione del Container:

1.  Vai su **Variables & Secrets**.
2.  Tab **Secrets**: Clicca "Reference a Secret".
    - **Secret**: `job-scraper-credentials`
    - **Reference method**: Mounted as volume.
    - **Mount path**: `credentials.json` (o meglio `/app/credentials.json`) -> *Importante: Cloud Run monta i secret come file.*
    
    *Attenzione*: Cloud Run monta i secrets in una cartella, non come singoli file nella root di lavoro solitamente, a meno che non si specifici il path esatto. 
    **Strategia Consigliata**: Monta i secrets nella cartella `/secrets`.
    - Mount path: `/secrets`.
    - I file saranno `/secrets/credentials.json` e `/secrets/token.json`.
    
    *Tuttavia, il tuo codice cerca i file nella cartella corrente (`/app`).*
    *Opzione A (Semplice)*: Se Cloud Run te lo permette, prova a montare su `/app/credentials.json`.
    *Opzione B (Consigliata)*: Monta su `/secrets` e imposta una variabile d'ambiente o modifica leggermente il codice per cercare lì.
    
    Per ora, proviamo a montare i singoli file come volumi se l'interfaccia lo permette, oppure montiamo il volume `/app/credentials_dir` e spostiamo il file lì.
    
    **Soluzione più robusta senza cambiare codice**:
    - Monta il secret `job-scraper-credentials` nel path `/app/credentials.json` (Seleziona "Mount as file" e specifica il path completo se possibile, altrimenti monta la cartella).
    *Nota: Spesso è più facile montare la DIRECTORY `/secrets` e dire al programma di cercare lì.*

### Risorse
- **Memory**: 1 GiB o 2 GiB (Firefox consuma un po').
- **CPU**: 1 o 2.
- **Timeout**: Imposta un tempo generoso (es. 10 minuti o 600 secondi) a seconda di quanti link hai.

## 4. Esecuzione

Una volta creato, puoi cliccare **EXECUTE** manualmente dalla console, oppure impostare uno **Scheduler** (Cloud Scheduler) per lanciarlo ogni mattina alle 8:00.

---
## Checklist Sicurezza
- [x] `.dockerignore` configurato per escludere `credentials.json` e `token.json` dalla build pubblica.
- [x] GitHub Action configurata per build automatica.
