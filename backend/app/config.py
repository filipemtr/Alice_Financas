import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./dev.sqlite3')
USERNAME = 'alicefoufa'
SESSION_HOURS = int(os.getenv('SESSION_HOURS', '12'))
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
COOKIE_SAMESITE = os.getenv('COOKIE_SAMESITE', 'lax').lower()
if COOKIE_SAMESITE not in ('lax', 'strict', 'none'):
    raise ValueError('COOKIE_SAMESITE inválido')
if COOKIE_SAMESITE == 'none' and not COOKIE_SECURE:
    raise ValueError('SameSite=None exige cookie seguro')
ALLOWED_ORIGINS = [v.strip().rstrip('/') for v in os.getenv('ALLOWED_ORIGINS', 'http://localhost:8088').split(',') if v.strip()]
