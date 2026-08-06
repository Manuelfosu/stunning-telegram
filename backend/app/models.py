from datetime import date, datetime
from sqlalchemy import Boolean,Column,Date,DateTime,Float,ForeignKey,Integer,String,Text,UniqueConstraint
from .database import Base

class User(Base):
 __tablename__='users'
 id=Column(Integer,primary_key=True); full_name=Column(String(120),nullable=False); phone=Column(String(24),unique=True,index=True,nullable=False); password_hash=Column(String(255),nullable=False)
 deposit_balance=Column(Float,default=0,nullable=False); earnings_balance=Column(Float,default=0,nullable=False)
 is_admin=Column(Boolean,default=False); is_active=Column(Boolean,default=True); email=Column(String(255),default=''); telegram=Column(String(80),default='')
 referral_code=Column(String(12),unique=True,index=True,nullable=False); referred_by=Column(Integer,ForeignKey('users.id'),nullable=True)
 payout_number=Column(String(24),default=''); payout_network=Column(String(30),default=''); payout_name=Column(String(120),default='')
 notify_transactions=Column(Boolean,default=True); notify_marketing=Column(Boolean,default=True); token_version=Column(Integer,default=0,nullable=False); created_at=Column(DateTime,default=datetime.utcnow)
 @property
 def balance(self): return round(self.deposit_balance+self.earnings_balance,2)

class Wallet(Base):
 __tablename__='wallets'
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),unique=True,index=True,nullable=False); deposit_credit=Column(Float,default=0,nullable=False); earnings_credit=Column(Float,default=0,nullable=False); updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class Setting(Base):
 __tablename__='settings'; key=Column(String(80),primary_key=True); value=Column(Text,default='')
class Package(Base):
 __tablename__='packages'; id=Column(Integer,primary_key=True); name=Column(String(100),nullable=False); description=Column(Text,default=''); image_url=Column(String(500),default=''); min_amount=Column(Float,nullable=False); max_amount=Column(Float,nullable=False); daily_income=Column(Float,nullable=False); duration_days=Column(Integer,nullable=False); status=Column(String(20),default='active'); featured=Column(Boolean,default=False); created_at=Column(DateTime,default=datetime.utcnow)
class Investment(Base):
 __tablename__='investments'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); package_id=Column(Integer,ForeignKey('packages.id'),nullable=False); package_name=Column(String(100)); amount=Column(Float,nullable=False); daily_income=Column(Float,nullable=False); duration_days=Column(Integer,nullable=False); start_date=Column(Date,default=date.today); end_date=Column(Date,nullable=False); days_credited=Column(Integer,default=0); total_credited=Column(Float,default=0); status=Column(String(20),default='active'); created_at=Column(DateTime,default=datetime.utcnow)
class IncomeCredit(Base):
 __tablename__='income_credits'; __table_args__=(UniqueConstraint('investment_id','credit_date',name='uq_investment_daily_income'),)
 id=Column(Integer,primary_key=True); investment_id=Column(Integer,ForeignKey('investments.id'),nullable=False,index=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True); credit_date=Column(Date,nullable=False,default=date.today); amount=Column(Float,nullable=False); created_at=Column(DateTime,default=datetime.utcnow)
class Transaction(Base):
 __tablename__='transactions'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); wallet=Column(String(12),nullable=False); type=Column(String(30),nullable=False); amount=Column(Float,nullable=False); note=Column(String(255),default=''); created_at=Column(DateTime,default=datetime.utcnow)
class Deposit(Base):
 __tablename__='deposits'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); amount=Column(Float,nullable=False); momo_number=Column(String(24),nullable=False); network=Column(String(30),nullable=False); momo_name=Column(String(120),nullable=False); status=Column(String(20),default='pending'); admin_note=Column(String(255),default=''); created_at=Column(DateTime,default=datetime.utcnow); reviewed_at=Column(DateTime,nullable=True)
class Withdrawal(Base):
 __tablename__='withdrawals'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); amount=Column(Float,nullable=False); fee=Column(Float,nullable=False); net_amount=Column(Float,nullable=False); momo_number=Column(String(24),nullable=False); network=Column(String(30),nullable=False); momo_name=Column(String(120),nullable=False); status=Column(String(20),default='pending'); admin_note=Column(String(255),default=''); created_at=Column(DateTime,default=datetime.utcnow); reviewed_at=Column(DateTime,nullable=True)
class Question(Base):
 __tablename__='questions'; id=Column(Integer,primary_key=True); category=Column(String(60),default='Financial literacy'); text=Column(Text,nullable=False); option_a=Column(String(255),nullable=False); option_b=Column(String(255),nullable=False); option_c=Column(String(255),nullable=False); option_d=Column(String(255),nullable=False); correct_option=Column(String(1),nullable=False); explanation=Column(Text,nullable=False); active=Column(Boolean,default=True); created_at=Column(DateTime,default=datetime.utcnow)
