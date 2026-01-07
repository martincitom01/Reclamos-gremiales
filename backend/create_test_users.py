#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_USERS = [
    {"username": "martin", "email": "martin@uta.com", "password": "94017448", "linea": "A"},
    {"username": "Mara", "email": "mara@uta.com", "password": "123456", "linea": "H"},
    {"username": "Luisina", "email": "luisina@uta.com", "password": "123456", "linea": "A"}
]

async def create_users():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]

    for u in TEST_USERS:
        existing = await db.users.find_one({"username": u['username']})
        if existing:
            print(f"Usuario {u['username']} ya existe, saltando")
            continue

        user_doc = {
            "id": str(uuid.uuid4()),
            "username": u['username'],
            "email": u['email'],
            "password_hash": pwd_context.hash(u['password']),
            "role": "EMISOR_RECLAMO",
            "linea_asignada": u['linea'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }

        await db.users.insert_one(user_doc)
        print(f"Usuario {u['username']} creado")

    client.close()

if __name__ == '__main__':
    asyncio.run(create_users())
