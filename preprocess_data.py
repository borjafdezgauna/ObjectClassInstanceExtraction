import argparse
import os
import random
import shutil
import json
#import warnings
#warnings.filterwarnings("ignore")

def tryMakedir(dir, clear_folder = False):
    
    try:
        if os.path.exists(dir):
            if clear_folder:
                shutil.rmtree(dir)
                os.mkdir(dir)
        else:
            os.mkdir(dir)
    except:
        pass

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def printAnnotationStats(annotations):
    avg_length = 0
    min_length = 99999999
    max_length = 0
    longest = 0
    num_annotations = 0
    for annotation in annotations['annotations']:
        num_annotations += len(annotation[1]['entities'])
        length = len(annotation[0])
        avg_length += length
        if length < min_length:
            min_length = length
        if length > max_length:
            max_length = length
            longest = annotation[0]
    
    print(f"Num items: {len(annotations['annotations'])}")
    print(f"Avg num annotations/item: {num_annotations / len(annotations['annotations'])}")
    print(f"Avg length = {avg_length / len(annotations['annotations'])}, min = {min_length}, max = {max_length}")
    print(f"Longest : {longest[:100]}")

   

def showStats(hierarchical_annotated_texts, hierarchical_labels, filename):
    print(f"{len(hierarchical_annotated_texts)} annotated texts read from {filename}")
    text_lengths = 0
    num_annotations = 0
    annotation_lengths = 0
    num_long_annotations = 0
    
    num_annotations_per_type = {}
    annotations_length_per_type = {}
    num_long_annotations_per_type = {}
    
    for hierarchical_annotated_text in hierarchical_annotated_texts:
        text_lengths += len(hierarchical_annotated_text.text)
        num_annotations += len(hierarchical_annotated_text.annotations)

        for annotation in hierarchical_annotated_text.annotations:
            annotation_lengths += len(annotation.text)
            if len(annotation.text) > 512:
                num_long_annotations += 1

            annotation_type = annotation.type
            if annotation_type not in num_annotations_per_type.keys():
                num_annotations_per_type[annotation_type] = 0
                annotations_length_per_type[annotation_type] = 0
                num_long_annotations_per_type[annotation_type] = 0

            num_annotations_per_type[annotation_type] += 1
            annotations_length_per_type[annotation_type] += len(annotation.text)
            if len(annotation.text) > 512:
                num_long_annotations_per_type[annotation_type] += 1
            

    print(f"Avg text length =  {text_lengths / len(hierarchical_annotated_texts)}")
    print(f"Avg num annotations = {num_annotations / len(hierarchical_annotated_texts)}")
    print(f"Avg annotation length = {annotation_lengths / len(hierarchical_annotated_texts)}")
    percent_long = (100* num_long_annotations) / len(hierarchical_annotated_texts)
    print(f"% annotations with >512 char = {percent_long}")

    for annotation_type in num_annotations_per_type.keys():
        print(f"{annotation_type}: {num_annotations_per_type[annotation_type]} items, avg. length = {annotations_length_per_type[annotation_type] / num_annotations_per_type[annotation_type]}, >512 = {(100* num_long_annotations_per_type[annotation_type]) / (num_annotations_per_type[annotation_type])}%")
    
    print("----------------------------")

