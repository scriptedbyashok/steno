import difflib
import re


def _tokenize(text: str) -> tuple[list[str], list[str]]:
    """Split text into (original words, normalized words).

    Normalization: lowercase, strip punctuation. A token that becomes
    empty after stripping (e.g. a lone "--") is dropped from both lists
    so the two stay index-aligned.
    """
    originals: list[str] = []
    normalized: list[str] = []
    for token in text.split():
        norm = re.sub(r"[^\w]", "", token).lower()
        if norm:
            originals.append(token)
            normalized.append(norm)
    return originals, normalized


def diff_words(reference: str, typed: str) -> dict:
    """Compare typed text against a reference transcript, word by word.

    Uses difflib.SequenceMatcher opcodes on normalized word lists:
    - equal   -> correct
    - replace -> paired positionally: wrong (leftover ref = missed,
                 leftover typed = extra)
    - delete  -> missed (reference word with no typed counterpart)
    - insert  -> extra (typed word with no reference counterpart)

    word_diff preserves the ORIGINAL (un-normalized) words for display.
    """
    ref_orig, ref_norm = _tokenize(reference)
    typed_orig, typed_norm = _tokenize(typed)

    word_diff: list[dict] = []
    correct = wrong = missed = extra = 0

    matcher = difflib.SequenceMatcher(None, ref_norm, typed_norm)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                word_diff.append({"word": ref_orig[i1 + k], "status": "correct"})
                correct += 1
        elif tag == "replace":
            n = min(i2 - i1, j2 - j1)
            for k in range(n):
                word_diff.append(
                    {
                        "word": ref_orig[i1 + k],
                        "status": "wrong",
                        "typed": typed_orig[j1 + k],
                    }
                )
                wrong += 1
            for k in range(n, i2 - i1):
                word_diff.append({"word": ref_orig[i1 + k], "status": "missed"})
                missed += 1
            for k in range(n, j2 - j1):
                word_diff.append({"word": typed_orig[j1 + k], "status": "extra"})
                extra += 1
        elif tag == "delete":
            for k in range(i1, i2):
                word_diff.append({"word": ref_orig[k], "status": "missed"})
                missed += 1
        elif tag == "insert":
            for k in range(j1, j2):
                word_diff.append({"word": typed_orig[k], "status": "extra"})
                extra += 1

    total_words = len(ref_norm)
    accuracy = round((correct / total_words) * 100, 2) if total_words else 0.0

    return {
        "accuracy": accuracy,
        "total_words": total_words,
        "correct": correct,
        "wrong": wrong,
        "missed": missed,
        "extra": extra,
        "word_diff": word_diff,
    }
