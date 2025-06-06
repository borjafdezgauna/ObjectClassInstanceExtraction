import tqdm
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



class OcieFile(dict):
    def __init__(self, classes: list, annotations : list):
        dict.__init__(self, classes = classes, annotations = annotations)
        self.entities = annotations
        self.classes = classes
        
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def isTokenValid(token) -> bool:
    if ' ' in token or '..' in token:
        return False
    return True

# def _convertAnnotatedText(annotatedText, i, nlp) -> Item:
#     try:

#         entities = []
#         ##char-based annotations -> word-based annotations
#         for annotation in annotatedText.annotations:
#             label = annotation.label
#             entity = Entity(annotation.start_char, annotation.end_char, label)
#             entities.append(entity)
#         piqnItem = Item(entities, i, annotatedText.fullText)

        

#         return piqnItem
    
#     except Exception as error:
#     # handle the exception
#         print("An exception occurred:", error)

# def convert(annotatedTexts, num_workers = 50) -> list:
#     print("Converting annotated texts to OCIE (Spacy) format...")
#     import spacy
#     from spacy.tokenizer import Tokenizer

#     nlp = spacy.blank("xx")#.load("xx_ent_wiki_sm")
    
#     if nlp == None:
#         return None
    
#     tokenizer_creator = common.spacy.make_customize_tokenizer()
#     tokenizer_creator(nlp)
#     indices = [index for index in range(0, len(annotatedTexts))]

#     with Pool(num_workers) as p:
#         cnn_ner_items = p.starmap(_convertAnnotatedText, tqdm.tqdm(zip(annotatedTexts, indices, itertools.repeat(nlp)),total= len(annotatedTexts)))
#     return cnn_ner_items

def _save_annotations_by_type(filename, label, hierarchical_annotations, classes):
    print(f"Saving {len(hierarchical_annotations)} annotations of type {label} to {filename}")
    with open(filename, "w", encoding='utf8') as f:
        ocieAnnotatedTexts = []
        for hierarchical_annotation in hierarchical_annotations:
            annotations = [[annotation.start, annotation.end, annotation.type] 
                           for annotation in hierarchical_annotation.annotations]
            

            texts = []
            for ann in hierarchical_annotation.annotations:
                ann_text = hierarchical_annotation.text[ann.start:ann.end]
                for subann in ann.annotations:
                    text = ann_text[subann.start:subann.end]
                    texts.append(text)

            entities = {}
            entities['entities'] = annotations
            ocieAnnotatedTexts.append([hierarchical_annotation.text, entities])

        ocieItems = OcieFile(classes, ocieAnnotatedTexts)
        json.dump(ocieItems, f, ensure_ascii= False)


def save(hierarchical_labels, hierarchical_annotated_texts, output_dir):
        #Export items
        items_per_label = {}
        for hierarchical_annotated_text in hierarchical_annotated_texts:
            key = 'Annotations'
            if key not in items_per_label.keys():
                items_per_label[key] = []
            hierarchical_annotated_text.offset = 0
            items_per_label[key].append(hierarchical_annotated_text)

            for hierarchical_annotation in hierarchical_annotated_text.annotations:
                key = hierarchical_annotation.type
                if key not in items_per_label.keys():
                    items_per_label[key] = []

                items_per_label[key].append(hierarchical_annotation)
        
        for label in items_per_label.keys():
            filename = os.path.join(output_dir, f"{label}.json")
            if label == 'Annotations':
                classes = [label.label for label in hierarchical_labels]
                _save_annotations_by_type(filename, label, items_per_label[label], classes)
            else:
                hierarchical_label = [hierarchical_label for hierarchical_label in hierarchical_labels if hierarchical_label.label==label][0]
                classes = [label.label for label in hierarchical_label.sublabels]
                _save_annotations_by_type(filename, label, items_per_label[label], classes)
            