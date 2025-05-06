from datetime import datetime
from app import db

class QuizAttempt(db.Model):
    """Model for tracking user quiz attempts and scores"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuizAttempt {self.id}: {self.score}/{self.total_questions}>"

class QuizQuestion(db.Model):
    """Model for storing quiz questions for reuse"""
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(256), nullable=False)
    option_b = db.Column(db.String(256), nullable=False)
    option_c = db.Column(db.String(256), nullable=False)
    option_d = db.Column(db.String(256), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    difficulty = db.Column(db.String(20), default='medium')  # 'easy', 'medium', 'hard'
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuizQuestion {self.id}: {self.question_text[:30]}...>"

class Feedback(db.Model):
    """Model for storing user feedback about the quiz"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=True)
    rating = db.Column(db.Integer)  # 1-5 star rating
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    quiz_attempt = db.relationship('QuizAttempt', backref=db.backref('feedback', lazy=True))
    
    def __repr__(self):
        return f"<Feedback {self.id}: Rating {self.rating}>"