import time
from collections import defaultdict, deque
from secrets import token_urlsafe
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

RULES={
 '/api/auth/login':(8,60),'/api/auth/register':(5,300),
 '/api/captcha/new':(30,60),'/api/uploads':(10,300),'/api/deposits':(8,60),
 '/api/withdrawals':(6,60),'/api/daily-quiz/answer':(15,60),
}

class SecurityMiddleware(BaseHTTPMiddleware):
 def __init__(self,app): super().__init__(app);self.hits=defaultdict(deque)
 async def dispatch(self,request:Request,call_next):
  request_id=request.headers.get('x-request-id') or token_urlsafe(10)
  path=request.url.path
  if path in RULES:
   limit,window=RULES[path];forwarded=request.headers.get('x-forwarded-for','');ip=(forwarded.split(',')[0].strip() if forwarded else request.client.host if request.client else 'unknown');key=f'{ip}:{path}';now=time.monotonic();q=self.hits[key]
   while q and q[0]<=now-window:q.popleft()
   if len(q)>=limit:return JSONResponse({'detail':'Too many requests. Please wait and try again.','request_id':request_id},429,headers={'Retry-After':str(max(1,int(window-(now-q[0]))))})
   q.append(now)
  response=await call_next(request)
  response.headers['X-Request-ID']=request_id
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['X-Frame-Options']='DENY'
  response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
  response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
  if path.startswith('/api/'):
   response.headers['Cache-Control']='no-store'
  else:
   response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; font-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
  if request.url.scheme=='https':response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
  return response
