from datetime import date,timedelta
import secrets
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from argon2.exceptions import VerifyMismatchError, VerificationError
from .db import get_db
from .models import User,Session as LoginSession,MonthlyBudget,FixedExpense,LeisureExpense,Purchase,Installment,MonthlyCardBill,Preference
from .schemas import LoginIn,IncomeIn,FixedIn,FixedPatch,LeisureIn,LeisurePatch,PurchaseIn,CardBillIn,PaidIn,ThemeIn
from .services import get_budget,check_month,money_summary,card_forecast,replace_installments,purchase_to_dict
from .security import Auth,auth_required,csrf_required,utcnow,sha,hasher,DUMMY_HASH,validate_origin,set_session_cookie,clear_session_cookie,client_ip,ensure_not_limited,add_failed_attempt,clear_failed_attempts
from .config import ALLOWED_ORIGINS,SESSION_HOURS

app=FastAPI(title='Alice Finanças',docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_credentials=True,allow_methods=['GET','POST','PATCH','PUT','DELETE'],allow_headers=['Content-Type','X-CSRF-Token'])

@app.get('/api/health')
def health():return {'ok':True}

@app.post('/api/auth/login')
def login(data:LoginIn,request:Request,response:Response,db:Session=Depends(get_db)):
    validate_origin(request)
    ip=client_ip(request)
    ensure_not_limited(db,ip)
    user=db.scalar(select(User).where(User.username==data.username)) if data.username=='alicefoufa' else None
    try:ok=hasher.verify(user.password_hash if user else DUMMY_HASH,data.password)
    except (VerifyMismatchError,VerificationError):ok=False
    if not user or not ok:
        add_failed_attempt(db,ip)
        raise HTTPException(401,'Usuário ou senha inválidos')
    clear_failed_attempts(db,ip)
    token=secrets.token_urlsafe(48)
    csrf=secrets.token_urlsafe(32)
    db.add(LoginSession(user_id=user.id,token_hash=sha(token),csrf_token=csrf,expires_at=utcnow()+timedelta(hours=SESSION_HOURS)))
    db.commit()
    set_session_cookie(response,token)
    return {'username':user.username,'csrf_token':csrf}

@app.get('/api/auth/me')
def me(auth:Auth=Depends(auth_required)):
    return {'username':auth.user.username,'csrf_token':auth.session.csrf_token}

