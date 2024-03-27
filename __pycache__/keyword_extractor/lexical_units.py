

class Sentence: 
    def __init__(self, words): 
        """ 
        initialises Sentence attributes 
        RETURNS: None 
        """ 
        self.words = words # list of tokens in the sentence
        self.stems = []
        self.length = len(words) # number of tokens in the sentence 


class Candidate: 
    def __init__(self): 
        """ 
        initialises Candidate attributes 
        RETURNS: None 
        """ 
        self.surface_forms = [] # candidate's surface forms 
        self.offsets = [] # offsets of the surface form 
        self.sentence_ids = [] # sentence id of each surface form
