"""
core/eval_runner.py – Evaluation mode orchestrator.

Fetches all offers with Status == 'SAVE' from Google Sheets,
deep-scrapes each job description, then runs the local LLM evaluator
and prints a structured report per offer.

Triggered by:  python main.py --eval
"""

import os
from core.deep_scraper import fetch_full_description
from services.llm import LocalLLMEvaluator

_DEFAULT_CV_PATH = "data/master_cv.md"
_DEFAULT_MODEL_PATH = "~/llama.cpp/models/gemma_e4b_q8.gguf"

_SEPARATOR = "=" * 60


class EvalRunner:
    def __init__(self, sheet_manager, cv_path=_DEFAULT_CV_PATH, model_path=_DEFAULT_MODEL_PATH):
        self.sheet_manager = sheet_manager
        self.cv_path = os.path.abspath(os.path.expanduser(cv_path))
        self.evaluator = LocalLLMEvaluator(model_path=model_path)

    def run(self):
        # 1. Load master CV
        master_cv = self._load_cv()
        if master_cv is None:
            return

        # 2. Fetch SAVE offers from all sheets
        saved = self.sheet_manager.get_saved_offers()
        if not saved:
            print("Nessuna offerta con status SAVE trovata.")
            return

        print(f"\n{_SEPARATOR}")
        print(f"EVAL MODE — {len(saved)} offerta/e con status SAVE")
        print(_SEPARATOR)

        reports = []
        for i, offer in enumerate(saved, 1):
            print(f"\n[{i}/{len(saved)}] {offer['title']} @ {offer['company']}  ({offer['sheet']})")
            print(f"  Link: {offer['link']}")

            # 3. Deep scrape job description
            jd_text = fetch_full_description(offer["link"])
            if not jd_text:
                print("  [SKIP] Impossibile recuperare la Job Description.")
                reports.append({**offer, "report": "ERRORE: JD non recuperata."})
                continue

            print(f"  [OK] JD estratta ({len(jd_text)} chars)")

            # 4. LLM evaluation
            if self.evaluator.model:
                report = self.evaluator.evaluate_job(
                    offer["title"], offer["company"], jd_text, master_cv
                )
            else:
                report = "[MOCK] Modello LLM non trovato — valutazione saltata."

            reports.append({**offer, "report": report})

        # 5. Print full report summary
        self._print_summary(reports)

    # ------------------------------------------------------------------

    def _load_cv(self):
        if not os.path.exists(self.cv_path):
            print(f"[Eval] Errore: CV non trovato in {self.cv_path}")
            return None
        with open(self.cv_path, encoding="utf-8") as f:
            return f.read()

    def _print_summary(self, reports):
        print(f"\n\n{_SEPARATOR}")
        print("REPORT FINALE — EVALUATION MODE")
        print(_SEPARATOR)
        for r in reports:
            print(f"\n### {r['title']} @ {r['company']}  [{r['sheet']}]")
            print(f"Link: {r['link']}")
            print("-" * 40)
            print(r["report"])
            print("-" * 40)
        print(f"\n{_SEPARATOR}\n")
