"""
	Build Index and Postings
"""

class Postings:
	def __init__(self, docid, tfidf, fields):
		self.docid = docid
		seld.tfidf = tfidf # should be the frequency of words for now 
		self.fields = fields



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
		tokens = tokenize(d)
		# remove duplicate tokens here
		# get word coutns here i think
		word_counts = None
		for token in tokens:
			if token not in Index:
				Index[token] = [] # empty list of postings
			Index[token].append(Posting(n, word_counts, fields)
	return Index


