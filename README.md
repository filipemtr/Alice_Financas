# Alice Finanças 🎀

Aplicação **privada** de finanças pessoais, com interface rosa, login exclusivo, pagamentos fixos, gastos de lazer com anotações, fatura do próximo mês, compras parceladas, histórico mensal e **PostgreSQL persistente**.

**Status da entrega:** backend validado com pytest e migração Alembic em SQLite de teste. O build React e a execução de contêineres PostgreSQL não puderam ser testados neste ambiente por indisponibilidade do registro npm e do Docker; execute as verificações abaixo antes de colocar dados reais em produção.

## Stack

- Frontend: React 19, TypeScript, Vite, Tailwind CSS 4, Motion, Lucide, Recharts, TanStack Query.
- Backend: FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, Argon2id.
- Database: PostgreSQL 16 (volume persistente no Docker).
- Proxy local: Nginx servindo app e encaminhando `/api` para o backend **no mesmo domínio**, facilitando cookies seguros.

## Instalação via Docker (recomendada)

**Pré-requisitos:** Docker com Compose v2, Python 3 para configurar as variáveis.

```bash
./setup.sh
# A senha solicitada no terminal é a senha inicial privada da Alice.
docker compose up --build -d
docker compose ps
```

Acesse **http://localhost:8088** e entre com o usuário `alicefoufa` e a senha inicial que você informou ao executar `./setup.sh`.

O script cria `.env` com permissão restrita; esse arquivo é ignorado pelo Git. **Nenhuma senha real está embutida no código ou no ZIP.** Na primeira inicialização, `python -m app.seed` cria uma conta única com hash Argon2id. Reinicializações não mudam a senha.

O banco persiste em um volume nomeado (`pgdata`); `docker compose down` não o apaga. **Não execute `docker compose down -v`**, pois remove os volumes.

### Incorporar personagens PNG transparentes

Antes de subir o site, com internet disponível, execute:

```bash
python3 scripts/baixar-imagens.py
```

Se alguma fonte bloquear o download, veja as cinco páginas e os nomes dos arquivos em [docs/IMAGENS.md](docs/IMAGENS.md); o site ainda funciona com fallback online ou ícones. Para deixar tudo embutido e independente de sites externos, baixe os cinco PNGs localmente antes de reconstruir a imagem frontend.

### Subir os serviços

```bash
docker compose logs -f api
docker compose restart
# Encerrar sem excluir os dados:
docker compose down
```

### Alterar a senha após a primeira inicialização

Como a senha inicial foi mencionada em uma conversa, **recomenda-se substituí-la antes de publicar o site**:

```bash
docker compose exec -it api python -m app.change_password
```

O script pede a nova senha sem exibi-la, atualiza o hash e revoga as sessões existentes. Depois, remova a senha inicial do ambiente da aplicação após criar a conta, ou atualize sua configuração privada, pois o seed só a utiliza quando o usuário ainda não existe.

## Funcionalidades

| Área | O que faz |
|---|---|
| Login | Apenas `alicefoufa`, sem registro e sem e-mail; cookie HttpOnly e CSRF; logout renderiza login imediatamente sem recarregar |
| Renda mensal | Valor editável que compõe o orçamento do mês selecionado |
| Pagamentos fixos | Fatura, transporte, celular e categorias extras, pagos/pendentes |
| Gastos de lazer | Valor, descrição, data, anotações, edição e exclusão |
| Saldo | Renda − pagamentos fixos − lazer, com cálculo no servidor |
| Próxima fatura | Compras e parcelas no mês em que serão cobradas |
| Aplicar previsão | Copia a previsão para a única fatura do mês, sem desconto duplicado |
| Histórico | Consulta meses anteriores sem sobrescrever seus registros |
| Configurações | Cinco temas com paletas globais, personagens decorativos, painéis, gráficos e fundos, salvos no banco |

**Regra da fatura:** compras programadas criam previsão de cobrança, mas **não são debitadas da renda** até o valor ser colocado na fatura daquele mês. A fatura é representada uma única vez nos pagamentos fixos; marcar um item como pago não volta a subtraí-lo.

**Imagens dos temas:** os componentes decorativos agora usam PNGs existentes de Hello Kitty, Fluttershy, Snoopy, Coraline e Amélie Poulain, selecionados na internet. Os temas mudam os fundos, gradientes, cores de cards, botões, navegação, gráficos e as ilustrações do site. Os arquivos de terceiros não foram incluídos no ZIP por restrições de acesso externo do ambiente de geração; veja [docs/IMAGENS.md](docs/IMAGENS.md) para baixar imagens originais para o site. Links externos são usados como fallback quando os arquivos locais ainda não existem.

**Nota de direitos:** as páginas de origem indicam uso pessoal/não comercial. Os personagens continuam sujeitos aos direitos dos respectivos titulares; confira a permissão antes de uso comercial.

## Testes

Backend (em ambiente Python com dependências):

```bash
cd backend
python -m pip install -r requirements-dev.txt
pytest -q tests
```

