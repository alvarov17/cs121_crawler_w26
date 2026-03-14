# Tokenizer from A1

import sys
import re
from collections import Counter

stopwords = set("""
i me my myself we our ours ourselves you your yours yourself yourselves he him his she her hers herself it its itself they them their theirs themselves what which who whom this that these
those am is are was were be been being have has had having do does did doing a an the and but if
or because as until while of at by for with about against between into through during before after above below to from up down in out on off over under again further then once here there when where
why how all any both each few more most other some such no not nor only own same so than too
very s t can will just don should now
""".split())

TOKEN_PATTERN = re.compile(r"[a-z0-9\'-]+")

def is_number(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False

def tokenize(text: str) -> list[str]:
    # extract valid chunks
    matches = TOKEN_PATTERN.findall(text.lower())
    
    # filter stop words numbers
    tokens = [word for word in matches if word not in stopwords and not is_number(word)]
    
    return tokens

def compute_word_frequencies(tokens: list[str]) -> dict:
    return dict(Counter(tokens))