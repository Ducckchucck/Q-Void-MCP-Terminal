import pandas as pd
import numpy as np

def get_dna_stats(query):
    stats = {
        "length": len(query),
        "num_quotes": query.count("'"),
        "num_semicolon": query.count(";"),
        "num_equals": query.count("="),
        "num_logical": sum(query.lower().count(k) for k in ["or", "and", "not"]),
        "num_keywords": sum(query.lower().count(k) for k in ["select", "insert", "union", "update", "sleep", "where"]),
        "num_numeric": sum(char.isdigit() for char in query),
    }
    return stats

def apply_dna_features(df, column="Query"):
    return pd.DataFrame([get_dna_stats(q) for q in df[column]])
