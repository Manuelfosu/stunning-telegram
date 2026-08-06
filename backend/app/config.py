import os
SECRET_KEY=os.getenv('SECRET_KEY','change-me-in-production')
ALGORITHM='HS256'
ACCESS_TOKEN_MINUTES=int(os.getenv('ACCESS_TOKEN_MINUTES','10080'))
DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./ssga.db')
ALLOWED_ORIGINS=[x.strip() for x in os.getenv('ALLOWED_ORIGINS','*').split(',')]
UPLOAD_DIR=os.getenv('UPLOAD_DIR','./uploads')
ADMIN_PHONE=os.getenv('ADMIN_PHONE','0200000000')
ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD','admin123')
CURRENCY='GHS'
DEFAULTS={
 'min_deposit':'100','min_withdrawal':'50','withdrawal_fee':'16',
 'merchant_name':'SSGA HOLDINGS','merchant_number':'0550000000',
 'merchant_account_name':'SSGA HOLDINGS','merchant_network':'MTN',
 'merchant_instructions':'Send the exact amount from the MoMo account entered. Keep your confirmation message until approval.',
 'signup_bonus':'10','referral_l1':'20','referral_l2':'10','referral_l3':'3','ad_reward':'0.50','telegram_link':'https://t.me/ssgaholdings','login_reward':'0.20','deposit_disclaimer':'Automated payment processing is temporarily unavailable. We are working hard to restore automatic verification. For now, all deposits are verified manually — your funds will be credited once an admin confirms your payment. Thank you for your patience.'
}
