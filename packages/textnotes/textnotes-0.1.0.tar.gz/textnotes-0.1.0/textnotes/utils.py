import re
from collections import defaultdict

def clean_text(text: str) -> str:
    """Basic text cleaning: remove extra spaces and normalize."""
    return re.sub(r"\s+", " ", text).strip()

def split_sentences(text: str):
    """Split text into sentences using punctuation."""
    text = clean_text(text)
    return re.split(r"[.!?]+", text)

def shorten_sentence(sentence: str) -> str:
    """Shorten long sentences for bullets."""
    sentence = sentence.strip()
    if len(sentence) > 80:
        return sentence[:77] + "..."
    return sentence

def extract_keywords(sentences):
    """Highlight keywords by bolding capitalized words."""
    highlighted = []
    for s in sentences:
        parts = s.split()
        new_parts = []
        for p in parts:
            if p[:1].isupper():
                new_parts.append(f"**{p}**")
            else:
                new_parts.append(p)
        highlighted.append(" ".join(new_parts))
    return highlighted

def group_topics(sentences):
    """Group sentences by first keyword."""
    groups = defaultdict(list)

    for s in sentences:
        words = s.split()
        if not words:
            continue
        key = words[0].lower()
        groups[key].append(s)

    return dict(groups)
