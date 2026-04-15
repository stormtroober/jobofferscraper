import os
from core.deep_scraper import fetch_full_description
from services.llm import LocalLLMEvaluator

def main():
    # 1. Configurazione test rapido
    test_url = "https://theprotocol.it/szczegoly/praca/data-scientist-warszawa-aleje-jerozolimskie-44,oferta,dc570000-1d37-3e55-45dd-08de9abff320"
    cv_path = os.path.abspath(os.path.expanduser("data/master_cv.txt"))
    model_path = os.path.abspath(os.path.expanduser("~/llama.cpp/models/gemma_e4b_q8.gguf"))
    
    print(f"=== TEST RAPIDO SPECIFICO ===")
    print(f"URL: {test_url}")
    
    # 2. Caricamento Master CV
    if not os.path.exists(cv_path):
        print(f"Errore: File CV non trovato in {cv_path}")
        return
        
    with open(cv_path, "r", encoding="utf-8") as f:
        master_cv = f.read()
    
    # 3. Deep Scraping (Strategy Pattern)
    jd_text = fetch_full_description(test_url)
    
    if not jd_text:
        print("Impossibile recuperare la Job Description. Test interrotto.")
        return
        
    print(f"\n--- TESTO ESTRATTO (Primi 1000 caratteri) ---")
    print(jd_text[:1000] + "...")
    print("-" * 50)
    
    # 4. Inizializzazione LLM e Valutazione
    job_title = "Data Scientist"
    company = "Britenet Sp. z o.o."
    
    evaluator = LocalLLMEvaluator(model_path=model_path)
    
    if evaluator.model:
        report = evaluator.evaluate_job(job_title, company, jd_text, master_cv)
        print("\n" + "="*50)
        print("REPORT DI VALUTAZIONE LLM")
        print("="*50)
        print(report)
        print("="*50)
    else:
        print("\n[MOCK MODE] Modello LLM non trovato.")

if __name__ == "__main__":
    main()
