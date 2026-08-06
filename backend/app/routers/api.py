import json,random,secrets,string,os,uuid
from datetime import date,datetime,timedelta
from fastapi import APIRouter,Depends,HTTPException,Query,UploadFile,File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func,or_
from sqlalchemy.orm import Session
from ..config import DEFAULTS,CURRENCY,UPLOAD_DIR
from ..database import get_db
from ..deps import current_user,admin_user
from ..domain import move,debit,notify,accrue_today,quiz_complete
from ..models import *
from ..schemas import *
from ..security import create_token,hash_password,verify_password
from ..realtime import hub
r=APIRouter(prefix='/api')

def setting(db,k):
 x=db.get(Setting,k); return x.value if x else DEFAULTS.get(k,'')
def public_user(u):
 return {'id':u.id,'full_name':u.full_name,'phone':u.phone,'balance':u.balance,'withdrawable':round(u.earnings_balance,2),'is_admin':u.is_admin,'email':u.email,'telegram':u.telegram,'referral_code':u.referral_code,'notify_transactions':u.notify_transactions,'notify_marketing':u.notify_marketing,'created_at':u.created_at.isoformat()}
def txn(t): return {'id':t.id,'wallet':t.wallet,'type':t.type,'amount':t.amount,'note':t.note,'created_at':t.created_at.isoformat()}
def inv(i): return {'id':i.id,'package_id':i.package_id,'package_name':i.package_name,'amount':i.amount,'daily_income':i.daily_income,'duration_days':i.duration_days,'days_credited':i.days_credited,'total_credited':i.total_credited,'status':i.status,'progress':round(i.days_credited/max(i.duration_days,1)*100),'created_at':i.created_at.isoformat()}
def dep(d): return {'id':d.id,'amount':d.amount,'momo_number':d.momo_number,'network':d.network,'momo_name':d.momo_name,'status':d.status,'admin_note':d.admin_note,'created_at':d.created_at.isoformat()}
def wd(x): return {'id':x.id,'amount':x.amount,'fee':x.fee,'net_amount':x.net_amount,'momo_number':x.momo_number,'network':x.network,'momo_name':x.momo_name,'status':x.status,'admin_note':x.admin_note,'created_at':x.created_at.isoformat()}
def pkg(p): return {'id':p.id,'name':p.name,'description':p.description,'image_url':p.image_url,'price':p.min_amount,'min_amount':p.min_amount,'max_amount':p.max_amount,'daily_income':p.daily_income,'duration_days':p.duration_days,'status':p.status,'featured':p.featured}
def task(t,done=0): return {'id':t.id,'title':t.title,'description':t.description,'category':t.category,'reward':t.reward,'external_link':t.external_link,'timer_seconds':t.timer_seconds,'daily_limit':t.daily_limit,'completed_today':done,'active':t.active,'available':t.active and done<t.daily_limit}
def mask(phone):
 if len(phone)<7:return phone
 return phone[:5]+'*'*(len(phone)-7)+phone[-2:]
def unique_code(db):
 while True:
  code=''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(7))
  if not db.query(User).filter(User.referral_code==code).first(): return code
def deleted_user(db,u):
 blocked=db.get(BlockedPhone,u.phone) if u else None
 return bool(blocked and blocked.reason.lower().startswith('deleted'))
def active_ad(x): return bool(x and x.status=='approved' and datetime.utcnow()<(x.approved_at or x.created_at)+timedelta(days=max(1,x.duration_days)))
def today_start(): return datetime.combine(date.today(),datetime.min.time())

@r.get('/health')
def health(db:Session=Depends(get_db)):
 db.query(User.id).limit(1).all();return {'status':'ok','service':'SSGA HOLDINGS','database':'connected'}
