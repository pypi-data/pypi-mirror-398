import pandas as pd
from typing import List, Union
from dataclasses import asdict

def save_tokens_to_csv(tokens: Union[List[str], List[List[str]]], save_csv: str, conll_style: bool = True):
    """Save tokenized text to CSV (CoNLL-style or sentence-per-row)."""
    if not tokens:
        sublists = []
    elif isinstance(tokens[0], list):
        sublists = tokens
    elif isinstance(tokens, list):
        sublists = [[t] for t in tokens]
    else:
        sublists = [[str(tokens)]]


    if conll_style:
        rows = []
        num_sublists = len(sublists)
        for token_index, sublist in enumerate(sublists):
            string_sublist = [str(token).strip() for token in sublist]
            for token in string_sublist:
                rows.append({"sentence_id": token_index,"token": token})
            if token_index < num_sublists - 1:
                rows.append({"sentence_id": token_index,"token": ""})
        pd.DataFrame(rows).to_csv(save_csv, index=False, encoding="utf-8-sig")
    else:
        
        df_rows = pd.DataFrame(sublists)
        df_rows.columns = [f"Token_{i+1}" for i in range(df_rows.shape[1])]
        df_rows.insert(0, "sentence_id", range(len(df_rows)))
        df_rows.to_csv(save_csv, index=False, encoding="utf-8-sig")



def save_tags_to_csv(chunks, save_csv_filename):
    rows = []

    if not chunks:
        pd.DataFrame().to_csv(save_csv_filename, index=False, encoding="utf-8-sig")
        return

    # Case 1: chunks is List[List[Chunk]] → sentence-aware
    if isinstance(chunks[0], list):
        for sentence_id, sentence in enumerate(chunks):
            for ch in sentence:
                if ch.tag == "PUNCT":
                    continue
                row = asdict(ch)
                row["sentence_id"] = sentence_id
                rows.append(row)

    # Case 2: chunks is List[Chunk] → single sentence
    else:
        for ch in chunks:
            if ch.tag == "PUNCT":
                continue
            row = asdict(ch)
            row["sentence_id"] = 0
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(save_csv_filename, index=False, encoding="utf-8-sig")
