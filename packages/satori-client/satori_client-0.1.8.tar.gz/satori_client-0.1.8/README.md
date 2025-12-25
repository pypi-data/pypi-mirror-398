# 📚 Satori Python SDK

This library allows you to easily and efficiently interact with the Satori database via WebSockets, supporting CRUD operations, real-time notifications, and advanced queries.

---

## ✨ Main Features

- **Ultra-fast CRUD operations** ⚡
- **Advanced queries** using `field_array` 🔍
- **Real-time notifications** 📢
- **Graph-like relations** (vertices and references) 🕸️
- **Data encryption and decryption** 🔐

---

## 🚀 Installation

```bash
pip install satori-client
```

Or, if you use the repository directly:

```bash
pip install websockets uuid
```

---

## 🏁 Basic Usage

```python
import asyncio
from satori import Satori

async def main():
    client = Satori(
        username='user',
        password='password',
        host='ws://localhost:8000'
    )
    await client.connect()

asyncio.run(main())
```

---

## 🗃️ CRUD Operations

### Create Data

```python
await client.set({
    'key': 'user:123',
    'data': { 'name': 'John', 'email': 'john@example.com' },
    'type': 'user'
})
```
If you are inserting a vector you must specify data to a [f32] and type to vector

### Read Data

```python
user = await client.get({ 'key': 'user:123' })
```

### Modify a Field

```python
await client.put({
    'key': 'user:123',
    'replace_field': 'name',
    'replace_value': 'Peter'
})
```

### Delete Data

```python
await client.delete({ 'key': 'user:123' })
```

---

## 🧩 Advanced Queries with `field_array` 🔍

You can perform operations on multiple objects that meet certain conditions using the `field_array` field:

```python
await client.get({
    'field_array': [
        { 'field': 'email', 'value': 'john@example.com' }
    ]
})
```

- **`field_array`** is an array of conditions `{ field, value }`.
- You can combine it with `one: True` to get only the first matching result.

---

## 🔔 Real-time Notifications

Receive automatic updates when an object changes:

```python
async def on_update(data):
    print('User updated!', data)

await client.notify('user:123', on_update)
```


---

## 🕸️ Relations and Graphs

You can create relationships between objects (vertices):

```python
await client.set_vertex({
    'key': 'user:123',
    'vertex': 'friend:456',
    'relation': 'friend',
    'encryption_key': 'secret'
})
```

Traverse the graph with DFS:

```python
await client.dfs({ 'node': 'user:123', 'encryption_key': 'secret' })
```

Get all neighbors of an object:

```python
await client.get_vertex({
    'key': 'user:123',
    'encryption_key': 'secret',
    'relation': 'friends'
})
```

Delete a specific neighbor:

```python
await client.delete_vertex({
    'key': 'user:123',
    'vertex': 'user:512',
    'encryption_key': 'secret'
})
```

---

## 🔐 Encryption and Security

Easily encrypt and decrypt data:

```python
await client.encrypt({ 'key': 'user:123', 'encryption_key': 'secret' })
await client.decrypt({ 'key': 'user:123', 'encryption_key': 'secret' })
```

---

## 📦 Array Manipulation Methods

Below are the available methods to manipulate arrays in the Satori database using the Python client:

### 🔹 push
Adds a value to an existing array in an object.
```python
await client.push({ 'key': 'user:123', 'array': 'friends', 'value': 'user:456' })
```
- **key**: Object key.
- **array**: Name of the array.
- **value**: Value to add.

### 🔹 pop
Removes the last element from an array in an object.
```python
await client.pop({ 'key': 'user:123', 'array': 'friends' })
```
- **key**: Object key.
- **array**: Name of the array.

### 🔹 splice
Modifies an array in an object (for example, to cut or replace elements).
```python
await client.splice({ 'key': 'user:123', 'array': 'friends' })
```
- **key**: Object key.
- **array**: Name of the array.

