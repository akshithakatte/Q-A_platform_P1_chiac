from models.question import Question, Tag, Vote
from models.answer import Answer
from models import db
from datetime import datetime

class QuestionService:
    """Service layer for question and answer operations"""
    
    @staticmethod
    def create_question(title, content, tag_names, user_id):
        """Create a new question with tags"""
        question = Question(
            title=title,
            content=content,
            user_id=user_id
        )
        
        # Process tags
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
        """Create a new answer"""
        answer = Answer(
            content=content,
            question_id=question_id,
            user_id=user_id
        )
        
        db.session.add(answer)
        db.session.commit()
        
        return answer
    
    @staticmethod
    def accept_answer(answer_id, user_id):
        """Accept an answer (only question author can do this)"""
        answer = Answer.query.get_or_404(answer_id)
        question = answer.question
        
        if question.user_id != user_id:
            raise PermissionError('Only question author can accept answers')
        
        # Unaccept all other answers
        for ans in question.answers:
            ans.is_accepted = False
        
        # Accept this answer
        answer.is_accepted = True
        db.session.commit()
        
        return answer
    
    @staticmethod
    def vote(item_type, item_id, user_id, value):
        """Vote on question or answer"""
        if item_type == 'question':
            existing_vote = Vote.query.filter_by(
                user_id=user_id,
                question_id=item_id,
                answer_id=None
            ).first()
            
            if existing_vote:
                existing_vote.value = value
            else:
                vote = Vote(
                    value=value,
                    user_id=user_id,
                    question_id=item_id
                )
                db.session.add(vote)
        
        elif item_type == 'answer':
            existing_vote = Vote.query.filter_by(
                user_id=user_id,
                answer_id=item_id,
                question_id=None
            ).first()
            
            if existing_vote:
                existing_vote.value = value
            else:
                vote = Vote(
                    value=value,
                    user_id=user_id,
                    answer_id=item_id
                )
                db.session.add(vote)
        
        db.session.commit()
    
    @staticmethod
    def get_vote_count(item_type, item_id):
        """Get vote count for question or answer"""
        if item_type == 'question':
            question = Question.query.get(item_id)
            return sum(vote.value for vote in question.votes) if question else 0
        else:
            answer = Answer.query.get(item_id)
            return sum(vote.value for vote in answer.votes) if answer else 0
    
    @staticmethod
    def get_question_with_votes(question_id):
        """Get question with vote count"""
        question = Question.query.get_or_404(question_id)
        vote_count = QuestionService.get_vote_count('question', question_id)
        return question, vote_count
    
    @staticmethod
    def get_answers_with_votes(question_id):
        """Get answers for question with vote counts, sorted by accepted then votes"""
        answers = Answer.query.filter_by(question_id=question_id).all()
        
        answers_with_votes = []
        for answer in answers:
            vote_count = QuestionService.get_vote_count('answer', answer.id)
            answers_with_votes.append((answer, vote_count))
        
        # Sort: accepted first, then by vote count (descending)
        answers_with_votes.sort(key=lambda x: (not x[0].is_accepted, -x[1]))
        
        return answers_with_votes
