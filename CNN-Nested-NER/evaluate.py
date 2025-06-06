import pickle
import torch
from data.ner_pipe import SpanNerPipe
from model.metrics_utils import decode
from model.model import CNNNer
import argparse
import xml.etree.ElementTree as ElementTree
import os
import json
from fastNLP import DataSet, Instance
from fastNLP.io import Loader, DataBundle, iob2
from common.annotations import AnnotatedText, Annotation
import scipy.sparse
from sparse import COO
import tqdm

def sparse_coo_to_tensor(coo : COO):
    
    coo_tensor = torch.sparse_coo_tensor(coo.coords, coo.data, coo.shape)
    tensor = coo_tensor.to_dense()
    return torch.unsqueeze(tensor, 0)

def evaluate(args, folder, dataset_name):
   
    model_name = args.model_name
    n_head = args.n_head
    ######hyper
    non_ptm_lr_ratio = 100
    schedule = 'linear'
    weight_decay = 1e-2
    size_embed_dim = 25
    ent_thres = 0.5
    kernel_size = 3

    #Read xml test files
    # maxNumTestItems = 100
    testSamples = []
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if 'test' in filename:
                with open(dirpath + "/" + filename, 'r', encoding= 'utf-8') as file:
                    line = file.readline()
                    ds = DataSet()
                    while line != None and line != '':
                        data = json.loads(line)
                        testSamples.append(data)
                        
                        line = file.readline()

    models_folder = os.path.join(folder,'models')

    tags_filename = os.path.join(models_folder, dataset_name + "-tags.pkl")
    tagToIds = {}
    with open(tags_filename, 'rb') as f:
        tagToIds = pickle.load(f)
    idToTags = {v: k for k, v in tagToIds.items()}

    pipe = SpanNerPipe(model_name=model_name)

    ds = pipe.process_from_file(folder)
 
    #data_bundle = DataBundle(datasets={'train', ds}, vocabs=)
    #result = pipe.process(data_bundle.datasets, tagToIds)#texts, tagToIds)
    pad_token_id = pipe.tokenizer.pad_token_id

    model = CNNNer(model_name, num_ner_tag=len(tagToIds), cnn_dim=args.cnn_dim, biaffine_size=args.biaffine_size,
                        size_embed_dim=size_embed_dim, logit_drop=args.logit_drop,
                    kernel_size=kernel_size, n_head=n_head, cnn_depth=args.cnn_depth)

    
    
    model_filename = os.path.join(models_folder, dataset_name + ".pkl");
    with open(model_filename, 'rb') as file:
        state_dict = torch.load(file, weights_only=True)
        model.load_state_dict(state_dict)

    model.eval()

    test_dataset = ds.datasets['test']
    
    test_case = 0
    num_ignored_entities = 0
    for item in tqdm.tqdm(test_dataset):
    
        input_ids = torch.tensor([item['input_ids']])
        bpe_len = torch.tensor([item['bpe_len']])
        indices = torch.tensor([item['indexes']])
        matrix = sparse_coo_to_tensor(item['matrix'])
        #converted_matrix = torch.tensor([item['matrix']])
        
        scores = model(input_ids= input_ids, bpe_len= bpe_len, indexes= indices, matrix= matrix)
        ent_scores = scores['scores'].sigmoid()  # bsz x max_len x max_len x num_class
        ent_scores = (ent_scores + ent_scores.transpose(1, 2))/2
        span_pred = ent_scores.max(dim=-1)[0]
        word_len = torch.tensor([matrix[0].size()[0]])

        span_ents = decode(span_pred, word_len, allow_nested=True, thres=ent_thres)

        # full_text2 = " ".join(testSamples[test_case])
        full_text = testSamples[test_case]['text']
        annotatedText = AnnotatedText(full_text)
        for span_ent, ent_pred in zip(span_ents, ent_scores.cpu().detach().numpy()):
            pred_ent = set()
            for s, e, l in span_ent:
                score = ent_pred[s, e]
                ent_type = score.argmax()
                if score[ent_type]>=ent_thres:
                    pred_ent.add((s, e, ent_type))
            i = 0
            for entity in pred_ent:
                text = ''
                start = entity[0]
                end = entity[1]
                label = idToTags[entity[2]]

                if start >= len(testSamples[test_case]['tokens_source']) or end >= len(testSamples[test_case]['tokens_source']):
                    num_ignored_entities = num_ignored_entities + 1
                    continue
                start_char = testSamples[test_case]['tokens_source'][start]['start_char']
                end_char = testSamples[test_case]['tokens_source'][end]['end_char']

                text = full_text[start_char:end_char]
                annotatedText.addAnnotation(annotation= Annotation(start_char, end_char, label))
                i= i+1
                # text2 = " ".join(testSamples[testCase]['tokens'][start:end+1])
                # #print(f"Entity #{i}: {label} ({start}-{end}: {text})")
                # start_char = 0
                # for token_index in range(0, min(len(testSamples[testCase]['tokens']), start)):
                #     start_char = start_char + len(testSamples[testCase]['tokens'][token_index]) + 1
                # end_char = start_char
                # for token_index in range(start, min(len(testSamples[testCase]['tokens']), end)):
                #     end_char = end_char + len(testSamples[testCase]['tokens'][token_index]) + 1
                # if end < len(testSamples[testCase]['tokens']):
                #     end_char = end_char + len(testSamples[testCase]['tokens'][end])
                # i= i+1
                # annotatedText.addAnnotation(annotation= Annotation(start_char, end_char, label))
        

        output_folder = os.path.join(folder, "output")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_file = os.path.join(output_folder, f"{test_case}.result.xml")
        annotatedText.saveAsNerResult(output_file)
        test_case = test_case + 1

    if num_ignored_entities > 0:
            print(f"A total of {num_ignored_entities} entities were ignored because they were out of bounds")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lr', default=7e-5, type=float)
    parser.add_argument('-b', '--batch_size', default=8, type=int)
    parser.add_argument('-n', '--n_epochs', default=50, type=int)
    parser.add_argument('--warmup', default=0.1, type=float)
    parser.add_argument('--model_name', default='roberta-base', type=str)
    parser.add_argument('--cnn_depth', default=3, type=int)
    parser.add_argument('--cnn_dim', default=200, type=int)
    parser.add_argument('--logit_drop', default=0, type=float)
    parser.add_argument('--biaffine_size', default=400, type=int)
    parser.add_argument('--n_head', default=4, type=int)
    parser.add_argument('--seed', default=None, type=int)
    parser.add_argument('--accumulation_steps', default=1, type=int)
    parser.add_argument('--folder', type=str, required=True)
    parser.add_argument('--num_folds', type=int, default = 0)
    
    args = parser.parse_args()
    
    if args.num_folds == 0:
        evaluate(args, args.folder)
    else:
        folders = args.folder.split(',')
        num_folds = int(args.num_folds)
        for folder in folders:
            for i in range(0, args.num_folds):
                fold_folder = f"{folder}-{i}"
                dataset_name = folder.split('/')[-1]
                print(f"Evaluating: folder={fold_folder}, dataset={dataset_name}")
                evaluate(args, fold_folder, dataset_name)