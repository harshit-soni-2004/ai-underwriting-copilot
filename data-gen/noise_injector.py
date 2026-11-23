"""
Controlled Noise Injector for synthetic documents.
Injects OCR-style typos, missing fields, and date format variations into raw documents
without modifying the pristine ground-truth transactions.json.
"""

import random
from typing import Dict, Any, List

OCR_TYPO_MAP = {
    "0": "O",
    "1": "I",
    "5": "S",
    "8": "B",
    "A": "4",
    "E": "3"
}

class NoiseInjector:

    @staticmethod
    def apply_ocr_noise(text: str, noise_prob: float = 0.05, seed: int = 42) -> str:
        rng = random.Random(seed)
        chars = list(text)
        for i in range(len(chars)):
            if rng.random() < noise_prob and chars[i] in OCR_TYPO_MAP:
                chars[i] = OCR_TYPO_MAP[chars[i]]
        return "".join(chars)

    @staticmethod
    def inject_noise_into_rendered_records(records: List[Dict[str, Any]], noise_ratio: float = 0.15, seed: int = 42) -> List[Dict[str, Any]]:
        rng = random.Random(seed)
        noisy = []
        for r in records:
            item = dict(r)
            if rng.random() < noise_ratio:
                # Randomly alter formatting
                choice = rng.choice(["TYPO_NARRATION", "REMOVE_REF", "INVERT_DATE"])
                if choice == "TYPO_NARRATION" and "narration" in item:
                    item["narration"] = NoiseInjector.apply_ocr_noise(item["narration"], seed=seed)
                elif choice == "REMOVE_REF" and "Chq/Ref No" in item:
                    item["Chq/Ref No"] = ""
                elif choice == "INVERT_DATE" and "date" in item:
                    parts = item["date"].split("-")
                    if len(parts) == 3:
                        item["date"] = f"{parts[2]}/{parts[1]}/{parts[0]}"
            noisy.append(item)
        return noisy
