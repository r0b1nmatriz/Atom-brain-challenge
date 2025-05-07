from datetime import datetime
from database import db

class User(db.Model):
    """Model for storing user information for enrollment"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    pin_code = db.Column(db.String(10), nullable=True)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_id = db.Column(db.String(100), nullable=True)  # Razorpay payment ID
    payment_order_id = db.Column(db.String(100), nullable=True)  # Razorpay order ID
    payment_signature = db.Column(db.String(256), nullable=True)  # Razorpay signature
    amount_paid = db.Column(db.Float, default=99.00)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # mobile, tablet, desktop
    session_id = db.Column(db.String(128), nullable=True)  # Session ID for user tracking
    
    # Relationships
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)
    
    def __repr__(self):
        return f"<User {self.id}: {self.name}>"

class QuizAttempt(db.Model):
    """Model for tracking user quiz attempts and scores"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # mobile, tablet, desktop
    
    # Quiz response analysis
    answer_pattern = db.Column(db.String(20), nullable=True)  # e.g., 'ABCDABCD'
    personality_type = db.Column(db.String(50), nullable=True)  # based on answer patterns
    
    # Categorization
    category = db.Column(db.String(50), nullable=True)  # auto-generated category
    
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