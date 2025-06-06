Requires Python 3.8!!!!!
https://linuxcapable.com/install-python-3-8-on-ubuntu-linux/

python3.8 -m venv .env
source .env/bin/activate

/home/bortx/source/Python-3.8.15/python -m venv .env
source .env/bin/activate

#If only CPU support is needed:
#pip install torch==2.2.0
#pip install torch-scatter -f https://data.pyg.org/whl/torch-2.2.0+cpu.html

#For CUDA-support:
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
pip install torch-scatter==2.1.2 -f https://data.pyg.org/whl/torch-2.2.0+cu121.html

pip install fastNLP
pip install fitlog
pip install transformers
pip install sparse==0.15.5
pip install numba==0.56.4
pip install numpy==1.18.5
