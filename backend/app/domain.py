from datetime import date,datetime
from sqlalchemy.orm import Session
from .models import Transaction,Notification,DailyQuiz,Investment,IncomeCredit,User,Wallet

def move(db:Session,u:User,wallet:str,type_:str,amount:float,note=''):
 if wallet=='deposit': u.deposit_balance=round(u.deposit_balance+amount,2)
 else: u.earnings_balance=round(u.earnings_balance+amount,2)
 ledger=db.query(Wallet).filter(Wallet.user_id==u.id).first()
 if not ledger:
  ledger=Wallet(user_id=u.id,deposit_credit=u.deposit_balance,earnings_credit=u.earnings_balance);db.add(ledger)
 else:
  ledger.deposit_credit=u.deposit_balance;ledger.earnings_credit=u.earnings_balance
 db.add(Transaction(user_id=u.id,wallet=wallet,type=type_,amount=round(amount,2),note=note))

def debit(db:Session,u:User,wallet:str,amount:float,type_:str,note=''):
 amount=round(float(amount),2)
 if amount<=0:return False
 field=User.deposit_balance if wallet=='deposit' else User.earnings_balance
 changed=db.query(User).filter(User.id==u.id,field>=amount).update({field:field-amount},synchronize_session=False)
 if changed!=1:return False
 db.flush();db.refresh(u)
 if wallet=='deposit':u.deposit_balance=round(u.deposit_balance,2)
 else:u.earnings_balance=round(u.earnings_balance,2)
 ledger=db.query(Wallet).filter(Wallet.user_id==u.id).first()
 if not ledger:ledger=Wallet(user_id=u.id);db.add(ledger)
 ledger.deposit_credit=u.deposit_balance;ledger.earnings_credit=u.earnings_balance
 db.add(Transaction(user_id=u.id,wallet=wallet,type=type_,amount=-amount,note=note))
 return True

def notify(db,user_id,title,message,type_='dashboard',image_url=''):
 db.add(Notification(user_id=user_id,target='user' if user_id else 'all',title=title,message=message,type=type_,image_url=image_url))
def quiz_complete(db,u):
 q=db.query(DailyQuiz).filter(DailyQuiz.user_id==u.id,DailyQuiz.quiz_date==date.today(),DailyQuiz.completed.is_(True)).first(); return bool(q)
def accrue_today(db:Session,u:User):
 # Daily package income is available only after all five questions are completed today.
 if not quiz_complete(db,u): return 0.0
 total=0.0; today=date.today()
 for inv in db.query(Investment).filter(Investment.user_id==u.id,Investment.status=='active').all():
  eligible=min((today-inv.start_date).days+1,inv.duration_days)
  if inv.days_credited>=eligible: continue
  if db.query(IncomeCredit).filter(IncomeCredit.investment_id==inv.id,IncomeCredit.credit_date==today).first(): continue
  # Exactly one credit per active package per calendar day after quiz completion.
  inv.days_credited+=1; inv.total_credited=round(inv.total_credited+inv.daily_income,2); total+=inv.daily_income
  db.add(IncomeCredit(investment_id=inv.id,user_id=u.id,credit_date=today,amount=inv.daily_income))
  move(db,u,'earnings','income',inv.daily_income,f'Daily income — {inv.package_name} (day {inv.days_credited})')
  if inv.days_credited>=inv.duration_days: inv.status='completed'
 if total: notify(db,u.id,'Daily earnings credited',f'GHS {total:.2f} in daily package income was credited automatically.')
 return round(total,2)
