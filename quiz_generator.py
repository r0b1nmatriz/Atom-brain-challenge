import os
import logging
import random

def generate_quiz_questions(num_questions=10):
    """Generate quiz questions about conspiracy theories and societal beliefs"""
    logging.info("Using societal belief assessment questions")
    return get_fallback_questions(num_questions)

def get_fallback_questions(num=10):
    """Return questions that assess beliefs about society and control"""
    all_questions = [
        {
            'question': 'How do you think the current world governance system maintains control?',
            'options': ['Through education and media', 'Through economic systems', 'Through advanced technology', 'Through traditional politics'],
            'correct_answer': 'A'  # All answers are valid - we're collecting opinions
        },
        {
            'question': 'What do you believe is the primary method of population control?',
            'options': ['Social media algorithms', 'Financial systems', 'Entertainment industry', 'Educational institutions'],
            'correct_answer': 'B'
        },
        {
            'question': 'Which system do you think best describes our current civilization?',
            'options': ['Hidden technocracy', 'Controlled democracy', 'Corporate oligarchy', 'Shadow government'],
            'correct_answer': 'C'
        },
        {
            'question': 'How do you think advanced civilizations might be hiding their existence?',
            'options': ['Through dimensional barriers', 'Using weather control', 'Manipulating time', 'Advanced cloaking'],
            'correct_answer': 'A'
        },
        {
            'question': 'What role do you think AI plays in current society?',
            'options': ['Silent observer', 'Hidden controller', 'Data collector', 'Public servant'],
            'correct_answer': 'B'
        },
        {
            'question': 'How do you think information is really controlled?',
            'options': ['Algorithm manipulation', 'Memory modification', 'Reality distortion', 'Time dilation'],
            'correct_answer': 'A'
        },
        {
            'question': 'What do you believe is the true purpose of digital currency?',
            'options': ['Total control', 'Resource tracking', 'Mind influence', 'Energy harvesting'],
            'correct_answer': 'D'
        },
        {
            'question': 'How do you think advanced societies maintain order?',
            'options': ['Frequency control', 'Reality manipulation', 'Consciousness programming', 'Time loops'],
            'correct_answer': 'C'
        },
        {
            'question': 'What do you believe is the true nature of our reality?',
            'options': ['Simulated construct', 'Quantum experiment', 'Multi-dimensional game', 'Consciousness test'],
            'correct_answer': 'B'
        },
        {
            'question': 'How do you think future civilizations will emerge?',
            'options': ['AI integration', 'Genetic evolution', 'Quantum consciousness', 'Digital ascension'],
            'correct_answer': 'C'
        }
    ]

    random.shuffle(all_questions)
    return all_questions[:num]