"""
    Build Index and Postings
"""

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

MAX_INDEX = 50000 

seen_hashes = set()
unique_tokens = set()
file_names_sizes = {}

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

def near_duplicate(text):
    return False

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

    for chunk in chunk_generator(documents, 200):
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
                    
                tokens = tokenizer.tokenize(text)
                frequency = tokenizer.compute_word_frequencies(tokens)
                
                for token_lower, freq in frequency.items():
                    if len(token_lower) > 200: 
                        continue           
                    # hash the word to save on ram
                    unique_tokens.add(hash(token_lower))          
                    if token_lower not in Index:
                        Index[token_lower] = [] 
                    Index[token_lower].append(Posting(n, freq))
                    
                # delete to save ram again
                del html
                del text
                del tokens
                
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
        f.write(f"Number of unique tokens: \n{len(unique_tokens)}\n\n")
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
    paths = collect_paths("/home/alvarov2/crawler_w26/DEV")
    build_index(paths)
    convert_pickles_to_sorted_text()
    merge_sorted_text_files()
    write_report()