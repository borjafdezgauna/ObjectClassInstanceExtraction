#-*- coding: utf-8 -*-

import os
import sys

def PreProcessJsonFiles(folder):
    inputFiles = []
    for (dirpath, dirnames, filenames) in os.walk(folder):
        for filename in filenames:
            if filename.endswith('.json'): 
                inputFiles.append(os.path.join(dirpath, filename)) # dirpath + filename #os.path.join(dirpath, filename)
    
    import spacy
    from spacy.tokens import DocBin
    from tqdm import tqdm
    import re
    from spacy.tokenizer import Tokenizer
    from spacy.util import compile_prefix_regex, compile_suffix_regex, compile_infix_regex
    import functions
    import json
    
    for inputFile in inputFiles :
        nlp = spacy.blank("xx") # load a new spacy model
        
        customTokenizerCreator = functions.make_customize_tokenizer()
        customTokenizerCreator(nlp)
        
        db = DocBin() # create a DocBin object
    
        print("Processing file " + inputFile)
        outputFile = inputFile.replace(".json",".spacy")
        f = open(inputFile, encoding="utf8")
        TRAIN_DATA = json.load(f)
    
        invalid_span_tokens = re.compile(r'[\s\-/:;,\.ºª“”\n]')
        numErrors = 0
    
        for text, annot in tqdm(TRAIN_DATA['annotations']):
            #Preprocessing: remove utf-8 characters
            text = text.replace('–','-')#.replace('\n','|') #JUST TESTING!!
            
            doc = nlp.make_doc(text) 
            ents = []
            for start, end, label in annot["entities"]:
                valid_start = max(0, start)
                valid_end = min(len(text),end)
                while valid_start < len(text) and invalid_span_tokens.match(text[valid_start]):
                    valid_start += 1
                while valid_end > 1 and valid_end > valid_start and invalid_span_tokens.match(text[valid_end - 1]):
                    valid_end -= 1
                span = doc.char_span(valid_start, valid_end, label=label, alignment_mode="contract")
                if span is None:
                    numErrors = numErrors + 1
                    print("Skipping entity: '" + text[start:end] + "' -> '" + text[start-10:valid_end+10] + "'")
                else:
                    ents.append(span)
            doc.ents = ents 
            db.add(doc)
    #    print("Skipped entities: " + str(numErrors))
        db.to_disk(outputFile) # save the docbin object

if __name__== '__main__':
    if len(sys.argv) == 2:
        PreProcessJsonFiles(sys.argv[1])
    elif len(sys.argv) == 3:
        numFolds = int(sys.argv[2])
        for i in range(0,numFolds):
            folder = sys.argv[1] + "-" + str(i)
            PreProcessJsonFiles(folder)
    else:
        print("Wrong number of arguments. Usage: preprocess-training-data <folder> [<numFolds>]")