Frontend, depois de conectar a npm:

```bash
cd frontend
npm install
npm run build
npm test
```

E2E (requer a aplicação completa executando):

```bash
cd frontend
npx playwright install chromium
E2E_PASSWORD='sua-senha-de-TESTE' npm run test:e2e
```

Use uma conta/banco de testes para os testes E2E. Não compartilhe nem publique a senha real no terminal de terceiros ou em logs.

## Desenvolvimento sem Docker

1. Instale o Python 3.12+, Node 22+ e PostgreSQL 16+.
2. Configure `DATABASE_URL` apontando para um PostgreSQL local, `INITIAL_PASSWORD`, `INITIAL_USERNAME=alicefoufa`, `ALLOWED_ORIGINS=http://localhost:5173`, `COOKIE_SECURE=false`.
3. Rode no diretório `backend`: `alembic upgrade head`, `python -m app.seed`, `uvicorn app.main:app --reload --port 8000`.
4. Rode em `frontend`: `npm install && npm run dev`.
5. Abra `http://localhost:5173`; o Vite encaminha `/api` ao backend.

## Estrutura

```text
alice-financas/
├── backend/
│   ├── alembic/versions/0001_initial.py
│   ├── app/{main,models,services,schemas,security,db,seed,change_password}.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/{App.tsx,api.ts,types.ts,style.css}
│   ├── public/favicon.svg
│   ├── nginx.conf
│   └── package.json
├── compose.yaml
├── .env.example
├── setup.sh
└── docs/DEPLOY.md
```

## Segurança e responsabilidade

- Apenas backend acessa o PostgreSQL; banco não tem porta pública em `compose.yaml`.
- Senhas são verificadas com Argon2id e ficam como hash no banco.
- Sessões: token aleatório no cookie HttpOnly, hash no banco e expiração configurável.
- Escritas usam CSRF em cabeçalho, origin check e validação Pydantic.
- Login limitado a cinco falhas por IP a cada 15 minutos em tabela compartilhada.
- Não há cadastro de novos usuários e os endpoints privados exigem sessão.
- Em produção, HTTPS e `COOKIE_SECURE=true` são obrigatórios.
- **Backups são responsabilidade do operador:** o volume é persistente, mas não substitui cópias externas.

Veja [docs/DEPLOY.md](docs/DEPLOY.md) para orientações de deploy e backup.

## Atualização v1.3 — logout e aparência

Esta revisão foi feita para corrigir o problema de a interface não exibir as mudanças anteriores.

- **Logout imediato:** a navegação privada é desmontada no clique em **Sair da conta**, antes de aguardar a resposta da API; a revogação da sessão continua no servidor e uma falha é informada no login.
- **Cinco aparências distintas:** fundos, barras de navegação, cabeçalhos, painéis, cards, gráficos e gradientes mudam em cada tema; um seletor direto foi adicionado ao topo do painel.
- **Imagens:** o `Content-Security-Policy` do Nginx anteriormente bloqueava os endereços das fontes de PNG. As fontes explicitamente utilizadas foram autorizadas em `img-src`. Os PNGs não estão empacotados, pois o ambiente de desenvolvimento não conseguiu baixá-los; rode `python3 scripts/baixar-imagens.py` conectado à internet para incorporá-los no site.
- **Versão visível:** depois de entrar, a página mostra `v1.3 • 11/11/2026` no rodapé. Também existe `http://localhost:8088/version.json` com `"version":"1.3.0"`.

### Atualizar uma instalação existente sem apagar o banco

1. Faça backup do volume do PostgreSQL antes de qualquer operação de manutenção.
2. **Extraia os arquivos do ZIP sobre o diretório `alice-financas` que você já usa**, preservando o `.env` e a pasta de dados. Não crie uma instalação separada se deseja manter os históricos.
3. Na raiz do projeto, execute `./atualizar-site.sh`. Ele faz o download opcional das imagens e reconstrói **somente o serviço web**, preservando o serviço de banco e seus volumes. **Não use `docker compose down -v`.**
4. Visite `http://localhost:8088/version.json` e confirme `1.3.0`. Depois abra o dashboard, confirme que o rodapé mostra `v1.3` e alterne os temas pelo seletor no topo da página. Se o navegador estiver mostrando arquivos antigos, faça um recarregamento completo com `Ctrl+Shift+R`.

A pasta `docs/temas-v13.html` contém uma **demonstração estática das paletas**, não a aplicação conectada ao backend. O arquivo `docs/comparativo-temas-v13.png` mostra cinco renderizações da mesma estrutura com os novos estilos. Os personagens aparecem no app somente quando os PNGs externos são carregados corretamente.

**Limites de validação:** 9 testes automatizados do backend passaram. Os arquivos TypeScript passaram por validação de sintaxe e os temas por inspeção de CSS computado no Chromium. O build completo React e os testes E2E contra Docker/PostgreSQL não puderam ser executados neste ambiente, pois faltam dependências npm e o Docker executável.
