import os
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from quiz_generator import generate_quiz_questions
from image_generator import create_result_image

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "hardbrainchallenge")

# In-memory storage for caching questions
question_cache = {}

@app.route('/')
def index():
    # Create a unique session ID if not already exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    session_id = session.get('session_id')
    
    # Check if questions already exist for this session
    if session_id in question_cache:
        questions = question_cache[session_id]
    else:
        # Generate new questions
        try:
            questions = generate_quiz_questions()
            # Cache the questions
            question_cache[session_id] = questions
        except Exception as e:
            logging.error(f"Error generating questions: {e}")
            flash("Sorry, we couldn't generate questions at this time. Please try again.", "error")
            return redirect(url_for('index'))
    
    # Store questions in session for validation later
    session['questions'] = questions
    return render_template('quiz.html', questions=questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'questions' not in session:
        flash("Session expired. Please start a new quiz.", "error")
        return redirect(url_for('index'))
    
    questions = session['questions']
    score = 0
    user_answers = {}
    
    # Calculate score
    for i, question in enumerate(questions):
        question_id = f"q{i}"
        user_answer = request.form.get(question_id, '')
        user_answers[question_id] = user_answer
        
        if user_answer == question['correct_answer']:
            score += 1
    
    # Generate result message based on score
    result_messages = {
        0: "Better luck next time!",
        1: "Keep trying!",
        2: "You're just getting started!",
        3: "Not bad, but you can do better!",
        4: "You're warming up!",
        5: "Halfway there!",
        6: "Good job!",
        7: "Very good!",
        8: "Excellent performance!",
        9: "Almost perfect!",
        10: "Perfect score! You're a Brain Champion!"
    }
    
    result_message = result_messages.get(score, "You completed the challenge!")
    
    # Create a shareable result image and get its path
    try:
        image_path = create_result_image(score, 10, result_message)
    except Exception as e:
        logging.error(f"Error creating result image: {e}")
        image_path = None
    
    # Store results in session
    session['result'] = {
        'score': score,
        'total': len(questions),
        'message': result_message,
        'image_path': image_path
    }
    
    # Prepare share text
    share_text = f"I scored {score}/10 on India's Hardest Brain Challenge! Can you beat me? Try now and win an iPhone 16 Pro 512GB!"
    
    # Encode for URL
    from urllib.parse import quote
    encoded_share_text = quote(share_text)
    
    # Current app URL (for sharing)
    app_url = request.host_url.rstrip('/')
    
    return render_template(
        'result.html', 
        score=score, 
        total=len(questions), 
        message=result_message,
        share_text=share_text,
        encoded_share_text=encoded_share_text,
        app_url=app_url,
        image_path=image_path
    )

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/clear_session')
def clear_session():
    session_id = session.get('session_id')
    if session_id and session_id in question_cache:
        del question_cache[session_id]
    session.clear()
    return redirect(url_for('index'))

# Cleanup old cache entries periodically
@app.before_request
def cleanup_cache():
    # Keep cache size manageable (limit to 1000 entries)
    if len(question_cache) > 1000:
        # Remove oldest 100 entries (simplified approach)
        keys_to_remove = list(question_cache.keys())[:100]
        for key in keys_to_remove:
            del question_cache[key]
