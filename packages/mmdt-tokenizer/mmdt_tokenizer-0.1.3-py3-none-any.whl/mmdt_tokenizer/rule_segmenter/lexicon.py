from .scanner import build_trie
import unicodedata 
import json
import os


def build_all_independent_trees(LEXICON_TREES={}):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "lexicons.json")
    with open(json_path, "r", encoding="utf-8") as f:
        full_lexicon = json.load(f)

    for tag, word_list in full_lexicon.items():

        tag_patterns = {}
        for word in word_list:

            if isinstance(word, list):
                key = tuple(unicodedata.normalize('NFC', part) for part in word)
            else:
                key = (unicodedata.normalize('NFC', word),)
            
            tag_patterns[key] = tag

        LEXICON_TREES[tag] = build_trie(tag_patterns)
    
    return LEXICON_TREES

  

