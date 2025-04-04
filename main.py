from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy import text
from models import Organization, AdminUser
from database import get_db, master_engine, Base
from passlib.context import CryptContext
import jwt
import datetime
import asyncpg
import os

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
SECRET_KEY = "1234"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# start....
async def init_db():
    async with master_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def startup():
    await init_db()


# pass
def hash_password(password: str):
    return pwd_context.hash(password)


# pass verify
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# JWT
def create_jwt_token(username: str, db_url: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({"sub": username, "exp": expiration, "db_url": db_url}, SECRET_KEY, algorithm="HS256")
    return token


# user token
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        db_url = payload["db_url"]

        result = await db.execute(select(AdminUser).where(AdminUser.email == payload["sub"]))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user, db_url
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/org/create")
async def create_organization(org_name: str, email: str, password: str, db: AsyncSession = Depends(get_db)):
    db_name = f"{org_name.lower()}_db"
    db_url = f"postgresql+asyncpg://postgres:admin@127.0.0.1:5433/{db_name}"


    try:
        conn = await asyncpg.connect(database="master_db", user="postgres", password="admin", host="localhost", port="5433")
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        await conn.close()
    except asyncpg.exceptions.DuplicateDatabaseError:
        raise HTTPException(status_code=400, detail="Database already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database creation failed: {str(e)}")


    async with db.begin():
        new_org = Organization(name=org_name, db_url=db_url)
        db.add(new_org)
        await db.flush()

    hashed_password = hash_password(password)


    org_engine = create_async_engine(db_url)
    async with org_engine.begin() as org_conn:
        await org_conn.run_sync(Base.metadata.create_all)


    async with org_engine.connect() as org_db:
        async with org_db.begin():
            await org_db.execute(
                text("INSERT INTO organizations (id, name, db_url) VALUES (:id, :name, :db_url)"),
                {"id": new_org.id, "name": org_name, "db_url": db_url}
            )
            await org_db.execute(
                text("INSERT INTO admin_users (email, password, org_id) VALUES (:email, :password, :org_id)"),
                {"email": email, "password": hashed_password, "org_id": new_org.id}
            )

    return {"message": "Organization and admin created successfully"}

from sqlalchemy.ext.asyncio import create_async_engine

@app.get("/org/get")
async def get_organization(organization_name: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Organization).where(Organization.name == organization_name))
    organization = result.scalars().first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")


    org_db_url = organization.db_url
    async with create_async_engine(org_db_url).connect() as org_db:
        result = await org_db.execute(text("SELECT id, email, password FROM admin_users WHERE org_id = :org_id"), {"org_id": organization.id})
        admin_user = result.mappings().first()

    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found in organization database")

    return {
        "organization_id": organization.id,
        "organization_name": organization.name,
        "admin_email": admin_user["email"],
        "admin_password": admin_user["password"]
    }


@app.post("/admin/login")
async def admin_login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin_user = result.scalars().first()

    if not admin_user or not verify_password(password, admin_user.password):
        raise HTTPException(status_code=400, detail="Invalid admin credentials")

    result = await db.execute(select(Organization).where(Organization.id == admin_user.org_id))
    org = result.scalars().first()

    token = create_jwt_token(email, org.db_url)
    return {"access_token": token, "token_type": "bearer"}



@app.post("/admin/user/create")
async def create_user(user_email: str, password: str, token: str = Depends(oauth2_scheme)):
    current_user, db_url = await get_current_user(token)
    hashed_password = hash_password(password)

    org_engine = create_async_engine(db_url)
    async with org_engine.connect() as org_db:
        async with org_db.begin():
            await org_db.execute(
                text("INSERT INTO admin_users (email, password, org_id) VALUES (:email, :password, :org_id)"),
                {"email": user_email, "password": hashed_password, "org_id": current_user.org_id}
            )

    return {"message": "User created successfully"}
