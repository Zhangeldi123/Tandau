### Quizbit MCQ API

This is a MCQ Simulation API, a platform for practicing Multiple Choice Questions (MCQs).<br>
A web app that implemented Django Rest Framework and provided functionality for user registration, login, question retrieval, submit answer and view user submission history.<br>
The API used PostgreSQL as the database and Django Simple JWT for authentication.

### Features
1. User Authentication
- User Registration with password confirmation
- User Login with email and password
2. Question Retrieval
- Retrieve a specific question from the database
- Retrive a list of questions from the database
3. Anwser Submission
- Submit an answer to a question
- Validate the answer and check the result
4. User Submission History
- Retrieve a list of user submission history, attempt number, accuracy (score) and time taken

### Prerequisites
- Python 3.8
- Django REST framework
- Django Simple JWT
- PostgreSQL (Database)

### Installation
1. Clone the repository
```bash
git clone https://github.com/YeakubSadlil/quizbit.git
cd quizbit
```
2. Install the dependencies
```bash
pip install -r requirements.txt
```
3. Apply the database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
4. Run the server
```bash
python manage.py runserver
```

### API Endpoints
1. **User Registration**
```
POST /api/register/
```
- Request Body:
```json
{
    "email": "demo@gmail.com",
    "name": "Shahed Afridi",
    "password": "1234",
    "password2": "1234"
}
```
- Response:
```json
{
    "token": {
        "refresh": "<refresh-token>",
        "access": "<access-token>"
    },
    "msg": "Registration success"
}
```
2. **User Login**
```bash
POST /api/login/
```
- Request Body:
```json
{
    "email":"ab5@gmail.com",
    "password":"456"
}
```
- Response:
```json
{
    "token": {
        "refresh": "<refresh-token>",
        "access": "<access-token>"
    },
    "msg": "Login Success",
    "email": "ab5@gmail.com"
}
```
3 . **Question Retrieval**
```bash
GET /api/questionlist/
```
- Headers:
```json
{
    "Authorization": "Bearer <access_token>"
}
```
- Response:
```json
{
    "Total num. of Questions": 3,
    "All questions": [
        {
            "id": 2,
            "text": "What is the symbol for Gold?",
            "difficulty": "medium",
            "category_name": "Chemistry",
            "options": [
                {
                    "id": 5,
                    "solution": "Au"
                },
                {
                    "id": 6,
                    "solution": "Gu"
                },
                {
                    "id": 7,
                    "solution": "Gd"
                },
                {
                    "id": 8,
                    "solution": "Gl"
                }
            ]
        }
        ...
    ]
}
```
4. **Retrieve a specific question detail by id**
```bash
GET /api/question-detail/<id>/
```
- Headers:
```json
{
    "Authorization": "Bearer <access_token>"
}
```
- Response:
```json
{
    "id": 2,
    "text": "What is the symbol for Gold?",
    "difficulty": "medium",
    "category_name": "Physics",
    "choice": [
        {
            "id": 5,
            "solution": "Au"
        },
        {
            "id": 6,
            "solution": "Gu"
        },
        {
            "id": 7,
            "solution": "Gd"
        },
        {
            "id": 8,
            "solution": "Gl"
        }
    ]
}
```
5. **Answer Submission**
```
POST /api/submit-answer/
```
- Headers:
```json
{
    "Authorization": "Bearer <access_token>"
}
```
- Request Body:
```json
{
    "question": 2,
    "selected_answer": 6     
}
```
- Response:
```json
{
    "msg": "Solution submitted successfully.",
    "is_correct": true
}
```
6. **User Submission History**
```
POST /api/user_history/
```

- Headers:
```json
{
    "Authorization": "Bearer <access_token>"
}
```
- Response:
```json
{
    "Num of questions attempted": 2,
    "no_correct_answers": 1,
    "question data": [
        {
            "question": 1,
            "question_descr": "What is 1 + 3?",
            "is_correct": true,
            "answered_at": "2024-11-18T12:44:47.022316Z"
        },
        {
            "question": 2,
            "question_descr": "What is the symbol for Gold?",
            "is_correct": false,
            "answered_at": "2024-11-18T11:52:19.614287Z"
        }
    ]
}
```