from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import shutil
from jose import jwt, JWTError
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)

# JWT and Password configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Mount uploads directory for serving files (use /api/uploads for proper routing)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    role: str = "EMISOR_RECLAMO"  # ADMIN or EMISOR_RECLAMO
    linea_asignada: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    linea_asignada: Optional[str]
    created_at: datetime

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AdminChangePasswordRequest(BaseModel):
    new_password: str

class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    linea_asignada: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    reclamo_id: str
    reclamo_numero: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Invitation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password: str
    linea_asignada: Optional[str] = None
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))

class InvitationCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    linea_asignada: Optional[str] = None

class InvitationResponse(BaseModel):
    id: str
    token: str
    username: str
    email: str
    linea_asignada: Optional[str]
    invitation_link: str
    expires_at: datetime

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    author: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Reclamo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero_reclamo: str
    linea: str
    categoria: str
    sector_estacion: str
    descripcion: str
    archivos: List[str] = []
    estado: str = "Pendiente"
    responsable: Optional[str] = None
    comentarios: List[dict] = []
    creator_id: Optional[str] = None  # ID del usuario que creó el reclamo
    creator_username: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_cierre: Optional[datetime] = None
    solucion: Optional[str] = None
    responsable_cierre: Optional[str] = None

class ReclamoCreate(BaseModel):
    linea: str
    categoria: str
    sector_estacion: str
    descripcion: str

class ReclamoUpdate(BaseModel):
    estado: Optional[str] = None
    responsable: Optional[str] = None
    solucion: Optional[str] = None
    responsable_cierre: Optional[str] = None

class CommentCreate(BaseModel):
    text: str
    author: str

class EstadisticasResponse(BaseModel):
    total_reclamos: int
    reclamos_por_linea: dict
    reclamos_por_categoria: dict
    reclamos_por_estado: dict
    tiempo_promedio_resolucion: Optional[float]
    reclamos_por_mes: dict

# Password and JWT utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def create_notification(user_id: str, reclamo_id: str, reclamo_numero: str, message: str):
    notification = Notification(
        user_id=user_id,
        reclamo_id=reclamo_id,
        reclamo_numero=reclamo_numero,
        message=message
    )
    doc = notification.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.notifications.insert_one(doc)

# Generate reclamo number
def generar_numero_reclamo(linea: str, categoria: str, contador: int) -> str:
    categoria_map = {
        "Condiciones de trabajo": "CON",
        "Faltante de materiales o elementos de seguridad": "MAT",
        "Higiene y salubridad": "HIG",
        "Seguridad y prevención": "SEG",
        "Personal y recursos humanos": "PER",
        "Conflictos o situaciones laborales": "LAB",
        "Otros reclamos gremiales": "OTR"
    }
    codigo_cat = categoria_map.get(categoria, "OTR")
    return f"Línea{linea}-{codigo_cat}-{contador:04d}"

# Routes
@api_router.get("/")
async def root():
    return {"message": "Sistema de Reclamos Gremiales UTA"}

# Authentication endpoints (auto-registro eliminado)

@api_router.get("/admin/access", response_model=TokenResponse)
async def admin_access():
    """Acceso directo para administrador sin credenciales"""
    # Buscar usuario admin
    admin_user = await db.users.find_one({"role": "ADMIN"}, {"_id": 0, "password_hash": 0})
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Create access token
    access_token = create_access_token(data={"sub": admin_user["id"]})
    
    if isinstance(admin_user['created_at'], str):
        admin_user['created_at'] = datetime.fromisoformat(admin_user['created_at'])
    
    user_response = UserResponse(**admin_user)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is disabled")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    if isinstance(user['created_at'], str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    user_response = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        linea_asignada=user.get("linea_asignada"),
        created_at=user["created_at"]
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    if isinstance(current_user['created_at'], str):
        current_user['created_at'] = datetime.fromisoformat(current_user['created_at'])
    
    return UserResponse(**current_user)

