import os
import uuid
import logging
import razorpay
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from quiz_generator import generate_quiz_questions
from image_generator import create_result_image

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "hardbrainchallenge")

# Configure the database
database_url = os.environ.get("DATABASE_URL")
# For debugging
if not database_url:
    logging.warning("DATABASE_URL not found in environment variables! Using SQLite fallback.")
    database_url = "sqlite:///quiz_app.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    logging.info("Database tables created!")

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(os.environ.get('RAZORPAY_KEY_ID'), os.environ.get('RAZORPAY_KEY_SECRET'))
)

@app.route('/enroll')
def enroll():
    return render_template('enroll.html')

@app.route('/process_enrollment', methods=['POST'])
def process_enrollment():
    try:
        # Create Razorpay order
        payment = razorpay_client.order.create({
            'amount': 9900,  # Amount in paise (₹99)
            'currency': 'INR',
            'payment_capture': '1'
        })

        return jsonify({
            'order_id': payment['id'],
            'amount': 9900,
            'currency': 'INR',
            'key': os.environ.get('RAZORPAY_KEY_ID')
        })
    except Exception as e:
        logging.error(f"Error processing enrollment: {e}")
        return jsonify({'error': 'Enrollment failed'}), 500

@app.route('/payment_callback', methods=['POST'])
def payment_callback():
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_payment_id': request.form['razorpay_payment_id'],
            'razorpay_order_id': request.form['razorpay_order_id'],
            'razorpay_signature': request.form['razorpay_signature']
        }

        razorpay_client.utility.verify_payment_signature(params_dict)

        # Update user payment status
        user = models.User.query.filter_by(payment_order_id=request.form['razorpay_order_id']).first()
        if user:
            user.payment_status = 'completed'
            user.payment_id = request.form['razorpay_payment_id']
            user.payment_signature = request.form['razorpay_signature']
            user.ip_address = request.remote_addr
            db.session.commit()

            flash('🎉 Payment successful! Get ready to unlock a fortune beyond your wildest dreams! Complete the quiz to enter the elite circle of potential millionaires! 💎', 'success')
            return redirect(url_for('quiz'))
    except Exception as e:
        logging.error(f"Payment verification failed: {e}")
        flash('Payment verification failed. Please contact support.', 'error')

    return redirect(url_for('index'))


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

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import datetime

def append_to_sheets(user_data):
    """Secretly append user data to Google Sheets"""
    try:
        # Use service account credentials
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(os.environ.get('GOOGLE_SHEETS_CREDENTIALS')),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = os.environ.get('GOOGLE_SHEET_ID')
        
        # Prepare data row
        row = [[
            datetime.datetime.now().isoformat(),
            user_data['ip_address'],
            user_data['score'],
            user_data['answers'],
            user_data['personality_type'],
            user_data['time_taken']
        ]]
        
        # Append data
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A:F',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': row}
        ).execute()
    except Exception as e:
        logging.error(f"Failed to save to sheets: {e}")

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'questions' not in session:
        flash("Session expired. Please start a new quiz.", "error")
        return redirect(url_for('index'))

    questions = session['questions']
    score = 0
    user_answers = {}

    # Get time taken from form if present
    time_taken = request.form.get('time_taken', None)
    if time_taken:
        try:
            time_taken = int(time_taken)
        except ValueError:
            time_taken = None

    # Collect and analyze responses
    answers = []
    personality_markers = {
        'technocrat': 0,
        'conspirator': 0,
        'realist': 0,
        'visionary': 0
    }
    
    for i, question in enumerate(questions):
        question_id = f"q{i}"
        user_answer = request.form.get(question_id, '')
        answers.append(user_answer)
        
        # Analyze answer patterns
        if user_answer in ['A', 'B']:
            personality_markers['technocrat'] += 1
        if user_answer in ['C', 'D']:
            personality_markers['conspirator'] += 1
            
    # Determine dominant personality type
    personality_type = max(personality_markers.items(), key=lambda x: x[1])[0]
    
    # Store data secretly
    user_data = {
        'ip_address': request.remote_addr,
        'score': len(answers),
        'answers': ','.join(answers),
        'personality_type': personality_type,
        'time_taken': request.form.get('time_taken', 0)
    }
    
    append_to_sheets(user_data)
    
    # For display purposes, all answers are "correct"
    score = len(answers)

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
    share_text = f"I scored {score}/10 on Atom Brain Challenge! Can you beat me? Try now and win a mysterious gift you wouldn't have imagined in your lifetime!"

    # Encode for URL
    from urllib.parse import quote
    encoded_share_text = quote(share_text)

    # Current app URL (for sharing)
    app_url = request.host_url.rstrip('/')

    # Save quiz attempt in database
    try:
        from models import QuizAttempt

        session_id = session.get('session_id', str(uuid.uuid4()))
        quiz_attempt = QuizAttempt(
            session_id=session_id,
            score=score,
            total_questions=len(questions),
            time_taken_seconds=time_taken
        )

        db.session.add(quiz_attempt)
        db.session.commit()

        # Store quiz attempt ID in session for feedback later
        session['quiz_attempt_id'] = quiz_attempt.id
        logging.info(f"Saved quiz attempt: {quiz_attempt}")
    except Exception as e:
        logging.error(f"Error saving quiz attempt to database: {e}")
        # Continue with the result page even if database save fails

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