class DailyQuiz(Base):
 __tablename__='daily_quizzes'; __table_args__=(UniqueConstraint('user_id','quiz_date',name='uq_daily_quiz'),)
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); quiz_date=Column(Date,nullable=False,default=date.today); question_ids=Column(Text,nullable=False); answers=Column(Text,default='{}'); score=Column(Integer,default=0); completed=Column(Boolean,default=False); completed_at=Column(DateTime,nullable=True)
class QuizAnswer(Base):
 __tablename__='answers'; __table_args__=(UniqueConstraint('daily_quiz_id','question_id',name='uq_quiz_question_answer'),)
 id=Column(Integer,primary_key=True); daily_quiz_id=Column(Integer,ForeignKey('daily_quizzes.id'),nullable=False); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); question_id=Column(Integer,ForeignKey('questions.id'),nullable=False); selected_option=Column(String(1),nullable=False); correct=Column(Boolean,nullable=False); answered_at=Column(DateTime,default=datetime.utcnow)
class Task(Base):
 __tablename__='tasks'; id=Column(Integer,primary_key=True); title=Column(String(140),nullable=False); description=Column(Text,default=''); category=Column(String(60),default='General'); reward=Column(Float,nullable=False); external_link=Column(String(500),default=''); timer_seconds=Column(Integer,default=0); daily_limit=Column(Integer,default=1); active=Column(Boolean,default=True); created_at=Column(DateTime,default=datetime.utcnow)
class TaskCompletion(Base):
 __tablename__='task_completions'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); task_id=Column(Integer,ForeignKey('tasks.id')); reward=Column(Float); created_at=Column(DateTime,default=datetime.utcnow)
class Commission(Base):
 __tablename__='commissions'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); from_user_id=Column(Integer,ForeignKey('users.id')); level=Column(Integer); percent=Column(Float); amount=Column(Float); created_at=Column(DateTime,default=datetime.utcnow)
class Referral(Base):
 __tablename__='referrals'; __table_args__=(UniqueConstraint('referred_id',name='uq_referred_member'),)
 id=Column(Integer,primary_key=True); referrer_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True); referred_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True); referral_code=Column(String(12),nullable=False); created_at=Column(DateTime,default=datetime.utcnow)
class Advertisement(Base):
 __tablename__='ads'; id=Column(Integer,primary_key=True); owner_id=Column(Integer,ForeignKey('users.id')); title=Column(String(140)); description=Column(Text,default=''); image_url=Column(String(500),default=''); link=Column(String(500),default=''); duration_days=Column(Integer,default=1); price=Column(Float,default=0); status=Column(String(20),default='pending'); approved_at=Column(DateTime,nullable=True); created_at=Column(DateTime,default=datetime.utcnow)
class AdView(Base):
 __tablename__='ad_views'; __table_args__=(UniqueConstraint('user_id','ad_id','view_date',name='uq_ad_view_daily'),)
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True); ad_id=Column(Integer,ForeignKey('ads.id'),nullable=False,index=True); view_date=Column(Date,nullable=False,default=date.today); reward=Column(Float,default=0); created_at=Column(DateTime,default=datetime.utcnow)
class LoginReward(Base):
 __tablename__='login_rewards'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); reward_date=Column(Date,default=date.today); amount=Column(Float,default=0); created_at=Column(DateTime,default=datetime.utcnow)
 __table_args__=(UniqueConstraint('user_id','reward_date',name='uq_login_reward_daily'),)
class Notification(Base):
 __tablename__='notifications'; id=Column(Integer,primary_key=True); type=Column(String(20),default='dashboard'); title=Column(String(140)); message=Column(Text,default=''); image_url=Column(String(500),default=''); target=Column(String(12),default='all'); user_id=Column(Integer,ForeignKey('users.id'),nullable=True); active=Column(Boolean,default=True); created_at=Column(DateTime,default=datetime.utcnow)
class NotificationRead(Base):
 __tablename__='notification_reads'; __table_args__=(UniqueConstraint('user_id','notification_id',name='uq_notif_read'),); id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); notification_id=Column(Integer,ForeignKey('notifications.id')); created_at=Column(DateTime,default=datetime.utcnow)
class ActivityLog(Base):
 __tablename__='logs'; id=Column(Integer,primary_key=True); admin_id=Column(Integer,ForeignKey('users.id'),nullable=True); action=Column(String(80)); target=Column(String(60),default=''); detail=Column(Text,default=''); created_at=Column(DateTime,default=datetime.utcnow)
class BlockedPhone(Base):
 __tablename__='blocked_phones'; phone=Column(String(24),primary_key=True); reason=Column(String(160),default=''); created_at=Column(DateTime,default=datetime.utcnow)
class Captcha(Base):
 __tablename__='captchas'; token=Column(String(40),primary_key=True); answer=Column(String(10)); used=Column(Boolean,default=False); expires_at=Column(DateTime); created_at=Column(DateTime,default=datetime.utcnow)
