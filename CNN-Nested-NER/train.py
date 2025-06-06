import json
import os
import warnings
import argparse
import pickle

from fastNLP import cache_results, prepare_torch_dataloader
from fastNLP import print
from fastNLP import Trainer, Evaluator
from fastNLP import TorchGradClipCallback, MoreEvaluateCallback
from fastNLP import FitlogCallback
from fastNLP import SortedSampler, BucketedBatchSampler
from fastNLP import TorchWarmupCallback
from multiprocessing import Pool
import itertools
import tqdm

import numpy as np
import torch

import fitlog
# fitlog.debug()

from model.model import CNNNer
from model.metrics import NERMetric
from data.ner_pipe import SpanNerPipe
from data.padder import Torch3DMatrixPadder

def densify(x):
    x = x.todense().astype(np.float32)
    return x
    
#@cache_results('caches/ner_caches.pkl', _refresh=False)
def get_data(folder, model_name):

    pipe = SpanNerPipe(model_name=model_name)
    dl = pipe.process_from_file(folder)

    return dl, pipe.matrix_segs

def train(args, folder, dataset_name):
    
    model_name = args.model_name
    n_head = args.n_head
    ######hyper
    non_ptm_lr_ratio = 100
    schedule = 'linear'
    weight_decay = 1e-2
    size_embed_dim = 25
    ent_thres = 0.5
    kernel_size = 3
    ######hyper
    
    fitlog.set_log_dir('logs/')
    seed = fitlog.set_rng_seed(rng_seed=args.seed)
    os.environ['FASTNLP_GLOBAL_SEED'] = str(seed)
    fitlog.add_hyper(args)
    fitlog.add_hyper_in_file(__file__)
    
    dl, matrix_segs = get_data(folder, model_name)
    
    ## This took too much memory for the CVs dataset. Now we do this in Torch3DMatrixPadder that is called for each batch as needed
    ## instead of once for all instances in the dataset
    #dl.apply_field(densify, field_name='matrix', new_field_name='matrix', progress_bar='Densify')
    
    print(dl)
    label2idx = getattr(dl, 'ner_vocab') if hasattr(dl, 'ner_vocab') else getattr(dl, 'label2idx')
    print(f"{len(label2idx)} labels: {label2idx}, matrix_segs:{matrix_segs}")
    dls = {}
    for name, ds in dl.iter_datasets():
        ds.set_pad('matrix', pad_fn=Torch3DMatrixPadder(pad_val=ds.collator.input_fields['matrix']['pad_val'],
                                                        num_class=matrix_segs['ent'],
                                                        batch_size=args.batch_size))
    
        n_workers = 0
        if name == 'train':
            _dl = prepare_torch_dataloader(ds, batch_size=args.batch_size, num_workers=n_workers,# multiprocessing_context='spawn',
                                            prefetch_factor=None,
                                           batch_sampler=BucketedBatchSampler(ds, 'input_ids', batch_size=args.batch_size, num_batch_per_bucket=30),
                                           pin_memory=True, shuffle=True)
    
        else:
            _dl = prepare_torch_dataloader(ds, batch_size=args.batch_size, num_workers=n_workers,# multiprocessing_context='spawn',
                                                        prefetch_factor=None,
                                          sampler=SortedSampler(ds, 'input_ids'), pin_memory=True, shuffle=False)
        dls[name] = _dl
    num_ner_tags = matrix_segs['ent']
    model = CNNNer(model_name, num_ner_tag=num_ner_tags, cnn_dim=args.cnn_dim, biaffine_size=args.biaffine_size,
                     size_embed_dim=size_embed_dim, logit_drop=args.logit_drop,
                    kernel_size=kernel_size, n_head=n_head, cnn_depth=args.cnn_depth)
    
    # optimizer
    parameters = []
    ln_params = []
    non_ln_params = []
    non_pretrain_params = []
    non_pretrain_ln_params = []
    
    import collections
    counter = collections.Counter()
    for name, param in model.named_parameters():
        counter[name.split('.')[0]] += torch.numel(param)
    print(counter)
    print("Total param ", sum(counter.values()))
    fitlog.add_to_line(json.dumps(counter, indent=2))
    fitlog.add_other(value=sum(counter.values()), name='total_param')
    
    for name, param in model.named_parameters():
        name = name.lower()
        if param.requires_grad is False:
            continue
        if 'pretrain_model' in name:
            if 'norm' in name or 'bias' in name:
                ln_params.append(param)
            else:
                non_ln_params.append(param)
        else:
            if 'norm' in name or 'bias' in name:
                non_pretrain_ln_params.append(param)
            else:
                non_pretrain_params.append(param)
    optimizer = torch.optim.AdamW([{'params': non_ln_params, 'lr': args.lr, 'weight_decay': weight_decay},
                                   {'params': ln_params, 'lr': args.lr, 'weight_decay': 0},
                                   {'params': non_pretrain_ln_params, 'lr': args.lr*non_ptm_lr_ratio, 'weight_decay': 0},
                                   {'params': non_pretrain_params, 'lr': args.lr*non_ptm_lr_ratio, 'weight_decay': weight_decay}])
    # callbacks
    callbacks = []
    callbacks.append(FitlogCallback())
    callbacks.append(TorchGradClipCallback(clip_value=5))
    callbacks.append(TorchWarmupCallback(warmup=args.warmup, schedule=schedule))
    
    allow_nested = True
    metrics = {'f': NERMetric(matrix_segs=matrix_segs, ent_thres=ent_thres, allow_nested=allow_nested)}
    
    trainer = Trainer(model=model,
                      #driver='torch',
    #                  devices=-1,accelerator="auto",
    #                  gpus=None,
    #                  accelerator='cpu',
    #                  devices=-1,
                      device= "cuda",
                      #multiprocessing_context='spawn',
                      train_dataloader=dls.get('train'),
                      evaluate_dataloaders=dls.get('test'),
                      optimizers=optimizer,
                      callbacks=callbacks,
                      overfit_batches=0,
                      #device=0,
                      n_epochs=args.n_epochs,
                      metrics=metrics,
                      monitor='f#f#dev',
                      evaluate_every=-1,
                      evaluate_use_dist_sampler=True,
                      accumulation_steps=args.accumulation_steps,
    #                  fp16=True,
                      progress_bar='rich')
    
    trainer.run(num_train_batch_per_epoch=-1, num_eval_batch_per_dl=-1, num_eval_sanity_batch=1)
    fitlog.finish()

    print("Saving the model and tags...")
    folder = os.path.join(folder,'models')
    #Save the model
    if not os.path.exists(folder):
        os.makedirs(folder)
    model_filename = os.path.join(folder, dataset_name + ".pkl");
    torch.save(model.state_dict(), model_filename)
    print ("Model saved to " + model_filename)

    #Save the tags
    tags_filename = os.path.join(folder, dataset_name + "-tags.pkl");
    with open(tags_filename, 'wb') as f:
        pickle.dump(dl.label2idx, f, protocol=pickle.HIGHEST_PROTOCOL)
        print ("Tags saved to " + model_filename)

if __name__ == '__main__':
    if 'p' in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = os.environ['p']
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['MKL_THREADING_LAYER'] = 'GNU'
    warnings.filterwarnings('ignore')
    
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


    folders = args.folder.split(',')
    num_folds = int(args.num_folds)
    for folder in folders:
        for fold in range(0, num_folds):
            dataset_name = folder.split('/')[-1]
            fold_folder = f"{folder}-{fold}"

            # with Pool(num_workers) as p:
            #     p.starmap(train, tqdm.tqdm(zip(itertools.repeat(args), folders),total= len(folders)))
                    
            print(f"Training: folder={fold_folder}, dataset={dataset_name}")
            train(args, fold_folder, dataset_name)