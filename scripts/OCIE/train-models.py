#-*- coding: utf-8 -*-

import os
import sys

def TrainModels(trainingFolder, testFolder, configFile = "config.cfg"):
    print("Training models using Json files in: " + trainingFolder)
    inputFiles = []
    for (dirpath, dirnames, filenames) in os.walk(trainingFolder):
        for filename in filenames:
            if filename.endswith('.spacy'):
                inputFiles.append(os.path.join(dirpath, filename)) # dirpath + filename #os.path.join(dirpath, filename)
    
    for filename in inputFiles:
        if filename.endswith('.spacy'):
            testFilename = filename.replace(trainingFolder,testFolder)
            if os.path.isfile(filename) and os.path.isfile(testFilename):
                print("Training model with file: " + filename)
                print("Testing model with file: " + testFilename)
                outputDir = os.path.join(dirpath,filename[:-6])
                print("The model will be saved in: " + outputDir)
                command = "python -m spacy train " + configFile + " --code functions.py --output \"" + outputDir + "\" --paths.train \"" + filename + "\" --paths.dev \"" +  testFilename + "\" --gpu-id 0"# > Annotations.log"
                print(command)
                os.system(command)
            elif os.path.isfile(filename):
                #no test samples
                print("Training and testing model with file: " + filename)
                outputDir = os.path.join(dirpath,filename[:-6])
                print("The model will be saved in: " + outputDir)
                command = "python -m spacy train " + configFile + " --code functions.py --output \"" + outputDir + "\" --paths.train \"" + filename + "\" --paths.dev \"" +  filename + "\" --gpu-id 0"# > Annotations.log"
                print(command)
                os.system(command)
            else:
                print("No training data found for model")
            #print (command)
    

if __name__== '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 5:
        numFolds = int(sys.argv[3])
        for i in range(0,numFolds):
            trainingFolder = sys.argv[1] + "-" + str(i)
            testFolder = sys.argv[2] + "-" + str(i)
            configFile = "config.cfg"
            if (len(sys.argv) == 5):
                configFile = sys.argv[4]
            TrainModels(trainingFolder, testFolder, configFile)
    else:
        if len(sys.argv) == 3:
            TrainModels(sys.argv[1], sys.argv[2])
        else:
            print("Not enough arguments. Usage: train-models <trainingFolder> <testFolder> [<numFolds>] [<configFile>]")