from .questions import questions_bp
from .users import users_bp
from .stats import stats_bp

def register_api_blueprints(app):
    """Register all API v1 blueprints"""
    app.register_blueprint(questions_bp, url_prefix='/api/v1')
    app.register_blueprint(users_bp, url_prefix='/api/v1')
    app.register_blueprint(stats_bp, url_prefix='/api/v1')
