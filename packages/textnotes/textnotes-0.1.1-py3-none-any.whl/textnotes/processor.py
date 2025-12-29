import json
from .utils import (
    split_sentences,
    clean_text,
    shorten_sentence,
    extract_keywords,
    group_topics
)

def to_bullets(text, emoji="👉", highlight=True):
    text = clean_text(text)
    sentences = split_sentences(text)
    sentences = [shorten_sentence(s) for s in sentences if s.strip()]
    if highlight:
        sentences = extract_keywords(sentences)
    return "\n".join([f"{emoji} {s}" for s in sentences])

def auto_title(text):
    words = text.split()
    for w in words:
        if w[0].isalpha() and w[0].isupper():
            return f"{w} Overview"
    return "Text Notes"

def auto_summary(text):
    first = split_sentences(text)[0]
    return first

def to_json(title, summary, bullets):
    return json.dumps({
        "title": title,
        "summary": summary,
        "bullets": bullets.split("\n")
    }, indent=4, ensure_ascii=False)

def flashcards(text):
    sentences = [s for s in split_sentences(text) if s.strip()]
    return "\n".join([f"Q: What about this?\nA: {s}\n" for s in sentences])

def process_all(text):
    # Get clean values
    title = auto_title(text)        
    summary = auto_summary(text)     
    bullets = to_bullets(text)
    json_data = to_json(title, summary, bullets)
    flash = flashcards(text)
    topics = group_topics(split_sentences(text))

    # Output formatted with labels only for display
    final_output = (
        f"Title: {title}\n"
        f"Summary: {summary}\n\n"
        f"✨ NOTES:\n{bullets}\n\n"
        f"📘 JSON:\n{json_data}\n\n"
        f"🎴 FLASHCARDS:\n{flash}\n\n"
        f"📂 TOPIC GROUPS:\n{topics}\n"
    )

    filepath = "textnotes_output.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_output)

    return final_output, filepath
