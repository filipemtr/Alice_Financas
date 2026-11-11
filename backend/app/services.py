from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import MonthlyBudget,FixedExpense,LeisureExpense,MonthlyCardBill,Installment,Purchase

DEFAULT_EXPENSES = ('Transporte da faculdade e trabalho','Plano do celular')

def check_month(year:int,month:int):
    if not (2000<=year<=2100 and 1<=month<=12):
        from fastapi import HTTPException
        raise HTTPException(422,'Mês ou ano inválido')

def get_budget(db:Session,user_id:int,year:int,month:int,create:bool=True):
    check_month(year,month)
    budget=db.scalar(select(MonthlyBudget).where(MonthlyBudget.user_id==user_id, MonthlyBudget.year==year,MonthlyBudget.month==month))
    if budget or not create:return budget
    budget=MonthlyBudget(user_id=user_id,year=year,month=month,income_cents=0)
    db.add(budget)
    db.flush()
    for name in DEFAULT_EXPENSES:
        db.add(FixedExpense(budget_id=budget.id,name=name,amount_cents=0))
    db.add(MonthlyCardBill(budget_id=budget.id))
    db.commit()
    db.refresh(budget)
    return budget

def card_forecast(db:Session,year:int,month:int,user_id:int)->int:
    val=db.scalar(select(func.coalesce(func.sum(Installment.amount_cents),0)).join(Purchase,Purchase.id==Installment.purchase_id).where(Purchase.user_id==user_id,Installment.billing_year==year,Installment.billing_month==month))
    return int(val or 0)

def money_summary(db:Session,budget:MonthlyBudget):
    fixed=db.scalars(select(FixedExpense).where(FixedExpense.budget_id==budget.id).order_by(FixedExpense.id)).all()
    leisure=db.scalars(select(LeisureExpense).where(LeisureExpense.budget_id==budget.id).order_by(LeisureExpense.expense_date.desc(),LeisureExpense.id.desc())).all()
    bill=db.scalar(select(MonthlyCardBill).where(MonthlyCardBill.budget_id==budget.id))
    fixed_sum=sum(x.amount_cents for x in fixed)
    leisure_sum=sum(x.amount_cents for x in leisure)
    bill_final= bill.final_amount_cents if bill and bill.final_amount_cents is not None else 0
    total_fixed=fixed_sum+bill_final
    forecast=card_forecast(db,budget.year,budget.month,budget.user_id)
    return {
        'year':budget.year,'month':budget.month,'income_cents':budget.income_cents,
        'fixed_total_cents':total_fixed,'leisure_total_cents':leisure_sum,
        'remaining_cents':budget.income_cents-total_fixed-leisure_sum,
        'forecast_cents':forecast,'card_bill_cents':bill_final,
        'card_bill_configured':bool(bill and bill.final_amount_cents is not None),
        'card_bill_paid':bill.is_paid if bill else False,
        'fixed_expenses':[{'id':e.id,'name':e.name,'amount_cents':e.amount_cents,'is_paid':e.is_paid,'due_date':e.due_date.isoformat() if e.due_date else None} for e in fixed],
        'leisure_expenses':[{'id':e.id,'name':e.name,'amount_cents':e.amount_cents,'expense_date':e.expense_date.isoformat(),'notes':e.notes} for e in leisure]
    }

def installment_schedule(total:int,count:int,year:int,month:int):
    """Conserva os centavos exatos e distribui primeiro as parcelas com 1 centavo extra."""
    base,extra=divmod(total,count)
    return [(n+1, year+(month-1+n)//12, (month-1+n)%12+1, base+(n<extra)) for n in range(count)]

def replace_installments(db:Session,purchase:Purchase):
    for obj in db.scalars(select(Installment).where(Installment.purchase_id==purchase.id)).all():db.delete(obj)
    db.flush()
    for n,y,m,cents in installment_schedule(purchase.total_amount_cents,purchase.installment_count,purchase.first_billing_year,purchase.first_billing_month):
        db.add(Installment(purchase_id=purchase.id,installment_number=n,billing_year=y,billing_month=m,amount_cents=cents))

def purchase_to_dict(db:Session,p:Purchase):
    installments=db.scalars(select(Installment).where(Installment.purchase_id==p.id).order_by(Installment.installment_number)).all()
    return {'id':p.id,'name':p.name,'total_amount_cents':p.total_amount_cents,'purchase_date':p.purchase_date.isoformat(),'description':p.description,'category':p.category,'installment_count':p.installment_count,'first_billing_year':p.first_billing_year,'first_billing_month':p.first_billing_month,
            'installments':[{'installment_number':i.installment_number,'billing_year':i.billing_year,'billing_month':i.billing_month,'amount_cents':i.amount_cents} for i in installments]}
