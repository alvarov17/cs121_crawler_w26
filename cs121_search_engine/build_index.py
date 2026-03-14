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
from urllib.parse import urljoin, urldefrag  # <-- Restored for PageRank
import warnings
import re
import pickle
import gc
from krovetzstemmer import Stemmer
import page_rank

seen_hashes = set()
file_names_sizes = {}

# ── SimHash state (persists across all documents) ───────────────────────────
SIMHASH_BITS = 64
SIMHASH_THRESHOLD = 3  # documents differing by <= 3 bits are near-dupes
seen_fingerprints: list[int] = []  # stores fingerprint of every accepted doc


def collect_paths(root: str):
    paths = []
    for root, dirs, files in os.walk(root):
        for filename in files:
            full_path = os.path.abspath(os.path.join(root, filename))
            paths.append(full_path)
    return paths


# ── PageRank Link Extractor ─────────────────────────────────────────────────
def extract_outgoing_links(html: str, base_url: str) -> list[str]:
    """Return a list of absolute URLs linked from this page."""
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')

    links = []
    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()
        # skip empty links or non-http links
        if not href or href.startswith(("mailto:", "javascript:", "#")):
            continue

        try:
            # try to get outgoing links
            abs_url = urljoin(base_url, href)
            abs_url, _ = urldefrag(abs_url)
            links.append(abs_url)
        except ValueError:
            # skips broken url link
            continue

    soup.decompose()
    return links


# ── Weighted Content Extractor ──────────────────────────────────────────────
def extract_and_weight_content(html: str):
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')

    # grabs title used in meta data
    title_tag = soup.find("title")
    display_title = title_tag.get_text(strip=True) if title_tag else "No Title"

    # weights for important tags
    tag_weights = {'title': 10, 'h1': 5, 'h2': 3, 'h3': 2, 'b': 2, 'strong': 2}
    weighted_freqs = {}

    for tag_name, weight in tag_weights.items():
        for tag in soup.find_all(tag_name):
            tag_text = tag.get_text().lower()
            tokens = tokenizer.tokenize(tag_text)
            for t in tokens:
                weighted_freqs[t] = weighted_freqs.get(t, 0) + weight # assigns weight to term

    # gets all visible text, weight is just 1
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    full_text = soup.get_text(" ").lower()
    all_tokens = tokenizer.tokenize(full_text)

    for t in all_tokens:
        weighted_freqs[t] = weighted_freqs.get(t, 0) + 1

    soup.decompose()
    return display_title, weighted_freqs


# ── Duplicate Detection ─────────────────────────────────────────────────────
def is_duplicate_page(text: str):
    hash_val = hashlib.md5(text.encode()).hexdigest()
    if hash_val in seen_hashes: # if hashed text is in the seen_hashes set
        return True
    seen_hashes.add(hash_val)
    return False


def _hash_token(token: str) -> int:
    return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) & ((1 << SIMHASH_BITS) - 1)


def _simhash(tokens: list) -> int:
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
    return bin(h1 ^ h2).count('1')


def near_duplicate(text: str) -> bool:
    tokens = re.findall(r'[a-z0-9]+', text)
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


def build_index(documents: list[str]):
    Index = {}
    doc_meta = {} # doc meta data dict
    link_graph = {}  # for page rank
    n = 0 # doc id counter
    file_num = 1
    stemmer = Stemmer() # krovetz stemmer

    for chunk in chunk_generator(documents, 1000):
        for doc in chunk:
            try:
                with open(doc, 'r') as d:
                    doc_content = json.load(d)
                n += 1

                html = doc_content.get("content", "")
                if not html:
                    continue

                # 1. Grab the URL immediately so we can build the link graph
                url = doc_content.get("url", "")

                # 2. Extract outgoing links for PageRank BEFORE duplicate checks
                #    (Even if a page is a duplicate, its links might be valuable)
                outgoing = extract_outgoing_links(html, url)
                if url:
                    link_graph[url] = outgoing

                # 3. Extract the weighted text & title
                title, weighted_freqs = extract_and_weight_content(html)

                # 4. Create string for duplicate check
                token_string = " ".join(weighted_freqs.keys())
                if is_duplicate_page(title + token_string) or near_duplicate(token_string):
                    continue

                # 5. Save to Metadata map
                doc_meta[n] = {'url': url, 'title': title}

                # 6. Build index with weighted scores
                for token, freq in weighted_freqs.items():
                    stemmed_token = stemmer.stem(token)
                    log_tf = 1 + math.log10(freq)

                    if stemmed_token not in Index:
                        Index[stemmed_token] = []
                    Index[stemmed_token].append(Posting(n, log_tf))

                # clean up memory
                del html
                del url
                del token_string

            except json.JSONDecodeError:
                print(f"JSON file could not be read: {doc}")
            except Exception as e:
                import traceback
                print(f"Skipping file {doc} due to error: {e}")
                traceback.print_exc() # in case any errors occur, can see which line

        if Index:
            write_to_file(Index, file_num)
            file_num += 1
            Index.clear()

        gc.collect()

    with open("doc_metadata.json", "w") as f: # Save the doc meta data file
        json.dump(doc_meta, f)

    with open("link_graph.json", "w") as f:  # Save the Link Graph
        json.dump(link_graph, f)

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
    print("Collecting Paths...")
    paths = collect_paths(
        "/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/cs121_search_engine/DEV"
    )
    print("Building Partial Indexes...")
    build_index(paths)
    convert_pickles_to_sorted_text()
    merge_sorted_text_files()
    print("Ranking Pages...")
    page_rank.main()
