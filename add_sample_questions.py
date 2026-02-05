#!/usr/bin/env python3
"""
Script to add 100 sample questions to the Q&A platform
"""

from app import app, db, User, Question, Tag, Answer
from datetime import datetime, timedelta
import random

def create_sample_questions():
    with app.app_context():
        # Get existing user or create one
        user = User.query.first()
        if not user:
            user = User(
                username='sample_user',
                email='sample@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
        
        # Create comprehensive tag list
        tag_names = [
            'python', 'javascript', 'java', 'c++', 'csharp', 'ruby', 'php', 'go', 'rust', 'swift',
            'flask', 'django', 'react', 'vue', 'angular', 'nodejs', 'express', 'spring', 'laravel',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'webpack', 'vite',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'database',
            'git', 'github', 'gitlab', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'devops',
            'algorithm', 'data-structures', 'machine-learning', 'ai', 'deep-learning', 'nlp',
            'web-development', 'mobile-development', 'android', 'ios', 'react-native', 'flutter',
            'testing', 'unit-testing', 'integration-testing', 'tdd', 'ci-cd',
            'security', 'authentication', 'authorization', 'encryption', 'oauth',
            'performance', 'optimization', 'caching', 'load-balancing', 'scaling',
            'api', 'rest', 'graphql', 'microservices', 'soa', 'websockets',
            'frontend', 'backend', 'fullstack', 'ui', 'ux', 'design',
            'linux', 'ubuntu', 'windows', 'macos', 'bash', 'shell', 'powershell',
            'networking', 'http', 'tcp', 'udp', 'dns', 'ssl', 'tls',
            'debugging', 'logging', 'monitoring', 'metrics', 'observability'
        ]
        
        # Create tags if they don't exist
        tags = {}
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags[tag_name] = tag
        
        db.session.commit()
        
        # Sample questions data
        questions_data = [
            {
                'title': 'How to implement authentication in Flask using JWT?',
                'content': 'I want to implement token-based authentication in my Flask application. What are the best practices for using JWT tokens? Should I store them in cookies or localStorage? How do I handle token refresh?',
                'tags': ['python', 'flask', 'authentication', 'jwt', 'security']
            },
            {
                'title': 'What is the difference between REST and GraphQL APIs?',
                'content': 'I am trying to decide between REST and GraphQL for my new API. What are the main differences? When should I choose GraphQL over REST? What are the performance implications?',
                'tags': ['api', 'rest', 'graphql', 'web-development', 'backend']
            },
            {
                'title': 'How to optimize database queries in Django?',
                'content': 'My Django application is running slow due to database queries. I have N+1 query problems. What are the best ways to optimize database queries? Should I use select_related or prefetch_related?',
                'tags': ['python', 'django', 'database', 'optimization', 'performance']
            },
            {
                'title': 'React Hooks vs Class Components - Which should I use?',
                'content': 'I am starting a new React project and wondering whether to use Hooks or class components. What are the advantages of Hooks? Are there any performance differences? When should I still use class components?',
                'tags': ['react', 'javascript', 'frontend', 'web-development']
            },
            {
                'title': 'How to implement caching in Node.js applications?',
                'content': 'I want to implement caching in my Node.js application to improve performance. What are the best caching strategies? Should I use Redis or Memcached? How do I implement cache invalidation?',
                'tags': ['nodejs', 'caching', 'performance', 'redis', 'backend']
            },
            {
                'title': 'What is the difference between SQL and NoSQL databases?',
                'content': 'I am trying to choose between SQL and NoSQL databases for my project. What are the main differences? When should I use MongoDB over PostgreSQL? What are the trade-offs in terms of scalability and consistency?',
                'tags': ['database', 'sql', 'nosql', 'mongodb', 'postgresql']
            },
            {
                'title': 'How to handle file uploads in Python Flask?',
                'content': 'I need to implement file upload functionality in my Flask application. What are the security considerations? How do I handle large files? Should I store files locally or use cloud storage?',
                'tags': ['python', 'flask', 'file-upload', 'security', 'web-development']
            },
            {
                'title': 'Best practices for API versioning?',
                'content': 'I am designing a public API and need to implement versioning. What are the different approaches to API versioning? Should I use URL versioning, header versioning, or query parameters? What are the pros and cons of each approach?',
                'tags': ['api', 'rest', 'web-development', 'backend', 'design']
            },
            {
                'title': 'How to implement real-time features in web applications?',
                'content': 'I want to add real-time features like chat and notifications to my web application. Should I use WebSockets, Server-Sent Events, or polling? What are the best libraries for implementing real-time functionality?',
                'tags': ['websockets', 'real-time', 'javascript', 'nodejs', 'frontend']
            },
            {
                'title': 'What is the difference between Docker containers and virtual machines?',
                'content': 'I am trying to understand the difference between Docker containers and virtual machines. What are the main differences in terms of resource usage, isolation, and portability? When should I use containers vs VMs?',
                'tags': ['docker', 'virtualization', 'devops', 'containers', 'infrastructure']
            },
            {
                'title': 'How to implement pagination in SQL queries?',
                'content': 'I need to implement pagination for large datasets in my SQL database. What are the different pagination techniques? How do I handle OFFSET vs keyset pagination? What are the performance implications?',
                'tags': ['sql', 'database', 'pagination', 'performance', 'optimization']
            },
            {
                'title': 'Best practices for error handling in JavaScript?',
                'content': 'What are the best practices for error handling in JavaScript applications? How should I handle async errors? Should I use try-catch blocks or .catch() methods? How do I create custom error classes?',
                'tags': ['javascript', 'error-handling', 'frontend', 'programming']
            },
            {
                'title': 'How to implement OAuth 2.0 authentication?',
                'content': 'I want to implement OAuth 2.0 for third-party authentication in my application. What are the different OAuth flows? How do I handle access tokens and refresh tokens? What are the security considerations?',
                'tags': ['oauth', 'authentication', 'security', 'api', 'backend']
            },
            {
                'title': 'What is the difference between Git merge and rebase?',
                'content': 'I am confused about when to use git merge vs git rebase. What are the differences? How do they affect commit history? What are the best practices for maintaining a clean Git history?',
                'tags': ['git', 'version-control', 'development', 'workflow']
            },
            {
                'title': 'How to optimize CSS for better performance?',
                'content': 'My website CSS is getting bloated and affecting performance. What are the best practices for CSS optimization? Should I use CSS-in-JS, CSS modules, or traditional CSS? How do I eliminate unused CSS?',
                'tags': ['css', 'performance', 'optimization', 'frontend', 'web-development']
            },
            {
                'title': 'Best practices for database indexing?',
                'content': 'I want to improve my database query performance through indexing. What are the best practices for creating indexes? When should I use composite indexes? How do I analyze query performance?',
                'tags': ['database', 'sql', 'indexing', 'performance', 'optimization']
            },
            {
                'title': 'How to implement microservices architecture?',
                'content': 'I am considering moving from a monolithic application to microservices. What are the key considerations? How do I handle inter-service communication? What are the challenges of microservices?',
                'tags': ['microservices', 'architecture', 'backend', 'design', 'devops']
            },
            {
                'title': 'What is the difference between HTTP/1.1 and HTTP/2?',
                'content': 'I am trying to understand the benefits of HTTP/2 over HTTP/1.1. What are the main differences? How does multiplexing work? What are the performance improvements?',
                'tags': ['http', 'networking', 'web-development', 'performance']
            },
            {
                'title': 'How to implement secure password storage?',
                'content': 'What are the best practices for storing user passwords securely? Should I use bcrypt, scrypt, or Argon2? How do I handle password resets? What about password policies?',
                'tags': ['security', 'authentication', 'encryption', 'backend', 'best-practices']
            },
            {
                'title': 'How to handle state management in React applications?',
                'content': 'I am confused about state management in React. Should I use useState, useReducer, Context API, or external libraries like Redux? What are the best practices for managing complex state?',
                'tags': ['react', 'state-management', 'javascript', 'frontend', 'web-development']
            }
        ]
        
        # Generate more questions to reach 100
        additional_questions = [
            {
                'title': 'What is the difference between async/await and Promises in JavaScript?',
                'content': 'I am trying to understand async/await syntax compared to Promises. What are the advantages? How do they handle error handling? When should I use one over the other?',
                'tags': ['javascript', 'async', 'promises', 'frontend', 'programming']
            },
            {
                'title': 'How to implement rate limiting in APIs?',
                'content': 'I want to implement rate limiting for my API to prevent abuse. What are the different approaches? Should I use token bucket or sliding window algorithms? How do I store rate limit data?',
                'tags': ['api', 'rate-limiting', 'security', 'backend', 'performance']
            },
            {
                'title': 'Best practices for mobile app development?',
                'content': 'I am starting mobile app development. Should I choose native development or cross-platform frameworks? What are the pros and cons of React Native vs Flutter? How do I handle platform-specific features?',
                'tags': ['mobile-development', 'react-native', 'flutter', 'android', 'ios']
            },
            {
                'title': 'How to implement search functionality in web applications?',
                'content': 'I need to implement search functionality for my web application. Should I use database full-text search or dedicated search engines like Elasticsearch? How do I handle search relevance and ranking?',
                'tags': ['search', 'elasticsearch', 'database', 'web-development', 'backend']
            },
            {
                'title': 'What is the difference between monolithic and microservices architecture?',
                'content': 'I am trying to decide between monolithic and microservices architecture for my new project. What are the trade-offs? When does it make sense to use microservices? What are the operational challenges?',
                'tags': ['architecture', 'microservices', 'design', 'backend', 'devops']
            },
            {
                'title': 'How to implement data validation in web applications?',
                'content': 'What are the best practices for data validation? Should I validate on both client and server side? How do I handle complex validation rules? What validation libraries should I use?',
                'tags': ['validation', 'security', 'web-development', 'backend', 'frontend']
            },
            {
                'title': 'Best practices for API documentation?',
                'content': 'I need to create comprehensive API documentation. Should I use Swagger/OpenAPI, API Blueprint, or custom documentation? What should be included in good API docs? How do I keep documentation in sync with code?',
                'tags': ['api', 'documentation', 'swagger', 'openapi', 'web-development']
            },
            {
                'title': 'How to implement background jobs in web applications?',
                'content': 'I need to run background jobs for tasks like sending emails and processing data. What are the best approaches? Should I use Celery, Sidekiq, or custom solutions? How do I handle job failures?',
                'tags': ['background-jobs', 'celery', 'queue', 'backend', 'performance']
            },
            {
                'title': 'What is the difference between SQL inner join and outer join?',
                'content': 'I am confused about different types of SQL joins. What is the difference between inner join, left join, right join, and full outer join? When should I use each type? How do they affect performance?',
                'tags': ['sql', 'database', 'joins', 'querying', 'backend']
            },
            {
                'title': 'How to implement internationalization in web applications?',
                'content': 'I want to make my web application available in multiple languages. What are the best practices for i18n? How do I handle date/time formats and currency? What tools should I use?',
                'tags': ['internationalization', 'i18n', 'localization', 'web-development', 'frontend']
            },
            {
                'title': 'Best practices for logging in production applications?',
                'content': 'What should I log in production applications? How do I handle sensitive data in logs? What logging levels should I use? How do I aggregate and analyze logs?',
                'tags': ['logging', 'monitoring', 'production', 'devops', 'observability']
            },
            {
                'title': 'How to implement WebSocket connections in Node.js?',
                'content': 'I want to add real-time functionality to my Node.js application using WebSockets. What libraries should I use? How do I handle connection management? How do I scale WebSocket connections?',
                'tags': ['websockets', 'nodejs', 'real-time', 'backend', 'javascript']
            },
            {
                'title': 'What is the difference between PUT and PATCH HTTP methods?',
                'content': 'I am confused about when to use PUT vs PATCH for updating resources. What are the semantic differences? How should they handle partial updates? What are the best practices?',
                'tags': ['http', 'api', 'rest', 'web-development', 'backend']
            },
            {
                'title': 'How to implement database transactions?',
                'content': 'I need to ensure data consistency in my application using database transactions. What are ACID properties? How do I handle transaction rollbacks? What are the performance implications?',
                'tags': ['database', 'transactions', 'sql', 'backend', 'consistency']
            },
            {
                'title': 'Best practices for responsive web design?',
                'content': 'I want to create responsive web designs that work on all devices. What are the best practices? Should I use CSS Grid, Flexbox, or Bootstrap? How do I handle different screen sizes?',
                'tags': ['responsive-design', 'css', 'frontend', 'mobile', 'web-development']
            },
            {
                'title': 'How to implement caching strategies in web applications?',
                'content': 'What are the different caching strategies I should implement? How do I handle browser caching, CDN caching, and server-side caching? When should I invalidate cache?',
                'tags': ['caching', 'performance', 'optimization', 'web-development', 'backend']
            },
            {
                'title': 'What is the difference between GraphQL and REST for mobile apps?',
                'content': 'I am developing a mobile app and choosing between GraphQL and REST. What are the advantages of GraphQL for mobile? How does it handle data over-fetching? What are the implementation challenges?',
                'tags': ['graphql', 'rest', 'mobile-development', 'api', 'backend']
            },
            {
                'title': 'How to implement secure file uploads?',
                'content': 'What are the security considerations for file uploads? How do I prevent malicious file uploads? Should I scan uploaded files? How do I handle file storage securely?',
                'tags': ['security', 'file-upload', 'backend', 'web-development', 'validation']
            },
            {
                'title': 'Best practices for database connection pooling?',
                'content': 'I want to optimize database performance using connection pooling. What are the best practices? How do I configure pool size? What are the common pitfalls to avoid?',
                'tags': ['database', 'connection-pooling', 'performance', 'optimization', 'backend']
            },
            {
                'title': 'How to implement API testing strategies?',
                'content': 'What are the best practices for testing APIs? Should I use unit tests, integration tests, or end-to-end tests? What tools should I use? How do I test authentication and authorization?',
                'tags': ['testing', 'api', 'integration-testing', 'backend', 'quality-assurance']
            }
        ]
        
        # Combine all questions
        all_questions = questions_data + additional_questions
        
        # Generate more questions to reach 100
        while len(all_questions) < 100:
            base_question = random.choice(all_questions[:20])  # Use first 20 as templates
            new_question = {
                'title': f"How to {random.choice(['optimize', 'implement', 'debug', 'test', 'deploy'])} {random.choice(['React', 'Python', 'SQL', 'JavaScript', 'Docker'])} {random.choice(['applications', 'databases', 'APIs', 'services', 'components'])}?",
                'content': f"I am working on {random.choice(['a new project', 'an existing application', 'a microservice', 'a web app'])} and need to {random.choice(['improve performance', 'add new features', 'fix bugs', 'implement security', 'scale the application'])}. What are the best practices and tools I should use?",
                'tags': random.sample(tag_names, random.randint(2, 5))
            }
            all_questions.append(new_question)
        
        # Create questions with random dates
        created_questions = []
        for i, q_data in enumerate(all_questions[:100]):
            # Random date within last year
            days_ago = random.randint(0, 365)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            question = Question(
                title=q_data['title'],
                content=q_data['content'],
                user_id=user.id,
                created_at=created_at
            )
            
            # Add tags
            for tag_name in q_data['tags']:
                if tag_name in tags:
                    question.tags.append(tags[tag_name])
            
            db.session.add(question)
            created_questions.append(question)
        
        db.session.commit()
        
        # Add some answers to random questions
        for i in range(150):  # Add 150 answers total
            question = random.choice(created_questions)
            answer_content = random.choice([
                "This is a common challenge in development. I recommend using established patterns and libraries that have been tested by the community.",
                "I faced a similar issue recently. The key is to break down the problem into smaller, manageable components and test each one individually.",
                "Great question! The best approach depends on your specific requirements, but generally speaking, you should consider scalability and maintainability from the start.",
                "There are several ways to approach this. I've found that starting with a simple solution and iterating based on feedback works well.",
                "This requires careful consideration of your use case. I suggest prototyping different approaches before committing to a full implementation."
            ])
            
            answer = Answer(
                content=answer_content + f" Here's a detailed explanation of how to handle this scenario effectively.",
                user_id=user.id,
                question_id=question.id,
                created_at=question.created_at + timedelta(hours=random.randint(1, 72))
            )
            
            # Randomly accept some answers
            if random.random() < 0.3:  # 30% chance of being accepted
                answer.is_accepted = True
            
            db.session.add(answer)
        
        db.session.commit()
        
        print(f"Successfully added {len(created_questions)} questions and 150 answers!")
        print(f"Total questions in database: {Question.query.count()}")
        print(f"Total answers in database: {Answer.query.count()}")
        print(f"Total tags in database: {Tag.query.count()}")

if __name__ == '__main__':
    create_sample_questions()
