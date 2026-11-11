export type Theme = 'kitty' | 'pony' | 'snoopy' | 'amelie' | 'coraline'
export type View = 'overview' | 'card' | 'history' | 'settings'
export interface FixedExpense {id:number;name:string;amount_cents:number;due_date:string|null;is_paid:boolean}
export interface LeisureExpense {id:number;name:string;amount_cents:number;expense_date:string;notes:string}
export interface Summary {year:number;month:number;income_cents:number;fixed_total_cents:number;leisure_total_cents:number;remaining_cents:number;forecast_cents:number;card_bill_cents:number;card_bill_configured:boolean;card_bill_paid:boolean;fixed_expenses:FixedExpense[];leisure_expenses:LeisureExpense[]}
export interface HistoryItem extends Omit<Summary,'fixed_expenses'|'leisure_expenses'> {}
export interface Installment {installment_number:number;billing_year:number;billing_month:number;amount_cents:number}
export interface MonthlyInstallment {purchase_id:number;name:string;purchase_date:string;description:string;amount_cents:number;installment_number:number;installment_count:number}
export interface Purchase {id:number;name:string;total_amount_cents:number;purchase_date:string;description:string;category:string;installment_count:number;first_billing_year:number;first_billing_month:number;installments:Installment[]}
export interface PurchaseInput {name:string;total_amount_cents:number;purchase_date:string;description:string;category:string;installment_count:number;first_billing_year:number;first_billing_month:number}
