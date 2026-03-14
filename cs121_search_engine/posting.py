class Posting:
    __slots__ = ['docid', 'tfidf']

    def __init__(self, docid: int, tfidf: float):
        self.docid = docid
        self.tfidf = tfidf
