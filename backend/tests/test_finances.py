from .conftest import TEST_PASSWORD

def test_authentication_and_csrf(client):
    assert client.get('/api/months/2026/11').status_code==401
    assert client.post('/api/auth/login',json={'username':'outro','password':TEST_PASSWORD}).status_code==401
    assert client.post('/api/auth/login',json={'username':'alicefoufa','password':'errada'}).status_code==401
    r=client.post('/api/auth/login',json={'username':'alicefoufa','password':TEST_PASSWORD})
    assert r.status_code==200
    assert 'alice_session' in client.cookies
    assert client.get('/api/auth/me').json()['username']=='alicefoufa'
    assert client.put('/api/months/2026/11/income',json={'income_cents':1000}).status_code==403
    token={'X-CSRF-Token':r.json()['csrf_token']}
    assert client.put('/api/months/2026/11/income',json={'income_cents':1000},headers={**token,'Origin':'https://evil.example'}).status_code==403
    assert client.put('/api/months/2026/11/income',json={'income_cents':1000},headers=token).status_code==200
    assert client.post('/api/auth/logout',headers=token).status_code==200
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/register',json={'username':'x','password':'x'}).status_code==404

def test_income_fixed_leisure_and_month_isolation(logged):
    c,h=logged
    m='/api/months/2026/11'
    assert c.put(m+'/income',json={'income_cents':150000},headers=h).status_code==200
    defaults=c.get(m).json()['fixed_expenses']
    assert {e['name'] for e in defaults}=={'Transporte da faculdade e trabalho','Plano do celular'}
    transport=next(e for e in defaults if e['name'].startswith('Transporte'))
    phone=next(e for e in defaults if e['name']=='Plano do celular')
    assert c.patch(m+f'/fixed/{transport["id"]}',json={'amount_cents':18000},headers=h).status_code==200
    assert c.patch(m+f'/fixed/{phone["id"]}',json={'amount_cents':5000},headers=h).status_code==200
    assert c.put(m+'/card-bill',json={'final_amount_cents':40000,'is_paid':False},headers=h).status_code==200
    create=c.post(m+'/leisure',json={'name':'Cinema','amount_cents':12000,'expense_date':'2026-11-12','notes':'Com amigos'},headers=h)
    assert create.status_code==201
    info=create.json()
    assert info['remaining_cents']==75000
    assert info['fixed_total_cents']==63000
    assert info['leisure_total_cents']==12000
    leisure=info['leisure_expenses'][0]
    assert c.patch(m+f'/leisure/{leisure["id"]}',json={'notes':'Sessão de cinema'},headers=h).status_code==200
    assert c.patch(m+f'/leisure/{leisure["id"]}',json={'amount_cents':10000},headers=h).json()['remaining_cents']==77000
    assert c.put(m+'/card-bill',json={'final_amount_cents':40000,'is_paid':True},headers=h).json()['remaining_cents']==77000
    assert c.patch(m+f'/fixed/{phone["id"]}',json={'is_paid':True},headers=h).json()['remaining_cents']==77000
    dec=c.get('/api/months/2026/12').json()
    assert dec['income_cents']==0 and dec['fixed_total_cents']==0 and dec['leisure_expenses']==[]
    assert c.patch('/api/months/2026/12/fixed/'+str(phone['id']),json={'amount_cents':999},headers=h).status_code==404
    assert c.get(m).json()['remaining_cents']==77000
    assert c.delete(m+f'/leisure/{leisure["id"]}',headers=h).json()['remaining_cents']==87000
    assert c.get('/api/history').status_code==200
    assert len(c.get('/api/history').json())==2
    # Frontend e backend devem rejeitar gastos fora do mês.
    assert c.post(m+'/leisure',json={'name':'Errado','amount_cents':100,'expense_date':'2026-12-01'},headers=h).status_code==422

def test_purchases_installments_and_card_accounting(logged):
    c,h=logged
    november='/api/months/2026/11'
    december='/api/months/2026/12'
    c.put(november+'/income',json={'income_cents':150000},headers=h)
    c.put(december+'/income',json={'income_cents':150000},headers=h)
    purchase={'name':'Tênis','total_amount_cents':10001,'purchase_date':'2026-11-14','description':'Presente','category':'Roupas','installment_count':3,'first_billing_year':2026,'first_billing_month':12}
    response=c.post('/api/purchases',json=purchase,headers=h)
    assert response.status_code==201,response.text
    p=response.json()
    assert [(x['billing_year'],x['billing_month'],x['amount_cents']) for x in p['installments']]==[(2026,12,3334),(2027,1,3334),(2027,2,3333)]
    assert c.get(november).json()['remaining_cents']==150000
    dec=c.get(december).json()
    assert dec['forecast_cents']==3334 and dec['remaining_cents']==150000
    dec=c.post(december+'/card-bill/apply-forecast',headers=h).json()
    assert dec['card_bill_cents']==3334 and dec['remaining_cents']==146666
    assert c.post(december+'/card-bill/apply-forecast',headers=h).json()['remaining_cents']==146666
    assert len(c.get('/api/installments/2027/1').json())==1
    assert c.get('/api/months/2027/1').json()['forecast_cents']==3334
    assert c.get('/api/months/2027/2').json()['forecast_cents']==3333
    purchase['total_amount_cents']=9000
    assert c.put(f'/api/purchases/{p["id"]}',json=purchase,headers=h).json()['installments'][0]['amount_cents']==3000
    assert c.get(december).json()['forecast_cents']==3000
    # Fatura contabilizada é independente da projeção, sem desconto automático.
    assert c.get(december).json()['remaining_cents']==146666
    assert c.delete(f'/api/purchases/{p["id"]}',headers=h).status_code==200
    assert c.get(december).json()['forecast_cents']==0
    assert c.get(december).json()['card_bill_cents']==3334
    assert c.get(december).json()['remaining_cents']==146666


