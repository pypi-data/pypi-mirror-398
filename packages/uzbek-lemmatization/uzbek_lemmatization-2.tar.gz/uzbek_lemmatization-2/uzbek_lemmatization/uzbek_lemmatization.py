from __future__ import annotations

import os
import re
from typing import List


# -----------------------------
# Apostrophe normalization
# -----------------------------
_APOS_MAP = {
    "’": "'",
    "‘": "'",
    "ʻ": "'",
    "´": "'",
    "`": "'",
    "ʼ": "'",
    "ʹ": "'",
    "ˈ": "'",
    "ꞌ": "'",
}


def change_apostrophe(text: str) -> str:
    if not text:
        return text
    for k, v in _APOS_MAP.items():
        text = text.replace(k, v)
    # normalize o‘ / g‘ written as o' / g'
    text = text.replace("o`", "o'").replace("g`", "g'")
    text = text.replace("O`", "O'").replace("G`", "G'")
    return text


# -----------------------------
# Dictionary loading
# -----------------------------
exceptions: List[str] = []

mFel: List[str] = []
mOlmosh: List[str] = []
mOt: List[str] = []
mRavish: List[str] = []
mSifat: List[str] = []
mSon: List[str] = []

oModal: List[str] = []
oTaqlid: List[str] = []
oUndov: List[str] = []

yBoglovchi: List[str] = []
yKomakchi: List[str] = []
yYuklama: List[str] = []

_DICT_LOADED = False


def _load_lemma_list(path: str) -> List[str]:
    items: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            s = line.strip()
            if not s:
                continue
            s = change_apostrophe(s).lower()
            items.append(s)
    return items


def read_all_pos_lemmas() -> None:
    """Load all dictionaries once."""
    global _DICT_LOADED
    if _DICT_LOADED:
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    suzlar = os.path.join(base_dir, "suzlar")

    global exceptions
    exceptions = _load_lemma_list(os.path.join(suzlar, "istisnolar.txt"))

    global mFel, mOlmosh, mOt, mRavish, mSifat, mSon
    mFel = _load_lemma_list(os.path.join(suzlar, "mustaqil__fel.txt"))
    mOlmosh = _load_lemma_list(os.path.join(suzlar, "mustaqil__olmosh.txt"))
    mOt = _load_lemma_list(os.path.join(suzlar, "mustaqil__ot.txt"))
    mRavish = _load_lemma_list(os.path.join(suzlar, "mustaqil__ravish.txt"))
    mSifat = _load_lemma_list(os.path.join(suzlar, "mustaqil__sifat.txt"))
    mSon = _load_lemma_list(os.path.join(suzlar, "mustaqil__son.txt"))

    global oModal, oTaqlid, oUndov
    oModal = _load_lemma_list(os.path.join(suzlar, "oraliq__modal.txt"))
    oTaqlid = _load_lemma_list(os.path.join(suzlar, "oraliq__taqlid.txt"))
    oUndov = _load_lemma_list(os.path.join(suzlar, "oraliq__undov.txt"))

    global yBoglovchi, yKomakchi, yYuklama
    yBoglovchi = _load_lemma_list(os.path.join(suzlar, "yordamchi__boglovchi.txt"))
    yKomakchi = _load_lemma_list(os.path.join(suzlar, "yordamchi__komakchi.txt"))
    yYuklama = _load_lemma_list(os.path.join(suzlar, "yordamchi__yuklama.txt"))

    _DICT_LOADED = True


# -----------------------------
# Core: "longest prefix lemma" match
# -----------------------------
def _best_match_from_entries(word: str, entries: List[str]) -> str:
    """
    entries are dictionary lines that may contain backslashes.
    We treat lemma as the part BEFORE the first backslash.
    We DO NOT validate the remaining suffix in 'word'.
    We return the longest lemma that is a prefix of 'word'.
    """
    if not word:
        return ""

    w = word
    w2 = w[:2] if len(w) >= 2 else w

    best = ""
    for e in entries:
        if w2 and not e.startswith(w2):
            continue

        lemma = e.split("\\", 1)[0]
        if not lemma:
            continue

        if w.startswith(lemma) and len(lemma) > len(best):
            best = lemma

    return best


def _lemma_from_all_pos(word: str) -> str:
    # Combine POS lists. We keep POS separate only for potential future use;
    # for now we just want the longest lemma across ALL relevant dictionaries.
    return _best_match_from_entries(word, mOlmosh + mOt + mRavish + mSifat + mSon)


def _lemma_from_verbs(word: str) -> str:
    return _best_match_from_entries(word, mFel)


def lemmatize_word(word: str) -> str:
    """
    Lemmatize a single word using "longest dictionary prefix lemma".
    No suffix validation.
    """
    read_all_pos_lemmas()

    w = change_apostrophe(word).lower().strip()
    if not w:
        return ""

    if w.isdigit():
        return w

    if w in exceptions:
        return w

    # helper words: if exact match, return itself
    if (w in yYuklama or w in yKomakchi or w in yBoglovchi or
        w in oUndov or w in oModal or w in oTaqlid):
        return w

    # Choose the longest lemma among POS and VERB dictionaries.
    p = _lemma_from_all_pos(w)
    v = _lemma_from_verbs(w)

    if len(p) > len(v):
        return p
    if len(v) > len(p):
        return v
    # tie: prefer POS if non-empty
    return p or v or w


