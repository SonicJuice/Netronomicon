import re 
from collections import defaultdict 
from statistics import stdev, mean 
from math import log 


class YAKE(PreProcessText): 
    def __init__(self): 
        """ 
        redefines and initialises YAKE 
        RETURNS: None 
        """ 
        super(YAKE, self).__init__() 
        self.words = defaultdict(set) # vocabulary container 
        self.contexts = defaultdict(lambda: ([], [])) 
        self.features = defaultdict(dict) 

    def candidate_selection(self, n=2): 
        """ 
        selects ngrams of a given length as candidate phrases 
        RETURNS: None 
        """ 
        self.ngram_selection(n=n) 
        self.candidate_filtering() 

        for k in list(self.candidates): # further filters candidates starting/beginning with stopwords 
            v = self.candidates[k] 
            if v.surface_forms[0][0].lower() in self.stoplist or v.surface_forms[0][-1].lower() in self.stoplist: 
                del self.candidates[k] 

    def _vocabulary_building(self): 
        """ 
        builds the vocabulary used to weight candidates. Only keeps words containing at least one alpha-numeric character 
        RETURNS: None 
        """ 
        for i, sentence in enumerate(self.sentences): 
            shift = sum([s.length for s in self.sentences[0:i]]) # computes offset shift for the sentence 
            for j, word in enumerate(sentence.words): 
                index = word.lower() 
                self.words[index].add((shift + j, shift, i, word)) # add word occurrence 

    def _contexts_building(self, window=2): 
        """ 
        builds the contexts used to calculate relatedness. Words occurring within an n word window are considered as context words. 
        Only words co-occurring in a block (sequence of words that appear in the vocabulary) are considered. 
        RETURNS: None 
        """ 
        for i, sentence in enumerate(self.sentences): 
            words = [w.lower() for w in sentence.words] 
            block = [] 
            for j, word in enumerate(words): 
                if word not in self.words: 
                    block = [] # word is skipped and block is emptied if word isn't in the vocabulary 
                    continue 

                self.contexts[word][0].extend([w for w in block[max(0, len(block) - window):len(block)]]) # adds left context

                for w in block[max(0, len(block) - window):len(block)]: 
                    self.contexts[w][1].append(word) # adds right context 
                    block.append(word) 

    def _feature_extraction(self): 
        """ 
        computes the weight of individual words in terms of casing, position, frequency, 
        relatedness to context, and occurrence in different sentences 
        RETURNS: None 
        """ 
        term_frequency = [len(self.words[w]) for w in self.words] # term frequency of each word  
        term_frequency_nsw = [len(self.words[w]) for w in self.words if w not in self.stoplist] # term frequency of non-stopwords 
        mean_term_frequency = mean(term_frequency_nsw) 
        stdev_term_frequency = stdev(term_frequency_nsw) 
        max_term_frequency = max(term_frequency) 
        
        for word in self.words:    
            self.features[word]['isstop'] = word in self.stoplist 
            self.features[word]['TF'] = len(self.words[word]) # term frequency 
            self.features[word]['TF_A'] = 0 # acronym term frequency 
            self.features[word]['TF_U'] = 0 # upper case term frequency 

            for (offset, shift, sent_id, surface_form) in self.words[word]: 
                if surface_form.isupper() and len(word) > 1: 
                    self.features[word]['TF_A'] += 1 
                elif surface_form[0].isupper() and offset != shift: 
                    self.features[word]['TF_U'] += 1 

            # 1. Casing - importance to acronyms or words starting with a capital 
            self.features[word]['CASING'] = max(self.features[word]['TF_A'], 
            self.features[word]['TF_U']) 
            self.features[word]['CASING'] /= 1.0 + log( 
            self.features[word]['TF']) 

            # 2. Position - importance to words that occurring at the beginning of the document 
            sentence_ids = list(set([t[2] for t in self.words[word]])) 
            self.features[word]['POSITION'] = log(3.0 + median(sentence_ids)) 
            self.features[word]['POSITION'] = log(self.features[word]['POSITION']) 

            # 3. Frequency - importance to frequent words 
            self.features[word]['FREQUENCY'] = self.features[word]['TF'] 
            self.features[word]['FREQUENCY'] /= (mean_term_frequency + stdev_term_frequency) 

            # 4. Relatedness - importance to words that don't stopword characteristics 
            self.features[word]['WL'] = 0.0 
            if len(self.contexts[word][0]): 
                self.features[word]['WL'] = len(set(self.contexts[word][0])) 
                self.features[word]['WL'] /= len(self.contexts[word][0]) 
                self.features[word]['PL'] = len(set(self.contexts[word][0])) / max_term_frequency 

            self.features[word]['WR'] = 0.0 
            if len(self.contexts[word][1]): 
                self.features[word]['WR'] = len(set(self.contexts[word][1])) 
                self.features[word]['WR'] /= len(self.contexts[word][1]) 
            self.features[word]['PR'] = len(set(self.contexts[word][1])) / max_term_frequency 
            
            self.features[word]['RELATEDNESS'] = 1 
            self.features[word]['RELATEDNESS'] += (self.features[word]['WR'] + 
            self.features[word]['WL']) * \ 
            (self.features[word]['TF'] / max_term_frequency) 
            
            # 5. Different - importance to words that occur in multiple sentences 
            self.features[word]['DIFFERENT'] = len(set(sentence_ids)) 
            self.features[word]['DIFFERENT'] /= len(self.sentences) 

            # assembles featues for to weight words 
            A = self.features[word]['CASING'] 
            B = self.features[word]['POSITION'] 
            C = self.features[word]['FREQUENCY'] 
            D = self.features[word]['RELATEDNESS'] 
            E = self.features[word]['DIFFERENT'] 
            self.features[word]['weight'] = (D * B) / (A + (C / D) + (E / D)) 

    def candidate_weighting(self, window=2): 
        """ 
        calculates weighting as per YAKE paper 
        RETURNS: None 
        """ 
        if not self.candidates: 
            return 
        self._vocabulary_building() 
        self._contexts_building(window=window) 
        self._feature_extraction() 

        for k, v in self.candidates.items(): 
            lowercase_forms = [' '.join(t).lower() for t in v.surface_forms] # differentiated weights for words and stopwords 
            for i, candidate in enumerate(lowercase_forms): 
                term_frequency = lowercase_forms.count(candidate) 
                tokens = [t.lower() for t in v.surface_forms[i]] 
                prod_ = 1. 
                sum_ = 0.
                
                for j, token in enumerate(tokens): 
                    if self.features[token]['isstop']: 
                        term_stop = token 
                        prob_t1 = prob_t2 = 0 
                        if j - 1 >= 0: 
                            term_left = tokens[j-1] 
                            prob_t1 = self.contexts[term_left][1].count(term_stop) / self.features[term_left]['TF'] 

                        if j + 1 < len(tokens): 
                            term_right = tokens[j+1] 
                            prob_t2 = self.contexts[term_stop][0].count(term_right)/ self.features[term_right]['TF'] 
                            prob = prob_t1 * prob_t2 
                            prod_ *= (1 + (1 - prob)) 
                            sum_ -= (1 - prob) 

                        else: 
                            prod_ *= self.features[token]['weight'] 
                            sum_ += self.features[token]['weight'] 

                    """ sets sum_ to -1+eps so 1+sum_ != 0 if the candidate is a one token stopword at the 
                    start or the end of the sentence 
                    """
                    if sum_ == -1:  
                        sum_ = -0.99999999999 
                        self.weights[candidate] = prod_ 
                        self.weights[candidate] /= term_frequency * (1 + sum_) 

    def is_redundant(self, candidate, prev, threshold=0.8): 
        """ 
        tests if one candidate is redundant with respect to a list of already ones. 
        A candidate is considered redundant if its Levenshtein distance with another candidate 
        that is ranked higher in the list exceeds the pre-set threshold.  
        RETURNS: bool 
        """ 
        for prev_candidate in prev: 
            dist = levenshtein_distance(candidate, prev_candidate) 
            dist /= max(len(candidate), len(prev_candidate)) 
            if (1.0 - dist) > threshold: 
                return True 
            return False