def test_copy_fixed_from_previous_month_without_card_bill(logged):
    c,h=logged
    prev='/api/months/2026/11';dest='/api/months/2026/12'
    defaults=c.get(prev).json()['fixed_expenses']
    phone=next(x for x in defaults if x['name']=='Plano do celular')
    c.patch(prev+f'/fixed/{phone["id"]}',json={'amount_cents':4900,'is_paid':True},headers=h)
    c.put(prev+'/card-bill',json={'final_amount_cents':10000,'is_paid':True},headers=h)
    result=c.post(dest+'/copy-fixed',headers=h)
    assert result.status_code==200,result.text
    assert result.json()['fixed_total_cents']==4900
    assert result.json()['card_bill_cents']==0
    assert all(not x['is_paid'] for x in result.json()['fixed_expenses'])
    assert c.post(dest+'/copy-fixed',headers=h).status_code==409


def test_rate_limiting_and_validation(client):
    for _ in range(5):
        assert client.post('/api/auth/login',json={'username':'alicefoufa','password':'incorrect'}).status_code==401
    assert client.post('/api/auth/login',json={'username':'alicefoufa','password':TEST_PASSWORD}).status_code==429


def test_preferences_persist_after_relogin(logged):
    c,h=logged
    assert c.put('/api/preferences',json={'selected_theme':'coraline'},headers=h).status_code==200
    assert c.get('/api/preferences').json()['selected_theme']=='coraline'
    assert c.post('/api/auth/logout',headers=h).status_code==200
    login=c.post('/api/auth/login',json={'username':'alicefoufa','password':TEST_PASSWORD})
    assert login.status_code==200
    assert c.get('/api/preferences').json()['selected_theme']=='coraline'
    assert c.put('/api/preferences',json={'selected_theme':'nonsense'},headers={'X-CSRF-Token':login.json()['csrf_token']}).status_code==422

def test_finances_persist_after_new_session(logged):
    c,h=logged
    url='/api/months/2026/11'
    assert c.put(url+'/income',json={'income_cents':245678},headers=h).status_code==200
    assert c.post(url+'/leisure',json={'name':'Café','amount_cents':2350,'expense_date':'2026-11-05','notes':'Anotação preservada'},headers=h).status_code==201
    assert c.post('/api/auth/logout',headers=h).status_code==200
    assert c.get(url).status_code==401
    login=c.post('/api/auth/login',json={'username':'alicefoufa','password':TEST_PASSWORD})
    assert login.status_code==200
    result=c.get(url).json()
    assert result['income_cents']==245678
    assert result['remaining_cents']==243328
    assert result['leisure_expenses'][0]['notes']=='Anotação preservada'


def test_expired_sessions_cannot_access_finances(logged):
    from app.db import get_db
    from app.main import app
    from app.models import Session as LoginSession
    from app.security import utcnow
    from datetime import timedelta
    from sqlalchemy import select
    c,h=logged
    gen=app.dependency_overrides[get_db]()
    db=next(gen)
    session=db.scalar(select(LoginSession))
    session.expires_at=utcnow()-timedelta(minutes=1)
    db.commit()
    gen.close()
    assert c.get('/api/auth/me').status_code==401
    assert c.get('/api/months/2026/11').status_code==401


def test_purchase_validation_and_month_bounds(logged):
    c,h=logged
    purchase={'name':'Produto','total_amount_cents':1,'purchase_date':'2026-11-14','description':'','category':'Outros','installment_count':3,'first_billing_year':2026,'first_billing_month':12}
    assert c.post('/api/purchases',json=purchase,headers=h).status_code==422
    assert c.get('/api/months/2026/13').status_code==422
    assert c.put('/api/months/2026/11/income',json={'income_cents':12.5},headers=h).status_code==422
    assert c.post('/api/purchases',json={**purchase,'total_amount_cents':300,'installment_count':1},headers=h).status_code==201
