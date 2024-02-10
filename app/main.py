from functools import lru_cache
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import Depends, FastAPI, Form, HTTPException, status, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from . import crud, models, schemas, config
from .database import SessionLocal, engine
from .utils import verify_password
from .exceptions import RequiresLogin


@lru_cache
def get_settings():
    return config.Settings()

settings = get_settings()
# print('settings =', settings.json())
SECRET_KEY = settings.JWT_PRIVATE_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
API_VERSION = settings.API_VERSION

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Exception handlers
# login redirection
@app.exception_handler(RequiresLogin)
async def requires_login(request: Request, _: Exception):
    return RedirectResponse(f"/login?next={quote(request.url.path)}", status_code=status.HTTP_302_FOUND)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
async def _get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
    ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('email')
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def _authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def _create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def _get_request_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('auth_token')
    if token:
        try:
            user = await _get_current_user(token, db)
            return user
        except:
            return None
    return None

# Template Responses
# Auth views
@app.get("/register", response_class=HTMLResponse)
async def register(request: Request) -> schemas.Token:
    user = await _get_request_user(request)
    if user:
        print('redirectiing to /messages/ ...')
        return RedirectResponse('/messages/', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="register.html")


@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    name: str = Form(...), email: str = Form(...), gender: str = Form(...), password: str = Form(...),
    db: Session = Depends(get_db)
) -> schemas.Token:
    try:
        info = schemas.UserCreate(email=email, name=name, gender=gender, password=password)
        user = crud.create_user(db, info)
        return RedirectResponse('/login/', status_code=status.HTTP_302_FOUND)
    except:
        return RedirectResponse('/register/', status_code=status.HTTP_302_FOUND)
        # return HTTPException(
        #     status_code=status.HTTP_400_BAD_REQUEST,
        #     detail="Incorrect email or password",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request) -> schemas.Token:
    print('get login')
    user = await _get_request_user(request)
    print('user =', user)
    if user:
        print('redirectiing to /messages/ ...')
        return RedirectResponse('/messages/', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> schemas.Token:
    print('form data =', form_data.username,  form_data.password)
    print(f'query_params = {request.query_params}')
    print(f'path_params = {request.path_params}')
    user = _authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = _create_access_token(
        data={'email': user.email}, expires_delta=access_token_expires
    )
    target = request.query_params.get('next', default='/messages/')
    response = RedirectResponse(target, status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='auth_token', value=access_token, httponly=True)
    return response


@app.get("/logout")
def logout(request: Request):
  response = RedirectResponse('/login/', status_code=status.HTTP_302_FOUND)
  response.delete_cookie(key='auth_token')
  return response


# User views
@app.get('/profile/', response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    request_user = await _get_request_user(request, db)
    if not request_user:
        raise RequiresLogin("You must be logged in to access this")
    context = {'user': request_user}
    return templates.TemplateResponse(
        request=request, name="profile.html", context=context
    )


@app.post(f'{API_VERSION}/info/', response_class=HTMLResponse)
async def update_user_info(
    request: Request,
    name: str = Form(...), email: str = Form(...), gender: str = Form(...), bio: str = Form(...),
    db: Session = Depends(get_db)
    ):
    user = await _get_request_user(request, db)
    if not user:
        raise RequiresLogin("You must be logged in to access this")
    try:
        info = schemas.UserInfo(name=name, email=email, gender=gender, bio=bio)
        user = crud.update_user_info(db, user.id, info)
        return RedirectResponse('/profile/', status_code=status.HTTP_302_FOUND)
    except:
        return templates.TemplateResponse(request, name='components/alert.html', context={'type': 'danger', 'message': 'Error try again later'})


@app.post(f'{API_VERSION}/privacy', response_class=HTMLResponse)
async def update_user_privacy_settings(
    request: Request,
    allow_new_messages: Optional[bool] = Form(False),
    allow_anonymous_users_messages: Optional[bool] = Form(False),
    allow_sending_images: Optional[bool] = Form(False),
    allow_notifications: Optional[bool] = Form(False),
    hide_visitors_count: Optional[bool] = Form(False),
    hide_last_seen: Optional[bool] = Form(False),
    appear_in_search_results: Optional[bool] = Form(False),
    db: Session = Depends(get_db)
    ):
    user = await _get_request_user(request, db)
    if not user:
        raise RequiresLogin("You must be logged in to access this")
    try:
        settings = schemas.PrivacySettings(
            allow_new_messages=allow_new_messages,
            allow_anonymous_users_messages=allow_anonymous_users_messages,
            allow_sending_images=allow_sending_images,
            allow_notifications=allow_notifications,
            hide_visitors_count=hide_visitors_count,
            hide_last_seen=hide_last_seen,
            appear_in_search_results=appear_in_search_results,
        )
        print('settings =', settings.dict())
        user = crud.update_user_privacy_settings(db, user.id, settings)
        return RedirectResponse('/profile/', status_code=status.HTTP_302_FOUND)
        # templates.TemplateResponse(request, name='profile.html', context={'user': user})
    except:
        return templates.TemplateResponse(request, name='components/alert.html', context={'type': 'danger', 'message': 'Error try again later'})

    
@app.get('/messages/', response_class=HTMLResponse)
async def messages_page(request: Request, db: Session = Depends(get_db)):
    request_user = await _get_request_user(request, db)
    if not request_user:
        raise RequiresLogin("You must be logged in to access this")
    context = {'user': request_user, 'messages': request_user.received_messages}
    return templates.TemplateResponse(
        request=request, name="messages.html", context=context
    )
    

@app.get(f'/search/', response_class=HTMLResponse)
def search_page(request: Request):
    return templates.TemplateResponse(request, name='search_page.html')


@app.get(f'{API_VERSION}/users/', response_class=HTMLResponse)
def search_users(request: Request, db: Session = Depends(get_db)):
    q = request.query_params.get('q')
    users = crud.search_users(q, db)
    print('users =', users)
    if users:
        users = [schemas.UserSearchResult(email=u.email, name=u.name, gender=u.gender, bio=u.bio or '', id=u.id, joined_at=u.joined_at) for u in users]
        return templates.TemplateResponse(request, name='components/users_list.html', context={'users': users})
    return templates.TemplateResponse(request, name='components/user_not_found.html')


@app.get('/users/{user_id}', response_class=HTMLResponse)
async def read_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    request_user = await _get_request_user(request, db)
    if request_user and request_user.id == db_user.id:
        return RedirectResponse('/messages/', status_code=status.HTTP_302_FOUND)
    messages = crud.get_public_messages(db, user_id)
    user = crud.increase_user_visitors(db, user_id)
    context = {'user': user, 'messages': messages}
    return templates.TemplateResponse(
        request=request, name="user_page.html", context=context
    )


@app.post('/users/{user_id}/messages/', response_class=HTMLResponse)
async def create_messsage_for_user(
    request: Request,
    user_id: int,
    content: str = Form(...),
    anonymously: Optional[bool] = Form(False),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    request_user = await _get_request_user(request, db)
    kwargs = {
        'content': content,
        'is_anonymous': anonymously,
        'receiver_id': user.id,
        'sender_id': request_user.id if request_user else None
    }
    new_message = schemas.MessageCreate(**kwargs)
    # save the message
    message = crud.create_message(db=db, message=new_message)
    if message:
        return RedirectResponse('/success/', status_code=status.HTTP_302_FOUND)
    return '<div> error </div>'


@app.get('/success/', response_class=HTMLResponse)
async def message_sent_successfuly(request: Request):
    return templates.TemplateResponse(request, 'message_sent_successfuly.html')


@app.patch(API_VERSION+'/messages/{message_id}', response_class=HTMLResponse)
async def edit_message(
    request: Request,
    message_id: int,
    db: Session = Depends(get_db)
):
    data = await request.json()
    is_public = data.get('is_public')
    is_featured = data.get('is_featured')
    message = crud.get_message_by_id(db, message_id)
    if not message:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message Not Found"
        )
    request_user = await _get_request_user(request, db)
    if not request_user or message.receiver_id != request_user.id:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized action",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if is_public is not None:
        message.is_public = is_public
        db.commit()
        return templates.TemplateResponse(
            request=request,
            name=f'components/{"hide" if is_public else "show"}_message_btn.html',
            context={'message_id': message_id}
        )
    elif is_featured is not None:
        message.is_featured = is_featured
        db.commit()
        return templates.TemplateResponse(
            request=request,
            name=f'components/{"unfav" if is_featured else "fav"}_btn.html',
            context={'message_id': message_id}
        )
    return ''


@app.get(f'{API_VERSION}/messages/', response_class=HTMLResponse)
async def read_received_messages(request: Request, db: Session = Depends(get_db)):
    request_user = await _get_request_user(request, db)
    if not request_user:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    crud.set_user_messages_seen(db, request_user.id)
    messages = crud.get_messages(db, filters={'receiver_id': request_user.id})
    if messages:
        messages = [
            schemas.AnonymousMessage(**m.__dict__) if m.is_anonymous else schemas.Message(**m.__dict__) for m in messages
        ]
        return templates.TemplateResponse(
            request=request,
            name='components/messages_list.html',
            context={'messages': messages, 'public': False}
        )
    return templates.TemplateResponse(
        request=request,
        name='components/no_received_messages.html'
    )


@app.get(f'{API_VERSION}/messages/sent', response_class=HTMLResponse)
async def read_sent_messages(request: Request, db: Session = Depends(get_db)):
    request_user = await _get_request_user(request, db)
    if not request_user:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    messages = crud.get_messages(db, filters={'sender_id': request_user.id})
    if messages:
        messages = [schemas.SentMessage(**m.__dict__, receiver=m.receiver.__dict__) for m in messages]
        return templates.TemplateResponse(
            request=request,
            name='components/messages_list.html',
            context={'type': 'sent', 'messages': messages, 'public': False}
        )
    return templates.TemplateResponse(
        request=request,
        name='components/no_sent_messages.html'
    )


@app.get(f'{API_VERSION}/messages/fav', response_class=HTMLResponse)
async def read_fav_messages(request: Request, db: Session = Depends(get_db)):
    request_user = await _get_request_user(request, db)
    if not request_user:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    messages = crud.get_fav_messages(db, user_id=request_user.id)
    if messages:
        messages = [
            schemas.AnonymousMessage(**m.__dict__) if m.is_anonymous else schemas.Message(**m.__dict__) for m in messages
        ]
        return templates.TemplateResponse(
            request=request,
            name='components/messages_list.html',
            context={'user_type': 'R', 'messages': messages, 'public': False}
        )
    return templates.TemplateResponse(
        request=request,
        name='components/no_fav_messages.html'
    )