@api_router.patch("/users/me/password")
async def change_own_password(password_data: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    # Get user with password hash
    user = await db.users.find_one({"id": current_user["id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    if password_data.new_password == password_data.current_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")
    
    # Update password
    new_password_hash = get_password_hash(password_data.new_password)
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    return {"message": "Password changed successfully"}

@api_router.post("/reclamos", response_model=Reclamo)
async def crear_reclamo(input: ReclamoCreate, current_user: dict = Depends(get_current_user)):
    # Verify emisor can only create reclamos for their assigned linea
    if current_user["role"] == "EMISOR_RECLAMO":
        if not current_user.get("linea_asignada"):
            raise HTTPException(status_code=403, detail="No line assigned to this user. Contact administrator.")
        if input.linea != current_user["linea_asignada"]:
            raise HTTPException(status_code=403, detail=f"You can only create claims for line {current_user['linea_asignada']}")
    
    # Get count for numero generation
    count = await db.reclamos.count_documents({"linea": input.linea, "categoria": input.categoria})
    numero = generar_numero_reclamo(input.linea, input.categoria, count + 1)
    
    reclamo_dict = input.model_dump()
    reclamo_dict['numero_reclamo'] = numero
    reclamo_dict['creator_id'] = current_user["id"]
    reclamo_dict['creator_username'] = current_user["username"]
    reclamo_obj = Reclamo(**reclamo_dict)
    
    doc = reclamo_obj.model_dump()
    doc['fecha_creacion'] = doc['fecha_creacion'].isoformat()
    if doc['fecha_cierre']:
        doc['fecha_cierre'] = doc['fecha_cierre'].isoformat()
    
    await db.reclamos.insert_one(doc)
    return reclamo_obj

@api_router.get("/reclamos", response_model=List[Reclamo])
async def obtener_reclamos(
    linea: Optional[str] = None,
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    responsable: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    
    # Filter by role
    if current_user["role"] == "EMISOR_RECLAMO":
        # Only see own reclamos from assigned linea
        query['creator_id'] = current_user["id"]
        if current_user.get("linea_asignada"):
            query['linea'] = current_user["linea_asignada"]
    
    # Apply additional filters
    if linea and current_user["role"] == "ADMIN":
        query['linea'] = linea
    if categoria:
        query['categoria'] = categoria
    if estado:
        query['estado'] = estado
    if responsable:
        query['responsable'] = responsable
    if search:
        query['$or'] = [
            {'numero_reclamo': {'$regex': search, '$options': 'i'}},
            {'descripcion': {'$regex': search, '$options': 'i'}},
            {'sector_estacion': {'$regex': search, '$options': 'i'}}
        ]
    
    reclamos = await db.reclamos.find(query, {"_id": 0}).sort('fecha_creacion', -1).to_list(1000)
    
    for reclamo in reclamos:
        if isinstance(reclamo['fecha_creacion'], str):
            reclamo['fecha_creacion'] = datetime.fromisoformat(reclamo['fecha_creacion'])
        if reclamo.get('fecha_cierre') and isinstance(reclamo['fecha_cierre'], str):
            reclamo['fecha_cierre'] = datetime.fromisoformat(reclamo['fecha_cierre'])
        for comentario in reclamo.get('comentarios', []):
            if isinstance(comentario['timestamp'], str):
                comentario['timestamp'] = datetime.fromisoformat(comentario['timestamp'])
    
    return reclamos

@api_router.get("/reclamos/{reclamo_id}", response_model=Reclamo)
async def obtener_reclamo(reclamo_id: str, current_user: dict = Depends(get_current_user)):
    reclamo = await db.reclamos.find_one({"id": reclamo_id}, {"_id": 0})
    if not reclamo:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    
    # Verify emisor can only see their own reclamos
    if current_user["role"] == "EMISOR_RECLAMO":
        if reclamo.get("creator_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(reclamo['fecha_creacion'], str):
        reclamo['fecha_creacion'] = datetime.fromisoformat(reclamo['fecha_creacion'])
    if reclamo.get('fecha_cierre') and isinstance(reclamo['fecha_cierre'], str):
        reclamo['fecha_cierre'] = datetime.fromisoformat(reclamo['fecha_cierre'])
    for comentario in reclamo.get('comentarios', []):
        if isinstance(comentario['timestamp'], str):
            comentario['timestamp'] = datetime.fromisoformat(comentario['timestamp'])
    
    return reclamo

@api_router.patch("/reclamos/{reclamo_id}", response_model=Reclamo)
async def actualizar_reclamo(reclamo_id: str, update: ReclamoUpdate, current_user: dict = Depends(get_current_user)):
    reclamo = await db.reclamos.find_one({"id": reclamo_id}, {"_id": 0})
    if not reclamo:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    
    # Only admin can update reclamos
    if current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Only administrators can update claims")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update.estado == "Resuelto" and not reclamo.get('fecha_cierre'):
        update_data['fecha_cierre'] = datetime.now(timezone.utc).isoformat()
    
    if update_data:
        await db.reclamos.update_one({"id": reclamo_id}, {"$set": update_data})
    
    updated_reclamo = await db.reclamos.find_one({"id": reclamo_id}, {"_id": 0})
    
    if isinstance(updated_reclamo['fecha_creacion'], str):
        updated_reclamo['fecha_creacion'] = datetime.fromisoformat(updated_reclamo['fecha_creacion'])
    if updated_reclamo.get('fecha_cierre') and isinstance(updated_reclamo['fecha_cierre'], str):
        updated_reclamo['fecha_cierre'] = datetime.fromisoformat(updated_reclamo['fecha_cierre'])
    for comentario in updated_reclamo.get('comentarios', []):
        if isinstance(comentario['timestamp'], str):
            comentario['timestamp'] = datetime.fromisoformat(comentario['timestamp'])
    
    return updated_reclamo

@api_router.post("/reclamos/{reclamo_id}/comentarios")
async def agregar_comentario(reclamo_id: str, comment: CommentCreate, current_user: dict = Depends(get_current_user)):
    reclamo = await db.reclamos.find_one({"id": reclamo_id})
    if not reclamo:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    
    # Verify access
    if current_user["role"] == "EMISOR_RECLAMO":
        if reclamo.get("creator_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    nuevo_comentario = Comment(text=comment.text, author=comment.author)
    comment_dict = nuevo_comentario.model_dump()
    comment_dict['timestamp'] = comment_dict['timestamp'].isoformat()
    
    await db.reclamos.update_one(
        {"id": reclamo_id},
        {"$push": {"comentarios": comment_dict}}
    )
    
    # Create notification if admin responded to emisor's reclamo
    if current_user["role"] == "ADMIN" and reclamo.get("creator_id"):
        await create_notification(
            user_id=reclamo["creator_id"],
            reclamo_id=reclamo_id,
            reclamo_numero=reclamo["numero_reclamo"],
            message=f"El administrador ha respondido a tu reclamo {reclamo['numero_reclamo']}"
        )
    
    return {"message": "Comentario agregado", "comentario": comment_dict}

@api_router.post("/reclamos/{reclamo_id}/archivos")
async def subir_archivo(reclamo_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    reclamo = await db.reclamos.find_one({"id": reclamo_id})
    if not reclamo:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    
    # Verify access
    if current_user["role"] == "EMISOR_RECLAMO":
        if reclamo.get("creator_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Save file
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = UPLOADS_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/api/uploads/{filename}"
    
    await db.reclamos.update_one(
        {"id": reclamo_id},
        {"$push": {"archivos": file_url}}
    )
    
    return {"message": "Archivo subido", "url": file_url}

@api_router.delete("/reclamos/{reclamo_id}")
async def eliminar_reclamo(reclamo_id: str, current_admin: dict = Depends(get_current_admin)):
    result = await db.reclamos.delete_one({"id": reclamo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    return {"message": "Reclamo eliminado"}

# Notifications endpoints
@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort('created_at', -1).to_list(100)
    
    for notif in notifications:
        if isinstance(notif['created_at'], str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    
    return notifications

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@api_router.get("/notifications/unread/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": current_user["id"], "is_read": False})
    return {"count": count}

# Invitation endpoints (Admin only)
@api_router.post("/invitations/create", response_model=InvitationResponse)
async def create_invitation(invitation_data: InvitationCreate, current_admin: dict = Depends(get_current_admin)):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": invitation_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": invitation_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create invitation
    invitation = Invitation(
        username=invitation_data.username,
        email=invitation_data.email,
        password=invitation_data.password,  # Store plain password for invitation
        linea_asignada=invitation_data.linea_asignada
    )
    
    doc = invitation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['expires_at'] = doc['expires_at'].isoformat()
    
    await db.invitations.insert_one(doc)
    
    # Generate invitation link
    base_url = os.environ.get('FRONTEND_URL', 'https://metrofix-1.preview.emergentagent.com')
    invitation_link = f"{base_url}/invitacion/{invitation.token}"
    
    return InvitationResponse(
        id=invitation.id,
        token=invitation.token,
        username=invitation.username,
        email=invitation.email,
        linea_asignada=invitation.linea_asignada,
        invitation_link=invitation_link,
        expires_at=invitation.expires_at
    )

@api_router.get("/invitations/{token}")
async def get_invitation(token: str):
    invitation = await db.invitations.find_one({"token": token}, {"_id": 0})
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check expiration
    expires_at = invitation['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": invitation['username']})
    user_exists = existing_user is not None
    
    return {
        "username": invitation['username'],
        "email": invitation['email'],
        "password": invitation['password'],  # Include password for display
        "linea_asignada": invitation.get('linea_asignada'),
        "expires_at": invitation['expires_at'],
        "user_exists": user_exists  # Indicate if user already registered
    }

@api_router.post("/invitations/{token}/accept", response_model=TokenResponse)
async def accept_invitation(token: str):
    invitation = await db.invitations.find_one({"token": token}, {"_id": 0})
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check expiration
    expires_at = invitation['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Invitation expired")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": invitation['username']}, {"_id": 0})
    
    if existing_user:
        # User already exists, just authenticate them
        if isinstance(existing_user['created_at'], str):
            existing_user['created_at'] = datetime.fromisoformat(existing_user['created_at'])
        
        # Create access token
        access_token = create_access_token(data={"sub": existing_user["id"]})
        
        user_response = UserResponse(
            id=existing_user["id"],
            username=existing_user["username"],
            email=existing_user["email"],
            role=existing_user["role"],
            linea_asignada=existing_user.get("linea_asignada"),
            created_at=existing_user["created_at"]
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    
    # Create new user
    user = User(
        username=invitation['username'],
        email=invitation['email'],
        password_hash=get_password_hash(invitation['password']),
        role="EMISOR_RECLAMO",
        linea_asignada=invitation.get('linea_asignada')
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    # Mark invitation as used (for tracking purposes only)
    await db.invitations.update_one({"token": token}, {"$set": {"used": True}})
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        linea_asignada=user.linea_asignada,
        created_at=user.created_at
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/invitations")
async def get_invitations(current_admin: dict = Depends(get_current_admin)):
    invitations = await db.invitations.find({}, {"_id": 0}).sort('created_at', -1).to_list(100)
    
    for inv in invitations:
        if isinstance(inv['created_at'], str):
            inv['created_at'] = datetime.fromisoformat(inv['created_at'])
        if isinstance(inv['expires_at'], str):
            inv['expires_at'] = datetime.fromisoformat(inv['expires_at'])
    
    return invitations

# User management endpoints (Admin only)
@api_router.post("/users/create", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_admin: dict = Depends(get_current_admin)):
    # Check if username exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role="EMISOR_RECLAMO"
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        linea_asignada=user.linea_asignada,
        created_at=user.created_at
    )

@api_router.get("/users")
async def get_users(current_admin: dict = Depends(get_current_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    for user in users:
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return users

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_admin: dict = Depends(get_current_admin)):
    # Cannot delete self
    if user_id == current_admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@api_router.patch("/users/{user_id}/assign-line")
async def assign_line_to_user(user_id: str, linea: str, current_admin: dict = Depends(get_current_admin)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"linea_asignada": linea}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Line {linea} assigned to user"}

@api_router.patch("/users/{user_id}/role")
async def change_user_role(user_id: str, role: str, current_admin: dict = Depends(get_current_admin)):
    if role not in ["ADMIN", "EMISOR_RECLAMO"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Role updated to {role}"}

@api_router.get("/estadisticas", response_model=EstadisticasResponse)
async def obtener_estadisticas(current_user: dict = Depends(get_current_user)):
    query = {}
    
    # Filter by role
    if current_user["role"] == "EMISOR_RECLAMO":
        query['creator_id'] = current_user["id"]
        if current_user.get("linea_asignada"):
            query['linea'] = current_user["linea_asignada"]
    
    reclamos = await db.reclamos.find(query, {"_id": 0}).to_list(10000)
    
    total = len(reclamos)
    
    # Reclamos por línea
    por_linea = {}
    for r in reclamos:
        linea = r['linea']
        por_linea[linea] = por_linea.get(linea, 0) + 1
    
    # Reclamos por categoría
    por_categoria = {}
    for r in reclamos:
        cat = r['categoria']
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
    
    # Reclamos por estado
    por_estado = {}
    for r in reclamos:
        estado = r['estado']
        por_estado[estado] = por_estado.get(estado, 0) + 1
    
    # Tiempo promedio de resolución
    tiempos = []
    for r in reclamos:
        if r.get('fecha_cierre') and r['estado'] == 'Resuelto':
            fecha_creacion = r['fecha_creacion']
            fecha_cierre = r['fecha_cierre']
            if isinstance(fecha_creacion, str):
                fecha_creacion = datetime.fromisoformat(fecha_creacion)
            if isinstance(fecha_cierre, str):
                fecha_cierre = datetime.fromisoformat(fecha_cierre)
            dias = (fecha_cierre - fecha_creacion).days
            tiempos.append(dias)
    
    tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else None
    
    # Reclamos por mes
    por_mes = {}
    for r in reclamos:
        fecha = r['fecha_creacion']
        if isinstance(fecha, str):
            fecha = datetime.fromisoformat(fecha)
        mes_key = fecha.strftime('%Y-%m')
        por_mes[mes_key] = por_mes.get(mes_key, 0) + 1
    
    return EstadisticasResponse(
        total_reclamos=total,
        reclamos_por_linea=por_linea,
        reclamos_por_categoria=por_categoria,
        reclamos_por_estado=por_estado,
        tiempo_promedio_resolucion=tiempo_promedio,
        reclamos_por_mes=por_mes
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()