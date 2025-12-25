# schema.py

import uuid
import json

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
