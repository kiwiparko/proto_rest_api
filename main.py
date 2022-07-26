from fastapi import FastAPI, Depends
from fastapi.openapi.models import APIKey
from starlette.responses import JSONResponse

from model import PydanticAction
from repo import ActionAlchemyRepository, get_action_repo
from utils.auth import get_api_key

app = FastAPI()


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
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    action = repo.fetch_by_id(_id)
    return action


@app.put('/actions/{action_id}')
def action_update(action: PydanticAction, api_key: APIKey = Depends(get_api_key),
                  repo: ActionAlchemyRepository = Depends(get_action_repo)):
    print(action)
    repo.update(action)
    return action

