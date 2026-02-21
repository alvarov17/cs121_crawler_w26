class Posting:
    __slots__ = ['docid', 'tfidf'] 
    
    def __init__(self, docid: int, tfidf: int):
        self.docid = docid
        self.tfidf = tfidf