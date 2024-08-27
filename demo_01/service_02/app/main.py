from enum import Enum

import logging
import random
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI()
mongodb_client = MongoClient("demo_01_service_02_mongodb", 27017)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                    filename="/var/log/service_02.log")

logger = logging.getLogger(__name__)

class Player(BaseModel):
    id: str | None = None
    name: str
    age: int
    number: int
    team_id: str | None = None
    description: str = ""


class Country(str, Enum):
    chile = 'Chile'
    portugal = 'Portugal'
    españa = 'España'
    francia = "Francia"


class Team(BaseModel):
    id: str | None = None
    name: str
    country: Country

    description: str = ""

    def __init__(self, **kargs):
        if "_id" in kargs:
            kargs["id"] = str(kargs["_id"])
        BaseModel.__init__(self, **kargs)

class Log(BaseModel):
    message: str
    level: str
    
    def __init__(self, **kargs):
        BaseModel.__init__(self, **kargs)

@app.post("/logs")
def logs_create(log: Log):

    if log.level == "INFO":
        logger.info(log.message)
    elif log.level == "DEBUG":
        logger.debug(log.message)
    elif log.level == "WARNING":
        logger.warning(log.message)
    elif log.level == "ERROR":
        logger.error(log.message)

    return {"status": "ok"}

@app.get("/")
async def root():
    logger.info("👋 Hello world (end-point)!")
    return {"Hello": "World"}


def get_players_of_a_team(team_id) -> list[Player]:
        url = f"http://demo_01_service_01:80/players?team_id={team_id}"
        logger.info(f"🌍 Request [GET] {url}")

        return requests.get(url).json()

@app.get("/teams")
def teams_all(expand: list[str] = Query(default=[])):
    logger.info("Getting all teams")
    teams = [Team(**team).dict()
             for team in mongodb_client.service_02.teams.find({})]

    # n+1 problem...
    if expand and 'players' in expand:
        logger.warning("🚨 n+1 requests...")
        for i, team in enumerate(teams):
            teams[i]["players"] = get_players_of_a_team(team['id'])

    return teams


@app.get("/teams/{team_id}")
def teams_get(team_id: str, expand: list[str] = Query(default=[])):
    logger.info(f"Getting team {team_id}")
    try:
        team = Team(
            **mongodb_client.service_02.teams.find_one({"_id": ObjectId(team_id)})
        ).dict()

        if expand and 'players' in expand:
            team["players"] = get_players_of_a_team(team_id)

        return team
    except:
        logger.error(f"Team {team_id} not found")
        return {"error": "Team not found"}


@app.delete("/teams/{team_id}")
def teams_delete(team_id: str):
    mongodb_client.service_02.teams.delete_one({"_id": ObjectId(team_id)})
    return {"status": "ok"}


@app.post("/teams")
def teams_create(team: Team):
    inserted_id = mongodb_client.service_02.teams.insert_one(
        team.dict()
    ).inserted_id

    new_team = Team(
        **mongodb_client.service_02.teams.find_one(
            {"_id": ObjectId(inserted_id)}
        )
    )

    logger.info(f"✨ New team created: {new_team}")

    return new_team

#log loop every ten seconds
import asyncio
from datetime import datetime
# make stoppable
log_loop_task = None

@app.on_event("startup")
async def startup_event():
    global log_loop_task
    log_loop_task = asyncio.create_task(log_loop())

async def log_loop():
    while True:
        now = datetime.now()
        #import random
        if random.random() < 0.6:
            logger.info(f"🆗 Log en Servicio 02: La hora es {now.time()}")
        elif random.random() < 0.8:
            logger.warning(f"⚠️ Log en Servicio 02: La hora es {now.time()}")
        else:
            logger.error(f"❌ Log en Servicio 02: La hora es {now.time()}")
        await asyncio.sleep(3)

@app.post("/stop_log_loop")
def stop():
    global log_loop_task
    logger.info("🛑 Stopping log loop")
    if log_loop_task is not None and not log_loop_task.done():
        log_loop_task.cancel()
    return {"status": "ok"}

@app.post("/start_log_loop")
async def start():
    logger.info("✅ Starting log loop")  # Añadido icono de check
    global log_loop_task
    if log_loop_task is None or log_loop_task.done():
        log_loop_task = asyncio.create_task(log_loop())
    return {"status": "ok"}



        
