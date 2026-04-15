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
                n_ctx=16384,
                verbose=False,
            )

    def evaluate_job(self, job_title, company, job_description_text, master_cv_text):
        """
        Confronta la Job Description con il documento di Background del candidato.
        Restituisce una valutazione focalizzata sulla percentuale di match e l'analisi tecnica.
        """
        if not self.model:
            return "Errore: Modello LLM non inizializzato correttamente."

        user_message = f"""Sei un recruiter tecnico. Confronta il profilo con la JD e rispondi in modo brevissimo.

## PROFILO:
{master_cv_text}

## JD ({job_title} @ {company}):
{job_description_text}

## OUTPUT (solo questo, nient'altro):
MATCH: XX%
GAP:
- <gap 1>
- <gap 2>
..."""

        print(f"Valutazione match per {job_title} @ {company}... (prompt: ~{len(user_message)//4} token stimati)")
        response = self.model.create_chat_completion(
            messages=[{"role": "user", "content": user_message}],
            max_tokens=300,
            temperature=0.1,
        )

        return response['choices'][0]['message']['content'].strip()
