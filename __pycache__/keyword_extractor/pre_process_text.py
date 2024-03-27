from collections import defaultdict
from string import punctuation


class PreProcessText(object): 
    def __init__(self): 
        """ 
        initialises PreProcessText class attributes 
        RETURNS: None 
        """ 
        self.sentences = [] # list of Sentence objects 
        self.candidates = defaultdict(Candidate) # dict of Candidate objects 
        self.weights = {} 
        self.stoplist = set(stopwords.words('english')) 

    def _read(self, text): 
        """ 
        pre-processes text 
        RETURNS: list 
        """ 
        sentences = [] 
        for sentence_text in text.split('.'): # split text into sentences 
            words = re.findall(r'\b\w+\b', sentence_text) # extract words from each 
            if words: 
                sentences.append(Sentence(words)) 
        return sentences 

    def load_document(self, input): 
        """ 
        uses pre-processed text to populate stems 
        RETURNS: None 
        """ 
        self.__init__() 
        sents = self._read(text=input) 
        self.sentences = sents # populate the sentences 
        for i, sentence in enumerate(self.sentences): # populate stems 
            self.sentences[i].stems = [w.lower() for w in sentence.words] 

    def add_candidate(self, words, stems, offset, sentence_id): 
        """ 
        adds a keyphrase candidate to candidates container 
        RETURNS: None 
        """ 
        lexical_form = ' '.join(stems) 
        self.candidates[lexical_form].surface_forms.append(words) 
        self.candidates[lexical_form].lexical_form = stems 
        self.candidates[lexical_form].offsets.append(offset) 
        self.candidates[lexical_form].sentence_ids.append(sentence_id) 

    def ngram_selection(self, n=2): 
        """  
        selects all ngrams of a given length and populates candiates contianers 
        RETURNS: None 
        """
        self.candidates.clear() # resets candidates 
        for i, sentence in enumerate(self.sentences): 
            skip = min(n, sentence.length) # limits max n for short sentence 
            shift = sum([s.length for s in self.sentences[0:i]]) # computes offset shift for the sentence  
        for j in range(sentence.length): 
            for k in range(j + 1, min(j + 1 + skip, sentence.length + 1)): 
                self.add_candidate(words=sentence.words[j:k], stems=sentence.stems[j:k], offset=shift + j, sentence_id=i) 

    @staticmethod 
    def _is_alphanum(word, valid_punctuation='-'): 
        """ 
        checks if a word is alpha-numeric (excluding '-') 
        RETURNS: bool 
        """ 
        for punct in valid_punctuation.split(): 
            word = word.replace(punct, '') 
        return word.isalnum() 

 

    def candidate_filtering(self, minimum_length=2, minimum_word_size=2, valid_punctuation='-', maximum_word_number=5, only_alphanum=True): 
        """filters the candidates containing strings from the stoplist. Only 
        keeps those containing alpha-numeric characters and whose length exceeds a given number  
        RETURNS: None 
        """ 
        for k in list(self.candidates): # iterates through candidates 
            v = self.candidates[k] 
            words = [u.lower() for u in v.surface_forms[0]] # gets words via their-first occurring candidate forms 

            if set(words).intersection(self.stoplist): # discards if containing tokens that are in the stoplist 
                del self.candidates[k] 
            elif any(set(u).issubset(set(punctuation)) for u in words): # discards if containing tokens that are only punctuation 
                del self.candidates[k] 
            elif len(''.join(words)) < minimum_length: # dicards if containing tokens below the minimum number of characters 
                del self.candidates[k] 
            elif min([len(u) for u in words]) < minimum_word_size: # discards if containing small (1-character) tokens 
                del self.candidates[k] 
            elif len(v.lexical_form) > maximum_word_number: 
                del self.candidates[k] 

            if only_alphanum and k in self.candidates: 
                if not all([self._is_alphanum(w, valid_punctuation) for w in words]): 
            del self.candidates[k]
