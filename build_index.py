"""
    Build Index and Postings
"""
import math

from posting import Posting
from merge import convert_pickles_to_sorted_text, merge_sorted_text_files
import tokenizer
import hashlib
import json
import os
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning, MarkupResemblesLocatorWarning
import warnings
import re
import pickle
import gc
from nltk.stem import PorterStemmer

MAX_INDEX = 50000

seen_hashes = set()
file_names_sizes = {}

# ── SimHash state (persists across all documents) ───────────────────────────
SIMHASH_BITS = 64
SIMHASH_THRESHOLD = 3       # documents differing by <= 3 bits are near-dupes
seen_fingerprints: list[int] = []   # stores fingerprint of every accepted doc


def collect_paths(root: str):
    paths = []
    for root, dirs, files in os.walk(root):
        for filename in files:
            full_path = os.path.abspath(os.path.join(root, filename))
            paths.append(full_path)
    return paths


def get_visible_text(html: str):
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ")
    soup.decompose()
    return " ".join(text.split()).lower()


def is_duplicate_page(text: str):
    hash_val = hashlib.md5(text.encode()).hexdigest()
    if hash_val in seen_hashes:
        return True
    seen_hashes.add(hash_val)
    return False


# ── SimHash helpers ──────────────────────────────────────────────────────────

def _hash_token(token: str) -> int:
    """Hash a single token to a 64-bit integer."""
    return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) & ((1 << SIMHASH_BITS) - 1)


def _simhash(tokens: list) -> int:
    """
    Compute a SimHash fingerprint for a list of tokens.
    Each bit position gets +1 if that bit is set in the token hash, else -1.
    Final bit is 1 if the sum is positive, 0 otherwise.
    """
    vector = [0] * SIMHASH_BITS
    for token in tokens:
        h = _hash_token(token)
        for i in range(SIMHASH_BITS):
            if (h >> i) & 1:
                vector[i] += 1
            else:
                vector[i] -= 1
    fingerprint = 0
    for i in range(SIMHASH_BITS):
        if vector[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint


def _hamming_distance(h1: int, h2: int) -> int:
    """Count differing bits between two fingerprints."""
    return bin(h1 ^ h2).count('1')


def near_duplicate(text: str) -> bool:
    """
    Returns True if `text` is a near-duplicate of any previously seen document.
    Uses SimHash: documents whose fingerprints differ by <= SIMHASH_THRESHOLD
    bits are considered near-duplicates.
    If not a duplicate, stores the fingerprint for future comparisons.
    """
    tokens = re.findall(r'[a-z0-9]+', text)   # text is already lowercased
    if not tokens:
        return False

    fp = _simhash(tokens)

    for seen_fp in seen_fingerprints:
        if _hamming_distance(fp, seen_fp) <= SIMHASH_THRESHOLD:
            return True

    seen_fingerprints.append(fp)
    return False


# ── Index construction ───────────────────────────────────────────────────────

def chunk_generator(paths, chunk_size):
    for i in range(0, len(paths), chunk_size):
        yield paths[i:i + chunk_size]


def write_to_file(Index: dict, file_num: int):
    folder_name = "index_pickle"
    file_name = f"index_{file_num}.pickle"
    full_path = os.path.join(folder_name, file_name)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    with open(full_path, 'wb') as f:
        pickle.dump(Index, f, protocol=pickle.HIGHEST_PROTOCOL)
    file_names_sizes[file_name] = os.path.getsize(full_path) / 1024


def build_index(documents: list[str]):
    Index = {}
    n = 0
    file_num = 1
    stemmer = PorterStemmer()
    for chunk in chunk_generator(documents, 1000):
        for doc in chunk:
            try:
                with open(doc, 'r') as d:
                    doc_content = json.load(d)
                n += 1

                html = doc_content.get("content", "")

                if not html:
                    continue

                text = get_visible_text(html)
                if is_duplicate_page(text) or near_duplicate(text):
                    continue
                url = doc_content.get("url", "")
                tokens = tokenizer.tokenize(text)
                stemmed_tokens = [stemmer.stem(token) for token in tokens]
                frequency = tokenizer.compute_word_frequencies(stemmed_tokens)

                for token_lower, freq in frequency.items():
                    if len(token_lower) > 200:
                        continue
                    if token_lower not in Index:
                        Index[token_lower] = []
                    log_tf = 1 + math.log10(freq)
                    Index[token_lower].append(Posting(n, log_tf, url))

                del html
                del url
                del text
                del tokens
                del stemmed_tokens

            except json.JSONDecodeError:
                print(f"JSON file could not be read: {doc}")
            except Exception as e:
                print(f"Skipping file {doc} due to error: {e}")

        if Index:
            write_to_file(Index, file_num)
            file_num += 1
            Index.clear()

        gc.collect()


def write_report(filename="indexer_report.txt"):
    with open(filename, "w") as f:
        f.write(f"Indexed documents: {len(seen_hashes)}\n\n")
        # f.write(f"Number of unique tokens: \n{len(unique_tokens)}\n\n")
        f.write("Total size of index in KB:\n")
        total_size = os.path.getsize("master_index.txt") / 1024
        for name, size in file_names_sizes.items():
            f.write(f"{name}: {(size):.2f} KB\n")
            total_size += size
        f.write(f"\n Master Index Total : {(total_size):.2f} KB")
    print(f"Report written to {filename}")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    paths = collect_paths("/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/DEV")
    build_index(paths)
    convert_pickles_to_sorted_text()
    merge_sorted_text_files()