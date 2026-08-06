import json
from fastapi import WebSocket
class Hub:
 def __init__(self): self.clients:dict[WebSocket,bool]={}
 async def connect(self,ws,is_admin=False): await ws.accept(); self.clients[ws]=is_admin
 def disconnect(self,ws): self.clients.pop(ws,None)
 async def publish(self,event,payload,admin_only=False):
  dead=[]
  for ws,is_admin in list(self.clients.items()):
   if admin_only and not is_admin: continue
   try: await ws.send_text(json.dumps({'event':event,'payload':payload}))
   except Exception: dead.append(ws)
  for ws in dead: self.clients.pop(ws,None)
hub=Hub()