def __sound_change(word):
    sound_exchange = {'bilag': 'bilak', 'bo‘yo': 'bo‘ya', 'bolalig': 'bolalik', 'chirog': 'chiroq', 'elag': 'elak', 'etig': 'etik', 'ilg‘o': 'ilg‘a', 'ishqo': 'ishqa', 'kerag': 'kerak', 'ko‘ylag': 'ko‘ylak', 'kurag': 'kurak', 'o‘qu': 'o‘qi', 'o‘yno': 'o‘yna', 'ang': 'ong', 'ata': 'ot', 'qatig': 'qatiq', 'qayno': 'qayna', 'qishlog': 'qishloq', 'qulog': 'quloq', 'quvno': 'quvna', 'saylo': 'sayla', 'sayro': 'sayra', 'so‘ro': 'so‘ra', 'sana': 'son', 'tanlo': 'tanla', 'taro': 'tara', 'tarqo': 'tarqa', 'terag': 'terak', 'teshig': 'teshik', 'tilag': 'tilak', 'tirgag': 'tirgak', 'to‘qu': 'to‘qi', 'to‘shag': 'to‘shak', 'tomog‘': 'tomoq', 'tovug‘': 'tovuq', 'tuynug': 'tuynuk', 'yasha': 'yosh', 'yoshlig': 'yoshlik', 'yumsho': 'yumsha', 'yurag': 'yurak'}
    sound_increase = {'achch': 'achi', 'avzoy': 'avzo', 'bun': 'bu ', 'chuvv': 'chuv', 'dey': 'de', 'fann': 'fan ', "g‘urr": "g‘ur", 'hadd': 'had', 'haqq': 'haq', 'hiss': 'his', 'iss': 'isi ', 'jizz': 'jiz', 'mavqey': 'mavqe', 'mavzuy': 'mavzu', 'o‘shan': 'o‘sha', 'obro‘y': 'obro‘', 'parvoy': 'parvo', 'qatti': 'qati', 'robb': 'Rob', 'sass': 'sasi', 'sharr': 'shar', 'shartt': 'shart', 'shun': 'shu', 'taqq': 'taq', 'tibb': 'tib', 'varr': 'var', 'xurr ': 'xur ', 'yey': 'ye'}
    sound_decrease = {"ayri": "ayir", "bag‘ri": "bag‘ir", "burn": "burun", "buyru": "buyur", "ho‘ngr": "ho‘ngir", "ikkal": "ikki", "ikkov": "ikki", "ingra": "ingir", "ko‘ngli": "ko‘ngil", "o‘g‘l": "o‘g‘il", "o‘rna": "o‘rin", "o‘rni": "o‘rin", "o‘yn": "o‘yin", "og‘za": "og‘iz", "og‘zi": "og‘iz", "olto": "olti", "pasa": "past", "qayri": "qayir", "qiyn": "qiyin", "qiza": "qizil", "qorni": "qorina", "sarg‘": "sariq", "shahr": "shahar", "singl": "singil", "susa": "sust", "ulg‘a": "ulug‘", "yetto": "yetti", "yig‘l": "yig‘i", "zahr": "zahar"}
    sound_change = [sound_exchange, sound_increase, sound_decrease]
    lemma = None
    for sound in sound_change:
        for key, val in sound.items():
            if word.lower().startswith(key):
                lemma = val
        if lemma is not None:
            break
    return lemma


# -----------------------------
# Requested behavior: treat input as ONE unit (phrase)
# -----------------------------
def lemmatize(text: str) -> str:
    """
    Treat the input string as ONE unit (phrase), do NOT lemmatize all tokens.
    If multiple words are provided, only the last token is lemmatized.
    """
    if text is None:
        return ""

    s = change_apostrophe(text).strip()
    if not s:
        return ""

    # We only split to identify the last token; semantically we treat it as one unit.
    parts = s.split()
    if not parts:
        return ""

    last = parts[-1]
    lemma_last = __sound_change(last)
    if lemma_last is None:
        lemma_last = lemmatize_word(last)

    out_parts = [change_apostrophe(p) for p in parts[:-1]] + [lemma_last]
    return " ".join(out_parts)


# -----------------------------
# Optional: legacy behavior - lemmatize every token
# -----------------------------
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЎўҒғҚқҲҳЁёʻʼ’‘`´\-']+|\d+|[^\s]")


def _tokenize_keep_punct(text: str) -> List[str]:
    # keeps punctuation as separate tokens
    return _WORD_RE.findall(text)


def lemmatize_all_tokens(text: str) -> str:
    """
    Legacy helper: lemmatize each token (roughly), keeping punctuation.
    Not requested, but handy for debugging.
    """
    if text is None:
        return ""

    read_all_pos_lemmas()
    s = change_apostrophe(text)

    tokens = _tokenize_keep_punct(s)
    out: List[str] = []
    for t in tokens:
        if t.isspace():
            out.append(t)
            continue
        if re.fullmatch(r"\d+", t):
            out.append(t)
            continue
        # words-like
        if re.fullmatch(r"[A-Za-zА-Яа-яЎўҒғҚқҲҳЁёʻʼ’‘`´\-']+", t):
            out.append(lemmatize_word(t))
        else:
            out.append(t)

    # join with spaces where appropriate (simple)
    return " ".join(out).replace("  ", " ").strip()
