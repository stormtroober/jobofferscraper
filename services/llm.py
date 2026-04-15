import os
from llama_cpp import Llama

class LocalLLMEvaluator:
    def __init__(self, model_path="~/llama.cpp/models/gemma_e4b_q8.gguf"):
        """
        Inizializza il modello Gemma o simile via llama-cpp.
        """
        # Espande ~ e rende il percorso assoluto
        model_path = os.path.abspath(os.path.expanduser(model_path))
        
        if not os.path.exists(model_path):
            print(f"Attenzione: Modello non trovato in {model_path}")
            # Non solleviamo un errore qui per permettere il caricamento del modulo, 
            # ma l'invocazione di evaluate fallirà.
            self.model = None
        else:
            print(f"Caricamento modello LLM da {model_path}...")
            self.model = Llama(
                model_path=model_path,
                verbose=False
            )

    def evaluate_job(self, job_title, company, job_description_text, master_cv_text):
        """
        Confronta la Job Description con il documento di Background del candidato.
        Restituisce una valutazione focalizzata sulla percentuale di match e l'analisi tecnica.
        """
        if not self.model:
            return "Errore: Modello LLM non inizializzato correttamente."

        prompt = f"""
Sei un analista tecnico esperto di recruiting. Il tuo compito è valutare la compatibilità tra un'offerta di lavoro e il profilo di un candidato basandoti su un documento di background esteso.

### DOCUMENTO DI BACKGROUND DEL CANDIDATO (Informazioni complete):
{master_cv_text}

### OFFERTA DI LAVORO:
Titolo: {job_title}
Azienda: {company}

### JOB DESCRIPTION:
{job_description_text}

### RICHIESTA:
Analizza attentamente se le competenze richieste nella Job Description sono presenti nel documento di background del candidato. 
Genera un report sintetico con questa struttura:

1. **MATCH SCORE**: Esprimi una percentuale (0-100%) che rappresenti quanto il profilo copre i requisiti obbligatori e opzionali.
2. **ANALISI COMPETENZE PRESENTI**: Elenca le tecnologie e le esperienze confermate dal documento di background che corrispondono alla JD.
3. **GAP TECNICI & MANCANZE**: Identifica chiaramente cosa richiede l'azienda che NON è presente o non è esplicitato nel background del candidato.

NON suggerire modifiche al CV. Sii oggettivo e brutale nella valutazione del Match Score.
"""

        print(f"Valutazione match per {job_title} @ {company}...")
        response = self.model(
            prompt,
            max_tokens=1500,
            temperature=0.1, # Più deterministico per una valutazione analitica
            stop=["###"]
        )

        return response['choices'][0]['text'].strip()
