from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from datetime import datetime

# Import models from app (they're defined there)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the app to get access to models
from app import Question, Tag, Vote, Answer, db

# Import QuestionService if it exists, otherwise define basic functions
try:
    from services.question_service import QuestionService
except ImportError:
    class QuestionService:
        @staticmethod
        def create_question(title, content, tag_names, user_id):
            question = Question(title=title, content=content, user_id=user_id)
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                question.tags.append(tag)
            db.session.add(question)
            db.session.commit()
            return question
        
        @staticmethod
        def create_answer(content, question_id, user_id):
            answer = Answer(content=content, question_id=question_id, user_id=user_id)
            db.session.add(answer)
            db.session.commit()
            return answer
        
        @staticmethod
        def vote(item_type, item_id, user_id, value):
            if item_type == 'question':
                existing_vote = Vote.query.filter_by(user_id=user_id, question_id=item_id, answer_id=None).first()
                if existing_vote:
                    existing_vote.value = value
                else:
                    vote = Vote(value=value, user_id=user_id, question_id=item_id)
                    db.session.add(vote)
            elif item_type == 'answer':
                existing_vote = Vote.query.filter_by(user_id=user_id, answer_id=item_id, question_id=None).first()
                if existing_vote:
                    existing_vote.value = value
                else:
                    vote = Vote(value=value, user_id=user_id, answer_id=item_id)
                    db.session.add(vote)
            db.session.commit()
        
        @staticmethod
        def get_vote_count(item_type, item_id):
            if item_type == 'question':
                question = Question.query.get(item_id)
                return sum(vote.value for vote in question.votes) if question else 0
            else:
                answer = Answer.query.get(item_id)
                return sum(vote.value for vote in answer.votes) if answer else 0
        
        @staticmethod
        def get_answers_with_votes(question_id):
            answers = Answer.query.filter_by(question_id=question_id).all()
            answers_with_votes = []
            for answer in answers:
                vote_count = QuestionService.get_vote_count('answer', answer.id)
                answers_with_votes.append((answer, vote_count))
            answers_with_votes.sort(key=lambda x: (not x[0].is_accepted, -x[1]))
            return answers_with_votes

# Import AI helpers if available
try:
    from utils.helpers import get_ai_engines
except ImportError:
    def get_ai_engines():
        from ai_features import AIRecommendationEngine, SmartSearchEngine, ContentAnalyzer
        ai_engine = AIRecommendationEngine()
        smart_search = SmartSearchEngine()
        content_analyzer = ContentAnalyzer()
        return ai_engine, smart_search, content_analyzer

questions_bp = Blueprint('questions_v1', __name__)

# Question endpoints
@questions_bp.route('/questions', methods=['GET'])
def get_questions():
    """Get all questions with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    tag_filter = request.args.get('tag')
    search = request.args.get('search')
    
    query = Question.query
    
    # Apply filters
    if tag_filter:
        query = query.join(Question.tags).filter(Tag.name == tag_filter)
    
    if search:
        query = query.filter(
            Question.title.contains(search) | 
            Question.content.contains(search)
        )
    
    # Pagination
    questions = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'questions': [{
            'id': q.id,
            'title': q.title,
            'content': q.content[:200] + '...' if len(q.content) > 200 else q.content,
            'author': q.author.username,
            'created_at': q.created_at.isoformat(),
            'tags': [tag.name for tag in q.tags],
            'answers_count': len(q.answers),
            'votes': QuestionService.get_vote_count('question', q.id),
            'url': url_for('question_detail', id=q.id)
        } for q in questions.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': questions.total,
            'pages': questions.pages,
            'has_next': questions.has_next,
            'has_prev': questions.has_prev,
            'next_url': url_for('questions_v1.get_questions', page=page+1) if questions.has_next else None,
            'prev_url': url_for('questions_v1.get_questions', page=page-1) if questions.has_prev else None
        }
    })

@questions_bp.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get specific question with answers"""
    question = Question.query.get_or_404(question_id)
    
    # Increment view count
    question.author.profile_views += 1
    db.session.commit()
    
    # Get answers with votes
    answers_with_votes = QuestionService.get_answers_with_votes(question_id)
    
    return jsonify({
        'id': question.id,
        'title': question.title,
        'content': question.content,
        'author': {
            'id': question.author.id,
            'username': question.author.username,
            'reputation': question.author.reputation,
            'badge_level': question.author.badge_level
        },
        'created_at': question.created_at.isoformat(),
        'tags': [tag.name for tag in question.tags],
        'votes': QuestionService.get_vote_count('question', question.id),
        'answers': [{
            'id': answer.id,
            'content': answer.content,
            'author': {
                'id': answer.author.id,
                'username': answer.author.username,
                'reputation': answer.author.reputation
            },
            'created_at': answer.created_at.isoformat(),
            'is_accepted': answer.is_accepted,
            'votes': answer_votes
        } for answer, answer_votes in answers_with_votes]
    })

