from typing import List

from sqlalchemy.exc import IntegrityError
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.openapi.models import APIKey
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

from model import PydanticAction, PydanticNote, PydanticGroup
from repo import ActionAlchemyRepository, NoteAlchemyRepository, GroupAlchemyRepository, \
    get_action_repo, get_note_repo, get_group_repo
from utils.auth import get_api_key

app = FastAPI(swagger_ui_parameters={"tryItOutEnabled":True})


def raiser(value):
    if value is None:
        raise HTTPException(
            status_code=418, detail=f'no rows with such id'
        )
    else:
        return value


@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})


@app.post("/actions/", tags=['ACTIONS'])
def action_create(action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    try:
        out = repo.create_pydantic(action)
        return out
    except IntegrityError:
        return {'detail': f'no parent/group with such id({action.parent_id=},{action.group_id=})'}


@app.get("/actions/{_id}", tags=['ACTIONS'])
def action_fetch_by_id(_id: int, api_key: APIKey = Depends(get_api_key),
                       repo: ActionAlchemyRepository = Depends(get_action_repo)) -> PydanticAction:
    """Возвращает Action со всеми потомками и всей информацией о нём (теги, заметки)
        Ответ:
            {
              "action_id": 1,
              "action": "My first Action",
              "children": [
                {
                  "action_id": 2,
                  "action": "sub Action 1",
                  "children": [
                    {
                      "action_id": 3,
                      "action": "sub sub Action 1",
                      "group": "SOON",
                      "tags": [{"name": "work", "color": "#b0c4de"}],
                      "created_on": "2022-07-26T10:24:49.959Z",
                      "updated_on": "2022-07-26T10:24:49.959Z",
                      "notes": [
                        {
                          "action_id": 3,
                          "type": "image",
                          "payload": "BASE64=="
                        }
                      ]
                    }
                  ],
                  "group": "SOON",
                  "tags": [{"name": "work", "color": "#b0c4de"}],
                  "created_on": "2022-07-26T10:24:49.959Z",
                  "updated_on": "2022-07-26T10:24:49.959Z",
                  "notes": [ ]
                }
              ],
              "group": "SOON",
              "tags": [{"name": "work", "color": "#b0c4de"}],
              "created_on": "2022-07-26T10:24:49.959Z",
              "updated_on": "2022-07-26T10:24:49.959Z",
              "notes": [
                {
                  "action_id": 1,
                  "type": "image",
                  "payload": "BASE64=="
                }
              ]
            }
        """
    return raiser(repo.fetch_by_action_id(_id))


@app.get('/actions/by_name/{name}', tags=['ACTIONS'])
def action_fetch_by_action_name(action_name: str, api_key: APIKey = Depends(get_api_key),
                                repo: ActionAlchemyRepository = Depends(get_action_repo)) -> List[PydanticAction]:
    """Ищет похожие по Action.action (SQL LIKE). Возвращает список Action c sub-Actions первого уровня вложенности
        c limit 20.
         Пример:
            Запрос:
              action_name = 'My first'
            Ответ:
            [
              {
                "action_id": 1,
                "action": "My first Action",
                "children": [
                  {
                    "action_id": 2,
                    "action": "sub Action 1",
                    "group": "SOON",
                    "created_on": "2022-07-26T10:24:49.959Z",
                    "updated_on": "2022-07-26T10:24:49.959Z"
                  },
                  {
                    "action_id": 3,
                    "action": "sub Action 2",
                    "group": "SOON",
                    "created_on": "2022-07-26T10:24:49.959Z",
                    "updated_on": "2022-07-26T10:24:49.959Z"
                  }
                ],
                "group": "SOON",
                "tags": [{"name": "work", "color": "#b0c4de"}],
                "created_on": "2022-07-26T10:24:49.959Z",
                "updated_on": "2022-07-26T10:24:49.959Z"
              }
            ]
            """
    return repo.fetch_by_action_name(action_name)


@app.put('/actions/{action_id}', tags=['ACTIONS'])
def action_update(action_id: int, action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    return raiser(repo.update_pydantic(action, action_id))


@app.post('/notes/', tags=['NOTES'])
def note_create(note: PydanticNote, api_key: APIKey = Depends(get_api_key),
                repo: NoteAlchemyRepository = Depends(get_note_repo)):
    try:
        out = repo.create_pydantic(note)
        return out
    except IntegrityError:
        return {'detail': f'no action with such id({note.action_id=})'}


@app.get('/notes/{_id}', tags=['NOTES'])
def note_fetch_by_id(_id: int, api_key: APIKey = Depends(get_api_key),
                     repo: NoteAlchemyRepository = Depends(get_note_repo)):
    return raiser(repo.note_fetch_by_id(_id))


@app.put('/notes/{_id}', tags=['NOTES'])
def note_update(_id: int, note: PydanticNote, api_key: APIKey = Depends(get_api_key),
                     repo: NoteAlchemyRepository = Depends(get_note_repo)):
    return raiser(repo.update_pydantic(note, _id))


@app.delete('/notes/delete/{_id}', tags=['NOTES'])
def note_delete(_id: int, api_key: APIKey = Depends(get_api_key),
                repo: NoteAlchemyRepository = Depends(get_note_repo)):
    return raiser(repo.note_delete(_id))


@app.post('/groups/', tags=['GROUPS'])
def group_create(group: PydanticGroup, api_key: APIKey = Depends(get_api_key),
                 repo: GroupAlchemyRepository = Depends(get_group_repo)):
    return repo.create_pydantic(group)


@app.get('/groups/read', tags=['GROUPS'])
def fetch_all_groups(api_key: APIKey = Depends(get_api_key),
                     repo: GroupAlchemyRepository = Depends(get_group_repo)):
    return repo.fetch_all_groups()


@app.put('/groups/{_id}', tags=['GROUPS'])
def group_update(_id: int, group: PydanticGroup, api_key: APIKey = Depends(get_api_key),
                 repo: GroupAlchemyRepository = Depends(get_group_repo)):
    return raiser(repo.update_pydantic(group, _id))


@app.delete('/groups/delete/{_id}', tags=['GROUPS'])
def group_delete(_id: int, api_key : APIKey = Depends(get_api_key),
                 repo: GroupAlchemyRepository = Depends(get_group_repo)):
    return raiser(repo.group_delete(_id))


if __name__ == '__main__':
    uvicorn.run("__main__:app", host="127.0.0.1", port=8220, reload=True)
