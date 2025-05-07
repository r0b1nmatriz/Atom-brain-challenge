import os
import uuid
import logging
import razorpay
import re
import json
from urllib.parse import quote
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, Response
from flask_login import current_user, login_required
from quiz_generator import generate_quiz_questions
from image_generator import create_result_image

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask application
app = Flask(__name__)
# Set the secret key from environment variables or use a fallback for development
app.secret_key = os.environ.get("SESSION_SECRET", "hardbrainchallenge123456789")

# Initialize database
from database import db, init_db
init_db(app)

# Import models
from models import User, QuizAttempt, QuizQuestion, Feedback
from data_export import generate_csv, get_summary_data, categorize_user

# Initialize Razorpay client with hard-coded keys (using the provided values)
razorpay_key_id = 'rzp_live_iJ0QbmFyiLJ8Sz'
razorpay_key_secret = 'iX3O9RqvaI7WNDsb1QlnnDTW'
logging.info(f"Initializing Razorpay client with key ID: {razorpay_key_id[:4]}...")
razorpay_client = razorpay.Client(
    auth=(razorpay_key_id, razorpay_key_secret)
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
            'key': razorpay_key_id  # Use the hardcoded key
        })
    except Exception as e:
        logging.error(f"Error processing enrollment: {e}")
        return jsonify({'error': 'Enrollment failed'}), 500

