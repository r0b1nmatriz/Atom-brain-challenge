import csv
import io
import os
from datetime import datetime
from flask import Response
from sqlalchemy import func
from models import QuizAttempt, User, Feedback
from database import db

def generate_csv():
    """
    Generate a CSV file containing all quiz attempt data
    Returns a Flask Response object with the CSV file
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        'ID', 'Date', 'IP Address', 'Score', 'Total Questions', 'Time Taken (sec)', 
        'Browser', 'OS', 'Device Type', 'Answer Pattern', 'Personality Type', 
        'Category', 'User Agent', 'Session ID'
    ])
    
    # Get all quiz attempts from database
    attempts = QuizAttempt.query.order_by(QuizAttempt.created_at.desc()).all()
    
    # Write data rows
    for attempt in attempts:
        writer.writerow([
            attempt.id,
            attempt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            attempt.ip_address,
            attempt.score,
            attempt.total_questions,
            attempt.time_taken_seconds,
            attempt.browser,
            attempt.os,
            attempt.device_type,
            attempt.answer_pattern,
            attempt.personality_type,
            attempt.category,
            attempt.user_agent,
            attempt.session_id
        ])
    
    # Create response
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=quiz_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )
    
    return response

def get_summary_data():
    """
    Get summary data for dashboard visualization
    """
    # Get total attempts
    total_attempts = QuizAttempt.query.count()
    
    # Get average score
    from sqlalchemy import func
    avg_score = QuizAttempt.query.with_entities(func.avg(QuizAttempt.score)).scalar() or 0
    
    # Get personality type distribution
    personality_types = QuizAttempt.query.with_entities(
        QuizAttempt.personality_type, 
        func.count(QuizAttempt.id)
    ).group_by(QuizAttempt.personality_type).all()
    
    # Get device type distribution
    devices = QuizAttempt.query.with_entities(
        QuizAttempt.device_type, 
        func.count(QuizAttempt.id)
    ).group_by(QuizAttempt.device_type).all()
    
    # Get browser distribution
    browsers = QuizAttempt.query.with_entities(
        QuizAttempt.browser, 
        func.count(QuizAttempt.id)
    ).group_by(QuizAttempt.browser).all()
    
    # Get OS distribution
    os_data = QuizAttempt.query.with_entities(
        QuizAttempt.os, 
        func.count(QuizAttempt.id)
    ).group_by(QuizAttempt.os).all()
    
    return {
        'total_attempts': total_attempts,
        'avg_score': round(float(avg_score), 2),
        'personality_types': {pt[0] or 'Unknown': pt[1] for pt in personality_types},
        'devices': {d[0] or 'Unknown': d[1] for d in devices},
        'browsers': {b[0] or 'Unknown': b[1] for b in browsers},
        'os': {o[0] or 'Unknown': o[1] for o in os_data}
    }

def categorize_user(quiz_attempt):
    """
    Auto-categorize users based on their quiz performance and answers
    Returns a category string
    """
    # Base categorization on personality type and score
    if not quiz_attempt.personality_type:
        return "Uncategorized"
        
    personality = quiz_attempt.personality_type.lower()
    score = quiz_attempt.score
    total = quiz_attempt.total_questions or 10
    score_percentage = (score / total) * 100
    
    if 'technocrat' in personality:
        if score_percentage >= 80:
            return "Tech Enthusiast"
        elif score_percentage >= 60:
            return "Tech Adopter"
        else:
            return "Tech Curious"
            
    elif 'conspirator' in personality:
        if score_percentage >= 80:
            return "Truth Seeker"
        elif score_percentage >= 60:
            return "Questioner"
        else:
            return "Skeptic"
            
    elif 'realist' in personality:
        if score_percentage >= 80:
            return "Pragmatist"
        elif score_percentage >= 60:
            return "Rationalist"
        else:
            return "Objectivist"
            
    elif 'visionary' in personality:
        if score_percentage >= 80:
            return "Innovator"
        elif score_percentage >= 60:
            return "Creator"
        else:
            return "Dreamer"
            
    else:
        # Fallback
        if score_percentage >= 80:
            return "High Performer"
        elif score_percentage >= 60:
            return "Average Performer"
        else:
            return "Developing Performer"