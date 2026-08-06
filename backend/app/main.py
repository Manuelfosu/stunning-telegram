import os
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import inspect,text
from .config import ALLOWED_ORIGINS,UPLOAD_DIR
from .database import Base,engine,SessionLocal
from .deps import admin_user
from .models import User
from .security import decode_token
from .realtime import hub
from .routers.api import r
from .seed import seed
from .security_middleware import SecurityMiddleware
Base.metadata.create_all(engine)
# Lightweight forward migration for existing persistent SQLite/Postgres deployments.
with engine.begin() as connection:
 columns={c['name'] for c in inspect(connection).get_columns('users')}
 if 'token_version' not in columns:
  connection.execute(text('ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0'))
 ad_columns={c['name'] for c in inspect(connection).get_columns('ads')}
 if 'approved_at' not in ad_columns:
  connection.execute(text('ALTER TABLE ads ADD COLUMN approved_at DATETIME NULL'))
  connection.execute(text("UPDATE ads SET approved_at=created_at WHERE status='approved'"))
app=FastAPI(title='SSGA HOLDINGS API',version='4.12.0')
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_methods=['*'],allow_headers=['*'])
app.add_middleware(SecurityMiddleware)
os.makedirs(UPLOAD_DIR,exist_ok=True);app.mount('/uploads',StaticFiles(directory=UPLOAD_DIR),name='uploads');app.include_router(r)
@app.on_event('startup')
def startup():
 db=SessionLocal()
 try:seed(db)
 finally:db.close()
@app.websocket('/ws/live')
@app.websocket('/ws/admin')
async def live_socket(ws:WebSocket,token:str=''):
 payload=decode_token(token);uid=payload.get('sub') if payload else None;db=SessionLocal();u=db.get(User,int(uid)) if uid and str(uid).isdigit() else None;valid=bool(u and u.is_active and int(payload.get('ver',0))==int(u.token_version or 0));db.close()
 if not valid:await ws.close(code=4403);return
 await hub.connect(ws,u.is_admin)
 try:
  while True:await ws.receive_text()
 except WebSocketDisconnect:hub.disconnect(ws)
DIST=os.path.realpath(os.path.join(os.path.dirname(__file__),'..','dist'));INDEX=os.path.join(DIST,'index.html')
if os.path.exists(INDEX):
 assets=os.path.join(DIST,'assets')
 if os.path.isdir(assets):app.mount('/assets',StaticFiles(directory=assets),name='assets')
 @app.get('/{path:path}')
 def spa(path:str):
  requested=os.path.realpath(os.path.join(DIST,path))
  inside_dist=requested==DIST or requested.startswith(DIST+os.sep)
  if path and inside_dist and os.path.isfile(requested): return FileResponse(requested)
  if not os.path.splitext(path)[1]: return FileResponse(INDEX)
  raise HTTPException(status_code=404,detail='Asset not found')
