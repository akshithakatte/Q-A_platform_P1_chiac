from app import app, db, User, Question, Answer, Tag
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
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
        print(f'Users: {User.query.count()}')
        print(f'Questions: {Question.query.count()}')
        print(f'Answers: {Answer.query.count()}')
        print(f'Tags: {Tag.query.count()}')

if __name__ == '__main__':
    init_database()
