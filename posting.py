class Posting:
    __slots__ = ['docid', 'tfidf', 'url'] 
    
    def __init__(self, docid: int, tfidf: int, url: str = "none"):
        self.docid = docid
        self.tfidf = tfidf
        self.url = url