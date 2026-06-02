import spacy
from fuzzywuzzy import fuzz
from config import STAFF

nlp = spacy.load("ru_core_news_sm")

def extract_names(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "PER"]

def find_best_match(names):
    best_score = 0
    best_match = None
    for name in names:
        for staff_name in STAFF:
            score = fuzz.partial_ratio(name.lower(), staff_name.lower())
            if score > best_score:
                best_score = score
                best_match = staff_name
    return best_match
