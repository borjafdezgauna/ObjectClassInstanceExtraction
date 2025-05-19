#-*- coding: utf-8 -*-

import os
import sys
import CvNerProcessor
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

def EvaluateModel(model, testSet):
    print("Using test cases in: " + testSet)
    print("Using model in: " + model)
    command = "python -m spacy benchmark accuracy " + model + " " + testSet + " --code functions.py --output Evaluation.txt"# > Annotations.log"
    print(command)
    os.system(command)
    

if __name__== '__main__':
    EvaluateModel(sys.argv[1], sys.argv[2])