"""
	Build Index and Postings
"""

import tokenizer
import hashlib
import json
import os
from bs4 import BeautifulSoup,XMLParsedAsHTMLWarning
import warnings
import re
import pickle


# import warnings

# warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

MAX_INDEX = 50000 # might need to change this number 

# in the structure 
# hash value : list of pages would mean that the pages are duplicates/near duplicate
# this is due to a hash collision
# seen_hashes = dict{}

seen_hashes = set()
unique_tokens = set()
file_names_sizes = {}

class Posting:
	def __init__(self, docid: int, tfidf: int):
		self.docid = docid
		self.tfidf = tfidf # should be the frequency of words for now 
		# self.fields = fields

def collect_paths(root: str): # root should be the path to the DEV folder with all the JSON files
	paths = []
	for root, dirs, files in os.walk(root):
		for filename in files:
			full_path = os.path.abspath(os.path.join(root, filename))
			paths.append(full_path)
	return paths

def get_visible_text(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ")
    return re.sub(r"\s+", " ", text).lower()

def is_duplicate_page(text: str):
    hash = hashlib.md5(text.encode()).hexdigest()
    if hash in seen_hashes:
        return True
    seen_hashes.add(hash)
    return False

def near_duplicate(text):
	return False

def document_generator(documents: list[str]):
	yield from documents

def write_to_file(Index: dict, file_num: int):
	folder_name = "index_pickle"
	file_name = "index_" + str(file_num) + ".pickle"
	full_path = os.path.join(folder_name, file_name)
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	with open(full_path, 'wb') as f:
		pickle.dump(Index, f)
	file_names_sizes[file_name] = os.path.getsize(full_path)
	#Need to check the full path instead of assuming we're running the script from inside folder_name

def build_index(documents: list[str]): # documents are json files
	"""
		Function that builds inverted index

		:param documents: list

		:return: dict | HashMap

	"""
	Index = {}
	n = 0
	file_num = 1
	for doc in document_generator(documents):
		try:
			with open(doc, 'r') as d:
				doc_content = json.load(d)
			n += 1
			html = doc_content["content"]
			text = get_visible_text(html)
			if is_duplicate_page(text) or near_duplicate(text):
				continue
			tokens = tokenizer.tokenize(text)
			frequency = tokenizer.compute_word_frequencies(tokens)
			for token_lower, freq in frequency.items():
				# token_lower = token.data.lower()
				unique_tokens.add(token_lower)
				if token_lower not in Index:
					Index[token_lower] = [] # empty list of postings
				Index[token_lower].append(Posting(n, freq)) # no fields attribute for now
			if len(Index) >= MAX_INDEX:
				# store index into file here
				write_to_file(Index, file_num)
				file_num += 1
				Index = {}
		# store renaining index here once loop finishes
		# i guess we can return the index , or make this a void function
		except json.JSONDecodeError:
			print("JSON file could not be read")
	write_to_file(Index, file_num)
	print(len(seen_hashes)) # number of pages indexed
	return Index

def write_report(filename = "indexer_report.txt"):
	with open(filename, "w") as f:
		f.write(f"Indexed documents: {len(seen_hashes)}\n\n")
		f.write(f"Number of unique tokens: \n{len(unique_tokens)}\n\n")
		f.write("Total size of index in KB:\n")
		total_size = 0
		for name, size in file_names_sizes.items():
			f.write(f"{name}: {(size / 1024):.2f} KB\n")
			total_size += size
		f.write(f"\n Total : {(total_size / 1024):.2f}")
	print(f"Report written to {filename}")

if __name__ == "__main__":
	warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
	paths = collect_paths("/home/alvarov2/crawler_w26/DEV")
	index = build_index(paths)
	write_report()