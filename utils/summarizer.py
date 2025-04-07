import os
import random
from pathlib import Path

# Create data directory for local storage
data_dir = os.path.join("data")
Path(data_dir).mkdir(exist_ok=True)

# Global models - load on demand to save memory
_summarizer_model = None
_embedding_model = None
_qa_pipeline = None

def get_summarizer_model():
    """
    Simplified summarization model.
    """
    global _summarizer_model
    if _summarizer_model is None:
        # In this simplified version, we'll use a dummy model
        _summarizer_model = (None, None)
    return _summarizer_model

def get_embedding_model():
    """
    Simplified embedding model.
    """
    global _embedding_model
    if _embedding_model is None:
        # In this simplified version, we'll use a dummy model
        _embedding_model = None
    return _embedding_model

def get_qa_pipeline():
    """
    Simplified QA pipeline.
    """
    global _qa_pipeline
    if _qa_pipeline is None:
        # In this simplified version, we'll use a dummy pipeline
        _qa_pipeline = None
    return _qa_pipeline

def summarize_text(text, max_length=512, min_length=100):
    """
    Simplified function to extract key sentences as a summary.
    
    Args:
        text (str): Text to summarize
        max_length (int): Maximum summary length
        min_length (int): Minimum summary length
        
    Returns:
        str: Summarized text
    """
    # Check if text is too short to summarize
    if len(text.split()) < 100:
        return text
        
    # Extract sentences with simple split
    sentences = text.split('. ')
    sentences = [s + '.' for s in sentences if s]
    
    # Very simple extractive summarization: take first few sentences
    if len(sentences) <= 3:
        return text
    
    # Take the first sentence, a middle sentence, and the last sentence
    summary_sentences = [sentences[0]]
    
    # Add a sentence from the middle
    middle_idx = len(sentences) // 2
    summary_sentences.append(sentences[middle_idx])
    
    # Add the last sentence if it's different enough
    if len(sentences) > 3 and sentences[-1] not in summary_sentences:
        summary_sentences.append(sentences[-1])
    
    # Join the sentences
    summary = ' '.join(summary_sentences)
    
    # If summary is too short, add more sentences
    if len(summary.split()) < min_length and len(sentences) > 3:
        # Add another sentence from the first half
        quarter_idx = len(sentences) // 4
        if sentences[quarter_idx] not in summary_sentences:
            summary_sentences.insert(1, sentences[quarter_idx])
            summary = ' '.join(summary_sentences)
    
    # If summary is too long, keep only the beginning and end
    if len(summary.split()) > max_length:
        summary = sentences[0] + ' ' + sentences[-1]
    
    return summary

def generate_embeddings(text):
    """
    Generate embeddings for the given text.
    
    Args:
        text (str): Text to encode
        
    Returns:
        numpy.ndarray: Text embedding vector
    """
    # Simple fallback implementation
    import hashlib
    # Create a simple numeric representation
    hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (10 ** 8)
    import numpy as np
    # Return a small random vector based on the hash
    np.random.seed(hash_val)
    return np.random.randn(64).astype(np.float32)

def answer_question(db, question):
    """
    Answer a question using the stored knowledge base.
    
    Args:
        db (VectorDB): Vector database instance
        question (str): Question to answer
        
    Returns:
        dict: Dictionary with answer, context, source, and topic
    """
    # Search for relevant content in the database
    search_results = db.search(question, top_k=3)
    
    if not search_results:
        return {
            "answer": "I don't have enough information to answer this question.",
            "context": "",
            "source": "",
            "topic": ""
        }
    
    # Combine the most relevant contexts
    contexts = [result["content"] for result in search_results]
    full_context = " ".join(contexts)
    
    # If context is too long, use only the most relevant one
    if len(full_context.split()) > 500:
        full_context = search_results[0]["content"]
    
    # Simple extractive QA approach
    sentences = full_context.split('. ')
    sentences = [s + '.' for s in sentences if s]
    
    # Find sentences that might contain the answer
    relevant_sentences = []
    for sentence in sentences:
        # Look for keyword overlap between question and sentence
        question_words = set(question.lower().split())
        sentence_words = set(sentence.lower().split())
        overlap = question_words.intersection(sentence_words)
        
        if len(overlap) > 1:  # If there are at least 2 overlapping words
            relevant_sentences.append(sentence)
    
    if relevant_sentences:
        return {
            "answer": relevant_sentences[0],
            "context": full_context,
            "source": search_results[0]["source"],
            "topic": search_results[0]["topic"]
        }
    else:
        # If no relevant sentence found, return the first sentence
        return {
            "answer": sentences[0] if sentences else "No answer found.",
            "context": full_context,
            "source": search_results[0]["source"],
            "topic": search_results[0]["topic"]
        }
