from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import json
import uuid
import base_repr
import mmh3
import threading
import time

app = FastAPI()

with open('whoami.json', 'r') as whoamiFile:
    whoami = json.load(whoamiFile)

version = whoami['version']

players = {}

rooms = {}

roomplayers = {}

def getKeyByValue(d, value):
    for key, val in d.items():
        if val == value:
            return key
    return None

def createRoomCode(uuid):
    return str(base_repr.int_to_repr(mmh3.hash(uuid, 0, False), base=62))

def countdown(room):
    countdown = rooms[room]['countdown']

    while not countdown == 5:
        time.sleep(5)
        countdown = countdown - 5
        rooms[room]['countdown'] = countdown

    while not countdown == 0:
        time.sleep(1)
        countdown = countdown - 1
        rooms[room]['countdown'] = countdown

    rooms[room]['countdown'] = countdown

@app.get("/whoami")
async def returnWhoami():
    return whoami

class joinObj(BaseModel):
    name: str
    version: str

@app.post("/join")
async def join(obj: joinObj):
    if obj.version == version:
        playerUUID = str(uuid.uuid4())
        players[playerUUID] = {
            'name': obj.name,
            'room': None,
            'money': None
        }
        return {"response": "Succesfully joined the server.", "uuid": playerUUID}
    else:
        return {"error": "You have the wrong version, you need version " + version + " to play on this server."}

class createRoomObj(BaseModel):
    uuid: str
    game: int
    money: int

@app.post("/createroom")
async def createRoom(obj: createRoomObj):
    roomCode = createRoomCode(obj.uuid)
    players[obj.uuid]['room'] = roomCode
    players[obj.uuid]['money'] = obj.money
    rooms[roomCode] = {
        'game': obj.game,
        'countdown': None,
        'started': False,
        'money': obj.money,
        'players': "1",
        '1': obj.uuid,
        '2': None,
        '3': None,
        '4': None,
        '5': None,
        '6': None,
        '7': None
    }
    return {"response": "Succesfully created a room.", "roomcode": roomCode}

class joinRoomObj(BaseModel):
    uuid: str
    room: str

@app.post("/joinroom")
async def joinRoom(obj: joinRoomObj):
    if obj.room in rooms:
        playersInRoom = int(rooms[obj.room]['players'])
        if playersInRoom == 7:
            return {"response": "This room is full."}
        else:
            nextPlayerInRoom = str(playersInRoom + 1)
            rooms[obj.room][nextPlayerInRoom] = obj.uuid
            rooms[obj.room]['players'] = nextPlayerInRoom
            players[obj.uuid]['room'] = obj.room
            players[obj.uuid]['money'] = rooms[obj.room]['money']
            return {"response": "Joined room " + obj.room + ". There is/are " + nextPlayerInRoom + " player(s) in this room."}
    else:
        return {"error": "A room with this code doesn't exist."}

class leaveRoomObj(BaseModel):
    uuid: str

@app.post("/leaveroom")
async def leaveRoom(obj: leaveRoomObj):
    if obj.uuid in players:
        if players[obj.uuid]['room'] != None:
            playerRoom = players[obj.uuid]['room']
            playerKeyInt = int(getKeyByValue(rooms[playerRoom], obj.uuid))

            while playerKeyInt < 7:
                rooms[playerRoom][str(playerKeyInt)] = rooms[playerRoom][str(playerKeyInt + 1)]
                playerKeyInt = playerKeyInt + 1

            rooms[playerRoom]['players'] = str(int(rooms[playerRoom]['players']) - 1)
            players[obj.uuid]['room'] = None
            players[obj.uuid]['money'] = None

            return {"response": "Succesfully left room " + playerRoom + "."}
        else:
            return {"error": "You aren't in a room."}
    else:
        return {"error": "You need to register."}

class roomPlayersObj(BaseModel):
    uuid: str

@app.post("/roomplayers")
async def roomPlayers(obj: roomPlayersObj):
    if obj.uuid in players:
        if players[obj.uuid]['room'] != None:
            playerRoom = players[obj.uuid]['room']
            playersInRoomPlusOne = int(rooms[playerRoom]['players']) + 1

            roomplayers[playerRoom] = {'players': rooms[playerRoom]['players']}

            for key in range(1, playersInRoomPlusOne):
                key = str(key)
                player = rooms[playerRoom][key]
                if key == "1":
                    playerName = players[player]['name'] + " (Teamleader)"
                else:
                    playerName = players[player]['room']
                roomplayers[playerRoom][key] = playerName

            return roomplayers[playerRoom]
        else:
            return {"error": "You aren't in a room."}
    else:
        return {"error": "You need to register."}

#@app.websocket("/room")
#async def room(ws: WebSocket):
#    await ws.accept()
#    uuid = await ws.receive_text()
#    if uuid in players:
#        playerRoom = players[uuid]['room']
#        if playerRoom != None:
#            inRoom = True
#            while inRoom == True:
#                
#        else:
#            await ws.send_text("error: You aren't in a room.")
#    else:
#        await ws.send_text("error: You need to register.")

@app.websocket("/startgame")
async def startGame(ws: WebSocket):
    await ws.accept()
    uuid = await ws.receive_text()
    if uuid in players:
        playerRoom = players[uuid]['room']
        if playerRoom != None:
            if getKeyByValue(playerRoom, uuid) == "1":
                rooms[playerRoom]['countdown'] = 30
                await ws.send_text("Succesfully started the countdown.")
                await ws.send_text("30 seconds")
                countdown = rooms[playerRoom]['countdown']

                while not countdown == 5:
                    time.sleep(5)
                    countdown = countdown - 5
                    rooms[playerRoom]['countdown'] = countdown

                while not countdown == 0:
                    time.sleep(1)
                    countdown = countdown - 1
                    rooms[playerRoom]['countdown'] = countdown

                rooms[playerRoom]['countdown'] = countdown
            else:
                await ws.send_text("error: You aren't the teamleader.")
        else:
            await ws.send_text("error: You aren't in a room.")
    else:
        await ws.send_text("error: You need to register.")

@app.websocket("/game"):
async def game(ws: WebSocket):
    await ws.accept()
    uuid = await ws.receive_text()
    if uuid in players:
        playerRoom = players[uuid]['room']
        if playerRoom != None:
            pass
        else:
            await ws.send_text("error: You aren't in a room.")
    else:
        await ws.send_text("error: You need to register.")
