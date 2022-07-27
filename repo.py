import yaml
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

from model import PydanticAction, Action, Action_Tag, Group, Tag, Note

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
        orm_action = Action(
            action=pydantic_action.action,
            parent_id=pydantic_action.parent_id,
            group_id=pydantic_action.group_id,
            group=pydantic_action.group,
            tags=pydantic_action.tags,
            notes=pydantic_action.notes,
            created_on=pydantic_action.created_on,
            updated_on=pydantic_action.updated_on,
        )
        return orm_action

    def create(self, item: Action, return_pydantic=True):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        if return_pydantic:
            return PydanticAction.from_orm(item)
        return item

    def create_pydantic(self, item: PydanticAction, return_pydantic=True):
        orm_action = self._pydantic_to_orm(item)
        result = self.create(orm_action, return_pydantic=return_pydantic)
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
        except AttributeError: #искренне надеюсь что тут только NoneType вылетает
            actual_tag = None
        return actual_tag

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
        for i in range(main_action[0].children.__len__()):
            main_action[0].children[i].children = self.child_match(main_action[0].children[i].id)
        return main_action

    def fetch_by_action_name(self, name):
        main_action = (self.db.query(Action)
                       .filter(
                            Action.action.like(f'%{name}%')
                            )
                       .limit(20)
                       .all()
                       )

        for i in range(len(main_action)):

            #group vibe check
            if main_action[i].group_id is None:
                main_action[i].group = None
            else:
                main_action[i].group = self.group_match(main_action[i].id)

            #tag vibe check
            main_action[i].tag = self.tag_match(main_action[i].id)

            children_action = (self.db.query(Action)
                               .filter(
                                    Action.parent_id == main_action[i].id
                                    )
                               .all()
                               )
            if not children_action:
                continue
            else:
                for j in range(len(children_action)):
                    if children_action[j].group_id is None:
                        children_action[j].group = None
                    else:
                        children_action[j].group = self.group_match(children_action[j].id)
                    children_action[j].tag = self.tag_match(children_action[j].id)
                main_action[i].children = children_action
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

    async def update(self, item_data):
        updated_item = self.db.merge(item_data)
        self.db.commit()
        return updated_item


# Dependency
def get_action_repo():
    repo = ActionAlchemyRepository()
    try:
        yield repo
    finally:
        pass

