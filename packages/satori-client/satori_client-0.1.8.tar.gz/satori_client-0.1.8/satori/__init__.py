import asyncio
import websockets
import json
import uuid
import subprocess

class Satori:
    def __init__(self, username: str, password: str, host: str):
        self.username = username
        self.password = password
        self.host = host
        self.ws = None
        self.pending = {}
        self.subscriptions = {}

    async def connect(self):
        self.ws = await websockets.connect(self.host, ping_interval=None, ping_timeout=None)
        asyncio.create_task(self.listen())

    async def listen(self):
        async for message in self.ws:
            msg = json.loads(message)
            if msg.get("type") == "notification" and msg.get("key") in self.subscriptions:
                await self.subscriptions[msg["key"]](msg["data"])
            elif msg.get("id") in self.pending:
                fut = self.pending.pop(msg["id"])
                fut.set_result(msg)

    async def send(self, command: str, payload: dict = {}):
        req_id = str(uuid.uuid4())
        msg = {
            "id": req_id,
            "username": self.username,
            "password": self.password,
            "command": command,
            **payload
        }
        future = asyncio.get_event_loop().create_future()
        self.pending[req_id] = future
        await self.ws.send(json.dumps(msg))
        return await future

    async def set(self, payload): return await self.send("SET", payload)
    async def get(self, payload): return await self.send("GET", payload)
    async def put(self, payload): return await self.send("PUT", payload)
    async def delete(self, payload): return await self.send("DELETE", payload)
    async def set_vertex(self, payload): return await self.send("SET_VERTEX", payload)
    async def get_vertex(self, payload): return await self.send("GET_VERTEX", payload)
    async def delete_vertex(self, payload): return await self.send("DELETE_VERTEX", payload)
    async def dfs(self, payload): return await self.send("DFS", payload)
    async def encrypt(self, payload): return await self.send("ENCRYPT", payload)
    async def decrypt(self, payload): return await self.send("DECRYPT", payload)
    async def query(self, payload): return await self.send("QUERY", payload)
    async def push(self, payload): return await self.send("PUSH", payload)
    async def pop(self, payload): return await self.send("POP", payload)
    async def splice(self, payload): return await self.send("SPLICE", payload)
    async def remove(self, payload): return await self.send("REMOVE", payload)

    async def ask(self, payload):
        return await self.send("ASK", payload)

    async def query(self, payload):
        return await self.send("QUERY", payload)

    async def ann(self, payload: dict):
        return await self.send("ANN", payload)


    async def set_middleware(self, payload: dict):
        return await self.send("SET_MIDDLEWARE", payload)


    async def get_operations(self):
        return await self.send("GET_OPERATIONS")


    async def get_access_frequency(self, key):
        return await self.send("GET_ACCESS_FREQUENCY", {"key": key})

    async def notify(self, key, callback):
        self.subscriptions[key] = callback
        await self.send("NOTIFY", {"key": key})

  

class Schema:
    def __init__(self, satori, schema_name: str, body: dict, key: str = None):
        self.satori = satori
        self.schema_name = schema_name
        self.body = body
        self.key = key or str(uuid.uuid4())

    async def set(self):
        return await self.satori.set({
            "key": self.key,
            "data": self.body,
            "type": self.schema_name
        })

    async def delete(self):
        return await self.satori.delete({
            "key": self.key
        })

    async def encrypt(self, encryption_key: str):
        return await self.satori.encrypt({
            "key": self.key,
            "encryption_key": encryption_key
        })

    async def decrypt(self, encryption_key: str):
        return await self.satori.decrypt({
            "key": self.key,
            "encryption_key": encryption_key
        })

    async def set_vertex(self, vertex: str, relation: str, encryption_key: str = None):
        return await self.satori.set_vertex({
            "key": self.key,
            "vertex": vertex,
            "relation": relation,
            "encryption_key": encryption_key
        })

    async def get_vertex(self, encryption_key: str = None):
        return await self.satori.get_vertex({
            "key": self.key,
            "encryption_key": encryption_key
        })

    async def delete_vertex(self, vertex: str, encryption_key: str = None):
        return await self.satori.delete_vertex({
            "key": self.key,
            "vertex": vertex,
            "encryption_key": encryption_key
        })

    async def dfs(self, relation: str = None, encryption_key: str = None):
        return await self.satori.dfs({
            "node": self.key,
            "relation": relation,
            "encryption_key": encryption_key
        })

    async def set_ref(self, ref: str, encryption_key: str = None):
        return await self.satori.set_ref({
            "key": self.key,
            "ref": ref,
            "encryption_key": encryption_key
        })

    async def get_refs(self, encryption_key: str = None):
        return await self.satori.get_refs({
            "key": self.key,
            "encryption_key": encryption_key
        })

    async def delete_refs(self, encryption_key: str = None):
        return await self.satori.delete_refs({
            "key": self.key,
            "encryption_key": encryption_key
        })

    async def push(self, value, array: str, encryption_key: str = None):
        return await self.satori.push({
            "key": self.key,
            "value": value,
            "array": array,
            "encryption_key": encryption_key
        })

    async def pop(self, array: str, encryption_key: str = None):
        return await self.satori.pop({
            "key": self.key,
            "array": array,
            "encryption_key": encryption_key
        })

    async def splice(self, array: str, encryption_key: str = None):
        return await self.satori.splice({
            "key": self.key,
            "array": array,
            "encryption_key": encryption_key
        })

    async def remove(self, value, array: str, encryption_key: str = None):
        return await self.satori.remove({
            "key": self.key,
            "value": value,
            "array": array,
            "encryption_key": encryption_key
        })
