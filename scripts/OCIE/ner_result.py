
import xml.etree.ElementTree as ET

class NerResult:
    def __init__(self, text, entities):
        self.text = text
        self.entities = entities
    
    @staticmethod
    def load(ner_result_file):
        try:
            with open(ner_result_file, encoding="utf-8") as fp:
                xml_string = fp.read()
                tree = ET.fromstring(xml_string)

                text = tree.text

                entities = []
                for entity_node in tree.findall("Entity"):
                    
                    start = int(entity_node.get("Start"))
                    end = int(entity_node.get("End"))
                    name = entity_node.get("Name")
                    text = entity_node.find("Text").text
                    subentities = []
                    
                    for subentity_node in entity_node.findall("SubEntity"):
                        sub_start = int(subentity_node.get("Start"))
                        sub_end = int(subentity_node.get("End"))
                        sub_name = subentity_node.get("Name")
                        sub_text = subentity_node.text
                        subentities.append(SubEntity(sub_start, sub_end, sub_name, sub_text))
                    
                    entities.append(Entity(start, end, name, text, subentities))
                
                ner_result = NerResult(text, entities)
                return ner_result
        except Exception as e:
            print (f"Error loading NER result file: {ner_result_file}, Error: {e}")
            return None

class Entity:
    def __init__(self, start, end, name, text, subentities):
        self.start = start
        self.end = end
        self.name = name
        self.text = text
        self.subentities = subentities

    def overlaps(self, others : list, start: int) -> list:
        
        overlappingPredictions = [other for other in others if other.start >= start and
                    ((other.start >= self.start and other.start < self.end) or
                    (other.end >= self.start and other.end <= self.end) or
                    (other.start <= self.start and other.end >= self.end))]

        return overlappingPredictions
    

class SubEntity:
    def __init__(self, start, end, name, text):
        self.start = start
        self.end = end
        self.name = name
        self.text = text

    def overlaps(self, others : list, start : int = 0) -> list:
        
        overlappingPredictions = [other for other in others if other.start >= start and
                    ((other.start >= self.start and other.start < self.end) or
                    (other.end >= self.start and other.end <= self.end) or
                    (other.start <= self.start and other.end >= self.end))]

        return overlappingPredictions