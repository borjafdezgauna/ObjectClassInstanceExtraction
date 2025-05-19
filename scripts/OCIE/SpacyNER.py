#!/usr/bin/python
# -*- coding: utf-8 -*-
import spacy
import os

class NerProcessor:
    def __init__(self, baseDir):
        self.TopLevelModel = self.LoadModel(baseDir + "/Annotations/model-best")
        self.LowLevelModels = {
            "AcademicCourse" : self.LoadModel(baseDir + "/AcademicCourse/model-best"),
            "AcademicDegree" : self.LoadModel(baseDir + "/AcademicDegree/model-best"),
            "AcademicGrant" : self.LoadModel(baseDir + "/AcademicGrant/model-best"),
            "AcademicPhd" : self.LoadModel(baseDir + "/AcademicPhd/model-best"),
            "Book" : self.LoadModel(baseDir + "/Book/model-best"),
            "BookReview" : self.LoadModel(baseDir + "/BookReview/model-best"),
            "BookChapter" : self.LoadModel(baseDir + "/BookChapter/model-best"),
            "EducInnovProject" : self.LoadModel(baseDir + "/EducInnovProject/model-best"),
            "EducQualityEvaluation" : self.LoadModel(baseDir + "/EducQualityEvaluation/model-best"),
            "EducTraining" : self.LoadModel(baseDir + "/EducTraining/model-best"),
            "IndexedJournalArticle" : self.LoadModel(baseDir + "/IndexedJournalArticle/model-best"),
            "LanguageCertificate" : self.LoadModel(baseDir + "/LanguageCertificate/model-best"),
            "Patent" : self.LoadModel(baseDir + "/Patent/model-best"),
            "PersonalData" : self.LoadModel(baseDir + "/PersonalData/model-best"),
            "Phd" : self.LoadModel(baseDir + "/Phd/model-best"),
            "ProceedingsArticle" : self.LoadModel(baseDir + "/ProceedingsArticle/model-best"),
            "ProfessionalJob" : self.LoadModel(baseDir + "/ProfessionalJob/model-best"),
            "ResearchProject" : self.LoadModel(baseDir + "/ResearchProject/model-best"),
            "Stay" : self.LoadModel(baseDir + "/Stay/model-best"),
            "StudentProject" : self.LoadModel(baseDir + "/StudentProject/model-best"),
            "Subject" : self.LoadModel(baseDir + "/Subject/model-best"),
            "MasterProject" : self.LoadModel(baseDir + "/MasterProject/model-best"),
            "Questionnaire" : self.LoadModel(baseDir + "/Questionnaire/model-best"),
        }
        return
    
    def LoadModel(self, path_to_model):
        print("Loading model: " + path_to_model)
        if os.path.exists(path_to_model):
            nlp = spacy.load(path_to_model)
            print("OK")
        else:
            nlp = None
            print("Failed to load model")
        return nlp
    
    def TopLevelNer(self, text):
        if self.TopLevelModel != None:
            return self.TopLevelModel(text).ents
        else:
            return []
        
    def LowLevelNer(self, item_type, text):
        if (item_type in self.LowLevelModels.keys()):
            return self.LowLevelModels[item_type](text).ents
        else:
            return []


