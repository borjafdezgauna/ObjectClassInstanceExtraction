#Install RUST compiler
export RUSTFLAGS='-A warnings'
export RUSTFLAGS='-A invalid_reference_casting'
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

~/source/Python-3.8.15/python -m venv .env
source .env/bin/activate
pip install torch
pip install transformers
pip install -v "tqdm==4.54.0"
pip install -v "Jinja2==3.0.1"
pip install -v "scikit-learn==0.23.2"
pip install -v "scipy==1.5.4"
pip install -v "numpy==1.19.2"
pip install -v "pynvml==8.0.4"
pip install -v "tensorboard==2.13.0"
pip install wget
pip install -v "spacy==3.6"
