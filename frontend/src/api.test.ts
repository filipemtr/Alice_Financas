import {describe,it,expect} from 'vitest'
import {currency,parseMoney,monthLabel,shiftMonth} from './api'

describe('valores monetários exatos em centavos',()=>{
  it('entende notação brasileira',()=>{
    expect(parseMoney('1.500,00')).toBe(150000)
    expect(parseMoney('1500,00')).toBe(150000)
    expect(parseMoney('35,90')).toBe(3590)
    expect(parseMoney('R$ 1.500,01')).toBe(150001)
    expect(parseMoney('0,01')).toBe(1)
    expect(parseMoney('2.50')).toBe(250)
  })
  it('não aceita valores malformados ou negativos',()=>{
    expect(()=>parseMoney('-1,00')).toThrow()
    expect(()=>parseMoney('12,345')).toThrow()
    expect(()=>parseMoney('abc')).toThrow()
  })
  it('formata moeda e datas pt-BR',()=>{
    expect(currency(150000)).toContain('1.500,00')
    expect(monthLabel(2026,11)).toContain('novembro')
    expect(shiftMonth(2026,12,1)).toEqual({year:2027,month:1})
  })
})
