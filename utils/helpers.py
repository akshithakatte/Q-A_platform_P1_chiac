# Lazy initialization of AI engines
ai_engine = None
smart_search = None
content_analyzer = None

def get_ai_engines():
    """Lazy initialization of AI engines"""
    global ai_engine, smart_search, content_analyzer
    
    if ai_engine is None:
        from ai_features import AIRecommendationEngine, SmartSearchEngine, ContentAnalyzer
        ai_engine = AIRecommendationEngine()
        smart_search = SmartSearchEngine()
        content_analyzer = ContentAnalyzer()
    
    return ai_engine, smart_search, content_analyzer
