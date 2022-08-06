import sqlalchemy.exc
import yaml
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker


from model import PydanticAction, PydanticNote, PydanticGroup, Action, Action_Tag, Group, Tag, Note

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

    def create(self, item: Action):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Action, item_id):
        tbc = self.db.query(Action).filter(Action.id == item_id).first()
        tbc.action = item.action
        tbc.parent_id = item.parent_id
        tbc.group_id = item.group_id
        tbc.updated_on = item.updated_on
        self.db.commit()
        return item

    def create_pydantic(self, item: PydanticAction):
        orm_action = self._pydantic_to_orm(item)
        result = self.create(orm_action)
        return result

    def update_pydantic(self, item: PydanticAction, item_id):
        try:
            orm_action = self._pydantic_to_orm(item)
            result = self.update(orm_action, item_id)
        except AttributeError:
            return
        except sqlalchemy.exc.IntegrityError:
            return {'detail': 'no group/parent with such id'}
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
                note = output[0]
            except:
                raise AttributeError
        except AttributeError: # вероятен NoneType
            note = None
        return note

    def group_match(self, _id):
        return (self.db.query(Group)
                .filter(
                   Group.id == _id
                   )
                .first()
                ).name

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
        except AttributeError:  # искренне надеюсь что тут только NoneType вылетает
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
                if output[i].children.__len__() == 0:
                    output[i].children = None
        except AttributeError: # вдвойне усерднее надеюсь на NoneType
            output = None
        return output

    def fetch_by_action_id(self, _id):
        main_action = (self.db.query(Action)
                       .filter(
                            Action.id == _id
                            )
                       .first()
                       )
        if main_action is None:
            return

        if main_action.group_id is None:
            main_action.group = None
        else:
            main_action.group = self.group_match(main_action.group_id)

        main_action.tag = self.tag_match(main_action.id)

        main_action.note = self.note_match(main_action.id)

        main_action.children = self.child_match(main_action.id)

        if main_action.children.__len__() == 0:
            main_action.children = None

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
                    i.group = self.group_match(i.group_id)
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
                i.group = self.group_match(i.group_id)
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
        pydantic_note = PydanticNote.from_orm(orm_note)
        return pydantic_note

    @staticmethod
    def _pydantic_to_orm(pydantic_note: PydanticNote) -> Note:
        note = Note(
            action_id=pydantic_note.action_id,
            type=pydantic_note.type,
            payload=pydantic_note.payload
        )
        return note

    def create(self, item: Note):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Note, item_id):
        tbc = self.db.query(Note).filter(Note.id == item_id).first()
        tbc.action_id = item.action_id
        tbc.type = item.type
        tbc.payload = item.payload
        self.db.commit()
        return item

    def create_pydantic(self, item: PydanticNote):
        orm_note = self._pydantic_to_orm(item)
        result = self.create(orm_note)
        return result

    def update_pydantic(self, item: PydanticNote, item_id):
        try:
            orm_note = self._pydantic_to_orm(item)
            result = self.update(orm_note, item_id)
        except AttributeError:
            return
        except sqlalchemy.exc.IntegrityError:
            return
        return result

    def note_fetch_by_id(self, _id):
        try:
            note = (self.db.query(Note)
                    .filter(Note.id == _id)
                    .first()
                    )
            if note is None:
                raise AttributeError
        except AttributeError:
            return
        return note

    def note_delete(self, _id):
        note = (self.db.query(Note)
                .filter(Note.id == _id)
                .delete()
                )
        self.db.commit()
        if note == 1:
            return {'detail': 'deleted'}
        else:
            return


class GroupAlchemyRepository(object):
    def __init__(self):
        self.db = SessionLocal()

    @staticmethod
    def _orm_to_pydantic(orm_group: Group) -> PydanticGroup:
        pydantic_group = PydanticGroup.from_orm(orm_group)
        return pydantic_group

    @staticmethod
    def _pydantic_to_orm(pydantic_group: PydanticGroup) -> Group:
        group = Group(
            name=pydantic_group.name
        )
        return group

    def create(self, item: Group):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Group, item_id):
        tbc = self.db.query(Group).filter(Group.id == item_id).first()
        tbc.name = item.name
        self.db.commit()
        return item

    def create_pydantic(self, item: PydanticGroup):
        orm_group = self._pydantic_to_orm(item)
        result = self.create(orm_group)
        return result

    def update_pydantic(self, item: PydanticGroup, item_id):
        try:
            orm_group = self._pydantic_to_orm(item)
            result = self.update(orm_group, item_id)
        except AttributeError:
            return
        return result

    def fetch_all_groups(self):
        groups = (self.db.query(Group)
                  .all()
                  )
        if groups.__len__() == 0:
            return
        return groups

    def group_delete(self, _id):
        action = (self.db.query(Action)
                  .filter(Action.group_id == _id)
                  .all()
                  )
        for i in action:
            i.group_id = None
        self.db.commit()
        group = (self.db.query(Group)
                 .filter(Group.id == _id)
                 .delete()
                 )
        self.db.commit()
        if group == 1:
            return {'detail': 'deleted'}
        else:
            return


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


def get_group_repo():
    repo = GroupAlchemyRepository()
    try:
        yield repo
    finally:
        pass
