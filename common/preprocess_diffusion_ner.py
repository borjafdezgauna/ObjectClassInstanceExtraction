import tqdm
import xml.etree.ElementTree as ET
import json
import common.annotations
import common.spacy
from multiprocessing import Pool
import itertools
import os

def isTokenValid(token) -> bool:
    if ' ' in token or '..' in token or '\n' in token:
        return False
    return True

class Entity(dict):
    def __init__(self, start, end, type):
        dict.__init__(self, start = start, end = end, type = type)
        self.start = start
        self.end = end
        self.type = type
        
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Item(dict):
    def __init__(self, tokens : list, entities : list, ltokens : list, rtokens : list):
        dict.__init__(self, tokens = tokens, entities = entities,
                       ltokens = ltokens, rtokens = rtokens, 
                       relations = [], origId = "GIC")
        self.tokens = tokens
        self.entities = entities
        self.ltokens = ltokens
        self.rtokens = rtokens
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
class WordTokenSource:
    def __init__(self, word, start_char, end_char):
        self.word = word
        self.start_char = start_char
        self.end_char = end_char

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    list_chunks = []
    for i in range(0, len(lst), n):
        list_chunks.append(lst[i:i + n])
    return list_chunks

def _annotatedTextsToPiqn(annotatedText, nlp) -> Item:
    try:

        doc = nlp(annotatedText.fullText)
        tokens = []
        tokensSource = []
        for token in doc:
            if not isTokenValid(token.text):
                continue

            start_char = token.idx
            end_char = start_char + len(token.text)
            tokens.append(token.text)
            word_token_source = WordTokenSource(token.text, start_char, end_char)
            tokensSource.append(word_token_source)

        entities = []
        ##char-based annotations -> word-based annotations
        for annotation in annotatedText.annotations:
            label = annotation.label

            word_i = 0
            while word_i < len(tokensSource) and tokensSource[word_i].start_char < annotation.start_char:
                word_i = word_i + 1

            if word_i >= len(tokensSource):
                continue

            if (tokensSource[word_i].start_char != annotation.start_char):
                #the annotation might be miss-aligned?
                word_i = word_i - 1
                print(f"Miss-aligned annotation ignored:\n{annotatedText.fullText[annotation.start_char:annotation.end_char]}\n")
                continue

            start_word_token_index = word_i
            start_word_token = tokensSource[start_word_token_index]
            
            while word_i < len(tokensSource) and tokensSource[word_i].start_char < annotation.end_char:
                word_i = word_i + 1

            if word_i >= len(tokensSource):
                continue

            end_word_token_index = word_i
            end_word_token = tokensSource[end_word_token_index]

            
            entity = Entity(start_word_token_index, end_word_token_index, label)
            entities.append(entity)
            
        ltokens = []
        if annotatedText.left != None:
            doc = nlp(annotatedText.left)
            for token in doc:
                if isTokenValid(token.text):
                    ltokens.append(token.text)

        rtokens = []
        if annotatedText.right != None:
            doc = nlp(annotatedText.right)
            for token in doc:
                if isTokenValid(token.text):
                    rtokens.append(token.text)

        piqnItem = Item(tokens, entities, ltokens, rtokens)

        

        return piqnItem
    
    except Exception as error:
    # handle the exception
        print("An exception occurred:", error)

def convert(annotatedTexts, num_workers = 50) -> list:
    import math
    from spacy import blank
    from spacy.tokenizer import Tokenizer

    nlp = blank("xx")#.load("xx_ent_wiki_sm")
    
    if nlp == None:
        return None
    
    tokenizer_creator = common.spacy.make_customize_tokenizer()
    tokenizer_creator(nlp)

    with Pool(num_workers) as p:
        piqnItems = p.starmap(_annotatedTextsToPiqn, tqdm.tqdm(zip(annotatedTexts, itertools.repeat(nlp)),total= len(annotatedTexts)))
    return piqnItems

def save_labels(labels, output_dir):
    
    filename = os.path.join(output_dir, f"types.json")
    label_set = common.annotations.LabelSet(labels)
    print(f"{len(labels)} labels exported to {filename}")
    with open(filename, 'w', encoding='utf8') as outfile:
        json.dump(label_set, outfile, ensure_ascii=False)

def save(items, output_dir, prefix):
        #Export items
        test_filename = os.path.join(output_dir, f"{prefix}.json")
        print(f"{len(items)} items exported to {test_filename}")
        with open(test_filename, 'w', encoding='utf8') as outfile:
            json.dump(items, outfile, ensure_ascii=False)