import os
from core.deep_scraper import fetch_full_description
from services.llm import LocalLLMEvaluator

# ── Configurazione ────────────────────────────────────────────────────────────
TEST_URL   = "https://builtin.com/job/game-producer/9039317"
JOB_TITLE  = "Game Producer"
COMPANY    = "Kalamba Games"
CV_PATH    = os.path.join(os.path.dirname(__file__), "data", "master_cv.md")
MODEL_PATH = os.path.expanduser("~/llama.cpp/models/gemma_e4b_q8.gguf")
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print(f"=== TEST EVAL: BulldogJob deep strategy ===")
    print(f"URL    : {TEST_URL}")
    print(f"Offer  : {JOB_TITLE} @ {COMPANY}")

    if not os.path.exists(CV_PATH):
        print(f"Errore: CV non trovato in {CV_PATH}")
        return

    with open(CV_PATH, "r", encoding="utf-8") as f:
        master_cv = f.read()

    jd_text = fetch_full_description(TEST_URL)

    if not jd_text:
        print("Impossibile recuperare la Job Description. Test interrotto.")
        return

    print(f"\n--- JD estratta ({len(jd_text)} caratteri) ---")
    print(jd_text)
    print("-" * 50)

    evaluator = LocalLLMEvaluator(model_path=MODEL_PATH)

    if not evaluator.model:
        print("\n[MOCK MODE] Modello LLM non trovato — scraping OK, valutazione saltata.")
        return

    report = evaluator.evaluate_job(JOB_TITLE, COMPANY, jd_text, master_cv)
    print("\n" + "=" * 50)
    print("REPORT DI VALUTAZIONE LLM")
    print("=" * 50)
    print(report)
    print("=" * 50)


if __name__ == "__main__":
    main()
