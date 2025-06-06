import tqdm
import common.zenodoget
import sys
import os
import xml.etree.ElementTree as ET
import json
import common.annotations
import spacy
from collections import defaultdict, Counter
import common.spacy
from multiprocessing import Pool
import itertools
import random
import shutil

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    list_chunks = []
    for i in range(0, len(lst), n):
        list_chunks.append(lst[i:i + n])
    return list_chunks

def splitAnnotatedTexts(annotatedTexts, maxLength = 300, contextSize = 300) -> list:
    try:
        splitTexts = []

        end = 0
        for annotatedText in annotatedTexts:
            start = 0
            end = min(len(annotatedText.fullText), maxLength)

            while start < len(annotatedText.fullText):
                
                #shift start if it is inside any annotation
                overlappingAnnotations = [annotation for annotation in annotatedText.annotations 
                                    if annotation.start_char<start and annotation.end_char>start]
                for overlappingAnnotation in overlappingAnnotations:
                    start = min(start, overlappingAnnotation.start_char)

                #shift end if it is inside any annotation
                overlappingAnnotations = [annotation for annotation in annotatedText.annotations 
                                    if annotation.start_char<end and annotation.end_char>end]
                for overlappingAnnotation in overlappingAnnotations:
                    end = max(end, overlappingAnnotation.end_char)

                #find all annoations between start and end
                annotationsInside = [annotation for annotation in annotatedText.annotations 
                                    if annotation.start_char>=start and annotation.end_char<=end]
                
                splitAnnotatedText = common.annotations.AnnotatedText(annotatedText.fullText[start:end])
                for annotationInside in annotationsInside:
                    splitAnnotation = common.annotations.Annotation(annotationInside.start_char - start, 
                                                                annotationInside.end_char - start, 
                                                                annotationInside.label)
                    splitAnnotatedText.addAnnotation(splitAnnotation)

                #set context
                left = None
                right = None
                if (start > 0):
                    left = annotatedText.fullText[max(0, start - contextSize):start]
                if (end < len(annotatedText.fullText)):
                    right = annotatedText.fullText[end : min(len(annotatedText.fullText), end + contextSize)]
                splitAnnotatedText.addContext(left, right)

                #we don't discard chunks without annotations
                #splitTexts.append(splitAnnotatedText)
                if (len(splitAnnotatedText.annotations) > 0):
                    splitTexts.append(splitAnnotatedText)
                #else:
                #    print(f"Text chunk without annotations ignored")

                #shift current chunk's start and end
                start = end
                end = start + maxLength
                end = min(len(annotatedText.fullText), end)
        
        #with open("entities.txt", "w") as f:
        #    for annotatedText in splitTexts:
        #        for annotation in annotatedText.annotations:
        #            f.write(f"[{annotation.start_char}:{annotation.end_char}] {annotatedText.fullText[annotation.start_char:annotation.end_char]}\n\n")
        return splitTexts
    except Exception as ex:
        print(ex)

def isTokenValid(token):
    return ' ' not in token.text and '\n' not in token.text and not '..' in token.text

def _annotatedTextsToPiqn(annotatedText, nlp) -> common.annotations.PiqnItem:
    try:

        doc = nlp(annotatedText.fullText)
        tokens = []
        tokensSource = []
        numTokensWithWhitespaces = 0
        for token in doc:
            if isTokenValid(token):
                start_char = token.idx
                end_char = start_char + len(token.text)
                tokens.append(token.text)
                word_token_source = common.annotations.WordTokenSource(token.text, start_char, end_char)
                tokensSource.append(word_token_source)
            else:
                numTokensWithWhitespaces = numTokensWithWhitespaces + 1
        #print(f"{numTokensWithWhitespaces} tokens with whitespaces were discarded")

        ##char-based annotations -> word-based annotations
        entities = []
        for annotation in annotatedText.annotations:
            label = annotation.label

#{"entities": {"Subject": {"short": "Subject", "verbose": "Subject"}, "NameCas": {"short": "NameCas", "verbose": "NameCas"}, 
# "CourseYear": {"short": "CourseYear", "verbose": "CourseYear"}, "StartDate": {"short": "StartDate", "verbose": "StartDate"},
#  "EndDate": {"short": "EndDate", "verbose": "EndDate"}, "ProgramName": {"short": "ProgramName", "verbose": "ProgramName"}, 
# "CenterNameCas": {"short": "CenterNameCas", "verbose": "CenterNameCas"}, "Code": {"short": "Code", "verbose": "Code"},
#  "Hours": {"short": "Hours", "verbose": "Hours"}, "Credits": {"short": "Credits", "verbose": "Credits"}, 
# "EvalMark": {"short": "EvalMark", "verbose": "EvalMark"}, 
# "Language": {"short": "Language", "verbose": "Language"}, "University": {"short": "University", "verbose": "University"}},
#  "relations": {}}
            #if label != 'NameCas' and label != 'CourseYear' and label != 'StartDate' and label != :
             #   continue

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

            if start_word_token_index == end_word_token_index:
                end_word_token_index = end_word_token_index + 1

            
            entity = common.annotations.PiqnEntity(start_word_token_index, end_word_token_index, label)
            entities.append(entity)
            
        ltokens = []
        if annotatedText.left != None:
            doc = nlp(annotatedText.left)
            for token in doc:
                if isTokenValid(token):
                    ltokens.append(token.text)

        rtokens = []
        if annotatedText.right != None:
            doc = nlp(annotatedText.right)
            for token in doc:
                if isTokenValid(token):
                    rtokens.append(token.text)

        piqnItem = common.annotations.PiqnItem(tokens, entities, ltokens, rtokens)

        

        return piqnItem
    
    except Exception as error:
    # handle the exception
        print("An exception occurred:", error)

