from datetime import datetime

import yaml
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Action_Tag(Base):
    __tablename__ = 'action_tag'
    id = Column(Integer, primary_key=True)
    action_id = Column(Integer(), ForeignKey("actions.id"))
    tag_id = Column(Integer(), ForeignKey("tags.id"))


class Action(Base):
    __tablename__ = 'actions'
    id = Column(Integer, primary_key=True)
    action = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('actions.id'), nullable=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    actions = relationship("Action")


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    actions = relationship("Action_Tag", backref='tag')
    color = Column(String(12), nullable=True)


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey('actions.id'))
    type = Column(String(12), nullable=False)
    payload = Column(Text(), nullable=True)


PydanticAction = sqlalchemy_to_pydantic(Action, exclude=['id'])
PydanticGroup = sqlalchemy_to_pydantic(Group, exclude=['id'])
PydanticTag = sqlalchemy_to_pydantic(Tag, exclude=['id'])
PydanticActionTag = sqlalchemy_to_pydantic(Action_Tag, exclude=['id'])
PydanticNote = sqlalchemy_to_pydantic(Note, exclude=['id'])


if __name__ == '__main__':
    with open('settings.yml') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    engine = create_engine(
        f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}",
        echo=True)
    SessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)
