from sqlalchemy import desc, Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(127))
    email = Column(String, unique=True, index=True)
    bio = Column(String(300), nullable=True)
    gender = Column(String(1), default='M')
    hashed_password = Column(String)
    # is_active = Column(Boolean, default=False)
    joined_at = Column(DateTime, server_default=func.now())
    num_of_visitors = Column(Integer, default=0)
    # settings
    allow_new_messages = Column(Boolean, default=True)
    allow_sending_images = Column(Boolean, default=True)
    allow_anonymous_users_messages = Column(Boolean, default=True)
    allow_notifications = Column(Boolean, default=True)
    hide_visitors_count = Column(Boolean, default=False)
    hide_last_seen = Column(Boolean, default=False)
    appear_in_search_results = Column(Boolean, default=True)

    @property
    def full_name(self):
        return self.name
        

def sent_at_desc():
    return desc('sent_at')
class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    content = Column(String, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), index=True)
    receiver_id = Column(Integer, ForeignKey('users.id'), index=True)
    sender = relationship('User', backref='sent_messages', foreign_keys=[sender_id])
    receiver = relationship('User', backref='received_messages', foreign_keys=[receiver_id])
    is_anonymous = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    sent_at = Column(DateTime, server_default=func.now())
    is_seen = Column(Boolean, default=False)

    # Default ordering
    # default_order = sent_at.desc()
    # __mapper_args__ = {
    #     "order_by": sent_at.desc(),
    # }
