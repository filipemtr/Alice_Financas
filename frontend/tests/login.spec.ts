import {test,expect} from '@playwright/test'
test('login privado e painel mensal',async({page})=>{
  test.skip(!process.env.E2E_PASSWORD,'Defina E2E_PASSWORD em ambiente de teste')
  await page.goto('/')
  await expect(page.getByText('Organizar a vida')).toBeVisible()
  await page.getByPlaceholder('Digite seu usuário').fill('alicefoufa')
  await page.getByPlaceholder('Digite sua senha').fill(process.env.E2E_PASSWORD!)
  await page.getByRole('button',{name:'Entrar na minha conta'}).click()
  await expect(page.getByText('Olá, Alice')).toBeVisible()
  await expect(page.getByText('Pagamentos fixos').first()).toBeVisible()
  await page.getByRole('button',{name:'Próxima fatura'}).click()
  await expect(page.getByText('Compras registradas')).toBeVisible()
})

test('logout mostra login imediatamente, sem recarregar a página',async({page})=>{
  test.skip(!process.env.E2E_PASSWORD,'Defina E2E_PASSWORD em ambiente de teste')
  await page.goto('/')
  await page.getByPlaceholder('Digite seu usuário').fill('alicefoufa')
  await page.getByPlaceholder('Digite sua senha').fill(process.env.E2E_PASSWORD!)
  await page.getByRole('button',{name:'Entrar na minha conta'}).click()
  await expect(page.getByText('Olá, Alice')).toBeVisible()
  await page.getByRole('button',{name:'Sair da conta'}).click()
  // Verifica o login sem usar page.reload() e a saída do painel privado.
  await expect(page.getByPlaceholder('Digite seu usuário')).toBeVisible()
  await expect(page.getByRole('button',{name:'Entrar na minha conta'})).toBeVisible()
  await expect(page.getByText('Olá, Alice')).toHaveCount(0)
})

test('trocar tema altera paleta global da página',async({page})=>{
  test.skip(!process.env.E2E_PASSWORD,'Defina E2E_PASSWORD em ambiente de teste')
  await page.goto('/')
  await page.getByPlaceholder('Digite seu usuário').fill('alicefoufa')
  await page.getByPlaceholder('Digite sua senha').fill(process.env.E2E_PASSWORD!)
  await page.getByRole('button',{name:'Entrar na minha conta'}).click()
  await expect(page.getByText('Olá, Alice')).toBeVisible()
  await page.getByRole('button',{name:'Configurações'}).click()
  await page.getByRole('button',{name:/Fantasia Lunar/}).click()
  await expect(page.locator('.app-frame')).toHaveAttribute('data-theme','coraline')
  const bgCoraline=await page.locator('.sidebar').evaluate(el=>getComputedStyle(el).backgroundImage)
  await page.getByRole('button',{name:/Romântico Vintage/}).click()
  await expect(page.locator('.app-frame')).toHaveAttribute('data-theme','amelie')
  const bgAmelie=await page.locator('.sidebar').evaluate(el=>getComputedStyle(el).backgroundImage)
  expect(bgAmelie).not.toBe(bgCoraline)
})

test('logout troca para login mesmo que a resposta da API esteja lenta',async({page})=>{
  test.skip(!process.env.E2E_PASSWORD,'Defina E2E_PASSWORD no banco de teste')
  await page.goto('/')
  await page.getByPlaceholder('Digite seu usuário').fill('alicefoufa')
  await page.getByPlaceholder('Digite sua senha').fill(process.env.E2E_PASSWORD!)
  await page.getByRole('button',{name:'Entrar na minha conta'}).click()
  await expect(page.getByText('Olá, Alice')).toBeVisible()
  let releaseLogout:()=>void=()=>{}
  await page.route('**/api/auth/logout',async route=>{
    await new Promise<void>(resolve=>{releaseLogout=resolve})
    await route.continue()
  })
  await page.getByRole('button',{name:'Sair da conta'}).click()
  // Não espera a revogação da API para desmontar os dados privados.
  await expect(page.getByPlaceholder('Digite seu usuário')).toBeVisible()
  await expect(page.getByText('Olá, Alice')).toHaveCount(0)
  releaseLogout()
  await expect(page.getByRole('button',{name:'Entrar na minha conta'})).toBeEnabled()
})

test('a versão atualizada pode ser conferida na interface',async({page})=>{
  test.skip(!process.env.E2E_PASSWORD,'Defina E2E_PASSWORD no banco de teste')
  await page.goto('/')
  await page.getByPlaceholder('Digite seu usuário').fill('alicefoufa')
  await page.getByPlaceholder('Digite sua senha').fill(process.env.E2E_PASSWORD!)
  await page.getByRole('button',{name:'Entrar na minha conta'}).click()
  await expect(page.getByText('v1.3 • 11/11/2026')).toBeVisible()
  await expect(page.getByLabel('Tema visual')).toHaveValue('kitty')
})
