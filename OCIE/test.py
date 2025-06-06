import spacy
nlp= spacy.blank('xx')
nlp.tokenizer.explain('(8)')

nlp.tokenizer.rules = {}
nlp.tokenizer.explain('(8)')