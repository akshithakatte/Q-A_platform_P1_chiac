import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError, Regexp
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_socketio import SocketIO

# Import AI features
from ai_features import AIRecommendationEngine, SmartSearchEngine, ContentAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qa_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['WTF_CSRF_ENABLED'] = True

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register API blueprints (if available)
try:
    from rest_api import register_api_blueprints
    register_api_blueprints(app)
except ImportError:
    pass  # API not available, continue with web app only

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to <br> tags"""
    if text is None:
        return ''
    return re.sub(r'\r?\n', '<br>', text)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Reputation system
    reputation = db.Column(db.Integer, default=1)
    badge_level = db.Column(db.String(20), default='Beginner')
    profile_views = db.Column(db.Integer, default=0)
    
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)
    badges = db.relationship('UserBadge', backref='user', lazy=True)
    
    def calculate_reputation(self):
        """Calculate user reputation based on activity"""
        score = 1  # Base reputation
        
        # Points for questions
        score += len(self.questions) * 5
        
        # Points for answers
        score += len(self.answers) * 10
        
        # Points for accepted answers
        accepted_answers = len([a for a in self.answers if a.is_accepted])
        score += accepted_answers * 15
        
        # Points for votes received
        question_votes = sum(v.value for q in self.questions for v in q.votes if v.value > 0)
        answer_votes = sum(v.value for a in self.answers for v in a.votes if v.value > 0)
        score += (question_votes + answer_votes) * 2
        
        return max(score, 1)
    
    def update_badge_level(self):
        """Update user badge based on reputation"""
        rep = self.reputation
        if rep >= 1000:
            self.badge_level = 'Expert'
        elif rep >= 500:
            self.badge_level = 'Advanced'
        elif rep >= 100:
            self.badge_level = 'Intermediate'
        elif rep >= 50:
            self.badge_level = 'Apprentice'
        else:
            self.badge_level = 'Beginner'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='question', lazy=True)
    tags = db.relationship('Tag', secondary='question_tags', backref='questions')

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    
    votes = db.relationship('Vote', backref='answer', lazy=True)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)  # +1 or -1
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=True)

question_tags = db.Table('question_tags',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Badge system models
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='🏆')
    requirement_type = db.Column(db.String(20), nullable=False)  # questions, answers, votes, reputation
    requirement_value = db.Column(db.Integer, nullable=False)
    
    user_badges = db.relationship('UserBadge', backref='badge', lazy=True)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='info')  # info, success, warning, achievement
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

# Custom validators for password strength
def validate_password_strength(form, field):
    """Custom validator to ensure password meets security requirements"""
    password = field.data
    
    # Check for uppercase letters
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter (A-Z)')
    
    # Check for lowercase letters
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter (a-z)')
    
    # Check for numbers
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number (0-9)')
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
        raise ValidationError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}:"\\|,.<>/?))')
    
    # Check for common patterns
    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein']:
        raise ValidationError('Password cannot be a common password')
    
    # Check if password is too similar to username
    if hasattr(form, 'username') and form.username.data:
        username = form.username.data.lower()
        password_lower = password.lower()
        if username in password_lower or password_lower in username:
            raise ValidationError('Password is too similar to username')

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, max=128, message='Password must be between 8 and 128 characters'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Post Question')

class AnswerForm(FlaskForm):
    content = TextAreaField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Post Answer')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize AI engines (will be created when needed)
ai_engine = None
smart_search = None
content_analyzer = None

def get_ai_engines():
    """Lazy initialization of AI engines"""
    global ai_engine, smart_search, content_analyzer
    if ai_engine is None:
        ai_engine = AIRecommendationEngine()
        smart_search = SmartSearchEngine()
        content_analyzer = ContentAnalyzer()
    return ai_engine, smart_search, content_analyzer

# Routes
@app.route('/')
def index():
    search_form = SearchForm()
    
    # Get AI engines
    ai_engine, smart_search, content_analyzer = get_ai_engines()
    
    # Get personalized recommendations for logged-in users
    recommended_questions = []
    trending_topics = []
    
    if current_user.is_authenticated:
        recommended_questions = ai_engine.recommend_questions_for_user(current_user.id, limit=5)
    
    # Get trending topics
    trending_topics = smart_search.get_trending_topics(days=7, limit=5)
    
    # Get all questions
    questions = Question.query.order_by(Question.created_at.desc()).all()
    
    return render_template('index.html', 
                         questions=questions, 
                         search_form=search_form,
                         recommended_questions=recommended_questions,
                         trending_topics=trending_topics)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Debug information (remove in production)
        print(f"Login attempt for username: {form.username.data}")
        print(f"User found: {user is not None}")
        
        if user:
            print(f"Password check result: {check_password_hash(user.password_hash, form.password.data)}")
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    form = QuestionForm()
    if form.validate_on_submit():
        # Create question
        question = Question(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id
        )
        
        # Process tags
        tag_names = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            question.tags.append(tag)
        
        db.session.add(question)
        db.session.commit()
        flash('Question posted successfully!', 'success')
        return redirect(url_for('question_detail', id=question.id))
    
    return render_template('ask_question.html', form=form)

@app.route('/question/<int:id>')
def question_detail(id):
    question = Question.query.get_or_404(id)
    form = AnswerForm()
    
    # Increment profile views
    if question.author:
        question.author.profile_views += 1
        db.session.commit()
    
    # Calculate vote counts
    question_votes = sum(vote.value for vote in question.votes)
    
    # Calculate answer votes and sort
    answers_with_votes = []
    for answer in question.answers:
        answer_votes = sum(vote.value for vote in answer.votes)
        answers_with_votes.append((answer, answer_votes))
    
    # Sort answers: accepted first, then by vote count
    answers_with_votes.sort(key=lambda x: (not x[0].is_accepted, -x[1]))
    
    # Get AI engines and AI-powered features
    ai_engine, smart_search, content_analyzer = get_ai_engines()
    
    # Get AI-powered similar questions
    similar_questions = ai_engine.get_similar_questions(id, limit=3)
    
    # Analyze question quality
    quality_score = content_analyzer.analyze_question_quality(question)
    
    return render_template('question_detail.html', 
                         question=question, 
                         form=form, 
                         question_votes=question_votes,
                         answers_with_votes=answers_with_votes,
                         similar_questions=similar_questions,
                         quality_score=quality_score)

@app.route('/answer/<int:question_id>', methods=['POST'])
@login_required
def post_answer(question_id):
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        answer = Answer(
            content=form.content.data,
            user_id=current_user.id,
            question_id=question_id
        )
        db.session.add(answer)
        db.session.commit()
        flash('Answer posted successfully!', 'success')
    
    return redirect(url_for('question_detail', id=question_id))

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    data = request.get_json()
    item_type = data.get('item_type')  # 'question' or 'answer'
    item_id = data.get('item_id')
    value = data.get('value')  # 1 or -1
    
    if not all([item_type, item_id, value is not None]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    if item_type == 'question':
        existing_vote = Vote.query.filter_by(
            user_id=current_user.id,
            question_id=item_id,
            answer_id=None
        ).first()
        
        if existing_vote:
            existing_vote.value = value
        else:
            vote = Vote(
                value=value,
                user_id=current_user.id,
                question_id=item_id
            )
            db.session.add(vote)
    
    elif item_type == 'answer':
        existing_vote = Vote.query.filter_by(
            user_id=current_user.id,
            answer_id=item_id,
            question_id=None
        ).first()
        
        if existing_vote:
            existing_vote.value = value
        else:
            vote = Vote(
                value=value,
                user_id=current_user.id,
                answer_id=item_id
            )
            db.session.add(vote)
    
    db.session.commit()
    
    # Return new vote count
    if item_type == 'question':
        question = Question.query.get(item_id)
        vote_count = sum(vote.value for vote in question.votes)
    else:
        answer = Answer.query.get(item_id)
        vote_count = sum(vote.value for vote in answer.votes)
    
    return jsonify({'success': True, 'vote_count': vote_count})

@app.route('/accept_answer/<int:answer_id>', methods=['POST'])
@login_required
def accept_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    question = answer.question
    
    if question.user_id != current_user.id:
        flash('Only the question author can accept answers', 'danger')
        return redirect(url_for('question_detail', id=question.id))
    
    # Unaccept all other answers
    for ans in question.answers:
        ans.is_accepted = False
    
    # Accept this answer
    answer.is_accepted = True
    db.session.commit()
    
    flash('Answer accepted!', 'success')
    return redirect(url_for('question_detail', id=question.id))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    questions = []
    search_time = 0
    
    if form.validate_on_submit() or request.args.get('q'):
        import time
        start_time = time.time()
        
        query = request.args.get('q') or form.query.data
        
        # Get AI engines and use smart search
        ai_engine, smart_search, content_analyzer = get_ai_engines()
        
        if current_user.is_authenticated:
            questions = smart_search.search_questions(query, current_user.id, limit=20)
        else:
            questions = smart_search.search_questions(query, limit=20)
        
        search_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
        
        # Sort by creation date
        questions.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('search_results.html', questions=questions, form=form, query=request.args.get('q', ''), search_time=search_time)

@app.route('/dashboard')
@login_required
def dashboard():
    """Enhanced user dashboard with analytics"""
    user = current_user
    
    # Update user reputation and badge
    user.reputation = user.calculate_reputation()
    user.update_badge_level()
    db.session.commit()
    
    # User statistics
    stats = {
        'questions_asked': len(user.questions),
        'answers_given': len(user.answers),
        'accepted_answers': len([a for a in user.answers if a.is_accepted]),
        'reputation': user.reputation,
        'badge_level': user.badge_level,
        'profile_views': user.profile_views
    }
    
    # Recent activity
    recent_questions = Question.query.filter_by(user_id=user.id).order_by(Question.created_at.desc()).limit(5).all()
    recent_answers = Answer.query.filter_by(user_id=user.id).order_by(Answer.created_at.desc()).limit(5).all()
    
    # Badges
    user_badges = UserBadge.query.filter_by(user_id=user.id).order_by(UserBadge.earned_at.desc()).all()
    
    # Get AI engines and recommended questions
    ai_engine, smart_search, content_analyzer = get_ai_engines()
    recommended = ai_engine.recommend_questions_for_user(user.id, limit=10)
    
    return render_template('dashboard.html', 
                         user=user, 
                         stats=stats,
                         recent_questions=recent_questions,
                         recent_answers=recent_answers,
                         user_badges=user_badges,
                         recommended_questions=recommended)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add sample data if database is empty
        if User.query.count() == 0:
            # Create sample users
            user1 = User(username='john_doe', email='john@example.com', password_hash=generate_password_hash('password123'))
            user2 = User(username='jane_smith', email='jane@example.com', password_hash=generate_password_hash('password123'))
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Create sample tags
            tag1 = Tag(name='python')
            tag2 = Tag(name='flask')
            tag3 = Tag(name='database')
            tag4 = Tag(name='javascript')
            tag5 = Tag(name='html')
            db.session.add_all([tag1, tag2, tag3, tag4, tag5])
            db.session.commit()
            
            # Create sample questions
            question1 = Question(
                title='How to connect Flask to SQLite database?',
                content='I am new to Flask and want to connect my application to a SQLite database. What are the steps I need to follow?',
                user_id=user1.id
            )
            question1.tags.extend([tag1, tag2, tag3])
            
            question2 = Question(
                title='JavaScript vs Python for web development?',
                content='I am trying to decide between JavaScript and Python for web development. What are the pros and cons of each?',
                user_id=user2.id
            )
            question2.tags.extend([tag1, tag4])
            
            question3 = Question(
                title='Best practices for HTML forms?',
                content='What are the best practices for creating accessible and user-friendly HTML forms?',
                user_id=user1.id
            )
            question3.tags.extend([tag5])
            
            db.session.add_all([question1, question2, question3])
            db.session.commit()
            
            # Add some sample answers
            answer1 = Answer(
                content='To connect Flask to SQLite, you need to use Flask-SQLAlchemy. First install it with pip, then configure your app with the database URI, and define your models. The database will be created automatically.',
                user_id=user2.id,
                question_id=question1.id
            )
            
            answer2 = Answer(
                content='Python is great for backend development and has excellent frameworks like Flask and Django. JavaScript is essential for frontend development and can also be used for backend with Node.js. The choice depends on your specific needs.',
                user_id=user1.id,
                question_id=question2.id,
                is_accepted=True
            )
            
            db.session.add_all([answer1, answer2])
            db.session.commit()
            
            print('Sample data added successfully!')
    
    # Use socketio.run() instead of app.run() to handle SocketIO connections
    socketio.run(app, debug=True, port=5001)
