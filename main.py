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
    print(action)
    repo.create_pydantic(action, return_pydantic=True)
    return action


@app.get("/actions/{_id}")
def action_fetch_by_id(_id: int, api_key: APIKey = Depends(get_api_key),
                       repo: ActionAlchemyRepository = Depends(get_action_repo)) -> PydanticAction:
    action = repo.fetch_by_action_id(_id)
    return action


@app.get('/actions/by_name/{name}')
def action_fetch_by_action_name(action_name: str, api_key: APIKey = Depends(get_api_key),
                                repo: ActionAlchemyRepository = Depends(get_action_repo)) -> List[PydanticAction]:
    action = repo.fetch_by_action_name(action_name)
    return action


@app.put('/actions/{action_id}')
def action_update(action_id: int, action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    print(action)
    result = repo.update_pydantic(action, action_id)
    return result


if __name__ == '__main__':
    uvicorn.run("__main__:app", host="127.0.0.1", port=8220, reload=True)
