"""
	Build Index and Postings
"""

import tokenizer

class Postings:
	def __init__(self, docid, tfidf, fields):
		self.docid = docid
		seld.tfidf = tfidf # should be the frequency of words for now 
		self.fields = fields

def get_visible_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ")
    return re.sub(r"\s+", " ", text).lower()




def build_index(documents):
	"""
		Function that builds inverted index

		:param documents: list

		:return: dict | HashMap

	"""
	Index = {}
	n = 0
	for d in documents:
		n += 1
		text = get_visible_text(d)
		tokens = tokenize(text)
		# remove duplicate tokens here
		# get word coutns here i think
		freq = tokenizer.compute_word_frequencies(tokens)
		word_counts = None
		for token in tokens:
			token_lower = token.data.lower()
			if token_lower not in Index:
				Index[token_lower] = [] # empty list of postings
			Index[token_lower].append(Posting(n, freq[token_lower], fields)) # still not sure what 'fields' is
	return Index


