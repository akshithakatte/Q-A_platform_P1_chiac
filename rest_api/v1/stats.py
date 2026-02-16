from flask import Blueprint, jsonify
from datetime import datetime, timedelta

# Import models from app (they're defined there)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import User, Question, Tag, Answer, db

# Import badge models if available
try:
    from app import Badge, UserBadge
except ImportError:
    # Fallback if badge models aren't available
    Badge = None
    UserBadge = None

stats_bp = Blueprint('stats_v1', __name__)

@stats_bp.route('/stats', methods=['GET'])
def get_platform_stats():
    """Get platform-wide statistics"""
    return jsonify({
        'users': {
            'total': User.query.count(),
            'new_today': User.query.filter(
                User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            'new_this_week': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'new_this_month': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
        },
        'questions': {
            'total': Question.query.count(),
            'new_today': Question.query.filter(
                Question.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            'new_this_week': Question.query.filter(
                Question.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'new_this_month': Question.query.filter(
                Question.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count(),
            'unanswered': Question.query.filter(~Question.answers.any()).count()
        },
        'answers': {
            'total': Answer.query.count(),
            'new_today': Answer.query.filter(
                Answer.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            'new_this_week': Answer.query.filter(
                Answer.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'new_this_month': Answer.query.filter(
                Answer.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count(),
            'accepted': Answer.query.filter_by(is_accepted=True).count()
        },
        'tags': {
            'total': Tag.query.count(),
            'most_used': get_most_used_tags(10)
        },
        'badges': {
            'total': Badge.query.count(),
            'total_awarded': UserBadge.query.count()
        }
    })

@stats_bp.route('/stats/activity', methods=['GET'])
def get_activity_stats():
    """Get activity statistics for different time periods"""
    days = request.args.get('days', 7, type=int)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Questions per day
    questions_per_day = db.session.query(
        db.func.date(Question.created_at).label('date'),
        db.func.count(Question.id).label('count')
    ).filter(Question.created_at >= cutoff_date).group_by(
        db.func.date(Question.created_at)
    ).all()
    
    # Answers per day
    answers_per_day = db.session.query(
        db.func.date(Answer.created_at).label('date'),
        db.func.count(Answer.id).label('count')
    ).filter(Answer.created_at >= cutoff_date).group_by(
        db.func.date(Answer.created_at)
    ).all()
    
    return jsonify({
        'period_days': days,
        'questions_per_day': [{
            'date': str(q.date),
            'count': q.count
        } for q in questions_per_day],
        'answers_per_day': [{
            'date': str(a.date),
            'count': a.count
        } for a in answers_per_day]
    })

@stats_bp.route('/stats/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get user leaderboard by reputation"""
    period = request.args.get('period', 'all')  # all, week, month
    
    query = User.query
    
    if period == 'week':
        cutoff = datetime.utcnow() - timedelta(days=7)
        # This would need additional tracking for period-based reputation
        # For now, return overall reputation
    elif period == 'month':
        cutoff = datetime.utcnow() - timedelta(days=30)
        # This would need additional tracking for period-based reputation
        # For now, return overall reputation
    
    users = query.order_by(User.reputation.desc()).limit(50).all()
    
    return jsonify({
        'period': period,
        'leaderboard': [{
            'rank': idx + 1,
            'id': user.id,
            'username': user.username,
            'reputation': user.reputation,
            'badge_level': user.badge_level,
            'questions_count': len(user.questions),
            'answers_count': len(user.answers),
            'accepted_answers_count': len([a for a in user.answers if a.is_accepted])
        } for idx, user in enumerate(users)]
    })

def get_most_used_tags(limit=10):
    """Helper function to get most used tags"""
    tag_counts = db.session.query(
        Tag.name,
        db.func.count(Question.id).label('question_count')
    ).join(Question.tags).group_by(Tag.id).order_by(
        db.func.count(Question.id).desc()
    ).limit(limit).all()
    
    return [{
        'name': tag.name,
        'question_count': tag.question_count
    } for tag in tag_counts]
