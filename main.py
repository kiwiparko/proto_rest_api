from typing import List

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.openapi.models import APIKey
from starlette.responses import JSONResponse

from model import PydanticAction
from repo import ActionAlchemyRepository, get_action_repo
from utils.auth import get_api_key

app = FastAPI(swagger_ui_parameters={"tryItOutEnabled":True})


@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})


@app.post("/actions/")
def action_create(action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    pass


@app.get("/actions/{_id}")
def action_fetch_by_id(_id: int, api_key: APIKey = Depends(get_api_key),
                       repo: ActionAlchemyRepository = Depends(get_action_repo)) -> PydanticAction:
    """Возвращает Action со всеми потомками и всей информацией о нём (теги, заметки)
    Запрос:
        action_id = 1
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
    action = repo.fetch_by_action_id(_id)
    return action


@app.get('/actions/by_name/{name}')
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
    action = repo.fetch_by_action_name(action_name)
    return action


@app.put('/actions/{action_id}')
def action_update(action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    pass


if __name__ == '__main__':
    uvicorn.run("__main__:app", host="127.0.0.1", port=8220, reload=True)