def splitSetIndices(numItems, numSets = 10):
    print(f"Shuffling items and splitting into train/test sets")

    indices = [item for item in range(0, numItems)]
    random.shuffle(indices)

    itemsPerChunk = -((numItems) // -numSets)
    set_generator = chunks(indices, itemsPerChunk)
    sets= []
    totalSize = 0
    for s in set_generator:
        sets.append(s)
        totalSize = totalSize + len(s)
    assert(totalSize == numItems)
    splits = []
    for i in range(0, len(sets)):
        test_set = sets[i]
        dev_set = sets[(i+1) % len(sets)]
        random.shuffle(test_set)
        train_set = [item for j,set in enumerate(sets) for item in sets[j] if test_set != j and dev_set != j]
        random.shuffle(train_set)
        splits.append((train_set, test_set, dev_set))
    return splits

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('mode', type=str, help="Mode: 'download', 'preprocess'")
    arg_parser.add_argument('-m','--model', default='all', type=str)
    arg_parser.add_argument('-d','--dataset', type=str)
    args, _ = arg_parser.parse_known_args()

    if args.mode == 'preprocess':
        from common import preprocess_xml
        
        xml_directory = "data/xml"
        data_directory = "data"
        model = args.model
        for dirpath, dirnames, filenames in os.walk(xml_directory):
            for filename in filenames:
                if '.xml' in filename:
                    #1. read hierarchical labels and annotations
                    input_xml_file = os.path.join(xml_directory, filename)
                    print(f"Reading input file: {input_xml_file}")
                    labels, annotations, hierarchical_labels, hierarchical_annotated_texts = preprocess_xml.read_xml(input_xml_file)
                    showStats(hierarchical_annotated_texts, hierarchical_labels, filename)

                    _,prefix = os.path.split(input_xml_file)
                    if '-' in prefix:
                        prefix = prefix[:prefix.find('-')]
                    else:
                        prefix = prefix.replace(".xml", "")
                    
                    #2. split sets
                    sets = splitSetIndices(len(annotations), 10)
                    hierarchical_sets = splitSetIndices(len(hierarchical_annotated_texts), 10)
                    
                    #2. export
                    #OCIE (Spacy)
                    if model == 'ocie' or model == 'all':
                        from common import preprocess_ocie
                        for i, splitSet in enumerate(hierarchical_sets):
                            set_prefix = f"{prefix}-{i}"

                            def save_ocie_set(data_directory, model_dir, prefix, set_prefix, data_set):
                                output_dir = os.path.join(data_directory, model_dir)
                                tryMakedir(output_dir)
                                train_output_dir = os.path.join(output_dir, prefix)
                                tryMakedir(train_output_dir)
                                train_output_dir = os.path.join(train_output_dir, set_prefix)
                                tryMakedir(train_output_dir)
                                preprocess_ocie.save(hierarchical_labels, data_set, train_output_dir)

                            #OCIE-CNN
                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[0]]
                            save_ocie_set(data_directory, 'ocie', 'train', set_prefix, data_set)

                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[1]]
                            save_ocie_set(data_directory, 'ocie', 'test', set_prefix, data_set)

                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[2]]
                            save_ocie_set(data_directory, 'ocie', 'dev', set_prefix, data_set)

                            #OCIE-Transformers
                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[0]]
                            save_ocie_set(data_directory, 'ocie-transformers', 'train', set_prefix, data_set)

                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[1]]
                            save_ocie_set(data_directory, 'ocie-transformers', 'test', set_prefix, data_set)

                            data_set = [hierarchical_annotated_texts[item] for item in splitSet[2]]
                            save_ocie_set(data_directory, 'ocie-transformers', 'dev', set_prefix, data_set)

                    #Expected predictions
                    if model == 'all':
                        print('Saving expected results')
                        for i, splitSet in enumerate(sets):
                            set_prefix = f"{prefix}-{i}"

                            output_dir = os.path.join(data_directory, "expected")
                            tryMakedir(output_dir)
                            output_dir = os.path.join(output_dir, set_prefix)
                            tryMakedir(output_dir)
                            
                            test_set = [annotations[item] for item in splitSet[1]]
                            for j, annotatedText in enumerate(test_set):
    
                                output_file = os.path.join(output_dir, f"{j}.test.xml")
                                annotatedText.saveAsNerResult(output_file)
                        

                    #CNN-NER
                    if model == 'cnn-ner' or model == 'all':
                        from common import preprocess_cnn_ner
                        cnn_ner_items = preprocess_cnn_ner.convert(annotations)

                        for i, splitSet in enumerate(sets):
                            set_prefix = f"{prefix}-{i}"

                            output_dir = os.path.join(data_directory, "cnn-ner")
                            tryMakedir(output_dir)
                            output_dir = os.path.join(output_dir, set_prefix)
                            tryMakedir(output_dir)
                            
                            train_set = [cnn_ner_items[item] for item in splitSet[0]]
                            preprocess_cnn_ner.save(train_set, output_dir, 'train')

                            test_set = [cnn_ner_items[item] for item in splitSet[1]]
                            preprocess_cnn_ner.save(test_set, output_dir, 'test')

                            test_set = [cnn_ner_items[item] for item in splitSet[2]]
                            preprocess_cnn_ner.save(test_set, output_dir, 'dev')
                    
                    #Diffusion-NER
                    if model == 'diffusion-ner' or model == 'all':
                        from common import preprocess_diffusion_ner
                        cnn_ner_items = preprocess_diffusion_ner.convert(annotations)

                        for i, splitSet in enumerate(sets):
                            set_prefix = f"{prefix}-{i}"

                            output_dir = os.path.join(data_directory, "diffusion-ner")
                            tryMakedir(output_dir)
                            output_dir = os.path.join(output_dir, set_prefix)
                            tryMakedir(output_dir)

                            preprocess_diffusion_ner.save_labels(labels, output_dir)
                            
                            train_set = [cnn_ner_items[item] for item in splitSet[0]]
                            preprocess_diffusion_ner.save(train_set, output_dir, 'train')

                            test_set = [cnn_ner_items[item] for item in splitSet[1]]
                            preprocess_diffusion_ner.save(test_set, output_dir, 'test')

                            test_set = [cnn_ner_items[item] for item in splitSet[2]]
                            preprocess_diffusion_ner.save(test_set, output_dir, 'dev')
                    
                    

    else:
        raise Exception("Mode not in ['download'], e.g. 'python preprocess_data.py download ...'")
