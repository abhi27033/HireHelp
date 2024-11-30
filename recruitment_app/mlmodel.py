import requests, fitz, os, json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import torch

def skill_list_similarity_sbert_base_v2(skills_1, skills_2):
    """Calculate similarity between two skill lists using SBERT (all-mpnet-base-v2)."""
    model = SentenceTransformer('all-mpnet-base-v2')
    sen = skills_1 + skills_2
    sen_embeddings = model.encode(sen)

    score = 0

    # Iterate through each skill in skills_1
    for i in range(len(skills_1)):
        if skills_1[i] in skills_2:
            score += 1  # Add 1 for exact match
        else:
            # Calculate cosine similarity between the current skill in skills_1 and all skills in skills_2
            similarities = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(skills_1):])[0]

            # Add the maximum similarity if it's above the threshold (0.4)
            max_similarity = max(similarities)
            if max_similarity >= 0.4:
                score += max_similarity

    # Normalize the score by the number of skills in the first list (skills_1)
    score = score / len(skills_1)

    return round(score, 3)


def semantic_similarity_sbert_paraphrase_minilm_l6_v2(skills_1, skills_2):
    """calculate similarity with SBERT paraphrase-MiniLM-L6-v2"""
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    sen = skills_1 + skills_2
    sen_embeddings = model.encode(sen)

    score = 0
    
    # Iterate through each skill in skills_1
    for i in range(len(skills_1)):
        if skills_1[i] in skills_2:
            score += 1  # Add 1 for exact match
        else:
            # Calculate cosine similarity between the current skill in skills_1 and all skills in skills_2
            similarities = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(skills_1):])[0]

            # Add the maximum similarity if it's above the threshold (0.4)
            max_similarity = max(similarities)
            if max_similarity >= 0.4:
                score += max_similarity

    # Normalize the score by the number of skills in the first list (skills_1)
    score = score / len(skills_1)

    return round(score, 3)

def semantic_similarity_all_MiniLM_L12_v1(skills_1, skills_2):
    """calculate similarity with all-MiniLM-L12-v1"""
    model = SentenceTransformer('all-MiniLM-L12-v1')
    sen = skills_1 + skills_2
    sen_embeddings = model.encode(sen)

    score = 0

    # Iterate through each skill in skills_1
    for i in range(len(skills_1)):
        if skills_1[i] in skills_2:
            score += 1  # Add 1 for exact match
        else:
            # Calculate cosine similarity between the current skill in skills_1 and all skills in skills_2
            similarities = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(skills_1):])[0]

            # Add the maximum similarity if it's above the threshold (0.4)
            max_similarity = max(similarities)
            if max_similarity >= 0.4:
                score += max_similarity

    # Normalize the score by the number of skills in the first list (skills_1)
    score = score / len(skills_1)

    return round(score, 3)

def semantic_similarity_bert_base_nli_mean_tokens(skills_1, skills_2):
    """"calculate similarity with bert_base_nli_mean_tokens"""
    model = SentenceTransformer('bert-base-nli-mean-tokens')
    sen = skills_1 + skills_2
    sen_embeddings = model.encode(sen)

    score = 0

    # Iterate through each skill in skills_1
    for i in range(len(skills_1)):
        if skills_1[i] in skills_2:
            score += 1  # Add 1 for exact match
        else:
            # Calculate cosine similarity between the current skill in skills_1 and all skills in skills_2
            similarities = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(skills_1):])[0]

            # Add the maximum similarity if it's above the threshold (0.4)
            max_similarity = max(similarities)
            if max_similarity >= 0.4:
                score += max_similarity

    # Normalize the score by the number of skills in the first list (skills_1)
    score = score / len(skills_1)

    return round(score, 3)

def semantic_similarity_all_roberta_large_v1(skills_1,skills_2):
    """calculate similarity with all-roberta-large-v1"""
    model = SentenceTransformer('all-roberta-large-v1')
    sen = skills_1 + skills_2
    sen_embeddings = model.encode(sen)

    score = 0

    # Iterate through each skill in skills_1
    for i in range(len(skills_1)):
        if skills_1[i] in skills_2:
            score += 1  # Add 1 for exact match
        else:
            # Calculate cosine similarity between the current skill in skills_1 and all skills in skills_2
            similarities = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(skills_1):])[0]

            # Add the maximum similarity if it's above the threshold (0.4)
            max_similarity = max(similarities)
            if max_similarity >= 0.4:
                score += max_similarity

    # Normalize the score by the number of skills in the first list (skills_1)
    score = score / len(skills_1)

    return round(score, 3)


# Similarity calculation function wrapper
def run_similarity(model_func, skills_1, skills_2):
    with torch.no_grad():  # Disable gradients to save memory
        result = model_func(skills_1, skills_2)
        # Convert result to a float in case it's returned as a tensor
        return float(result)

def mlscore(skills_1,skills_2):
    # Calculate similarity scores using different models
    similarity_sbert_base_v2 = run_similarity(skill_list_similarity_sbert_base_v2, skills_1, skills_2)
    similarity_paraphrase_minilm_l6_v2 = run_similarity(semantic_similarity_sbert_paraphrase_minilm_l6_v2, skills_1, skills_2)
    # similarity_all_minilm_l12_v1 = run_similarity(semantic_similarity_all_MiniLM_L12_v1, skills_1, skills_2)
    # similarity_bert_base_nli_mean_tokens = run_similarity(semantic_similarity_bert_base_nli_mean_tokens, skills_1, skills_2)
    similarity_all_roberta_large_v1 = run_similarity(semantic_similarity_all_roberta_large_v1, skills_1, skills_2)
    average = (similarity_sbert_base_v2+similarity_paraphrase_minilm_l6_v2+similarity_all_roberta_large_v1)/3.0
    return average