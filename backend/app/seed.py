import random,string
from datetime import date,datetime,timedelta
from sqlalchemy.orm import Session
from .config import DEFAULTS,ADMIN_PHONE,ADMIN_PASSWORD
from .models import *
from .security import hash_password

def code(): return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(7))
def seed(db:Session):
 for k,v in DEFAULTS.items():
  if not db.get(Setting,k):db.add(Setting(key=k,value=v))
 if not db.query(User).filter(User.is_admin.is_(True)).first():db.add(User(full_name='SSGA Administrator',phone=ADMIN_PHONE,password_hash=hash_password(ADMIN_PASSWORD),referral_code=code(),is_admin=True))
 db.flush()
 for user in db.query(User).all():
  if not db.query(Wallet).filter(Wallet.user_id==user.id).first():db.add(Wallet(user_id=user.id,deposit_credit=user.deposit_balance,earnings_credit=user.earnings_balance))
 # Idempotent package catalog migration: fixes existing deployments too.
 canonical_packages=[
  ('Stable Yield','Entry-level investment package for steady daily returns over 30 days.',100,20,30,'/plan-images/stable-yield.svg',True),
  ('Core Income','A balanced portfolio designed for consistent daily income over 30 days.',200,40,30,'/plan-images/core-income.svg',False),
  ('Income Stream','Mid-tier package delivering dependable daily earnings for 30 days.',300,60,30,'/plan-images/income-stream.svg',False),
  ('Wealth Reserve','A solid capital package building daily wealth over a 30-day term.',500,100,30,'/plan-images/wealth-reserve.svg',False),
  ('Capital Plus','A structured capital plan delivering premium daily returns over 30 days.',700,140,30,'/plan-images/capital-plus.svg',False),
  ('Prime Capital','Premium package delivering high-value daily income for 30 days.',1000,200,30,'/plan-images/prime-capital.svg',False),
  ('Wealth Builder','High-capacity earning package with superior daily returns over 30 days.',1500,300,30,'/plan-images/wealth-builder.svg',False),
  ('Equity Growth','Large-cap portfolio with substantial daily earnings across 30 days.',3000,300,30,'/plan-images/equity-growth.svg',False),
  ('Premium Growth','Elite-tier package delivering premium daily income for 30 days.',5000,500,30,'/plan-images/premium-growth.svg',False),
  ('Profit Engine','Flagship plan powering top-tier daily returns over 30 days.',10000,1000,30,'/plan-images/profit-engine.svg',False),
 ]
 canonical_names={row[0] for row in canonical_packages}
 for name,description,price,daily,term,image_url,featured in canonical_packages:
  package=db.query(Package).filter(Package.name==name).first()
  if not package:
   package=Package(name=name);db.add(package)
  package.description=description;package.min_amount=price;package.max_amount=price;package.daily_income=daily;package.duration_days=term;package.featured=featured
  if not package.image_url or package.image_url.startswith('/assets/'): package.image_url=image_url
 for package in db.query(Package).all():
  if package.name not in canonical_names and package.name=='Growth Reserve': package.status='hidden'
 if db.query(Question).count()<500:
  # 520 deterministic, useful financial arithmetic questions: 104 days at 5/day.
  questions=[]
  for n in range(1,401):
   daily=2+(n%39);days=5+(n%26);correct=daily*days
   opts=[correct,correct+daily,correct-daily,max(1,correct//2)];random.Random(n).shuffle(opts);letter='ABCD'[opts.index(correct)]
   questions.append(Question(category='Investment arithmetic',text=f'An investment earns GHS {daily} daily for {days} days. What is the total income?',option_a=f'GHS {opts[0]}',option_b=f'GHS {opts[1]}',option_c=f'GHS {opts[2]}',option_d=f'GHS {opts[3]}',correct_option=letter,explanation=f'Daily income × days: {daily} × {days} = GHS {correct}.'))
  for n in range(1,121):
   amount=50+n*10;fee=16;correct=round(amount*(100-fee)/100,2);opts=[correct,amount,round(amount*.16,2),round(amount*.9,2)];random.Random(1000+n).shuffle(opts);letter='ABCD'[opts.index(correct)]
   questions.append(Question(category='Fees and withdrawals',text=f'After a 16% fee on GHS {amount}, how much does the user receive?',option_a=f'GHS {opts[0]:.2f}',option_b=f'GHS {opts[1]:.2f}',option_c=f'GHS {opts[2]:.2f}',option_d=f'GHS {opts[3]:.2f}',correct_option=letter,explanation=f'Net = {amount} × 0.84 = GHS {correct:.2f}.'))
  db.add_all(questions)
 if not db.query(Notification).first():db.add(Notification(type='popup',title='Welcome to SSGA HOLDINGS',message='Your account is ready. Explore packages, complete tasks and claim daily rewards to start earning.',target='all'))

 # Remove legacy synthetic rows that incorrectly affected admin totals.
 fake_names=['Kwame A.','Akua M.','Yaw B.','Efia S.','Kofi D.','Adwoa P.','Kwesi T.','Ama G.','Kojo F.','Esi N.']
 db.query(Withdrawal).filter(Withdrawal.user_id==1,Withdrawal.status=='completed',Withdrawal.momo_name.in_(fake_names),Withdrawal.admin_note=='').delete(synchronize_session=False)

 db.commit()
