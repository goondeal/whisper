from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas, utils


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def search_users(q: str, db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.User)
        .filter(models.User.appear_in_search_results==True)
        .filter(
            or_(
                models.User.name.icontains(q),
                models.User.email.icontains(q)
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_info(db: Session, user_id: int, info: schemas.UserInfo):
    user = get_user(db, user_id)
    if info.name and user.name != info.name:
        user.name = info.name
    if info.email and user.email != info.email:
        user.email = info.email
    if info.bio and user.bio != info.bio:
        user.bio = info.bio
    if info.gender and user.gender != info.gender:
        user.gender = info.gender
    db.commit()
    db.refresh(user)
    return user

def update_user_privacy_settings(db: Session, user_id: int, settings: schemas.PrivacySettings):
    user = get_user(db, user_id)
    user.allow_new_messages = settings.allow_new_messages
    user.allow_anonymous_users_messages = settings.allow_anonymous_users_messages
    user.allow_sending_images = settings.allow_sending_images
    user.allow_notifications = settings.allow_notifications
    user.hide_visitors_count = settings.hide_visitors_count
    user.hide_last_seen = settings.hide_last_seen
    user.appear_in_search_results = settings.appear_in_search_results
    db.commit()
    db.refresh(user)
    return user

def increase_user_visitors(db: Session, user_id: int):
    user = get_user(db, user_id)
    user.num_of_visitors = user.num_of_visitors + 1
    db.commit()
    db.refresh(user)
    return user

def set_user_messages_seen(db: Session, user_id: int):
    db.query(models.Message).filter(models.Message.receiver_id == user_id, models.Message.is_seen == False).update({models.Message.is_seen: True}, synchronize_session=False)
    db.commit()
    return True


def get_sent_messages(db: Session, user_id, skip: int = 0, limit: int = 100):
    return db.query(models.Message).filter(
        models.Message.sender_id == user_id
    ).offset(skip).limit(limit).join(models.User)

def get_messages(db: Session, filters: dict, skip: int = 0, limit: int = 100):
    return db.query(models.Message).filter_by(**filters).order_by(models.Message.sent_at.desc()).offset(skip).limit(limit).all()

def get_fav_messages(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    filters = {'receiver_id': user_id, 'is_featured': True}
    return get_messages(db, filters)

def get_public_messages(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    filters = {'receiver_id': user_id, 'is_public': True}
    return get_messages(db, filters)

def get_message_by_id(db: Session, message_id: int):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def create_message(db: Session, message: schemas.MessageCreate):
    db_message = models.Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
