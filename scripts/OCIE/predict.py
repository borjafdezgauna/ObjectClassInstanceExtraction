#-*- coding: utf-8 -*-

import os
import sys
import CvNerProcessor
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

def EvaluateModels(modelsFolder, testFile):


    print("Loading models in: " + modelsFolder)
    NerProcessor = CvNerProcessor.Processor(modelsFolder)

    #Read the input file
    print("Processing file " + testFile)
    try:
        file = open(testFile,mode='r', encoding='utf-8')
        text = file.read()
        file.close()

        #Run the NerProcessor
        result = NerProcessor.ProcessText(text)

        print(result)
        file.close()
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")

if __name__== '__main__':
    if len(sys.argv) == 3:
        modelsFolder = sys.argv[1]
        testFile = sys.argv[2]

        EvaluateModels(modelsFolder, testFile)
    else:
        print("Not enough arguments. Usage: predict <modelsFolder> <testFile>")