@app.post('/api/auth/logout')
def logout(response:Response,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    db.delete(auth.session);db.commit()
    clear_session_cookie(response)
    return {'ok':True}

@app.get('/api/months/{year}/{month}')
def month_summary(year:int,month:int,db:Session=Depends(get_db),auth:Auth=Depends(auth_required)):
    return money_summary(db,get_budget(db,auth.user.id,year,month))

@app.put('/api/months/{year}/{month}/income')
def set_income(year:int,month:int,data:IncomeIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    budget.income_cents=data.income_cents;db.commit()
    return money_summary(db,budget)

@app.post('/api/months/{year}/{month}/fixed',status_code=201)
def add_fixed(year:int,month:int,data:FixedIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    if data.due_date and (data.due_date.year,data.due_date.month)!=(year,month):raise HTTPException(422,'Vencimento fora do mês selecionado')
    e=FixedExpense(budget_id=budget.id,**data.model_dump())
    db.add(e);db.commit()
    return money_summary(db,budget)

def own_fixed(db:Session,budget:MonthlyBudget,item_id:int):
    e=db.scalar(select(FixedExpense).where(FixedExpense.budget_id==budget.id,FixedExpense.id==item_id))
    if not e:raise HTTPException(404,'Pagamento não encontrado')
    return e

@app.patch('/api/months/{year}/{month}/fixed/{item_id}')
def edit_fixed(year:int,month:int,item_id:int,data:FixedPatch,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    e=own_fixed(db,budget,item_id)
    changes=data.model_dump(exclude_unset=True)
    if 'due_date' in changes and changes['due_date'] and (changes['due_date'].year,changes['due_date'].month)!=(year,month):raise HTTPException(422,'Vencimento fora do mês')
    for key,val in changes.items():
        if val is None and key!='due_date': raise HTTPException(422,'Campo não pode ser nulo')
        setattr(e,key,val)
    db.commit()
    return money_summary(db,budget)

@app.delete('/api/months/{year}/{month}/fixed/{item_id}')
def delete_fixed(year:int,month:int,item_id:int,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    e=own_fixed(db,budget,item_id)
    db.delete(e);db.commit()
    return money_summary(db,budget)

@app.post('/api/months/{year}/{month}/leisure',status_code=201)
def add_leisure(year:int,month:int,data:LeisureIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    if (data.expense_date.year,data.expense_date.month)!=(year,month):raise HTTPException(422,'Data fora do mês selecionado')
    budget=get_budget(db,auth.user.id,year,month)
    db.add(LeisureExpense(budget_id=budget.id,**data.model_dump()))
    db.commit()
    return money_summary(db,budget)

def own_leisure(db:Session,budget:MonthlyBudget,item_id:int):
    e=db.scalar(select(LeisureExpense).where(LeisureExpense.budget_id==budget.id,LeisureExpense.id==item_id))
    if not e:raise HTTPException(404,'Gasto não encontrado')
    return e

@app.patch('/api/months/{year}/{month}/leisure/{item_id}')
def edit_leisure(year:int,month:int,item_id:int,data:LeisurePatch,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    e=own_leisure(db,budget,item_id)
    changes=data.model_dump(exclude_unset=True)
    for key,val in changes.items():
        if val is None:raise HTTPException(422,'Campo não pode ser nulo')
        setattr(e,key,val)
    if (e.expense_date.year,e.expense_date.month)!=(year,month):raise HTTPException(422,'Data fora do mês selecionado')
    db.commit()
    return money_summary(db,budget)

@app.delete('/api/months/{year}/{month}/leisure/{item_id}')
def delete_leisure(year:int,month:int,item_id:int,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    db.delete(own_leisure(db,budget,item_id));db.commit()
    return money_summary(db,budget)

@app.put('/api/months/{year}/{month}/card-bill')
def set_card_bill(year:int,month:int,data:CardBillIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    bill=db.scalar(select(MonthlyCardBill).where(MonthlyCardBill.budget_id==budget.id))
    bill.final_amount_cents=data.final_amount_cents;bill.is_paid=data.is_paid
    db.commit()
    return money_summary(db,budget)

@app.post('/api/months/{year}/{month}/card-bill/apply-forecast')
def apply_forecast(year:int,month:int,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    budget=get_budget(db,auth.user.id,year,month)
    bill=db.scalar(select(MonthlyCardBill).where(MonthlyCardBill.budget_id==budget.id))
    bill.final_amount_cents=card_forecast(db,year,month,auth.user.id)
    db.commit()
    return money_summary(db,budget)

@app.post('/api/months/{year}/{month}/copy-fixed')
def copy_fixed(year:int,month:int,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    check_month(year,month)
    prevyear=year-1 if month==1 else year
    prevmonth=12 if month==1 else month-1
    prev=get_budget(db,auth.user.id,prevyear,prevmonth,create=False)
    budget=get_budget(db,auth.user.id,year,month)
    if not prev:return money_summary(db,budget)
    existing=db.scalars(select(FixedExpense).where(FixedExpense.budget_id==budget.id)).all()
    if any(e.amount_cents or e.is_paid for e in existing):
        raise HTTPException(409,'Este mês já possui pagamentos preenchidos')
    prevs=db.scalars(select(FixedExpense).where(FixedExpense.budget_id==prev.id)).all()
    # Substitui somente as linhas não configuradas do mês atual. Fatura não é copiada.
    for e in existing:db.delete(e)
    db.flush()
    for e in prevs:
        db.add(FixedExpense(budget_id=budget.id,name=e.name,amount_cents=e.amount_cents,is_paid=False))
    db.commit()
    return money_summary(db,budget)

@app.get('/api/purchases')
def purchases(db:Session=Depends(get_db),auth:Auth=Depends(auth_required)):
    allp=db.scalars(select(Purchase).where(Purchase.user_id==auth.user.id).order_by(Purchase.purchase_date.desc(),Purchase.id.desc())).all()
    return [purchase_to_dict(db,p) for p in allp]

@app.post('/api/purchases',status_code=201)
def add_purchase(data:PurchaseIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    p=Purchase(user_id=auth.user.id,**data.model_dump())
    db.add(p);db.flush()
    replace_installments(db,p)
    db.commit()
    return purchase_to_dict(db,p)

def own_purchase(db:Session,user_id:int,purchase_id:int):
    p=db.scalar(select(Purchase).where(Purchase.id==purchase_id,Purchase.user_id==user_id))
    if not p:raise HTTPException(404,'Compra não encontrada')
    return p

@app.put('/api/purchases/{purchase_id}')
def edit_purchase(purchase_id:int,data:PurchaseIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    p=own_purchase(db,auth.user.id,purchase_id)
    for key,val in data.model_dump().items():setattr(p,key,val)
    replace_installments(db,p)
    db.commit()
    return purchase_to_dict(db,p)

@app.delete('/api/purchases/{purchase_id}')
def delete_purchase(purchase_id:int,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    p=own_purchase(db,auth.user.id,purchase_id)
    for i in db.scalars(select(Installment).where(Installment.purchase_id==p.id)).all():db.delete(i)
    db.delete(p);db.commit()
    return {'ok':True}

@app.get('/api/installments/{year}/{month}')
def monthly_installments(year:int,month:int,db:Session=Depends(get_db),auth:Auth=Depends(auth_required)):
    check_month(year,month)
    installments=db.scalars(select(Installment).join(Purchase,Purchase.id==Installment.purchase_id).where(Purchase.user_id==auth.user.id,Installment.billing_year==year,Installment.billing_month==month).order_by(Installment.id)).all()
    return [{'purchase_id':i.purchase_id,'name':i.purchase.name,'purchase_date':i.purchase.purchase_date.isoformat(),'description':i.purchase.description,'amount_cents':i.amount_cents,'installment_number':i.installment_number,'installment_count':i.purchase.installment_count} for i in installments]

@app.get('/api/history')
def history(db:Session=Depends(get_db),auth:Auth=Depends(auth_required)):
    budgets=db.scalars(select(MonthlyBudget).where(MonthlyBudget.user_id==auth.user.id).order_by(MonthlyBudget.year.desc(),MonthlyBudget.month.desc())).all()
    return [{k:v for k,v in money_summary(db,b).items() if k not in ('fixed_expenses','leisure_expenses')} for b in budgets]

@app.get('/api/preferences')
def get_preferences(db:Session=Depends(get_db),auth:Auth=Depends(auth_required)):
    p=db.scalar(select(Preference).where(Preference.user_id==auth.user.id))
    return {'selected_theme':p.selected_theme if p else 'kitty'}

@app.put('/api/preferences')
def save_preferences(data:ThemeIn,db:Session=Depends(get_db),auth:Auth=Depends(csrf_required)):
    p=db.scalar(select(Preference).where(Preference.user_id==auth.user.id))
    if not p: p=Preference(user_id=auth.user.id);db.add(p)
    p.selected_theme=data.selected_theme
    db.commit()
    return {'selected_theme':p.selected_theme}
