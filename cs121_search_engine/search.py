import json
import math
import os
import pickle

from krovetzstemmer import Stemmer
import tokenizer

INDEX_FILE = "/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/cs121_search_engine/master_index.txt"
METADATA_FILE = "/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/cs121_search_engine/metadata.json" # The "Seek Map" from merge.py
DOC_INFO_FILE = "/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/cs121_search_engine/doc_metadata.json"  # The "Display Map" with URLs/Titles
PAGERANK_FILE = "/Users/curly.mp4/Desktop/cs121 assignments/cs121_crawler_w26/cs121_search_engine/pagerank.json"
RESULTS_TO_PRINT = 5# to not print every result

PAGERANK_WEIGHT = 0.3  #weight of pagerank's contribution to final score

class Searcher:
    def __init__(self, index_path, metadata_path=METADATA_FILE, doc_info_path=DOC_INFO_FILE,
                 pagerank_path=PAGERANK_FILE):
        self.index_path = index_path

        with open(metadata_path, 'rb') as f: # move the offset calculations to merge.py
            metadata = pickle.load(f)
            self.term_offsets = metadata['offsets']
            self.N = metadata['N']

        with open(doc_info_path, 'r') as f:
            self.doc_metadata = json.load(f)

        # PageRank scoring
        self.pagerank = {}
        if os.path.exists(pagerank_path):
            with open(pagerank_path, 'r') as f:
                self.pagerank = json.load(f)

        self.stem = Stemmer()
        self.index_file = open(self.index_path, 'r', encoding='utf-8')

    def get_postings(self, term):
        if term not in self.term_offsets:
            return []

        self.index_file.seek(self.term_offsets[term])
        line = self.index_file.readline()
        _, postings_str = line.strip().split('\t', 1)
        return json.loads(postings_str)

    def search(self, query: str): # M3: changed from boolean search to tfidf search with some jaccard
        """
        Step 1: Tokenize & Stem
        """
        tokens = tokenizer.tokenize(query)
        if not tokens:
            tokens = query.lower().split()

        stemmed_query_tokens = [self.stem.stem(token) for token in tokens]

        """
        Step 2: calculate Query Vector Weights
        (TD-IDF the query)
        """
        query_freqs = {}
        for t in stemmed_query_tokens:
            query_freqs[t] = query_freqs.get(t,0)+1

        query_weights = {}
        cached_postings = {}
        query_norm_sq = 0   # squared norm

        for term, freq in query_freqs.items():
            if term not in self.term_offsets: continue
            postings = self.get_postings(term)
            cached_postings[term] = postings
            df = len(postings)
            idf = math.log10(self.N/df)
            term_weight = (1 + math.log10(freq)) * idf
            query_weights[term] = term_weight
            query_norm_sq += term_weight ** 2

        if not query_weights: return []
        query_norm = math.sqrt(query_norm_sq)

        """
        Step 3: Calculate Dot Products (scores) & Tracking Term Count
        """
        scores = {}     # docid -> dot_product
        term_counts = {}

        for term, q_weight in query_weights.items():

            for docid, doc_tf_weight in cached_postings[term]:
                str_docid = str(docid)  # JSON keys are always strings
                if str_docid not in scores:
                    # Pull URL and Title from metadata here
                    meta = self.doc_metadata.get(str_docid, {"url": "Unknown", "title": "No Title"})
                    scores[str_docid] = {
                        'score': 0,
                        'url': meta['url'],
                        'title': meta['title']
                    }
                    term_counts[str_docid] = 0

                scores[str_docid]['score'] += doc_tf_weight * q_weight
                term_counts[str_docid] += 1

        """
        Step4. Cos Normalization & some Jaccard-ing
        to ensure the score is relative to the query's length
        """
        total_query_terms = len(query_weights)
        for docid in scores:
            raw_score = scores[docid]['score'] / query_norm
            jaccard_boost = term_counts[docid] / total_query_terms
            tfidf_score = raw_score * jaccard_boost

            # Blend with PageRank if available
            pr_score = self.pagerank.get(docid, 0.0)
            scores[docid]['score'] = (1.0 - PAGERANK_WEIGHT) * tfidf_score + PAGERANK_WEIGHT * pr_score

        sorted_docs = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        return sorted_docs[:RESULTS_TO_PRINT]

    def __del__(self):
        if hasattr(self, 'index_file'):
            self.index_file.close()

if __name__ == "__main__":
    searcher = Searcher(INDEX_FILE)

    while True:
        query = input("\nEnter search query (or 'q' to quit): ").strip()
        if query.lower() == 'q':
            break

        results = searcher.search(query)

        if not results:
            print("No documents found.")
        else:
            print(f"Found in {len(results)} documents")
            for doc, data in results:
                print(f"Score: {data['score']:.4f} // URL: {data['url']}")


