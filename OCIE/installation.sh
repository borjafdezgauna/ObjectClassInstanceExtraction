python -m venv .env
source .env/bin/activate
pip install -U pip setuptools wheel
pip install -U 'spacy[cuda12x,transformers,lookups]'
pip install cupy-wheel
