#-*- coding: utf-8 -*-

import os
import sys
import CvNerProcessor
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

def EvaluateModels(modelsFolder, testCasesFolder):
    print("Loading test cases in: " + testCasesFolder)
    inputFiles = []
    for (dirpath, dirnames, filenames) in os.walk(testCasesFolder):
        for filename in filenames:
            if filename.endswith('.test.xml'):
                inputFiles.append(os.path.join(dirpath, filename)) # dirpath + filename #os.path.join(dirpath, filename)
    print(str(len(inputFiles)) + " test cases found.")

    print("Loading models in: " + modelsFolder)
    NerProcessor = CvNerProcessor.Processor(modelsFolder)
    for inputFile in inputFiles:
        #Read the input file
        print("Processing file " + inputFile)
        try:
            file = open(inputFile,mode='r', encoding='utf-8')
            xml = file.read()
            file.close()
            #Parse the input xml file
            xml = xml.encode('utf-16')
            tree = ET.fromstring(xml)
            text = tree.text

            #Run the NerProcessor
            result = NerProcessor.ProcessText(text)

            #Save the result in a .result.xml file
            outputFile = inputFile.replace(".test.xml",".result.xml")
            file = open(outputFile, mode='w', encoding='utf-8')
            text = file.write(result)
            file.close()
        except:
            print("Error processing file")

if __name__== '__main__':
    if len(sys.argv) == 4:
        numFolds = int(sys.argv[3])
        for i in range(0,numFolds):
            trainingFolder = sys.argv[1] + "-" + str(i)
            testFolder = sys.argv[2] + "-" + str(i)

            EvaluateModels(trainingFolder, testFolder)
    else:
        print("Not enough arguments. Usage: evaluate-models <modelsFolder> <testCasesFolder> <numFolds>")