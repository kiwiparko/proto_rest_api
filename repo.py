import sqlalchemy.exc
import yaml
from sqlalchemy import create_engine, desc, update
from sqlalchemy.orm import sessionmaker, Session

from model import PydanticAction, PydanticNote, Action, Action_Tag, Group, Tag, Note

with open('settings.yml') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)

engine = create_engine(f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}",
                       echo=True)
SessionLocal = sessionmaker(bind=engine)


class ActionAlchemyRepository(object):
    def __init__(self):
        self.db = SessionLocal()

    @staticmethod
    def _orm_to_pydantic(orm_action: Action) -> PydanticAction:
        pydantic_action = PydanticAction.from_orm(orm_action)
        return pydantic_action

    @staticmethod
    def _pydantic_to_orm(pydantic_action: PydanticAction) -> Action:
        action = Action(
            action=pydantic_action.action,
            parent_id=pydantic_action.parent_id,
            group_id=pydantic_action.group_id,
            created_on=pydantic_action.created_on,
            updated_on=pydantic_action.updated_on,
        )
        return action

    def create(self, item: Action, return_pydantic=True):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        if return_pydantic:
            return PydanticAction.from_orm(item)
        return item

    def update(self, item: Action, item_id, return_pydantic=True):
        tbc = self.db.query(Action).filter(Action.id == item_id).first()
        tbc.action = item.action
        tbc.parent_id = item.parent_id
        tbc.group_id = item.group_id
        tbc.updated_on = item.updated_on
        self.db.commit()
        if return_pydantic:
            return PydanticAction.from_orm(item)
        return item

    def create_pydantic(self, item: PydanticAction, return_pydantic=True):
        orm_action = self._pydantic_to_orm(item)
        result = self.create(orm_action, return_pydantic=return_pydantic)
        return result

    def update_pydantic(self, item: PydanticAction, item_id, return_pydantic=True):
        try:
            orm_action = self._pydantic_to_orm(item)
            result = self.update(orm_action, item_id, return_pydantic=return_pydantic)
        except AttributeError:
            result = 'no rows with such id'
        except sqlalchemy.exc.IntegrityError:
            result = 'no group/parent with such id'
        return result

    def note_match(self, _id):
        try:
            output = (self.db.query(Note)
                      .filter(
                            Note.action_id == _id
                            )
                      .all()
                      )
            try:
                a = output[0]
            except:
                raise AttributeError
        except AttributeError: #вероятен NoneType
            output = None
        return output

    def group_match(self, _id):
        return (self.db.query(Group)
                .filter(
                   Group.id == _id
                   )
                .all()
                )

    def tag_match(self, _id):
        try:
            action_tag = (self.db.query(Action_Tag)
                          .filter(
                                Action_Tag.action_id == _id
                                )
                          .first()
                          )
            actual_tag = (self.db.query(Tag)
                          .filter(
                                Tag.id == action_tag.tag_id
                                )
                          )
            full_tag = {
                "name": actual_tag.name,
                "color": actual_tag.color
            }
        except AttributeError: #искренне надеюсь что тут только NoneType вылетает
            full_tag = None
        return full_tag

    def child_match(self, _id):
        try:
            output = (self.db.query(Action)
                     .filter(
                         Action.parent_id == _id
                         )
                     .all()
                     )
            for i in range(output.__len__()):
                if output[i].group_id is None:
                    output[i].group = None
                else:
                    output[i].group = self.group_match(output[i].id)

                output[i].tag = self.tag_match(output[i].id)

                output[i].note = self.note_match(output[i].id)

                output[i].children = self.child_match(output[i].id)
        except AttributeError: #вдвойне усерднее надеюсь на NoneType
            output = None
        return output

    def fetch_by_action_id(self, _id):
        main_action = (self.db.query(Action)
                       .filter(
            Action.id == _id
        )
                       .all()
                       )

        if main_action[0].group_id is None:
            main_action[0].group = None
        else:
            main_action[0].group = self.group_match(main_action[0].id)

        main_action[0].tag = self.tag_match(main_action[0].id)

        main_action[0].note = self.note_match(main_action[0].id)

        main_action[0].children = self.child_match(main_action[0].id)
        return main_action

    def dogshit(self, _id):
        try:
            main_action = (self.db.query(Action)
                           .filter(Action.parent_id == _id)
                           .all()
                           )
            for i in main_action:
                i.tag = self.tag_match(i.id)
                if i.group_id is None:
                    i.group = None
                else:
                    i.group = self.group_match(i.id)
                i.children = None
        except:
            main_action = None
        return main_action

    def fetch_by_action_name(self, name):
        main_action = (self.db.query(Action)
                       .filter(
                            Action.action.like(f'%{name}%')
                            )
                       .limit(20)
                       .all()
                       )
        for i in main_action:
            i.children = self.dogshit(i.id)
            if i.group_id is None:
                i.group = None
            else:
                i.group = self.group_match(i.id)
            i.tag = self.tag_match(i.id)
        return main_action

    def fetch_all(self, skip: int = 0, limit: int = 100):
        return (self.db.query(Action)
                .offset(skip)
                .limit(limit)
                .order_by(
                    desc(Action.updated_on)
                    )
                .all()
                )

    async def delete(self, item_id):
        db_item = self.db.query(Action).filter_by(id=item_id).first()
        self.db.delete(db_item)
        self.db.commit()


class NoteAlchemyRepository(object):
    def __init__(self):
        self.db = SessionLocal()

    @staticmethod
    def _orm_to_pydantic(orm_note: Note) -> PydanticNote:
        pydantic_note = PydanticAction.from_orm(orm_note)
        return pydantic_note

    @staticmethod
    def _pydantic_to_orm(pydantic_note: PydanticNote) -> Note:
        note = Note(
            action_id=pydantic_note.action_id,
            type=pydantic_note.type,
            payload=pydantic_note.payload
        )
        return note

    def create(self, item: Note, return_pydantic=True):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        if return_pydantic:
            return PydanticNote.from_orm(item)
        return item

    def update(self, item: Note, item_id, return_pydantic=True):
        tbc = self.db.query(Note).filter(Note.id == item_id).first()
        tbc.action_id = item.action_id
        tbc.type = item.type
        tbc.payload = item.payload
        self.db.commit()
        if return_pydantic:
            return PydanticNote.from_orm(item)
        return item

    def create_pydantic(self, item: PydanticNote, return_pydantic=True):
        orm_note = self._pydantic_to_orm(item)
        result = self.create(orm_note, return_pydantic=return_pydantic)
        return result

    def update_pydantic(self, item: PydanticNote, item_id, return_pydantic=True):
        try:
            orm_note = self._pydantic_to_orm(item)
            result = self.update(orm_note, item_id, return_pydantic=return_pydantic)
        except AttributeError:
            result = 'no rows with such id'
        except sqlalchemy.exc.IntegrityError:
            result = 'no action with such id'
        return result

    def note_fetch_by_id(self, _id):
        try:
            note = (self.db.query(Note)
                    .filter(Note.id == _id)
                    .all()
                    )
            try:
                a = note[0]
            except:
                raise AttributeError
        except AttributeError:
            note = 'no rows with such id'
        return note

    def note_delete(self, _id):
        note = (self.db.query(Note)
                .filter(Note.id == _id)
                .delete()
                )
        self.db.commit()
        if note == 1:
            return 'deleted'
        else:
            return 'no rows with such id'


# Dependency
def get_action_repo():
    repo = ActionAlchemyRepository()
    try:
        yield repo
    finally:
        pass

def get_note_repo():
    repo = NoteAlchemyRepository()
    try:
        yield repo
    finally:
        pass