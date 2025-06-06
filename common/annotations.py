import json
from xml.sax.saxutils import escape

class HierarchicalLabel:
    def __init__(self, label):
        self.label = label
        self.sublabels = []

    def addSubLabel(self, label):
        self.sublabels.append(label)

class HierarchicalAnnotation:
    def __init__(self, start, end, type, text):
        self.start = start
        self.end = end
        self.type = type
        self.text = text
        self.annotations = []

    def addAnnotation(self, annotation):
        self.annotations.append(annotation)

class HierarchicalAnnotatedText:
    def __init__(self, text):
        self.text = text
        self.annotations = []

    def addAnnotation(self, annotation):
        self.annotations.append(annotation)

class Annotation:
    def __init__(self, start_char, end_char, label, text):
        self.start_char = start_char
        self.end_char = end_char
        self.label = label
        self.text = text

class AnnotatedText:
    def __init__(self, fullText):
        self.fullText = fullText
        self.annotations = []

    def addAnnotation(self, annotation : Annotation):
        self.annotations.append(annotation)
    
    def addContext(self, left, right):
        self.left = left
        self.right = right

    def saveAsNerResult(self, output_file: str):
        # if len(self.annotations) == 0:
        #     print(f"No annotations to save in file: {output_file}")
        #     return
        
        with open(output_file, "w") as f:
            f.write("<NerResult>")
            f.write(escape(self.fullText))
            for i, annotation in enumerate(self.annotations):
                
                subannotations = [subannotation for j, subannotation in enumerate(self.annotations) 
                                if i != j and 
                                annotation.start_char <= subannotation.start_char and 
                                annotation.end_char >= subannotation.end_char]
                if len(subannotations) > 0:
                    #It is a high-level annotation: export it
                    ##<Entity Name="ProfessionalJob" Start="1779" End="2058">
                    f.write(f"<Entity Name=\"{annotation.label}\" Start=\"{annotation.start_char}\" End=\"{annotation.end_char}\">\n")
                    f.write(f"\t<Text>{escape(self.fullText[annotation.start_char:annotation.end_char])}</Text>")
                    for subannotation in subannotations:
                        #<SubEntity Name="Company" Start="1797" End="1823">Universidad del País Vasco</SubEntity>
                        f.write(f"<SubEntity Name=\"{subannotation.label}\" Start=\"{subannotation.start_char}\" " +
                                f"End=\"{subannotation.end_char}\">{escape(self.fullText[subannotation.start_char:subannotation.end_char])}</SubEntity>")
                        #print(f" -> {subannotation.label}: {self.fullText[subannotation.start_char:subannotation.end_char]}")
                    f.write("</Entity>\n")

            f.write("</NerResult>")

class LabelSet(dict):
    def __init__(self, labels):
        self.labels = labels

        label_dict = {}
        for label in labels:
            label_dict[label] = label
        dict.__init__(self, entities = label_dict, relations = {})
        


class Label(dict):
    def __init__(self, label):
        dict.__init__(self, verbose = label, short = label)
        self.name = label