from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qa_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)

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
    value = db.Column(db.Integer, nullable=False)  # 1 for upvote, -1 for downvote
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=True)

question_tags = db.Table('question_tags',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
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

# Routes
@app.route('/')
def index():
    search_form = SearchForm()
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('index.html', questions=questions, search_form=search_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
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
    
    # Calculate vote counts
    question_votes = sum(vote.value for vote in question.votes)
    
    # Calculate answer votes and sort
    answers_with_votes = []
    for answer in question.answers:
        answer_votes = sum(vote.value for vote in answer.votes)
        answers_with_votes.append((answer, answer_votes))
    
    # Sort answers: accepted first, then by vote count
    answers_with_votes.sort(key=lambda x: (not x[0].is_accepted, -x[1]))
    
    return render_template('question_detail.html', 
                         question=question, 
                         form=form, 
                         question_votes=question_votes,
                         answers_with_votes=answers_with_votes)

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
    item_type = data.get('type')  # 'question' or 'answer'
    item_id = data.get('id')
    value = data.get('value')  # 1 or -1
    
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
    
    return jsonify({'vote_count': vote_count})

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
    
    if form.validate_on_submit() or request.args.get('q'):
        query = request.args.get('q') or form.query.data
        
        # Search by title and content
        questions = Question.query.filter(
            db.or_(
                Question.title.contains(query),
                Question.content.contains(query)
            )
        ).all()
        
        # Search by tags
        tag_questions = Question.query.join(Question.tags).filter(Tag.name.contains(query)).all()
        questions = list(set(questions + tag_questions))  # Remove duplicates
        
        # Sort by creation date
        questions.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('search_results.html', questions=questions, form=form, query=request.args.get('q', ''))

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
    
    app.run(debug=True, port=5001)
