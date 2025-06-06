import tqdm
import sys
import os
import xml.etree.ElementTree as ET
import common.annotations
from multiprocessing import Pool
import itertools

def splitAnnotatedTexts(annotatedTexts, maxLength = 500, contextSize = 500, num_workers = 50) -> list:
    with Pool(num_workers) as p:
        items = p.starmap(_splitAnnotatedText, tqdm.tqdm(zip(annotatedTexts, itertools.repeat(maxLength), itertools.repeat(contextSize)),total= len(annotatedTexts)))

    items = [item for l in items for item in l]
    return items

def _splitAnnotatedText(annotatedText, maxLength = 500, contextSize = 500) -> list:
    try:
        if len(annotatedText.annotations) == 0:
            return []
        splitTexts = []
        numIgnoredTexts = 0
        end = 0
    
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

            #find all annotations between start and end
            annotationsInside = [annotation for annotation in annotatedText.annotations 
                                if annotation.start_char>=start and annotation.end_char<=end]
            
            splitAnnotatedText = common.annotations.AnnotatedText(annotatedText.fullText[start:end])
            for annotationInside in annotationsInside:
                subannotationText = annotatedText.fullText[annotationInside.start_char:annotationInside.end_char]
                splitAnnotation = common.annotations.Annotation(annotationInside.start_char - start, 
                                                            annotationInside.end_char - start, 
                                                            annotationInside.label,
                                                            subannotationText)
                splitAnnotatedText.addAnnotation(splitAnnotation)

            #set context
            left = None
            right = None
            if (start > 0):
                left = annotatedText.fullText[max(0, start - contextSize):start]
            if (end < len(annotatedText.fullText)):
                right = annotatedText.fullText[end : min(len(annotatedText.fullText), end + contextSize)]
            splitAnnotatedText.addContext(left, right)

            #if (len(splitAnnotatedText.annotations) > 0):
            splitTexts.append(splitAnnotatedText)
            #else:
            #    numIgnoredTexts = numIgnoredTexts + 1
            #     print(f"Text chunk without annotations ignored")

            #shift current chunk's start and end
            start = end
            end = start + maxLength
            end = min(len(annotatedText.fullText), end)
        return splitTexts
    except Exception as ex:
        print(ex)

def read_xml(xml_filename):

    with open(xml_filename, encoding="utf-8") as fp:
        xml_string = fp.read()
        tree = ET.fromstring(xml_string)

        #output types files
        labels = []
        hierarchical_labels = []
        for label_node in tree.findall("Labels"):
            name = label_node.find("Name").text
            label = common.annotations.Label(name)
            labels.append(label)
            hierarchical_label = common.annotations.HierarchicalLabel(name)

            for sublabel in label_node.findall("Children"):
                name = sublabel.find("Name").text
                label = common.annotations.Label(name)
                labels.append(label)
                hierarchical_label.addSubLabel(common.annotations.HierarchicalLabel(name))
            
            hierarchical_labels.append(hierarchical_label)
        

        #output entities file
        hierarchical_labels_in_annotations = []
        labels_in_annotations = []

        numAnnotations = 0
        numSubannotations = 0
        annotatedTexts = []
        hierarchical_annotated_texts = []
        for item in tree.findall("Items"):
            finished = item.find("Finished").text
            if finished != "true":
                continue

            if len(item.findall("Children")) == 0:
                continue
            
            text = item.find("Text").text
            annotatedText = common.annotations.AnnotatedText(text)
            hierarchical_annotated_text = common.annotations.HierarchicalAnnotatedText(text)

            for annotation in item.findall("Children"):
                start = (int) (annotation.find("Start").text)
                end = (int) (annotation.find("End").text)
                label = annotation.find("Label").text
                annotation_text = text[start:end]

                #Add hierarchical label
                existing_label = [l for l in hierarchical_labels_in_annotations if l.label==label]
                if len(existing_label) == 0:
                    new_label = [l for l in hierarchical_labels  if l.label==label]
                    hierarchical_labels_in_annotations.append(new_label[0])
                
                    #Add regular label and sublabels
                    labels_in_annotations.append(label)
                    labels_in_annotations.extend([sl.label for sl in new_label[0].sublabels if sl.label not in labels_in_annotations])
                
                highLevelAannotation = common.annotations.Annotation(start, end, label, annotation_text)
                annotatedText.addAnnotation(highLevelAannotation)
                
                hierarchical_annotation = common.annotations.HierarchicalAnnotation(start, end, label, annotation_text)
                hierarchical_annotated_text.addAnnotation(hierarchical_annotation)
                
                numAnnotations = numAnnotations + 1

                for subannotation in annotation.findall("Children"):
                    sub_start = (int) (subannotation.find("Start").text)
                    sub_end = (int) (subannotation.find("End").text)
                    sub_label = subannotation.find("Label").text
                    sub_text = text[sub_start:sub_end]
                    if sub_start < start or sub_end < start:
                        continue
                    
                    lowLevelAnnotation = common.annotations.Annotation(sub_start, sub_end, sub_label, sub_text)
                    annotatedText.addAnnotation(lowLevelAnnotation)
                    hierarchical_subannotation = common.annotations.HierarchicalAnnotation(sub_start - start, sub_end - start, sub_label, sub_text)
                    hierarchical_annotation.addAnnotation(hierarchical_subannotation)

                    numSubannotations = numSubannotations + 1
            annotatedTexts.append(annotatedText)
            hierarchical_annotated_texts.append(hierarchical_annotated_text)

        annotatedTexts = splitAnnotatedTexts(annotatedTexts, 10000)
        
        return labels_in_annotations, annotatedTexts, hierarchical_labels_in_annotations, hierarchical_annotated_texts
       