def annotatedTextsToPiqn(annotatedTexts, num_workers = 50) -> list:
    import math
    import spacy
    from spacy.tokenizer import Tokenizer

    nlp = spacy.blank("xx")#.load("xx_ent_wiki_sm")
    #nlp = spacy.load("en_core_web_md")
    #nlp.tokenizer = Tokenizer(nlp.vocab)
    
    if nlp == None:
        return None
    
    tokenizer_creator = common.spacy.make_customize_tokenizer()
    tokenizer_creator(nlp)

    annotatedTexts = splitAnnotatedTexts(annotatedTexts)

    with Pool(num_workers) as p:
        piqnItems = p.starmap(_annotatedTextsToPiqn, tqdm.tqdm(zip(annotatedTexts, itertools.repeat(nlp)),total= len(annotatedTexts)))
    return piqnItems


def convertXmlToPiqn(xml_filename, output_dir):

    _,prefix = os.path.split(xml_filename)
    if '-' in prefix:
        prefix = prefix[:prefix.find('-')]
    else:
        prefix = prefix.replace(".xml", "")
    output_data_dir = os.path.join(output_dir, prefix)
    print(f"Saving data to output dir: {output_data_dir}")
    try:
        os.mkdir(output_data_dir)
    except:
        pass

    with open(xml_filename, encoding="utf-8") as fp:
        xml_string = fp.read()
        tree = ET.fromstring(xml_string)

        #output types files
        all_labels = []
        labels = {}
        labels["entities"] = {}
        labels["relations"] = {}
        for label in tree.findall("Labels"):
            name = label.find("Name").text

            if name != 'Subject':
                continue
            labels["entities"][name] = {}
            labels["entities"][name]["short"] = name
            labels["entities"][name]["verbose"] = name

            for sublabel in label.findall("Children"):
                name = sublabel.find("Name").text
                if (name not in all_labels):
                    all_labels.append(name)
                    labels["entities"][name] = {}
                    labels["entities"][name]["short"] = name
                    labels["entities"][name]["verbose"] = name

        labels_filename = os.path.join(output_data_dir, f"{prefix}_data_types.json")#xml_filename.replace(".xml", "") + "-data-types.json"
        with open(labels_filename, 'w', encoding='utf8') as outfile:
            json.dump(labels, outfile, ensure_ascii= False)

        #output entities file
        numAnnotations = 0
        numSubannotations = 0
        annotatedTexts = []
        for item in tree.findall("Items"):
            finished = item.find("Finished").text
            if finished != "true":
                continue

            text = item.find("Text").text
            annotatedText = common.annotations.AnnotatedText(text)

            for annotation in item.findall("Children"):

                highLevelLabel = annotation.find("Label").text
                if (highLevelLabel != 'Subject'):
                    continue
                
                highLevelAnnotation = common.annotations.Annotation((int) (annotation.find("Start").text),
                                                    (int) (annotation.find("End").text),
                                                    annotation.find("Label").text)
                #annotatedText.addAnnotation(highLevelAnnotation)
                #numAnnotations = numAnnotations + 1

                for subannotation in annotation.findall("Children"):
                    lowLevelAnnotation = common.annotations.Annotation((int) (subannotation.find("Start").text),
                                                    (int) (subannotation.find("End").text),
                                                    subannotation.find("Label").text)
                    annotatedText.addAnnotation(lowLevelAnnotation)
                    numSubannotations = numSubannotations + 1
            annotatedTexts.append(annotatedText)
        
        print(f"{str(len(annotatedTexts))} annotated texts read ({numAnnotations}/{numSubannotations} annotations)")
        print(f"Exporting as word tokens sentences with context")

        
        piqnItems = annotatedTextsToPiqn(annotatedTexts)

        print(f"Shuffling items and splitting into train/test sets")
        random.shuffle(piqnItems)

        numTestItems = int(len(piqnItems) * .20)
        testItems = piqnItems[:numTestItems]
        trainItems = piqnItems[numTestItems:]

        

        #Export test items
        test_filename = os.path.join(output_data_dir, f"{prefix}_test.json")
        print(f"{len(testItems)} items exported to {test_filename}")
        #with open(test_filename, 'w') as outfile:
        #    json.dump(testItems, outfile)
        with open(test_filename, 'w', encoding='utf8') as outfile:
            json.dump(testItems, outfile, ensure_ascii= False)
        
        #Export training items
        train_filename = os.path.join(output_data_dir, f"{prefix}_train.json")
        print(f"{len(trainItems)} items exported to {train_filename}")
        #with open(train_filename, 'w') as outfile:
        #    json.dump(trainItems, outfile)
        with open(train_filename, 'w', encoding='utf8') as outfile:
            json.dump(trainItems, outfile, ensure_ascii= False)

        


def download_files(doi, zenodo_access_token, output_dir = "tmp") -> list:
    downloaded_files = common.zenodoget.download(doi, output_dir, zenodo_access_token)
    return downloaded_files