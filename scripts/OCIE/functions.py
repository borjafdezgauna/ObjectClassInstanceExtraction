#-*- coding: utf-8 -*-

import re
from spacy.util import registry, compile_suffix_regex
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_suffix_regex, compile_infix_regex

@registry.callbacks("customize_tokenizer")
def make_customize_tokenizer():
    def customize_tokenizer(nlp):
        print('Overriding default Tokenizer')
        
        delimiters_re = r'[-—-−‐/:;,\.\(\)\?ºª“”"]';
        prefix_re = compile_prefix_regex(nlp.Defaults.prefixes + [delimiters_re]).search
        suffix_re = compile_suffix_regex(nlp.Defaults.suffixes + [delimiters_re]).search
        infix_re = re.compile(delimiters_re).finditer
          
        tokenizer = Tokenizer(nlp.vocab, prefix_search=prefix_re, suffix_search=suffix_re, infix_finditer=infix_re, rules=None)
        tokenizer.url_match = None
        nlp.tokenizer = tokenizer
    return customize_tokenizer