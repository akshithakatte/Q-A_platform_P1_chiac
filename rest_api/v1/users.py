from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

# Import models from app (they're defined there)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import User, db

# Import badge models if available
try:
    from app import UserBadge, Badge
except ImportError:
    # Fallback if badge models aren't available
    UserBadge = None
    Badge = None

users_bp = Blueprint('users_v1', __name__)

@users_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            User.username.contains(search) |
            User.email.contains(search)
        )
    
    # Pagination
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'reputation': user.reputation,
            'badge_level': user.badge_level,
            'profile_views': user.profile_views,
            'created_at': user.created_at.isoformat(),
            'questions_count': len(user.questions),
            'answers_count': len(user.answers)
        } for user in users.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': users.total,
            'pages': users.pages,
            'has_next': users.has_next,
            'has_prev': users.has_prev
        }
    })

@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user profile"""
    user = User.query.get_or_404(user_id)
    
    # Calculate fresh reputation
    user.reputation = user.calculate_reputation()
    user.update_badge_level()
    db.session.commit()
    
    # Get user badges
    user_badges = db.session.query(UserBadge, Badge).join(Badge).filter(
        UserBadge.user_id == user_id
    ).order_by(UserBadge.earned_at.desc()).all()
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'reputation': user.reputation,
        'badge_level': user.badge_level,
        'profile_views': user.profile_views,
        'created_at': user.created_at.isoformat(),
        'questions_count': len(user.questions),
        'answers_count': len(user.answers),
        'accepted_answers_count': len([a for a in user.answers if a.is_accepted]),
        'badges': [{
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'icon': badge.icon,
            'earned_at': user_badge.earned_at.isoformat()
        } for user_badge, badge in user_badges]
    })

@users_bp.route('/users/<int:user_id>/questions', methods=['GET'])
def get_user_questions(user_id):
    """Get questions by specific user"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    user = User.query.get_or_404(user_id)
    questions = Question.query.filter_by(user_id=user_id).order_by(
        Question.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'user_id': user_id,
        'username': user.username,
        'questions': [{
            'id': q.id,
            'title': q.title,
            'content': q.content[:200] + '...' if len(q.content) > 200 else q.content,
            'created_at': q.created_at.isoformat(),
            'tags': [tag.name for tag in q.tags],
            'answers_count': len(q.answers),
            'votes': sum(v.value for v in q.votes)
        } for q in questions.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': questions.total,
            'pages': questions.pages
        }
    })

@users_bp.route('/users/<int:user_id>/answers', methods=['GET'])
def get_user_answers(user_id):
    """Get answers by specific user"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    user = User.query.get_or_404(user_id)
    answers = Answer.query.filter_by(user_id=user_id).order_by(
        Answer.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'user_id': user_id,
        'username': user.username,
        'answers': [{
            'id': a.id,
            'content': a.content[:200] + '...' if len(a.content) > 200 else a.content,
            'created_at': a.created_at.isoformat(),
            'question_id': a.question_id,
            'question_title': a.question.title,
            'is_accepted': a.is_accepted,
            'votes': sum(v.value for v in a.votes)
        } for a in answers.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': answers.total,
            'pages': answers.pages
        }
    })

@users_bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user profile"""
    # Calculate fresh reputation
    current_user.reputation = current_user.calculate_reputation()
    current_user.update_badge_level()
    db.session.commit()
    
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'reputation': current_user.reputation,
        'badge_level': current_user.badge_level,
        'profile_views': current_user.profile_views,
        'created_at': current_user.created_at.isoformat(),
        'questions_count': len(current_user.questions),
        'answers_count': len(current_user.answers),
        'accepted_answers_count': len([a for a in current_user.answers if a.is_accepted])
    })

@users_bp.route('/users/me', methods=['PUT'])
@login_required
def update_current_user():
    """Update current user profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update allowed fields
    if 'email' in data:
        # Check if email is already taken
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Email already taken'}), 400
        current_user.email = data['email']
    
    # Note: Password update should be handled separately for security
    
    db.session.commit()
    
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'updated_at': datetime.utcnow().isoformat()
    })