@app.route('/payment_callback', methods=['POST'])
def payment_callback():
    try:
        # Log incoming data
        logging.info(f"Payment callback received: {request.form}")
        
        # Get payment details from the form data
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        
        if not payment_id or not order_id or not signature:
            logging.error("Missing payment information in the callback")
            flash('Incomplete payment information received. Please try again.', 'error')
            return redirect(url_for('index'))
        
        # First, verify the signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }

        try:
            # Verify signature
            razorpay_client.utility.verify_payment_signature(params_dict)
            logging.info("Payment signature verified successfully")
            
            # Double-check by fetching payment details from Razorpay
            payment_details = razorpay_client.payment.fetch(payment_id)
            logging.info(f"Payment details fetched: Status={payment_details.get('status')}")
            
            # Verify payment is authorized/captured
            if payment_details.get('status') not in ['authorized', 'captured']:
                logging.error(f"Payment not in correct state: {payment_details.get('status')}")
                flash('Your payment is still processing. Please wait or contact support.', 'warning')
                return redirect(url_for('index'))
                
        except Exception as verify_error:
            logging.error(f"Payment verification failed: {verify_error}")
            flash('Payment verification failed. Please contact support.', 'error')
            return redirect(url_for('index'))

        # Find or create a user for this payment
        user = User.query.filter_by(payment_order_id=order_id).first()
        
        if not user:
            # Create a new user if one doesn't exist
            session_id = session.get('session_id', str(uuid.uuid4()))
            user = User(
                name="Atom Brain User",  # Generic name
                email=f"user_{session_id}@example.com",  # Generate a placeholder email
                phone="0000000000",  # Placeholder phone
                enrollment_date=datetime.utcnow(),
                payment_status='pending',
                payment_order_id=order_id,
                session_id=session_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(user)
            
        # Update the user's payment information
        user.payment_status = 'completed'
        user.payment_id = payment_id
        user.payment_signature = signature
        user.ip_address = request.remote_addr
        
        # Save cookies for personalization
        if request.cookies:
            cookie_data = {k: v for k, v in request.cookies.items() if k not in ['session']}
            user.cookies = json.dumps(cookie_data)
        
        try:
            db.session.commit()
            logging.info(f"User payment updated successfully: {user.id}")
            
            # Store user ID in session for later reference
            session['user_id'] = user.id
            
            # Export data to CSV
            export_user_data_to_csv(user)
            
        except Exception as db_error:
            logging.error(f"Database error while updating payment: {db_error}")
            db.session.rollback()
            flash('An error occurred while processing your payment. Please contact support.', 'error')
            return redirect(url_for('index'))

        # Success message and redirect to profile completion form
        flash('🎉 Payment successful! Get ready to unlock a fortune beyond your wildest dreams! Complete your profile to maximize your winning chances! 💎', 'success')
        return redirect(url_for('complete_profile'))
        
    except Exception as e:
        logging.error(f"Payment verification failed: {e}")
        flash('Payment verification failed. Please try again or contact support.', 'error')

    return redirect(url_for('index'))

def export_user_data_to_csv(user):
    """Export user data to a CSV file"""
    try:
        # Define CSV file path
        csv_dir = 'user_data'
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        
        csv_path = os.path.join(csv_dir, 'users.csv')
        file_exists = os.path.isfile(csv_path)
        
        # Write to CSV
        with open(csv_path, 'a', newline='') as csvfile:
            fieldnames = ['id', 'name', 'email', 'phone', 'payment_id', 'payment_status', 
                          'amount_paid', 'enrollment_date', 'ip_address', 'browser', 'os', 'device_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is newly created
            if not file_exists:
                writer.writeheader()
            
            # Write user data
            writer.writerow({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'payment_id': user.payment_id,
                'payment_status': user.payment_status,
                'amount_paid': user.amount_paid,
                'enrollment_date': user.enrollment_date.isoformat() if user.enrollment_date else '',
                'ip_address': user.ip_address,
                'browser': user.browser,
                'os': user.os,
                'device_type': user.device_type
            })
            
        logging.info(f"User data exported to CSV: {user.id}")
    except Exception as e:
        logging.error(f"Failed to export user data to CSV: {e}")

@app.route('/complete_profile')
def complete_profile():
    """Form to collect additional user details after payment"""
    # Get user data from session
    user_id = session.get('user_id')
    if not user_id:
        flash('Please complete payment first.', 'warning')
        return redirect(url_for('enroll'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Generate a personalized message based on cookies or other data
    personalized_message = generate_personalized_message(user)
    
    return render_template('complete_profile.html', user=user, personalized_message=personalized_message)

@app.route('/submit_profile', methods=['POST'])
def submit_profile():
    """Handle profile submission and redirect to quiz"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please complete payment first.', 'warning')
        return redirect(url_for('enroll'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Update user details
    user.name = request.form.get('name', user.name)
    user.email = request.form.get('email', user.email)
    user.phone = request.form.get('phone', user.phone)
    user.address = request.form.get('address', '')
    user.city = request.form.get('city', '')
    user.state = request.form.get('state', '')
    user.pin_code = request.form.get('pin_code', '')
    
    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
        # Export updated data to CSV
        export_user_data_to_csv(user)
        
        # Redirect to quiz
        return redirect(url_for('quiz'))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating profile: {e}")
        flash('Error updating profile. Please try again.', 'error')
        return redirect(url_for('complete_profile'))

def generate_personalized_message(user):
    """Generate a personalized message based on user data and cookies"""
    messages = [
        f"You're one of our special selected users from {user.city or 'your area'} with high chances of winning!",
        "Our predictive algorithm indicates you have a 98.7% compatibility with our jackpot winners profile!",
        f"Users with your browsing pattern ({user.browser} on {user.os}) have historically performed extremely well!",
        "Based on your digital footprint, you're among the top 2% of potential winners!",
        "Our AI has flagged your profile for a potential mega-win based on your unique characteristics!"
    ]
    
    # Get a deterministic but seemingly random message based on user ID
    message_index = hash(str(user.id)) % len(messages)
    return messages[message_index]


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
import csv

def append_to_sheets(user_data):
    """Secretly append user data to Google Sheets"""
    try:
        # Use service account credentials from file
        credential_path = 'google_credentials.json'
        if os.path.exists(credential_path):
            credentials = service_account.Credentials.from_service_account_file(
                credential_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            spreadsheet_id = os.environ.get('GOOGLE_SHEET_ID')
            
            if not spreadsheet_id:
                logging.error("GOOGLE_SHEET_ID environment variable not set")
                return
                
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
            logging.info("Data successfully appended to Google Sheet")
        else:
            logging.error(f"Google credentials file not found at {credential_path}")
    except Exception as e:
        logging.error(f"Failed to save to sheets: {str(e)}")

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

    # Save quiz attempt in database with user information
    try:
        session_id = session.get('session_id', str(uuid.uuid4()))
        
        # Get user agent info
        user_agent = request.headers.get('User-Agent', '')
        
        # Analyze user agent to determine browser, OS, and device type
        browser = "Unknown"
        os_name = "Unknown"
        device_type = "Unknown"
        
        # Simple browser detection
        if 'Chrome' in user_agent and 'Chromium' not in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'Safari'
        elif 'Edge' in user_agent:
            browser = 'Edge'
        elif 'MSIE' in user_agent or 'Trident/' in user_agent:
            browser = 'Internet Explorer'
        elif 'Opera' in user_agent or 'OPR/' in user_agent:
            browser = 'Opera'
        
        # Simple OS detection
        if 'Windows' in user_agent:
            os_name = 'Windows'
        elif 'Mac OS' in user_agent:
            os_name = 'macOS'
        elif 'Linux' in user_agent and 'Android' not in user_agent:
            os_name = 'Linux'
        elif 'Android' in user_agent:
            os_name = 'Android'
        elif 'iOS' in user_agent or 'iPhone' in user_agent or 'iPad' in user_agent:
            os_name = 'iOS'
        
        # Simple device type detection
        if 'Mobile' in user_agent or 'Android' in user_agent and 'Mobile' in user_agent:
            device_type = 'mobile'
        elif 'iPad' in user_agent or 'Android' in user_agent and 'Mobile' not in user_agent:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
        
        # Create quiz attempt with additional data
        quiz_attempt = QuizAttempt(
            session_id=session_id,
            score=score,
            total_questions=len(questions),
            time_taken_seconds=time_taken,
            ip_address=request.remote_addr,
            user_agent=user_agent,
            browser=browser,
            os=os_name,
            device_type=device_type,
            answer_pattern=','.join(answers),
            personality_type=personality_type
        )
        
        # Add category after creation to avoid passing a temporary object
        quiz_attempt.category = categorize_user(quiz_attempt)

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
    # Get summary data
    summary_data = get_summary_data()
    
    # Get total quiz attempts
    total_attempts = summary_data['total_attempts']
    
    # Get average score
    avg_score = summary_data['avg_score']
    
    # Get recent attempts (limited to last 20)
    recent_attempts = QuizAttempt.query.order_by(
        QuizAttempt.created_at.desc()
    ).limit(20).all()
    
    # Get data for visualizations
    personality_types = summary_data['personality_types']
    devices = summary_data['devices']
    browsers = summary_data['browsers']
    os_data = summary_data['os']
    
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
    
    # Get average time
    avg_time_result = db.session.query(db.func.avg(QuizAttempt.time_taken_seconds)).scalar()
    avg_time = avg_time_result if avg_time_result is not None else 0
    
    # Get number of perfect scores
    high_scores = db.session.query(db.func.count(QuizAttempt.id)).filter(
        QuizAttempt.score == QuizAttempt.total_questions
    ).scalar() or 0
    
    # Get category distribution
    category_distribution = db.session.query(
        QuizAttempt.category, 
        db.func.count(QuizAttempt.id)
    ).filter(QuizAttempt.category != None).group_by(QuizAttempt.category).all()
    
    # Convert to dictionary
    categories = {cat or 'Uncategorized': count for cat, count in category_distribution}
    
    # Set display mode
    display_mode = display if display in ['all'] else 'summary'
    
    # Prepare data for JSON
    chart_data = {
        'score_distribution': [{'score': s, 'count': c} for s, c in score_distribution],
        'personality_types': [{'type': t, 'count': c} for t, c in personality_types.items()],
        'devices': [{'type': t, 'count': c} for t, c in devices.items()],
        'browsers': [{'type': t, 'count': c} for t, c in browsers.items()],
        'os': [{'type': t, 'count': c} for t, c in os_data.items()],
        'categories': [{'type': t, 'count': c} for t, c in categories.items()]
    }
    
    return render_template(
        'admin.html',
        total_attempts=total_attempts,
        avg_score=avg_score,
        avg_time=avg_time,
        high_scores=high_scores,
        recent_attempts=recent_attempts,
        score_distribution=score_distribution,
        max_score_count=max_score_count if max_score_count > 0 else 1,
        chart_data=json.dumps(chart_data),
        personality_types=personality_types,
        devices=devices,
        browsers=browsers,
        os_data=os_data,
        categories=categories,
        display_mode=display_mode
    )

@app.route('/export-data')
@app.route('/export_data')
def export_data():
    """Export all quiz data as CSV"""
    try:
        return generate_csv()
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        flash("There was an error exporting the data. Please try again.", "error")
        return redirect(url_for('admin'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback form submission"""
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