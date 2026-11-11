let csrfToken: string | null = null
export function setCsrf(token:string|null) {csrfToken = token}
export class ApiError extends Error {constructor(message:string, public status:number){super(message)}}
async function request<T>(path:string,method='GET',body?:unknown):Promise<T>{
  const headers:Record<string,string> = {}
  if(body!==undefined) headers['Content-Type']='application/json'
  if(method!=='GET' && csrfToken) headers['X-CSRF-Token']=csrfToken
  let response:Response
  try{response=await fetch('/api'+path,{method,headers,credentials:'include',body:body===undefined?undefined:JSON.stringify(body)})}
  catch{throw new ApiError('Não foi possível conectar ao servidor. Verifique sua conexão.',0)}
  if(!response.ok){
    let error='Não foi possível concluir a operação.'
    try{const data=await response.json();if(typeof data.detail==='string')error=data.detail;else if(Array.isArray(data.detail))error=data.detail.map((x:{msg:string})=>x.msg).join(' • ')}catch{}
    if(response.status===401)csrfToken=null
    throw new ApiError(error,response.status)
  }
  return response.json() as Promise<T>
}
export const api={
  get:<T>(path:string)=>request<T>(path),
  send:<T>(path:string,method:'POST'|'PUT'|'PATCH'|'DELETE',body?:unknown)=>request<T>(path,method,body),
  async me(){const value=await request<{username:string;csrf_token:string}>('/auth/me');setCsrf(value.csrf_token);return value},
  async login(username:string,password:string){const value=await request<{username:string;csrf_token:string}>('/auth/login','POST',{username,password});setCsrf(value.csrf_token);return value},
  async logout(){await request<{ok:boolean}>('/auth/logout','POST');setCsrf(null)}
}
export function currency(cents:number){return (cents/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'})}
export function inputMoney(cents:number){return (cents/100).toFixed(2).replace('.',',')}
export function parseMoney(value:string):number{
  let text=value.trim().replace(/\s/g,'').replace(/^R\$/i,'')
  if(!text)throw new Error('Informe um valor.')
  const comma=text.lastIndexOf(','), dot=text.lastIndexOf('.')
  if(comma>=0 && dot>=0){const dec=Math.max(comma,dot);text=text.slice(0,dec).replace(/[.,]/g,'')+'.'+text.slice(dec+1)}
  else if(comma>=0){text=text.replace(/\./g,'').replace(',','.')}
  else if(dot>=0){const parts=text.split('.');text=parts.length>2||parts.at(-1)?.length===3?parts.join(''):text}
  if(!/^\d+(?:\.\d{1,2})?$/.test(text))throw new Error('Valor inválido. Use, por exemplo, 35,90.')
  const [whole,dec='']=text.split('.')
  const total=Number(whole)*100+Number(dec.padEnd(2,'0'))
  if(!Number.isSafeInteger(total)||total>100_000_000_000)throw new Error('Valor muito alto.')
  return total
}
export function monthLabel(year:number,month:number){return new Date(year,month-1,1).toLocaleDateString('pt-BR',{month:'long',year:'numeric'})}
export function shortDate(d:string){return new Date(`${d}T12:00:00`).toLocaleDateString('pt-BR',{day:'2-digit',month:'short'})}
export function dateForMonth(year:number,month:number){const n=new Date();return n.getFullYear()===year&&n.getMonth()+1===month?`${year}-${String(month).padStart(2,'0')}-${String(n.getDate()).padStart(2,'0')}`:`${year}-${String(month).padStart(2,'0')}-01`}
export function shiftMonth(year:number,month:number,delta:number){const d=new Date(year,month-1+delta,1);return {year:d.getFullYear(),month:d.getMonth()+1}}
