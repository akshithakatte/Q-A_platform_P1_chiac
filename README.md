# Q&A Platform - Mini StackOverflow Clone

A web-based Q&A platform built with Flask that allows users to ask questions, post answers, and interact through voting and tagging systems.

## Features

- **User Authentication**: Register, login, and logout functionality
- **Question Posting**: Users can post questions with titles, descriptions, and tags
- **Answer System**: Users can post answers to questions
- **Voting System**: Upvote/downvote questions and answers
- **Search Functionality**: Search questions by keywords or tags
- **Accepted Answers**: Question authors can mark answers as accepted
- **Modern UI**: Responsive design with Bootstrap 5

## Requirements

- Python 3.7+
- Flask and related packages (see requirements.txt)

## Installation

1. Clone or download the project
2. Navigate to the project directory
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Make sure you're in the project directory with the virtual environment activated
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000`

## Usage

1. **Register**: Create a new account with username, email, and password
2. **Login**: Use your credentials to log in
3. **Ask Question**: Click "Ask Question" to post a new question with tags
4. **Answer Questions**: View questions and post answers
5. **Vote**: Upvote or downvote questions and answers
6. **Search**: Use the search bar to find questions by keywords or tags
7. **Accept Answers**: Question authors can mark the best answer as accepted

## Database

The application uses SQLite database which is automatically created when you first run the application. The database file `qa_platform.db` will be created in the project directory.

## Project Structure

```
qa_platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Home page with questions list
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── ask_question.html # Ask question form
│   ├── question_detail.html # Question and answers view
│   └── search_results.html # Search results page
└── README.md            # This file
```

## Technologies Used

- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: User authentication
- **Flask-WTF**: Form handling
- **Bootstrap 5**: Frontend styling
- **Font Awesome**: Icons
- **SQLite**: Database

## Contributing

Feel free to fork this project and submit pull requests for improvements.

## License

This project is open source and available under the MIT License.