@r.post('/uploads')
async def upload_image(file:UploadFile=File(...),u:User=Depends(current_user)):
 allowed={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif'}
 if file.content_type not in allowed: raise HTTPException(400,'Only JPG, PNG, WEBP and GIF images are allowed')
 data=await file.read(5*1024*1024+1)
 if len(data)>5*1024*1024: raise HTTPException(413,'Image must be 5 MB or smaller')
 valid=(file.content_type=='image/jpeg' and data.startswith(b'\xff\xd8\xff')) or (file.content_type=='image/png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or (file.content_type=='image/gif' and data[:6] in (b'GIF87a',b'GIF89a')) or (file.content_type=='image/webp' and data.startswith(b'RIFF') and data[8:12]==b'WEBP')
 if not valid: raise HTTPException(400,'The uploaded file is not a valid image')
 os.makedirs(UPLOAD_DIR,exist_ok=True);name=f'{uuid.uuid4().hex}{allowed[file.content_type]}';path=os.path.join(UPLOAD_DIR,name)
 with open(path,'wb') as out: out.write(data)
 return {'url':f'/uploads/{name}','filename':name}
@r.get('/public/config')
def config(db:Session=Depends(get_db)): return {'currency':CURRENCY,'signup_bonus':float(setting(db,'signup_bonus')),'min_deposit':float(setting(db,'min_deposit')),'min_withdrawal':float(setting(db,'min_withdrawal')),'withdrawal_fee':float(setting(db,'withdrawal_fee')),'referral_l1':float(setting(db,'referral_l1')),'referral_l2':float(setting(db,'referral_l2')),'referral_l3':float(setting(db,'referral_l3')),'ad_reward':float(setting(db,'ad_reward')),'telegram_link':setting(db,'telegram_link'),'deposit_disclaimer':setting(db,'deposit_disclaimer')}
@r.get('/captcha/new')
def captcha(db:Session=Depends(get_db)):
 answer=''.join(random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(5)); token=secrets.token_hex(18)
 db.add(Captcha(token=token,answer=answer,expires_at=datetime.utcnow()+timedelta(minutes=5))); db.commit()
 svg=f"""<svg xmlns="http://www.w3.org/2000/svg" width="180" height="54" viewBox="0 0 180 54"><rect width="180" height="54" rx="8" fill="#eef2f6"/><path d="M4 40L176 11M8 14L170 43" stroke="#b9c4d0"/><text x="90" y="36" text-anchor="middle" font-family="Georgia" font-size="26" font-weight="700" letter-spacing="7" fill="#102a43">{answer}</text></svg>"""
 return {'token':token,'svg':svg}
@r.post('/auth/register')
def register(p:RegisterIn,db:Session=Depends(get_db)):
 if p.password!=p.confirm_password: raise HTTPException(400,'Passwords do not match')
 c=db.get(Captcha,p.captcha_token)
 if not c or c.used or c.expires_at<datetime.utcnow() or c.answer.upper()!=p.captcha_answer.upper(): raise HTTPException(400,'CAPTCHA is invalid or expired')
 c.used=True
 if db.get(BlockedPhone,p.phone): raise HTTPException(400,'This phone number is not supported')
 if db.query(User).filter(User.phone==p.phone).first(): raise HTTPException(409,'Phone number already registered')
 ref=None
 if p.referral_code:
  ref=db.query(User).filter(User.referral_code==p.referral_code.strip().upper()).first()
  if not ref: raise HTTPException(400,'Referral code was not found')
 u=User(full_name=p.full_name,phone=p.phone,password_hash=hash_password(p.password),referral_code=unique_code(db),referred_by=ref.id if ref else None)
 db.add(u);db.flush();db.add(Wallet(user_id=u.id,deposit_credit=0,earnings_credit=0));db.flush()
 if ref:db.add(Referral(referrer_id=ref.id,referred_id=u.id,referral_code=p.referral_code.strip().upper()))
 bonus=float(setting(db,'signup_bonus'))
 if bonus: move(db,u,'earnings','bonus',bonus,'Welcome bonus')
 notify(db,u.id,'Welcome to SSGA HOLDINGS',f'Your account is ready. GHS {bonus:.2f} welcome bonus has been credited.','popup')
 db.commit();return {'access_token':create_token(u.id,u.token_version),'token_type':'bearer','user':public_user(u)}
@r.post('/auth/login')
def login(f:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
 phone=''.join(x for x in f.username if x.isdigit() or x=='+');u=db.query(User).filter(User.phone==phone).first()
 if u and not u.is_active: raise HTTPException(400,'Account does not exist')
 if not u or not verify_password(f.password,u.password_hash): raise HTTPException(400,'Invalid phone number or password')
 return {'access_token':create_token(u.id,u.token_version),'token_type':'bearer','user':public_user(u)}
@r.get('/users/me')
def me(u:User=Depends(current_user)): return public_user(u)
@r.patch('/users/me')
def update_me(p:ProfileIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 for k,v in p.model_dump(exclude_unset=True).items(): setattr(u,k,v)
 db.commit();db.refresh(u);return public_user(u)
@r.post('/users/change-password')
def password(p:PasswordIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 if not verify_password(p.current_password,u.password_hash): raise HTTPException(400,'Current password is incorrect')
 if p.new_password!=p.confirm_password: raise HTTPException(400,'New passwords do not match')
 u.password_hash=hash_password(p.new_password);u.token_version=int(u.token_version or 0)+1;db.commit();return {'message':'Password updated securely. Please sign in again.'}

@r.get('/dashboard')
def dashboard(u:User=Depends(current_user),db:Session=Depends(get_db)):
 accrued=accrue_today(db,u);db.commit()
 login_bonus=0.0; _lr=float(setting(db,'login_reward'))
 if _lr>0 and not db.query(LoginReward).filter(LoginReward.user_id==u.id,LoginReward.reward_date==date.today()).first():
  db.add(LoginReward(user_id=u.id,reward_date=date.today(),amount=_lr));move(db,u,'earnings','login_bonus',_lr,'Daily login reward');notify(db,u.id,'Login reward credited',f'GHS {_lr:.2f} daily login reward added to your earnings.');db.commit();login_bonus=_lr
 investments=db.query(Investment).filter(Investment.user_id==u.id).order_by(Investment.created_at.desc()).all()
 recent=db.query(Transaction).filter(Transaction.user_id==u.id).order_by(Transaction.created_at.desc()).limit(8).all()
 alerts=db.query(Notification).filter(Notification.active.is_(True),or_(Notification.target=='all',Notification.user_id==u.id),Notification.type=='dashboard').order_by(Notification.created_at.desc()).limit(3).all()
 return {'balance':u.balance,'earnings':round(u.earnings_balance,2),'deposit_credit':round(u.deposit_balance,2),'active_investments':sum(1 for x in investments if x.status=='active'),'total_income':round(sum(x.amount for x in db.query(Transaction).filter(Transaction.user_id==u.id,Transaction.type=='income').all()),2),'investments':[inv(x) for x in investments[:4]],'transactions':[txn(x) for x in recent],'quiz_complete':quiz_complete(db,u),'login_bonus':round(login_bonus,2),'accrued_now':accrued,'alerts':[{'id':n.id,'title':n.title,'message':n.message} for n in alerts]}
@r.get('/public/recent-withdrawals')
def recent_withdrawals(db:Session=Depends(get_db)):
 rows=(db.query(Withdrawal).join(User,Withdrawal.user_id==User.id).filter(Withdrawal.status.in_(['approved','completed']),User.is_admin.is_(False)).order_by(Withdrawal.created_at.desc()).limit(40).all())
 out=[{'id':f'withdrawal-{x.id}','withdrawal_number':mask(x.momo_number),'amount':round(x.net_amount,2),'at':x.created_at.isoformat(),'source':'verified'} for x in rows]
 display=[
  ('+23357******',50.00),('+23324******',84.00),('+23355******',126.00),('+23320******',158.00),
  ('+23354******',196.00),('+23359******',215.00),('+23326******',248.00),('+23327******',275.00),
  ('+23350******',300.00),('+23325******',72.00),('+23353******',142.00),('+23356******',232.00)
 ]
 seen={x['withdrawal_number'] for x in out}
 out.extend({'id':f'activity-{index}','withdrawal_number':number,'amount':amount,'at':'','source':'activity'} for index,(number,amount) in enumerate(display) if number not in seen)
 return out

@r.get('/packages')
def packages(db:Session=Depends(get_db)): return [pkg(x) for x in db.query(Package).filter(Package.status!='hidden').order_by(Package.featured.desc(),Package.min_amount).all()]
@r.get('/investments')
def investments(u:User=Depends(current_user),db:Session=Depends(get_db)): return [inv(x) for x in db.query(Investment).filter(Investment.user_id==u.id).order_by(Investment.created_at.desc()).all()]
@r.post('/investments')
def invest(p:InvestIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 x=db.get(Package,p.package_id)
 if not x or x.status=='hidden': raise HTTPException(404,'Package not found')
 if x.status!='active': raise HTTPException(400,'This package is currently unavailable')
 price=round(x.min_amount,2)
 if not debit(db,u,'deposit',price,'investment',f'Purchased {x.name}'): raise HTTPException(400,'Insufficient deposit credit')
 daily=round(x.daily_income,2)
 i=Investment(user_id=u.id,package_id=x.id,package_name=x.name,amount=price,daily_income=daily,duration_days=x.duration_days,end_date=date.today()+timedelta(days=x.duration_days));db.add(i)
 # referral commissions
 up=u.referred_by
 for level,key in enumerate(['referral_l1','referral_l2','referral_l3'],1):
  if not up: break
  owner=db.get(User,up); percent=float(setting(db,key)); amount=round(price*percent/100,2);move(db,owner,'earnings','referral',amount,f'Level {level} referral commission');db.add(Commission(user_id=owner.id,from_user_id=u.id,level=level,percent=percent,amount=amount));up=owner.referred_by
 db.commit();return inv(i)

@r.get('/daily-quiz')
def daily_quiz(u:User=Depends(current_user),db:Session=Depends(get_db)):
 q=db.query(DailyQuiz).filter(DailyQuiz.user_id==u.id,DailyQuiz.quiz_date==date.today()).first()
 if not q:
  ids=[x.id for x in db.query(Question).filter(Question.active.is_(True)).all()]
  if len(ids)<5: raise HTTPException(503,'The daily question bank is being prepared')
  chosen=random.Random(f'{u.id}:{date.today().isoformat()}').sample(ids,5);q=DailyQuiz(user_id=u.id,quiz_date=date.today(),question_ids=json.dumps(chosen));db.add(q);db.commit();db.refresh(q)
 answers=json.loads(q.answers or '{}');rows=[qq for qq in (db.get(Question,x) for x in json.loads(q.question_ids)) if qq]
 return {'date':q.quiz_date.isoformat(),'completed':q.completed,'score':q.score,'answered':len(answers),'questions':[{'id':x.id,'category':x.category,'text':x.text,'options':{'A':x.option_a,'B':x.option_b,'C':x.option_c,'D':x.option_d},'answered':str(x.id) in answers} for x in rows]}
@r.post('/daily-quiz/answer')
def answer(p:QuizAnswerIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 q=db.query(DailyQuiz).filter(DailyQuiz.user_id==u.id,DailyQuiz.quiz_date==date.today()).first()
 if not q or p.question_id not in json.loads(q.question_ids): raise HTTPException(400,'Question is not part of today’s quiz')
 answers=json.loads(q.answers or '{}')
 if str(p.question_id) in answers: raise HTTPException(409,'Question already answered')
 question=db.get(Question,p.question_id)
 if not question: raise HTTPException(404,'Question not found')
 correct=p.selected==question.correct_option;answers[str(p.question_id)]={'selected':p.selected,'correct':correct};q.answers=json.dumps(answers);q.score=sum(1 for a in answers.values() if a['correct']);db.add(QuizAnswer(daily_quiz_id=q.id,user_id=u.id,question_id=question.id,selected_option=p.selected,correct=correct))
 completed=len(answers)==5
 credited=0
 if completed:
  q.completed=True;q.completed_at=datetime.utcnow();db.flush();credited=accrue_today(db,u)
  if credited>0:notify(db,u.id,'Today’s earnings unlocked',f'You completed all five questions. GHS {credited:.2f} was credited automatically.','dashboard')
  else:notify(db,u.id,'Daily questions complete','You answered all five of today’s questions. Your package income for today was already credited automatically.','dashboard')
 db.commit();return {'correct':correct,'correct_option':question.correct_option,'explanation':question.explanation,'completed':completed,'score':q.score,'credited':credited}

@r.get('/deposits/info')
def deposit_info(u:User=Depends(current_user),db:Session=Depends(get_db)): return {'min_deposit':float(setting(db,'min_deposit')),'merchant_name':setting(db,'merchant_name'),'merchant_number':setting(db,'merchant_number'),'merchant_account_name':setting(db,'merchant_account_name'),'merchant_network':setting(db,'merchant_network'),'instructions':setting(db,'merchant_instructions')}
@r.get('/deposits/mine')
def deposits(u:User=Depends(current_user),db:Session=Depends(get_db)): return [dep(x) for x in db.query(Deposit).filter(Deposit.user_id==u.id).order_by(Deposit.created_at.desc()).all()]
@r.post('/deposits')
async def create_deposit(p:DepositIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 if p.amount<float(setting(db,'min_deposit')): raise HTTPException(400,f'Minimum deposit is GHS {setting(db,"min_deposit")}')
 duplicate=db.query(Deposit).filter(Deposit.user_id==u.id,Deposit.amount==round(p.amount,2),Deposit.momo_number==p.momo_number,Deposit.status=='pending',Deposit.created_at>=datetime.utcnow()-timedelta(minutes=10)).first()
 if duplicate: raise HTTPException(409,'An identical deposit request is already pending. Please wait for review.')
 values=p.model_dump();values['amount']=round(p.amount,2);x=Deposit(user_id=u.id,**values);db.add(x);notify(db,u.id,'Deposit pending approval',f'Your GHS {p.amount:.2f} payment request is pending review.');db.commit();db.refresh(x)
 await hub.publish('deposit.created',{'id':x.id,'phone':mask(u.phone),'amount':x.amount},admin_only=True);return dep(x)
@r.get('/withdrawals/info')
def withdrawal_info(u:User=Depends(current_user),db:Session=Depends(get_db)): return {'minimum':float(setting(db,'min_withdrawal')),'fee_percent':float(setting(db,'withdrawal_fee')),'withdrawable':round(u.earnings_balance,2),'saved':{'momo_number':u.payout_number,'network':u.payout_network,'momo_name':u.payout_name}}
@r.get('/withdrawals/mine')
def withdrawals(u:User=Depends(current_user),db:Session=Depends(get_db)): return [wd(x) for x in db.query(Withdrawal).filter(Withdrawal.user_id==u.id).order_by(Withdrawal.created_at.desc()).all()]
@r.post('/withdrawals')
async def create_withdrawal(p:WithdrawIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 minimum=float(setting(db,'min_withdrawal'));fee_rate=float(setting(db,'withdrawal_fee'))
 if p.amount<minimum: raise HTTPException(400,f'Minimum withdrawal is GHS {minimum:.2f}')
 pending=db.query(Withdrawal).filter(Withdrawal.user_id==u.id,Withdrawal.status=='pending').first()
 if pending: raise HTTPException(409,'You already have a withdrawal awaiting review')
 amount=round(p.amount,2);fee=round(amount*fee_rate/100,2)
 if not debit(db,u,'earnings',amount,'withdrawal','Withdrawal request'): raise HTTPException(400,'Withdrawal exceeds your withdrawable earnings')
 values=p.model_dump();values['amount']=amount;x=Withdrawal(user_id=u.id,fee=fee,net_amount=round(amount-fee,2),**values);u.payout_number=p.momo_number;u.payout_network=p.network;u.payout_name=p.momo_name;db.add(x);notify(db,u.id,'Withdrawal submitted',f'Your request is pending. You will receive GHS {x.net_amount:.2f}.');db.commit();db.refresh(x)
 await hub.publish('withdrawal.created',{'id':x.id,'phone':mask(u.phone),'amount':x.amount,'net_amount':x.net_amount},admin_only=True);return wd(x)

@r.get('/wallet/transactions')
def transactions(u:User=Depends(current_user),db:Session=Depends(get_db),limit:int=Query(50,le=200)): return [txn(x) for x in db.query(Transaction).filter(Transaction.user_id==u.id).order_by(Transaction.created_at.desc()).limit(limit).all()]
@r.get('/tasks')
def tasks(u:User=Depends(current_user),db:Session=Depends(get_db)):
 out=[]
 for x in db.query(Task).filter(Task.active.is_(True)).order_by(Task.created_at.desc()).all(): out.append(task(x,db.query(TaskCompletion).filter(TaskCompletion.user_id==u.id,TaskCompletion.task_id==x.id,TaskCompletion.created_at>=today_start()).count()))
 return out
@r.post('/tasks/{task_id}/complete')
def complete_task(task_id:int,p:TaskCompleteIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 x=db.get(Task,task_id)
 if not x or not x.active: raise HTTPException(404,'Task is unavailable')
 if p.elapsed_seconds<x.timer_seconds: raise HTTPException(400,'Complete the required viewing time first')
 if db.query(TaskCompletion).filter(TaskCompletion.user_id==u.id,TaskCompletion.task_id==x.id,TaskCompletion.created_at>=today_start()).count()>=x.daily_limit: raise HTTPException(400,'You reached today’s limit for this task')
 db.add(TaskCompletion(user_id=u.id,task_id=x.id,reward=x.reward));move(db,u,'earnings','task',x.reward,f'Task: {x.title}');db.commit();return {'reward':x.reward,'balance':u.balance}
@r.get('/referrals')
def referrals(u:User=Depends(current_user),db:Session=Depends(get_db)):
 refs=db.query(User).filter(User.referred_by==u.id).order_by(User.created_at.desc()).all();com=db.query(Commission).filter(Commission.user_id==u.id).order_by(Commission.created_at.desc()).all();return {'code':u.referral_code,'members':[{'name':x.full_name,'phone':mask(x.phone),'joined':x.created_at.isoformat()} for x in refs],'commissions':[{'level':x.level,'percent':x.percent,'amount':x.amount,'created_at':x.created_at.isoformat()} for x in com],'total':round(sum(x.amount for x in com),2)}
@r.get('/ads')
def ads(u:User=Depends(current_user),db:Session=Depends(get_db)):
 today=date.today();reward=round(float(setting(db,'ad_reward')),2);claimed={v.ad_id for v in db.query(AdView).filter(AdView.user_id==u.id,AdView.view_date==today).all()}
 return [{'id':x.id,'title':x.title,'description':x.description,'image_url':x.image_url,'link':x.link,'reward':reward,'claimed_today':x.id in claimed} for x in db.query(Advertisement).filter(Advertisement.status=='approved').order_by(Advertisement.created_at.desc()).all() if active_ad(x)]
@r.post('/ads')
def create_ad(p:AdIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 price=round(p.duration_days*5,2)
 if not debit(db,u,'earnings',price,'ad','Advertisement submission'): raise HTTPException(400,'Insufficient earnings balance')
 x=Advertisement(owner_id=u.id,price=price,**p.model_dump());db.add(x);db.commit();return {'id':x.id,'status':'pending','price':price}
@r.post('/ads/{ad_id}/reward')
def ad_reward(ad_id:int,p:AdRewardIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
 x=db.get(Advertisement,ad_id)
 if not active_ad(x): raise HTTPException(404,'Advertisement is unavailable or expired')
 if x.owner_id==u.id: raise HTTPException(400,'You cannot claim a gift from your own advertisement')
 if p.elapsed_seconds<60: raise HTTPException(400,'Spend at least a minute on the advertiser site to receive your gift')
 today=date.today()
 if db.query(AdView).filter(AdView.user_id==u.id,AdView.ad_id==ad_id,AdView.view_date==today).first(): raise HTTPException(409,'You already claimed this advertiser gift today')
 reward=round(float(setting(db,'ad_reward')),2)
 if reward<=0: raise HTTPException(400,'Advertiser gifts are not available right now')
 db.add(AdView(user_id=u.id,ad_id=ad_id,view_date=today,reward=reward));move(db,u,'earnings','ad_reward',reward,f'Advertiser gift: {x.title}');notify(db,u.id,'Advertiser gift credited',f'You earned GHS {reward:.2f} for visiting {x.title}.')
 db.commit();return {'reward':reward,'balance':u.balance}
@r.get('/notifications')
def notifications(u:User=Depends(current_user),db:Session=Depends(get_db)):
 reads={x.notification_id for x in db.query(NotificationRead).filter(NotificationRead.user_id==u.id).all()};rows=db.query(Notification).filter(Notification.active.is_(True),or_(Notification.target=='all',Notification.user_id==u.id)).order_by(Notification.created_at.desc()).limit(100).all();return [{'id':x.id,'type':x.type,'title':x.title,'message':x.message,'image_url':x.image_url,'is_read':x.id in reads,'created_at':x.created_at.isoformat()} for x in rows]
@r.post('/notifications/{nid}/read')
def read_notification(nid:int,u:User=Depends(current_user),db:Session=Depends(get_db)):
 if not db.query(NotificationRead).filter(NotificationRead.user_id==u.id,NotificationRead.notification_id==nid).first():db.add(NotificationRead(user_id=u.id,notification_id=nid));db.commit()
 return {'ok':True}

# Admin
@r.get('/admin/overview')
def admin_overview(a:User=Depends(admin_user),db:Session=Depends(get_db)): return {'users':db.query(User).filter(User.is_admin.is_(False),User.is_active.is_(True)).count(),'pending_deposits':db.query(Deposit).filter(Deposit.status=='pending').count(),'pending_withdrawals':db.query(Withdrawal).filter(Withdrawal.status=='pending').count(),'active_investments':db.query(Investment).filter(Investment.status=='active').count(),'total_deposited':round(db.query(func.coalesce(func.sum(Deposit.amount),0)).filter(Deposit.status=='approved').scalar() or 0,2),'total_withdrawn':round(db.query(func.coalesce(func.sum(Withdrawal.amount),0)).filter(Withdrawal.status.in_(['approved','completed'])).scalar() or 0,2),'questions':db.query(Question).count(),'tasks':db.query(Task).filter(Task.active.is_(True)).count()}
@r.get('/admin/users')
def admin_users(a:User=Depends(admin_user),db:Session=Depends(get_db)): return [{'id':x.id,'full_name':x.full_name,'phone':x.phone,'balance':x.balance,'earnings':x.earnings_balance,'email':x.email,'telegram':x.telegram,'active':x.is_active,'is_admin':x.is_admin,'created_at':x.created_at.isoformat()} for x in db.query(User).order_by(User.created_at.desc()).all() if not deleted_user(db,x)]
@r.post('/admin/users/{uid}/adjust')
def adjust(uid:int,p:WalletAdjustIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 u=db.get(User,uid)
 if not u or deleted_user(db,u): raise HTTPException(404,'User not found')
 current=u.deposit_balance if p.wallet=='deposit' else u.earnings_balance
 if current+p.amount<0: raise HTTPException(400,'Adjustment would create a negative wallet balance')
 move(db,u,p.wallet,'adjustment',p.amount,f'Admin adjustment: {p.reason}');db.add(ActivityLog(admin_id=a.id,action='wallet.adjust',target=str(uid),detail=p.reason));db.commit();return public_user(u)
@r.patch('/admin/users/{uid}')
def admin_user_edit(uid:int,p:AdminUserEditIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 u=db.get(User,uid)
 if not u or deleted_user(db,u): raise HTTPException(404,'User not found')
 data=p.model_dump(exclude_unset=True)
 if u.id==a.id and (data.get('is_active') is False or data.get('is_admin') is False): raise HTTPException(400,'You cannot remove your own admin access')
 if data.get('phone') and data['phone']!=u.phone and db.get(BlockedPhone,data['phone']): raise HTTPException(400,'This phone number is not supported')
 if data.get('phone') and data['phone']!=u.phone and db.query(User).filter(User.phone==data['phone'],User.id!=u.id).first(): raise HTTPException(409,'Phone number already in use')
 for k,v in data.items(): setattr(u,k,v)
 db.add(ActivityLog(admin_id=a.id,action='user.edit',target=str(u.id),detail=', '.join(data.keys())));db.commit();db.refresh(u)
 return {'id':u.id,'full_name':u.full_name,'phone':u.phone,'email':u.email,'telegram':u.telegram,'active':u.is_active,'is_admin':u.is_admin}
@r.get('/admin/packages')
def admin_packages(a:User=Depends(admin_user),db:Session=Depends(get_db)): return [pkg(x) for x in db.query(Package).order_by(Package.created_at.desc()).all()]
@r.post('/admin/packages')
async def add_package(p:PackageIn,a:User=Depends(admin_user),db:Session=Depends(get_db)): x=Package(**p.model_dump());db.add(x);db.flush();db.add(ActivityLog(admin_id=a.id,action='package.create',target=str(x.id),detail=x.name));db.commit();db.refresh(x);await hub.publish('packages.changed',{'id':x.id});return pkg(x)
@r.patch('/admin/packages/{pid}')
async def edit_package(pid:int,p:PackageIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Package,pid)
 if not x: raise HTTPException(404,'Package not found')
 for k,v in p.model_dump().items():setattr(x,k,v)
 db.add(ActivityLog(admin_id=a.id,action='package.update',target=str(x.id),detail=x.name));db.commit();await hub.publish('packages.changed',{'id':x.id});return pkg(x)
@r.delete('/admin/packages/{pid}')
async def delete_package(pid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Package,pid)
 if not x: raise HTTPException(404,'Package not found')
 if db.query(Investment).filter(Investment.package_id==pid).first():
  x.status='hidden';db.add(ActivityLog(admin_id=a.id,action='package.archive',target=str(pid),detail='Package has investments and was hidden instead of deleted'));db.commit();await hub.publish('packages.changed',{'id':pid});return {'ok':True,'archived':True}
 db.add(ActivityLog(admin_id=a.id,action='package.delete',target=str(x.id),detail=x.name));db.delete(x);db.commit();await hub.publish('packages.changed',{'id':pid});return {'ok':True}
@r.get('/admin/questions')
def admin_questions(a:User=Depends(admin_user),db:Session=Depends(get_db),limit:int=Query(100,le=500),offset:int=0): return [{'id':x.id,'category':x.category,'text':x.text,'option_a':x.option_a,'option_b':x.option_b,'option_c':x.option_c,'option_d':x.option_d,'correct_option':x.correct_option,'explanation':x.explanation,'active':x.active} for x in db.query(Question).order_by(Question.id.desc()).offset(offset).limit(limit).all()]
@r.post('/admin/questions')
def add_question(p:QuestionIn,a:User=Depends(admin_user),db:Session=Depends(get_db)): x=Question(**p.model_dump());db.add(x);db.flush();db.add(ActivityLog(admin_id=a.id,action='question.create',target=str(x.id),detail=x.category));db.commit();db.refresh(x);return {'id':x.id}
@r.patch('/admin/questions/{qid}')
def edit_question(qid:int,p:QuestionIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Question,qid)
 if not x: raise HTTPException(404,'Question not found')
 for k,v in p.model_dump().items():setattr(x,k,v)
 db.add(ActivityLog(admin_id=a.id,action='question.update',target=str(x.id),detail=x.category));db.commit();return {'id':x.id}
@r.delete('/admin/questions/{qid}')
def delete_question(qid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Question,qid)
 if not x: raise HTTPException(404,'Question not found')
 db.add(ActivityLog(admin_id=a.id,action='question.delete',target=str(x.id),detail=x.category));db.delete(x);db.commit();return {'ok':True}
@r.get('/admin/deposits')
def admin_deposits(a:User=Depends(admin_user),db:Session=Depends(get_db)): return [dict(dep(x),user_phone=db.get(User,x.user_id).phone,user_name=db.get(User,x.user_id).full_name) for x in db.query(Deposit).order_by(Deposit.created_at.desc()).all()]
@r.post('/admin/deposits/{did}/review')
async def review_deposit(did:int,p:ReviewIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Deposit,did)
 if not x or x.status!='pending': raise HTTPException(400,'Deposit is unavailable or already reviewed')
 u=db.get(User,x.user_id);x.admin_note=p.note;x.reviewed_at=datetime.utcnow();x.status='approved' if p.action=='approve' else 'rejected'
 if x.status=='approved':move(db,u,'deposit','deposit',x.amount,f'Deposit #{x.id} approved')
 notify(db,u.id,f'Deposit {x.status}',f'Your GHS {x.amount:.2f} deposit was {x.status}.');db.add(ActivityLog(admin_id=a.id,action='deposit.review',target=str(x.id),detail=f'{x.status}: {p.note}'));db.commit();await hub.publish('deposits.changed',{'id':x.id});return dep(x)
@r.get('/admin/withdrawals')
def admin_withdrawals(a:User=Depends(admin_user),db:Session=Depends(get_db)): return [dict(wd(x),user_phone=db.get(User,x.user_id).phone,user_name=db.get(User,x.user_id).full_name) for x in db.query(Withdrawal).order_by(Withdrawal.created_at.desc()).all()]
@r.post('/admin/withdrawals/{wid}/review')
async def review_withdrawal(wid:int,p:ReviewIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Withdrawal,wid)
 if not x:raise HTTPException(404,'Withdrawal not found')
 u=db.get(User,x.user_id)
 if p.action=='reject':
  if x.status!='pending': raise HTTPException(409,'Only a pending withdrawal can be rejected')
  move(db,u,'earnings','adjustment',x.amount,f'Withdrawal #{x.id} refund');x.status='rejected'
 elif p.action=='approve':
  if x.status!='pending': raise HTTPException(409,'Only a pending withdrawal can be approved')
  x.status='approved'
 elif p.action=='complete':
  if x.status!='approved': raise HTTPException(409,'Approve the withdrawal before marking it paid')
  x.status='completed'
 x.admin_note=p.note;x.reviewed_at=datetime.utcnow();notify(db,u.id,f'Withdrawal {x.status}',f'Your withdrawal request is now {x.status}.');db.add(ActivityLog(admin_id=a.id,action='withdrawal.review',target=str(x.id),detail=f'{x.status}: {p.note}'));db.commit();await hub.publish('withdrawals.changed',{'id':x.id});return wd(x)
@r.get('/admin/tasks')
def admin_tasks(a:User=Depends(admin_user),db:Session=Depends(get_db)): return [task(x) for x in db.query(Task).order_by(Task.created_at.desc()).all()]
@r.post('/admin/tasks')
async def admin_task_create(p:TaskIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=Task(**p.model_dump());db.add(x);db.flush();db.add(ActivityLog(admin_id=a.id,action='task.create',target=str(x.id),detail=x.title));db.commit();await hub.publish('tasks.changed',{'id':x.id});return task(x)
@r.patch('/admin/tasks/{tid}')
async def admin_task_update(tid:int,p:TaskIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Task,tid)
 if not x: raise HTTPException(404,'Task not found')
 for k,v in p.model_dump().items():setattr(x,k,v)
 db.add(ActivityLog(admin_id=a.id,action='task.update',target=str(x.id),detail=x.title));db.commit();await hub.publish('tasks.changed',{'id':x.id});return task(x)
@r.delete('/admin/tasks/{tid}')
async def admin_task_delete(tid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Task,tid)
 if not x: raise HTTPException(404,'Task not found')
 if db.query(TaskCompletion).filter(TaskCompletion.task_id==tid).first():x.active=False
 else:db.delete(x)
 db.add(ActivityLog(admin_id=a.id,action='task.archive',target=str(tid),detail=x.title));db.commit();await hub.publish('tasks.changed',{'id':tid});return {'ok':True}

@r.get('/admin/ads')
def admin_ads(a:User=Depends(admin_user),db:Session=Depends(get_db)):
 return [{'id':x.id,'title':x.title,'description':x.description,'image_url':x.image_url,'link':x.link,'duration_days':x.duration_days,'price':x.price,'status':x.status,'owner_phone':db.get(User,x.owner_id).phone,'created_at':x.created_at.isoformat()} for x in db.query(Advertisement).order_by(Advertisement.created_at.desc()).all()]
@r.post('/admin/ads/{aid}/review')
async def admin_ad_review(aid:int,p:ReviewIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Advertisement,aid)
 if not x or x.status!='pending':raise HTTPException(409,'Advertisement is unavailable or already reviewed')
 owner=db.get(User,x.owner_id);x.status='approved' if p.action=='approve' else 'rejected'
 if x.status=='approved':x.approved_at=datetime.utcnow()
 if x.status=='rejected':move(db,owner,'earnings','adjustment',x.price,f'Advertisement #{x.id} rejected refund')
 notify(db,owner.id,f'Advertisement {x.status}',f'Your campaign “{x.title}” was {x.status}.');db.add(ActivityLog(admin_id=a.id,action='ad.review',target=str(x.id),detail=f'{x.status}: {p.note}'));db.commit();await hub.publish('ads.changed',{'id':x.id});return {'id':x.id,'status':x.status}

@r.get('/admin/notifications')
def admin_notifications(a:User=Depends(admin_user),db:Session=Depends(get_db)):
 return [{'id':x.id,'type':x.type,'title':x.title,'message':x.message,'image_url':x.image_url,'target':x.target,'active':x.active,'created_at':x.created_at.isoformat()} for x in db.query(Notification).order_by(Notification.created_at.desc()).limit(200).all()]
@r.post('/admin/notifications')
async def admin_notification_create(p:NotificationIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 if p.target=='user' and not p.user_id:raise HTTPException(400,'Select a target user')
 x=Notification(**p.model_dump(),active=True);db.add(x);db.flush();db.add(ActivityLog(admin_id=a.id,action='notification.create',target=str(x.id),detail=x.title));db.commit();await hub.publish('notifications.changed',{'id':x.id});return {'id':x.id}
@r.delete('/admin/notifications/{nid}')
async def admin_notification_delete(nid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 x=db.get(Notification,nid)
 if not x:raise HTTPException(404,'Notification not found')
 db.query(NotificationRead).filter(NotificationRead.notification_id==nid).delete();title=x.title;db.delete(x);db.add(ActivityLog(admin_id=a.id,action='notification.remove',target=str(nid),detail=title));db.commit();await hub.publish('notifications.changed',{'id':nid});return {'ok':True}

@r.post('/admin/users/{uid}/toggle')
def admin_user_toggle(uid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 u=db.get(User,uid)
 if not u or u.is_admin or deleted_user(db,u):raise HTTPException(400,'User cannot be changed')
 u.is_active=not u.is_active
 blocked=db.get(BlockedPhone,u.phone)
 if not u.is_active and not blocked:db.add(BlockedPhone(phone=u.phone,reason='Disabled by admin'))
 if u.is_active and blocked:db.delete(blocked)
 db.add(ActivityLog(admin_id=a.id,action='user.toggle',target=str(u.id),detail=f'active={u.is_active}'));db.commit();return {'active':u.is_active}
@r.post('/admin/users/{uid}/reset-password')
def admin_user_reset_password(uid:int,p:AdminResetPasswordIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 u=db.get(User,uid)
 if not u or deleted_user(db,u): raise HTTPException(404,'User not found')
 u.password_hash=hash_password(p.new_password);u.token_version=int(u.token_version or 0)+1
 db.add(ActivityLog(admin_id=a.id,action='user.reset_password',target=str(u.id),detail=f'Password reset for {u.phone}'));db.commit();return {'ok':True}
@r.delete('/admin/users/{uid}')
def admin_user_delete(uid:int,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 u=db.get(User,uid)
 if not u or u.is_admin:raise HTTPException(400,'User cannot be deleted')
 u.is_active=False
 if not db.get(BlockedPhone,u.phone):db.add(BlockedPhone(phone=u.phone,reason='Deleted by admin'))
 db.add(ActivityLog(admin_id=a.id,action='user.delete',target=str(u.id),detail=f'{u.phone} deleted and blocked from re-registration'));db.commit();return {'ok':True,'phone_blocked':True}
@r.get('/admin/settings')
def admin_settings(a:User=Depends(admin_user),db:Session=Depends(get_db)): return {k:setting(db,k) for k in DEFAULTS}
@r.put('/admin/settings')
async def admin_settings_update(p:SettingsIn,a:User=Depends(admin_user),db:Session=Depends(get_db)):
 allowed=set(DEFAULTS);unknown=set(p.values)-allowed
 if unknown: raise HTTPException(400,f'Unknown settings: {", ".join(sorted(unknown))}')
 numeric={'min_deposit':(1,10000000),'min_withdrawal':(1,10000000),'withdrawal_fee':(0,90),'signup_bonus':(0,1000000),'referral_l1':(0,100),'referral_l2':(0,100),'referral_l3':(0,100),'ad_reward':(0,1000000),'login_reward':(0,1000000)}
 for k,v in p.values.items():
  value=str(v).strip()
  if k in numeric:
   try:number=float(value)
   except ValueError:raise HTTPException(400,f'{k} must be a number')
   low,high=numeric[k]
   if number<low or number>high:raise HTTPException(400,f'{k} must be between {low} and {high}')
  elif not value:raise HTTPException(400,f'{k} cannot be empty')
  x=db.get(Setting,k)
  if x:x.value=value
  else:db.add(Setting(key=k,value=value))
 db.add(ActivityLog(admin_id=a.id,action='settings.update',target='platform',detail=', '.join(p.values.keys())));db.commit();await hub.publish('settings.changed',{'keys':list(p.values)});return {k:setting(db,k) for k in DEFAULTS}

@r.get('/admin/logs')
def admin_logs(a:User=Depends(admin_user),db:Session=Depends(get_db),limit:int=Query(100,le=500)):
 return [{'id':x.id,'admin_id':x.admin_id,'action':x.action,'target':x.target,'detail':x.detail,'created_at':x.created_at.isoformat()} for x in db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()]
