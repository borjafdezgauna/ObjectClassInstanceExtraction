#-*- coding: utf-8 -*-

import os
import sys
import CvNerProcessor
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

def EvaluateModels(modelsFolder, testCasesFolder, outputFolder):
    #print("Loading test cases in: " + testCasesFolder)
    inputFiles = []
    for (dirpath, dirnames, filenames) in os.walk(testCasesFolder):
        for filename in filenames:
            if filename.endswith('.test.xml'):
                inputFiles.append(os.path.join(dirpath, filename)) # dirpath + filename #os.path.join(dirpath, filename)
    print(str(len(inputFiles)) + " test cases found.")

    #print("Loading models in: " + modelsFolder)
    NerProcessor = CvNerProcessor.Processor(modelsFolder)
    for inputFile in inputFiles:
        #Read the input file
        #print("Processing file " + inputFile)
        #try:
        file = open(inputFile, mode='r', encoding='utf-8')
        xml = file.read()
        file.close()
        #Parse the input xml file
        xml = xml.encode('utf-16')
        tree = ET.fromstring(xml)
        text = tree.text

        #Run the NerProcessor
        result = NerProcessor.ProcessText(text)

        #Save the result in a .result.xml file
        outputFilename = inputFile.replace(".test.xml",".result.xml").split('/')[-1]
        outputFile = os.path.join(outputFolder, outputFilename)
        file = open(outputFile, mode='w', encoding='utf-8')
        text = file.write(result)
        file.close()
        #except Exception as e:
         #   print(f"Error processing file : {inputFile}")

if __name__== '__main__':
    if len(sys.argv) == 5:
        numFolds = int(sys.argv[4])

        train_folders = sys.argv[1].split(',')
        test_folders = sys.argv[2].split(',')
        output_folders = sys.argv[3].split(',')
        if len(train_folders) != len(test_folders):
            print("Missmatched number of folders for training and evaluation")
            exit
        
        for set_i in range(0, len(train_folders)):
            for i in range(0,numFolds):
                training_folder = train_folders[set_i] + "-" + str(i)
                test_folder = test_folders[set_i] + "-" + str(i)
                output_folder = sys.argv[3]
                if not os.path.exists(output_folder):
                    os.mkdir(output_folder)
                output_folder = os.path.join(output_folder, training_folder.split('/')[-1])
                if not os.path.exists(output_folder):
                    os.mkdir(output_folder)
                print(f"Evaluating models {training_folder} - {test_folder} - {output_folder}")
                EvaluateModels(training_folder, test_folder, output_folder)
    else:
        print("Not enough arguments. Usage: evaluate-models <modelsFolder> <testCasesFolder> <numFolds>")