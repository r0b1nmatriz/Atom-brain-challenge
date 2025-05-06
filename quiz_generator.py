import os
import logging
import random

# We'll use fallback questions directly instead of trying to load transformers
def generate_quiz_questions(num_questions=10):
    """Generate quiz questions using fallback questions"""
    logging.info("Using fallback questions for the quiz")
    return get_fallback_questions(num_questions)

def get_fallback_questions(num=10):
    """Return fallback questions in case AI generation fails"""
    all_questions = [
        {
            'question': 'Which Indian city is known as the "City of Lakes"?',
            'options': ['Udaipur', 'Jaipur', 'Bhopal', 'Chandigarh'],
            'correct_answer': 'A'
        },
        {
            'question': 'In which year did India win its first Cricket World Cup?',
            'options': ['1975', '1983', '1987', '2011'],
            'correct_answer': 'B'
        },
        {
            'question': 'What is the chemical symbol for gold?',
            'options': ['Go', 'Ag', 'Au', 'Gl'],
            'correct_answer': 'C'
        },
        {
            'question': 'Which Indian received the first Nobel Prize in Physics?',
            'options': ['C.V. Raman', 'Hargobind Khorana', 'Amartya Sen', 'Rabindranath Tagore'],
            'correct_answer': 'A'
        },
        {
            'question': 'Which Indian state has the highest population?',
            'options': ['Maharashtra', 'Uttar Pradesh', 'Bihar', 'West Bengal'],
            'correct_answer': 'B'
        },
        {
            'question': 'Which river is known as "Ganga" in India?',
            'options': ['Brahmaputra', 'Yamuna', 'Ganges', 'Godavari'],
            'correct_answer': 'C'
        },
        {
            'question': 'Who was the first woman Prime Minister of India?',
            'options': ['Indira Gandhi', 'Sonia Gandhi', 'Sarojini Naidu', 'Pratibha Patil'],
            'correct_answer': 'A'
        },
        {
            'question': 'Which Indian film won an Oscar for Best Foreign Language Film?',
            'options': ['Lagaan', 'Slumdog Millionaire', 'Mother India', 'None of these'],
            'correct_answer': 'D'
        },
        {
            'question': 'Who composed the Indian national anthem "Jana Gana Mana"?',
            'options': ['Bankim Chandra Chattopadhyay', 'Rabindranath Tagore', 'Sarojini Naidu', 'Mahatma Gandhi'],
            'correct_answer': 'B'
        },
        {
            'question': 'Which Indian festival is known as the "Festival of Lights"?',
            'options': ['Holi', 'Diwali', 'Navratri', 'Durga Puja'],
            'correct_answer': 'B'
        },
        {
            'question': 'Which Indian scientist contributed to the Chandrayaan-1 mission?',
            'options': ['A.P.J. Abdul Kalam', 'Vikram Sarabhai', 'Mylswamy Annadurai', 'Satish Dhawan'],
            'correct_answer': 'C'
        },
        {
            'question': 'Who is known as the "Father of the Indian Constitution"?',
            'options': ['Mahatma Gandhi', 'Jawaharlal Nehru', 'B.R. Ambedkar', 'Sardar Vallabhbhai Patel'],
            'correct_answer': 'C'
        },
        {
            'question': 'Which was the first IPL team to win three championships?',
            'options': ['Mumbai Indians', 'Chennai Super Kings', 'Kolkata Knight Riders', 'Royal Challengers Bangalore'],
            'correct_answer': 'A'
        },
        {
            'question': 'In Indian mythology, who is the goddess of wealth?',
            'options': ['Saraswati', 'Lakshmi', 'Durga', 'Parvati'],
            'correct_answer': 'B'
        },
        {
            'question': 'Which ancient Indian university is considered one of the oldest in the world?',
            'options': ['Takshashila', 'Nalanda', 'Vikramshila', 'Kashi'],
            'correct_answer': 'B'
        }
    ]
    
    # Shuffle and return the requested number
    random.shuffle(all_questions)
    return all_questions[:num]
