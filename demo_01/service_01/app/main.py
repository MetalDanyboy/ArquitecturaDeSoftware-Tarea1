import logging

import random
from time import sleep
from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()
mongodb_client = MongoClient("demo_01_service_01_mongodb", 27017)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                    filename="/var/log/service_01.log")

logger = logging.getLogger(__name__)

class Player(BaseModel):
    id: str | None = None
    name: str
    age: int
    number: int
    team_id: str | None = None
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


@app.get("/players",
         response_model=list[Player])
def players_all(team_id: str | None = None):
    """Prueba"""
    logger.info(f"Getting all players (team_id: {team_id})")
    filters = {}

    sleep(3)

    if team_id:
        filters["team_id"] = team_id

    return [Player(**player) for player in mongodb_client.service_01.players.find(filters)]


@app.get("/players/{player_id}")
def players_get(player_id: str):
    return Player(**mongodb_client.service_01.players.find_one({"_id": ObjectId(player_id)}))


@app.delete("/players/{player_id}")
def players_delete(player_id: str):
    mongodb_client.service_01.players.delete_one(
        {"_id": ObjectId(player_id)}
    )
    return "ok"


@app.post("/players")
def players_create(player: Player):
    inserted_id = mongodb_client.service_01.players.insert_one(
        player.dict()
    ).inserted_id

    new_player = Player(
        **mongodb_client.service_01.players.find_one(
            {"_id": ObjectId(inserted_id)}
        )
    )

    logger.info(f"✨ New player created: {new_player}")

    return new_player

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
        if random.random() < 0.4:
            logger.info(f"🆗 Log en Servicio 02: La hora es {now.time()}")
        elif random.random() < 0.7:
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




        
