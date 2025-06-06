set 'PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:64'

python -m spacy train config-trf.cfg --output models --paths.train "C:\\Users\\Bortx\\AppData\\Local\\Xerka\\Temp\\Training\\Json\\top-level-training.spacy" --paths.dev "C:\\Users\\Bortx\\AppData\\Local\\Xerka\\Temp\\Training\\Json\\top-level-evaluation.spacy" --gpu-id 0
