#!/usr/bin/python
# -*- coding: utf-8 -*-

from html import entities
from xml.sax.saxutils import escape
import SpacyNER

class Processor:
    def __init__(self, modelsFolder = None):
        self.NerProcessor = SpacyNER.NerProcessor(modelsFolder)
        return
    def ProcessText(self, text):
        topLevelEntities = self.NerProcessor.TopLevelNer(text)
        output = ""
        for topLevelEntity in topLevelEntities:
            output += "<Entity Name=\"" + escape(topLevelEntity.label_) + "\" Start=\"" + str(topLevelEntity.start_char) + "\" End=\"" + str(topLevelEntity.end_char) + "\">\n"
            output += "  <Text>" + escape(topLevelEntity.text) + "</Text>\n"
            lowLevelEntities = self.NerProcessor.LowLevelNer(topLevelEntity.label_,topLevelEntity.text)
            for lowLevelEntity in lowLevelEntities:
                output += "  <SubEntity Name=\"" + escape(lowLevelEntity.label_) + "\" Start=\"" + str(topLevelEntity.start_char + lowLevelEntity.start_char) + "\" End=\"" + str(topLevelEntity.start_char + lowLevelEntity.end_char) + "\">" + escape(lowLevelEntity.text) + "</SubEntity>\n"
            output += "</Entity>\n"
        result = "<NerResult>\n" + output + "</NerResult>"
        return result
