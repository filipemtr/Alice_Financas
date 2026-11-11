# Alice Finanças 💗

### Gestão financeira pessoal, simples e personalizada.

O **Alice Finanças** é uma aplicação web full stack desenvolvida para facilitar o controle financeiro pessoal pra minha namorada, reunindo receitas, despesas, faturas e planejamento mensal em uma interface moderna, intuitiva e personalizável.

O projeto combina uma experiência visual agradável com uma arquitetura estruturada, autenticação privada e persistência de dados.

## Funcionalidades

- **Dashboard financeiro:** visualização de receitas, despesas e saldo disponível.
- **Organização mensal:** gerenciamento independente das informações financeiras de cada mês.
- **Despesas fixas e variáveis:** acompanhamento de compromissos recorrentes e gastos ocasionais.
- **Controle de cartões:** organização de faturas, compras futuras e parcelamentos.
- **Histórico financeiro:** consulta aos registros de meses anteriores.
- **Cálculos automáticos:** atualização dos valores disponíveis conforme os lançamentos.
- **Autenticação:** acesso privado com usuário e senha.
- **Temas personalizados:** diferentes identidades visuais, animações e elementos decorativos.
- **Interface responsiva:** experiência adaptada para computadores e dispositivos móveis.

## Tecnologias

**Frontend**
- React
- TypeScript
- Vite
- Tailwind CSS
- Motion
- Recharts

**Backend**
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Argon2

**Banco de dados e infraestrutura**
- PostgreSQL
- Docker e Docker Compose
- Supabase
- Render
- Vercel

## Arquitetura

A aplicação utiliza uma arquitetura cliente-servidor, separando as responsabilidades entre interface, lógica de negócio e persistência de dados.

O frontend em React se comunica com uma API REST desenvolvida em FastAPI, responsável pela autenticação, validação das operações e gerenciamento dos registros financeiros.

O PostgreSQL garante a persistência dos dados, enquanto o Alembic gerencia as migrações do esquema do banco.

A infraestrutura foi planejada para permitir execução local com Docker e implantação em serviços de nuvem.

## Segurança

O projeto contempla mecanismos de proteção como:

- Armazenamento de senhas com hash Argon2.
- Autenticação baseada em sessões.
- Cookies com atributos de segurança.
- Proteção contra CSRF.
- Validação de dados no backend.
- Credenciais configuradas por variáveis de ambiente.
- Comunicação HTTPS em produção.

## Objetivo

Desenvolver uma solução de gestão financeira que una **organização, praticidade e personalização**, demonstrando a integração entre desenvolvimento frontend, backend, banco de dados e infraestrutura.

---

**Desenvolvido por Filipe Monteiro.**