@questions_bp.route('/questions', methods=['POST'])
@login_required
def create_question():
    """Create a new question"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['title', 'content', 'tags']):
        return jsonify({'error': 'Missing required fields: title, content, tags'}), 400
    
    try:
        tag_names = data['tags'] if isinstance(data['tags'], list) else [tag.strip() for tag in data['tags'].split(',')]
        
        question = QuestionService.create_question(
            data['title'],
            data['content'],
            tag_names,
            current_user.id
        )
        
        return jsonify({
            'id': question.id,
            'title': question.title,
            'content': question.content,
            'created_at': question.created_at.isoformat(),
            'tags': [tag.name for tag in question.tags],
            'url': url_for('question_detail', id=question.id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@questions_bp.route('/questions/<int:question_id>/answers', methods=['POST'])
@login_required
def create_answer(question_id):
    """Create an answer for a question"""
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing required field: content'}), 400
    
    try:
        answer = QuestionService.create_answer(
            data['content'],
            question_id,
            current_user.id
        )
        
        return jsonify({
            'id': answer.id,
            'content': answer.content,
            'created_at': answer.created_at.isoformat(),
            'question_id': question_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@questions_bp.route('/questions/<int:question_id>/vote', methods=['POST'])
@login_required
def vote_question(question_id):
    """Vote on a question"""
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'error': 'Missing required field: value'}), 400
    
    if data['value'] not in [1, -1]:
        return jsonify({'error': 'Vote value must be 1 or -1'}), 400
    
    try:
        QuestionService.vote('question', question_id, current_user.id, data['value'])
        vote_count = QuestionService.get_vote_count('question', question_id)
        
        return jsonify({
            'question_id': question_id,
            'vote_count': vote_count,
            'user_vote': data['value']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@questions_bp.route('/answers/<int:answer_id>/vote', methods=['POST'])
@login_required
def vote_answer(answer_id):
    """Vote on an answer"""
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'error': 'Missing required field: value'}), 400
    
    if data['value'] not in [1, -1]:
        return jsonify({'error': 'Vote value must be 1 or -1'}), 400
    
    try:
        QuestionService.vote('answer', answer_id, current_user.id, data['value'])
        vote_count = QuestionService.get_vote_count('answer', answer_id)
        
        return jsonify({
            'answer_id': answer_id,
            'vote_count': vote_count,
            'user_vote': data['value']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@questions_bp.route('/answers/<int:answer_id>/accept', methods=['POST'])
@login_required
def accept_answer(answer_id):
    """Accept an answer"""
    try:
        answer = QuestionService.accept_answer(answer_id, current_user.id)
        
        return jsonify({
            'answer_id': answer_id,
            'question_id': answer.question_id,
            'accepted': True,
            'message': 'Answer accepted successfully'
        })
        
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# AI-powered endpoints
@questions_bp.route('/questions/<int:question_id>/similar', methods=['GET'])
def get_similar_questions(question_id):
    """Get questions similar to the specified question"""
    try:
        ai_engine, smart_search, content_analyzer = get_ai_engines()
        similar = ai_engine.get_similar_questions(question_id, limit=5)
        
        return jsonify({
            'question_id': question_id,
            'similar_questions': [{
                'id': q.id,
                'title': q.title,
                'created_at': q.created_at.isoformat(),
                'url': url_for('question_detail', id=q.id)
            } for q in similar]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/questions/suggest-tags', methods=['GET'])
def suggest_tags():
    """Suggest tags based on content"""
    title = request.args.get('title', '')
    content = request.args.get('content', '')
    
    if not title and not content:
        return jsonify({'error': 'At least title or content parameter is required'}), 400
    
    try:
        ai_engine, smart_search, content_analyzer = get_ai_engines()
        suggested = content_analyzer.suggest_tags(title, content, limit=5)
        
        return jsonify({
            'suggested_tags': [{
                'id': tag.id,
                'name': tag.name
            } for tag in suggested]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/tags', methods=['GET'])
def get_tags():
    """Get all tags with usage counts"""
    tags = Tag.query.all()
    
    tag_data = []
    for tag in tags:
        question_count = len(tag.questions)
        tag_data.append({
            'id': tag.id,
            'name': tag.name,
            'questions_count': question_count
        })
    
    # Sort by usage count
    tag_data.sort(key=lambda x: x['questions_count'], reverse=True)
    
    return jsonify({
        'tags': tag_data,
        'total': len(tag_data)
    })
