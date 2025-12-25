from typing import List
from .types import Chunk
from .config import SKIP
from .lexicon import build_all_independent_trees

from .scanner import scan_longest_at
from .merge_ops import merge_num_classifier, merge_predicate
from .cleanner import clean_cls_tag, clean_sfp_chunks, clean_wordnum_tag, clean_postp_tag,clean_chunks
from ..preprocessing import preprocess_burmese_text
from ..utils.patterns import TAG_PATTERNS


import pandas as pd

LEXICON_TREES = build_all_independent_trees()

TRIE_MCONJ  = LEXICON_TREES.get("MCONJ")
TRIE_CONJ  = LEXICON_TREES.get("CONJ")
TRIE_SFP   = LEXICON_TREES.get("SFP")
TRIE_QW   = LEXICON_TREES.get("QW")
TRIE_VEP   = LEXICON_TREES.get("VEP")
TRIE_POST  = LEXICON_TREES.get("POSTP")
TRIE_UNIT  = LEXICON_TREES.get("CL")

TRIE_CLEP   = LEXICON_TREES.get("CLEP")  
TRIE_MONTH = LEXICON_TREES.get("MONTH")
TRIE_DAY = LEXICON_TREES.get("DAY")
TRIE_REGION   = LEXICON_TREES.get("REGION")
TRIE_REG   = LEXICON_TREES.get("REG")
TRIE_SWORD  = LEXICON_TREES.get("SWORD")
TRIE_TITLE   = LEXICON_TREES.get("TITLE")
TRIE_PRN   = LEXICON_TREES.get("PRN") 



PIPELINE = [

    (TRIE_REGION,  "REGION"),
    (TRIE_MONTH, "MONTH"),
    (TRIE_DAY, "DAY"),
    (TRIE_REG,  "REG"),
    (TRIE_SWORD, "SWORD"),
    (TRIE_TITLE,  "TITLE"),
    (TRIE_PRN,  "PRN"),

    (TRIE_MCONJ,  "MCONJ"),
    (TRIE_CONJ,  "CONJ"),
    (TRIE_VEP,   "VEP"),
    (TRIE_SFP,   "SFP"),
    (TRIE_QW,   "QW"),
    (TRIE_POST,  "POSTP"),
    (TRIE_UNIT,  "CL"),   
    (TRIE_CLEP,  "CLEP"),  
    
]

def _check_pre_defined_tag(token: str):
    for tag, patterns in TAG_PATTERNS.items():
        if any(p.match(token) for p in patterns):
            return tag
    return None


def _flatten_if_nested(syl_tokens):
    if syl_tokens and isinstance(syl_tokens[0], list):
        flat = []
        for grp in syl_tokens: flat.extend(grp)
        return flat
    return syl_tokens or []


def rule_segment(text: str, protect: bool, get_syllabus):
    # 1) get syllables
    if protect: 
        phrase_tokens, protected = preprocess_burmese_text(text)  
        
        tokens = []
        for phrase in phrase_tokens:
            if phrase in protected:
                tokens.append(protected[phrase])
            else:
                syllable_tokens = _flatten_if_nested(get_syllabus(phrase))
                syllable_tokens.append(' ')
                tokens.extend(syllable_tokens)
    else:
        tokens = _flatten_if_nested(get_syllabus(text))  
    
    # 2) single pass labeling (priority + longest-match)
    chunks: List[Chunk] = []
    i = 0; n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in SKIP:
            chunks.append(Chunk((i,i), t, "PUNCT")); i += 1; continue
        
        tag = _check_pre_defined_tag(t)
        
        if tag: 
            chunks.append(Chunk((i,i), t, tag)); i += 1; continue
        m = scan_longest_at(tokens, i, PIPELINE)
        if m:
            chunks.append(m); i = m.span[1] + 1
        else:
            chunks.append(Chunk((i,i), t, "RAW")); i += 1
    
    # 3) structural merges
    
    chunks = clean_wordnum_tag(chunks)
    
    chunks = merge_num_classifier(chunks)
   
    chunks = merge_predicate(chunks)

    # 4) clean punct after merging
    
    chunks = clean_sfp_chunks(chunks)
    
    chunks = clean_cls_tag(chunks)

    chunks = clean_postp_tag(chunks)
    chunks = clean_chunks(chunks)

    return chunks
