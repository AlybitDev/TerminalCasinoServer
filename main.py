from fastapi import FastAPI
from pydantic import BaseModel
import json
import uuid

app = FastAPI()

class joinObject(BaseModel):
    name: str
    version: str

with open('whoami.json', 'r') as whoamiFile:
    whoami = json.load(whoamiFile)

version = whoami['version']
print(version)

players = {}

@app.get("/whoami")
async def returnWhoami():
    return whoami

@app.post("/join")
async def join(obj: joinObject):
    if obj.version == version:
        playerUUID = uuid.uuid4()
        print(playerUUID)
        players[playerUUID] = {
            'name': obj.name,
            'room': None
        }
        print(players[playerUUID]['name'])
        print(players[playerUUID]['room'])
        return {"response": "Succesfully joined the server.", "uuid": playerUUID}
    else:
        return {"error": "You have the wrong version, you need version " + version + " to play on this server."}
