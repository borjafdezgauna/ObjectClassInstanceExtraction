# Object Class Instance Extraction (OCIE)
(Borja Fernández-Gauna et al.)

In this repository, we have put together the code used for the paper "Object Class Instance Extraction": it features some Nested-NER algorithms to compare their performance extracting object class instances from text with our proposal (OCIE).

The papers of these algorithms are in the 'papers' folder

## Running the code
### Requirements

It might work on a different environment, but I am using:
* Ubuntu 24
* Python
    * 3.12 (main version)
    * 3.8 (installed as alternative following https://linuxcapable.com/install-python-3-8-on-ubuntu-linux/)
* Visual Studio Code with these extensions:
    * Pylance v2025.4.1
    * Python v2025.4.1
    * Python Debugger v2025.6.0
    * Python Environments v0.3.10991008 (pre-release)

### Steps to run the experiments

Before trying to run any of the configurations, you should create a virtual environment for that folder.
Some of the algorithms use packages that require Python 3.12, others require 3.8. In each folder there is a installation.sh script to set up the environment. This will be activated by VSCode when we open the folder.

_In some of the scripts, the number of workers is hardcoded to 50. Set it lower if your machine has less cores._

1. Preprocess data

    The common/shared code is in the main folder. Open it from VS Code to run the initialization scripts:

    1. Preprocess data (Run and debug -> Initialization: preprocess data (all))

    This should convert the xml file in data/xml to the different formats used by the different algorithms (in the folder 'data')

2. Run OCIE

    Create a virtual environment in OCIE following installation.sh and open the folder from VSCode
    
    1. Run "Convert Json files to Spacy"
    2. Run "Train all"
    3. Run "Evaluate all"

    It will take a lot of time. The results will be saved to 'data/ocie/results'.

3. Run CNN-Nested-NER

    Create a virtual environment in CNN-Nested-NER following installation.sh and open the folder from VSCode

    1. Run "Train : all"
    2. Run "Evaluate : all"

    It will take a lot of time. The results will be saved to 'data/cnn-nested-ner/results'.

4. Measure performance (from an object class/property perspective)

    Go back to the main folder, open it from VSCode

    1. Run "Measure performance (OCIE)"
    1. Run "Measure performance (CNN-Nested-NER)"

    The performance stats will be saved to 'data/ocie/stats-cvs', 'data/cnn-nested-ner/certificates', ...

