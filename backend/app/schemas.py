from pydantic import BaseModel,Field,field_validator,model_validator
class RegisterIn(BaseModel):
 full_name:str=Field(min_length=2,max_length=120); phone:str=Field(min_length=7,max_length=24); password:str=Field(min_length=6,max_length=72); confirm_password:str; captcha_token:str; captcha_answer:str; referral_code:str|None=None
 @field_validator('full_name')
 @classmethod
 def name(cls,v):
  v=' '.join(v.split())
  if len(v)<2: raise ValueError('Enter your full name')
  return v
 @field_validator('phone')
 @classmethod
 def phone_clean(cls,v):
  v=''.join(x for x in v if x.isdigit() or x=='+')
  if len(v)<7: raise ValueError('Enter a valid phone number')
  return v
class ProfileIn(BaseModel):
 full_name:str|None=Field(None,min_length=2,max_length=120); email:str|None=Field(None,max_length=255); telegram:str|None=Field(None,max_length=80); notify_transactions:bool|None=None; notify_marketing:bool|None=None
class PasswordIn(BaseModel): current_password:str; new_password:str=Field(min_length=6,max_length=72); confirm_password:str
class InvestIn(BaseModel): package_id:int; amount:float=Field(gt=0)
class DepositIn(BaseModel): amount:float=Field(gt=0); momo_number:str=Field(min_length=7,max_length=24); network:str=Field(pattern='^(MTN|Telecel|AirtelTigo)$'); momo_name:str=Field(min_length=2,max_length=120)
class WithdrawIn(DepositIn): pass
class QuizAnswerIn(BaseModel): question_id:int; selected:str=Field(pattern='^[ABCD]$')
class TaskCompleteIn(BaseModel): elapsed_seconds:int=Field(ge=0,default=0)
class TaskIn(BaseModel):
 title:str=Field(min_length=2,max_length=140); description:str=''; category:str=Field(default='General',max_length=60); reward:float=Field(gt=0); external_link:str=Field(default='',max_length=500); timer_seconds:int=Field(default=0,ge=0,le=3600); daily_limit:int=Field(default=1,ge=1,le=100); active:bool=True
class AdIn(BaseModel): title:str=Field(min_length=2,max_length=140); description:str=''; image_url:str=''; link:str=''; duration_days:int=Field(ge=1,le=90)
class AdRewardIn(BaseModel): elapsed_seconds:int=Field(ge=0,default=0)
class PackageIn(BaseModel):
 name:str=Field(min_length=2,max_length=100); description:str=''; image_url:str=''; min_amount:float=Field(gt=0); max_amount:float=Field(gt=0); daily_income:float=Field(gt=0); duration_days:int=Field(gt=0,le=3650); status:str=Field(default='active',pattern='^(active|locked|hidden)$'); featured:bool=False
 @model_validator(mode='after')
 def valid_range(self):
  if self.max_amount<self.min_amount: raise ValueError('Maximum amount must be greater than or equal to minimum amount')
  return self
class QuestionIn(BaseModel): category:str='Financial literacy'; text:str=Field(min_length=5); option_a:str; option_b:str; option_c:str; option_d:str; correct_option:str=Field(pattern='^[ABCD]$'); explanation:str=Field(min_length=3); active:bool=True
class ReviewIn(BaseModel): action:str=Field(pattern='^(approve|reject|complete)$'); note:str=''
class WalletAdjustIn(BaseModel): wallet:str=Field(pattern='^(deposit|earnings)$'); amount:float; reason:str=Field(min_length=2)
class NotificationIn(BaseModel): type:str=Field(pattern='^(popup|banner|dashboard|image)$'); title:str; message:str=''; image_url:str=''; target:str='all'; user_id:int|None=None
class SettingsIn(BaseModel): values:dict
class AdminUserEditIn(BaseModel): full_name:str|None=Field(None,max_length=120); phone:str|None=Field(None,max_length=24); email:str|None=Field(None,max_length=255); telegram:str|None=Field(None,max_length=80); is_active:bool|None=None; is_admin:bool|None=None
class AdminResetPasswordIn(BaseModel): new_password:str=Field(min_length=6,max_length=72)
