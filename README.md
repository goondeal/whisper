# Whisper
whisper is social platform where users can send and receive secret messages from their friends anonymously.
This project is inspired by: [Sarhne](https://www.sarhne.com/)

## Tech stack:
### Backend:
[Fastapi](https://fastapi.tiangolo.com/)
[SQLAlchemy](https://www.sqlalchemy.org/) ORM
[Jinja](https://jinja.palletsprojects.com/en/3.0.x/) templating engine
sqlite
### Frontend:
HTML 5
CSS 3
Vanilla JS
[Bootstrap5](https://getbootstrap.com/)
[htmx](https://htmx.org/)

## Installation
It's super easy to try it by downloading and run the code locally.
all the requied files to run it are provided including `.env`.

1. Clone the repo
2. Navigate into the repo folder
3. Start your virtual environment `optional`
```
python -m venv venv
source venv/bin/activate
```
4. Install the requirements
```
pip install < requirements.txt
```
5. Start the app
```
uvicorn app.main:app --reload
```
6. Test accounts 
(password is __pass123456__ for all test users)
- ali@gmail.com
- noha@gmail.com
- sam@gmail.com

## Future Work:
- Enable Media:
    - User profile pic.
    - Enable sending images with messages.
- Enable user to change password
- Auth:
    - Add remember-me feature
    - Forgot-password scenario
