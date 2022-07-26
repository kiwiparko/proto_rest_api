import yaml
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

from model import PydanticAction, Action

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

    def fetch_by_id(self, _id):
        return self.db.query(Action).filter(Action.id == _id).first()

    def fetch_by_action(self, action):
        return self.db.query(Action).filter(Action.action == action).first()

    def fetch_all(self, skip: int = 0, limit: int = 100):
        return ( self.db.query(Action)
                 .offset(skip)
                 .limit(limit)
                 .order_by(desc(Action.updated_on))
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