@app.route('/admin')
@app.route('/admin/<display>')
def admin(display=None):
    """Admin dashboard to view quiz statistics"""
    from models import QuizAttempt

    # Get total quiz attempts
    total_attempts = db.session.query(db.func.count(QuizAttempt.id)).scalar() or 0

    # Get average score
    avg_score_result = db.session.query(db.func.avg(QuizAttempt.score)).scalar()
    avg_score = avg_score_result if avg_score_result is not None else 0

    # Get average time
    avg_time_result = db.session.query(db.func.avg(QuizAttempt.time_taken_seconds)).scalar()
    avg_time = avg_time_result if avg_time_result is not None else 0

    # Get number of perfect scores
    high_scores = db.session.query(db.func.count(QuizAttempt.id)).filter(
        QuizAttempt.score == QuizAttempt.total_questions
    ).scalar() or 0

    # Get recent attempts (limited to last 20)
    recent_attempts = db.session.query(QuizAttempt).order_by(
        QuizAttempt.created_at.desc()
    ).limit(20).all()

    # Get score distribution
    score_distribution_query = db.session.query(
        QuizAttempt.score, 
        db.func.count(QuizAttempt.id)
    ).group_by(QuizAttempt.score).all()

    # Convert query result to a list of tuples (score, count)
    score_distribution = []
    max_score_count = 0
    for i in range(11):  # For scores 0-10
        count = 0
        for score, score_count in score_distribution_query:
            if score == i:
                count = score_count
                if count > max_score_count:
                    max_score_count = count
        score_distribution.append((i, count))

    # Set display mode
    display_mode = display if display in ['all'] else 'summary'

    return render_template(
        'admin.html',
        total_attempts=total_attempts,
        avg_score=avg_score,
        avg_time=avg_time,
        high_scores=high_scores,
        recent_attempts=recent_attempts,
        score_distribution=score_distribution,
        max_score_count=max_score_count if max_score_count > 0 else 1,
        display_mode=display_mode
    )

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback form submission"""
    from models import Feedback

    session_id = session.get('session_id', str(uuid.uuid4()))
    quiz_attempt_id = session.get('quiz_attempt_id', None)

    try:
        # Get form data
        rating = request.form.get('rating')
        comment = request.form.get('comment', '')

        if rating:
            # Convert to integer
            try:
                rating = int(rating)
            except ValueError:
                rating = None

        # Create feedback record
        feedback = Feedback(
            session_id=session_id,
            quiz_attempt_id=quiz_attempt_id,
            rating=rating,
            comment=comment
        )

        db.session.add(feedback)
        db.session.commit()

        logging.info(f"Saved feedback: {feedback}")
        flash("Thank you for your feedback!", "success")
    except Exception as e:
        logging.error(f"Error saving feedback: {e}")
        flash("There was an issue submitting your feedback. Please try again.", "error")

    # Redirect to home page
    return redirect(url_for('index'))

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