### 🔹 remove
Removes a specific value from an array in an object.
```python
await client.remove({ 'key': 'user:123', 'array': 'friends', 'value': 'user:456' })
```
- **key**: Object key.
- **array**: Name of the array.
- **value**: Value to remove.


---


## 🤖 AI Methods
Satori has AI features integrated that boost developers productivity. 

### 🔹 set_middleware
Make the LLM analyze incoming querys and decide if it must reject them, accept them or modify them.
```rust
await client.set_middleware({
    "operation": "SET",
    "middleware": "Only accept requests that have the amount field specified, and convert its value to dollars"
});
```

### 🔹 ann
Perform an Aproximate Nearest Neighbors search
```python
await client.ann({'key' : 'user:123', 'top_k' : '5'}); #you can specify vector instead of key
```
- **key**: Source object key.
- **vector**: Vector of f32 instead of key
- **top_k**: Number of nearest neighbors to return

### 🔹 query
Make querys in natural language
```python
await client.query({'query' : 'Insert the value 5 into the grades array of user:123', 'backend' : 'openai:gpt-4o-mini'});
```
- **query**: Your query in natural language.
- **ref**: The LLM backend. Must be `openai:model-name` or `ollama:model-name`, if not specified `openai:gpt-4o-mini` will be used as default. If you're using OpenAI as your backend you must specify the `OPENAI_API_KEY` env variable.

### 🔹 ask
Ask question about your data in natural language
```python
await client.ask({'question' : 'How many user over 25 years old do we have. Just return the number.', 'backend' : 'openai:gpt-4o-mini'});
```
- **question**: Your question in natural language.
- **ref**: The LLM backend. Must be `openai:model-name` or `ollama:model-name`, if not specified `openai:gpt-4o-mini` will be used as default. If you're using OpenAI as your backend you must specify the `OPENAI_API_KEY` env variable.

## Analytics

### 🔹 get_operations

Returns all operations executed on the database.

### 🔹 get_access_frequency

Returns the number of times an object has been queried or accessed.
```python
await client.get_access_frequency({'key' : 'jhon'})
```

## Schema Class (Data Model) 

You can use the `Schema` class to model your data in an object-oriented way:

```python
from satori_client import Satori, Schema
import asyncio

async def main():
    satori = Satori("username", "password", "ws://localhost:1234")
    await satori.connect()

    user = Schema(satori, "user", key="my_key", body={"name": "Anna"})
    await user.set()

asyncio.run(main())
```

It includes useful methods such as:

- `set`, `delete`, `encrypt`, `decrypt`, `set_vertex`, `get_vertex`, `delete_vertex`, `dfs`

- Array methods: `push`, `pop`, `splice`, `remove`

## 📝 Complete Example

```python
import asyncio
from satori import Satori

async def main():
    client = Satori(username='user', password='password', host='ws://localhost:8000')
    await client.connect()
    await client.set({
        'key': 'user:1',
        'data': { 'name': 'Carlos', 'age': 30 },
        'type': 'user'
    })
    async def on_update(data):
        print('Real-time update:', data)
    await client.notify('user:1', on_update)

asyncio.run(main())
```



---

## 🧠 Key Concepts

- **key**: Unique identifier of the object.
- **type**: Object type (e.g., 'user').
- **field_array**: Advanced filters for bulk operations.
- **notifications**: Subscription to real-time changes.
- **vertices**: Graph-like relationships between objects.

---

## Responses
All responses obbey the following pattern:

```ts
{
  data: any //the requested data if any
  message: string //status message
  type: string //SUCCESS || ERROR
}
```

AI responses obbey a different patern:
## ask
```ts
{
  response: string //response to the question
}
```

## query
```ts
{
  result: string //response from the operation made in the db
  status: string //status
}
```

## ann
```ts
{
  results: array //response from the operation made in the db
}
```

## 💬 Questions or Suggestions?

Feel free to open an issue or contribute!
With ❤️ from the Satori team.
