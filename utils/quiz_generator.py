import random
import re

# Initialize QA pipeline for quiz generation
_qa_gen_pipeline = None

def get_qa_gen_pipeline():
    """
    Load question generation pipeline on demand.
    """
    global _qa_gen_pipeline
    if _qa_gen_pipeline is None:
        # Simplified version that doesn't require transformers
        _qa_gen_pipeline = None
    return _qa_gen_pipeline

def generate_flashcards(text, num_cards=5):
    """
    Generate flashcards from text.
    
    Args:
        text (str): Source text for flashcards
        num_cards (int): Number of flashcards to generate
        
    Returns:
        list: List of dictionaries with questions and answers
    """
    # Split text into sentences
    sentences = text.split('. ')
    sentences = [s + '.' for s in sentences if s]
    
    # Group sentences into paragraphs (3-5 sentences each)
    paragraphs = []
    current_para = []
    
    for sentence in sentences:
        current_para.append(sentence)
        if len(current_para) >= random.randint(3, 5):
            paragraphs.append(" ".join(current_para))
            current_para = []
            
    if current_para:
        paragraphs.append(" ".join(current_para))
        
    # If we don't have enough paragraphs, repeat some
    while len(paragraphs) < num_cards:
        paragraphs.append(random.choice(paragraphs))
        
    # Shuffle and select paragraphs
    random.shuffle(paragraphs)
    selected_paragraphs = paragraphs[:num_cards]
    
    # Generate questions for each paragraph
    flashcards = []
    
    for i, paragraph in enumerate(selected_paragraphs):
        # Simple question generation based on the paragraph
        words = paragraph.split()
        
        if len(words) < 5:
            question = f"What is described in this text: '{paragraph[:20]}...'?"
        else:
            # Extract key terms from paragraph
            key_terms = []
            for word in words:
                if len(word) > 5 and word.lower() not in ['about', 'these', 'those', 'their', 'there']:
                    key_terms.append(word)
            
            if key_terms:
                key_term = random.choice(key_terms)
                question_types = [
                    f"What can you tell me about {key_term}?",
                    f"How does {key_term} relate to this topic?",
                    f"Explain the significance of {key_term}.",
                    f"What is meant by {key_term} in this context?",
                    f"Why is {key_term} important?"
                ]
                question = random.choice(question_types)
            else:
                question = f"What is the main idea of paragraph {i+1}?"
            
        # Create flashcard
        flashcard = {
            "question": question,
            "answer": paragraph
        }
        
        flashcards.append(flashcard)
        
    return flashcards

def generate_quiz(text, num_questions=5):
    """
    Generate a multiple-choice quiz from text.
    
    Args:
        text (str): Source text for quiz
        num_questions (int): Number of questions to generate
        
    Returns:
        list: List of dictionaries with questions, options and correct answers
    """
    # Generate flashcards first
    flashcards = generate_flashcards(text, num_questions)
    
    # Extract key information for distractors
    sentences = text.split('. ')
    sentences = [s + '.' for s in sentences if s]
    key_phrases = []
    
    for sentence in sentences:
        # Use longer sentences as potential distractors
        words = sentence.split()
        if len(words) > 5:  # Only use longer sentences
            key_phrases.append(sentence)
            
    # Generate the quiz
    quiz = []
    
    for card in flashcards:
        # Extract potential answer from the flashcard
        answer_sentences = card["answer"].split('. ')
        answer_sentences = [s + '.' for s in answer_sentences if s]
        correct_answer = random.choice(answer_sentences) if answer_sentences else card["answer"]
        
        # Generate distractors (wrong options)
        distractors = []
        potential_distractors = [phrase for phrase in key_phrases if phrase != correct_answer]
        
        # Get 3 distractors
        if len(potential_distractors) >= 3:
            distractors = random.sample(potential_distractors, 3)
        else:
            # If not enough distractors, generate some
            while len(distractors) < 3:
                distractor = f"This is not the correct answer related to {card['question'].replace('?', '')}"
                distractors.append(distractor)
                
        # Create options list with correct answer
        options = distractors + [correct_answer]
        random.shuffle(options)
        
        # Create question dict
        question = {
            "question": card["question"],
            "options": options,
            "correct_answer": correct_answer
        }
        
        quiz.append(question)
        
    return quiz
