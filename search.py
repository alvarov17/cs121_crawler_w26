import json
import os

INDEX_FILE = "master_index.txt" # merge.py output file
RESULTS_TO_PRINT = 5 # to not print every result

class Searcher:
    def __init__(self, index_path):
        self.index_path = index_path
        self.term_offsets = {}
        self.index_file = open(self.index_path, 'r', encoding='utf-8')
        self._build_seek_index()

    def _build_seek_index(self):
        """
        Step 1: Store the byte offset of each term
        """
        print("Step 1: Storing byte offsets...")
        while True:
            offset = self.index_file.tell()
            line = self.index_file.readline()
            if not line:
                break

            parts = line.split('\t', 1)
            if len(parts) == 2:
                self.term_offsets[parts[0]] = offset

    def get_postings(self, term):
        """
        Step 2: Retrieve postings list for a single term
        """
        if term not in self.term_offsets:
            return []

        self.index_file.seek(self.term_offsets[term])
        line = self.index_file.readline()
        _, postings_str = line.strip().split('\t', 1)
        return json.loads(postings_str)

    def intersect(self, p1, p2):
        """
        Step 3: AND merge two sorted postings
        O(N + M)
        """
        answer = []
        i = 0
        j = 0
        while i < len (p1) and j < len(p2):
            if p1[i][0] == p2[j][0]: # docid1 vs docid2
                answer.append(p1[i])
                i+=1
                j+=1
            elif p1[i][0] < p2[j][0]:
                i+=1
            else:
                j+=1
        return answer

    def search(self, query: str):
        """
        Process query as series of ANDs
        """
        terms = query.lower().split()
        if not terms:
            return []

        all_postings = []

        for term in terms:
            posting = self.get_postings(term)
            if not posting:
                return []
            all_postings.append(posting)

        all_postings.sort(key=len)

        result = all_postings[0]
        for next_p in all_postings[1:]:
            result = self.intersect(result, next_p)
            if not result:
                break

        return result

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
            for doc in results[:RESULTS_TO_PRINT]:
                print(f"DocID: {doc[0]} // Score {doc[1]}")


