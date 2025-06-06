#-*- coding: utf-8 -*-

import os
import sys
from subprocess import Popen, PIPE
from multiprocessing import Pool
import itertools
import tqdm

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def RunCommand(command):
    pid = Popen(command, shell=True, stdout=PIPE)
    pid.wait()

def PrepareCommands(trainingFolder, testFolder, configFile = "config.cfg"):
    
    inputFiles = []
    for (dirpath, dirnames, filenames) in os.walk(trainingFolder):
        for filename in filenames:
            if filename.endswith('.spacy'):
                inputFiles.append(os.path.join(dirpath, filename)) # dirpath + filename #os.path.join(dirpath, filename)
    commands = []
    for filename in inputFiles:
        if filename.endswith('.spacy'):
            testFilename = filename.replace(trainingFolder,testFolder)
            if os.path.isfile(filename) and os.path.isfile(testFilename):
                outputDir = filename[:-6]
                if not os.path.exists(outputDir):
                    os.makedirs(outputDir)
                command = f"python -m spacy train {configFile} --code functions.py --output \"{outputDir}\" --paths.train \"{filename}\" --paths.dev \"{testFilename}\" --gpu-id 0 > \"{outputDir}/log.txt\""
                commands.append(command)
            else:
                print(f"No training data found for model ({filename})")
    
    return commands
        

if __name__== '__main__':
    if len(sys.argv) == 4 or len(sys.argv) == 5 or len(sys.argv) == 6:
        numFolds = int(sys.argv[3])
        startFold = 0
        if len(sys.argv) == 6:
            startFold = int(sys.argv[5])

        train_folders = sys.argv[1].split(',')
        test_folders = sys.argv[2].split(',')
        if len(train_folders) != len(test_folders):
            print("Missmatched number of folders for training and evaluation")
            exit(-1)

        
        commands = []
        for set_i in range(0, len(train_folders)):
            for i in range(startFold,numFolds):
                trainingFolder = train_folders[set_i] + "-" + str(i)
                testFolder = test_folders[set_i] + "-" + str(i)
                configFile = "config.cfg"
                if (len(sys.argv) >= 5):
                    configFile = sys.argv[4]
                commands_in_fold = PrepareCommands(trainingFolder, testFolder, configFile)
                commands.extend(commands_in_fold)
        
        # num_workers = 50
        from tqdm.contrib.concurrent import process_map  # or thread_map
        # #process_map(RunCommand, commands, max_workers = num_workers)
        # for command in commands:
        #     print(command)
        #     os.system(command)

        # Commands not using transformers: they only use one CPU, can use a job per core
        cpu_commands = [command for command in commands if '-trf' not in command]
        num_cpus = 60
        commands_on_cpu = []
        for cpu_command in cpu_commands:
            cpu_command = cpu_command.replace("--gpu-id 0", "")
            commands_on_cpu.append(cpu_command)
            print(cpu_command)
        print("--------------")
        print(f"Running {len(commands_on_cpu)} experiments on CPU")
        process_map(RunCommand, commands_on_cpu, max_workers = num_cpus)
        
        
        # Filter commands using transformers
        gpu_commands = [command for command in commands if '-trf' in command]
        print("--------------")
        print(f"Running {len(gpu_commands)} experiments on GPU")
        num_gpus = 4
        for command_group in chunks(gpu_commands, num_gpus):
            commands_with_gpu = []
            for i, command in enumerate(command_group):
                commands_with_gpu.append(command.replace("--gpu-id 0", f"--gpu-id {i}"))
                print(commands_with_gpu[i])
            process_map(RunCommand, commands_with_gpu, max_workers = num_gpus)
            print("--------------")

    else:
        if len(sys.argv) == 3:
            PrepareCommands(sys.argv[1], sys.argv[2])
        else:
            print("Not enough arguments. Usage: train-models <trainingFolders> <testFolders> [<numFolds>] [<configFile>] [<startFold>]")