"""
	Build Index and Postings
"""

import tokenizer
import hashlib
import json
import os

# in the structure 
# hash value : list of pages would mean that the pages are duplicates/near duplicate
# this is due to a hash collision
# seen_hashes = dict{}

seen_hashes = set()

class Postings:
	def __init__(self, docid: int, tfidf: int):
		self.docid = docid
		seld.tfidf = tfidf # should be the frequency of words for now 
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

def is_duplicate_page(text): str:
    hash = hashlib.md5(text.encode()).hexdigest()
    if hash in seen_hashes:
        return True
    seen_hashes.add(hash)
    return False

def near_duplicate():
	return False

def build_index(documents: list[str]): # documents are json files
	"""
		Function that builds inverted index

		:param documents: list

		:return: dict | HashMap

	"""
	try:
		Index = {}
		n = 0
		for doc in documents:
			with open(doc, 'r') as d:
				doc_content = json.load(d)
			n += 1
			html = doc_content["content"]
			text = get_visible_text(html)
			if is_duplicate_page(text) or near_duplicate(text):
				continue
			tokens = tokenize(text)
			freq = tokenizer.compute_word_frequencies(tokens)
			for token in tokens:
				token_lower = token.data.lower()
				if token_lower not in Index:
					Index[token_lower] = [] # empty list of postings
				Index[token_lower].append(Posting(n, freq[token_lower])) # no fields attribute for now 
		return Index
	except json.JSONDecodeError:
		print("JSON file could not be read")


