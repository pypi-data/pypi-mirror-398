from typing import List
from .types import Chunk
from .config import FUN_TAG, COMMON_KEYS_PRE, PERCENT_WORD, SPECIAL_NUM
from .config import NEG_SENT_SFP, QUE_SENT_SFP, NEG_PREFIX, SPECIAL_POSTP_SFP

def merge_num_classifier(chunks: List[Chunk]) -> List[Chunk]:
    out: List[Chunk] = []
    i = 0
    n = len(chunks)
    NUMBER_TAGS = ("NUM", "WORDNUM")
    CL_TAGS = ("CL", "CLEP")
    
    while i< n: 
        cur = chunks[i]

        if cur.text == PERCENT_WORD:
            out.append(Chunk(cur.span, cur.text, "INUMCL"))
            i += 1
            continue

        if cur.tag in NUMBER_TAGS:
            num_start = cur.span[0]
            j = i
            wordnum = 0
            # Merge NUM and punctuation inside the number
            num_punct = {",", "." , " " }
            while j < n and (chunks[j].tag in NUMBER_TAGS or chunks[j].text in num_punct): 
                j += 1
                if j >n: break
                if j < n and chunks[j].tag == "WORDNUM": wordnum += 1
            if chunks[j - 1].text ==  SPECIAL_NUM and wordnum == 1: j -= 1   

            num_text = "".join(c.text for c in chunks[i:j]).strip().replace(" ", "")
            num_end = chunks[j - 1].span[1]
            out.append(Chunk((num_start, num_end), num_text, "NUM"))

  
            k = j
            while k < n and (chunks[k].tag in CL_TAGS or chunks[k].text in COMMON_KEYS_PRE):
                chunks[k].tag = "NUMCL"
                out.append(chunks[k])
                k += 1
       
                

            i = k
            continue

        out.append(cur)
        i +=1
    return out

def merge_predicate(chunks: List["Chunk"]) -> List["Chunk"]:
    n = len(chunks)
    i = n - 1
    out = []
    

    while i >= 0:
        if(chunks[i].tag in FUN_TAG):
            out.append(chunks[i])
            i-=1
            continue
        if chunks[i].tag == "SFP":
            j = i
            neg_index = None
            que_index = None
            raw_index = None
            while j >= 0 and chunks[j].tag in ("SFP", "VEP", "RAW", "QW"): 
                if (chunks[j].text in SPECIAL_POSTP_SFP):break
                if chunks[j].text == NEG_PREFIX and neg_index is None: neg_index = j
                if chunks[j].tag == "QW" and que_index is None: que_index = j
                if chunks[j].tag == "RAW" and raw_index is None: raw_index = j #last raw
                j -= 1
            pred_length = i - j
            if pred_length > 1 :
                start = chunks[j + 1].span[0]
                end = chunks[i].span[1]
                text = "".join(ch.text for ch in chunks[j + 1 : i + 1])
                if neg_index is not None and chunks[i].text in NEG_SENT_SFP: 
                    text = "".join(ch.text for ch in chunks[neg_index : i + 1]) 
                    pred_start = chunks[neg_index].span[0]       
                    out.append(Chunk((pred_start, end), text, "PRED"))
                    text = "".join(ch.text for ch in chunks[j + 1 : neg_index])
                    raw_end = chunks[neg_index-1].span[1]
                    out.append(Chunk((start,raw_end), text, "RAW"))
                
                elif que_index is not None and chunks[i].text in QUE_SENT_SFP: 
                    text = "".join(ch.text for ch in chunks[que_index : i + 1])  
                    pred_start = chunks[que_index].span[0]            
                    out.append(Chunk((pred_start, end), text, "PRED"))
                    text = "".join(ch.text for ch in chunks[j + 1 : que_index])
                    que_end = chunks[que_index-1].span[1]
                    out.append(Chunk((start, que_end), text, "RAW"))
                    

                elif raw_index is not None:
                    text = "".join(ch.text for ch in chunks[raw_index+1: i + 1]) 
                    pred_start = chunks[raw_index+1].span[0]       
                    out.append(Chunk((pred_start, end), text, "PRED"))
                    text = "".join(ch.text for ch in chunks[j + 1 : raw_index+1])
                    raw_end = chunks[raw_index+1].span[1]
                    out.append(Chunk((start,raw_end), text, "RAW"))

                else:
                    pred_star = chunks[j + 1].span[0]       
                    out.append(Chunk((pred_star, end), text, "PRED"))

     
                i = j
                continue     

        out.append(chunks[i])
        i -= 1
    return out[::-1]