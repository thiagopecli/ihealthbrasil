# ihealthbrasil

Backend de marketplace healthtech para saude mental e produtos com exigencias regulatorias, incluindo itens com prescricao.

## Objetivo

Construir uma base de API robusta com foco em:

- autenticacao segura com JWT
- controle de acesso por perfil (RBAC)
- catalogo de produtos com dados de saude
- boas praticas de engenharia e qualidade desde o inicio

## Stack atual

- Python 3.13
- Django 5.x
- Django REST Framework
- Simple JWT
- drf-spectacular (OpenAPI/Swagger)
- Stripe SDK (integração de pagamentos)
- SQLite no desenvolvimento local
- PostgreSQL em producao (via `DATABASE_URL`)

## Estrutura do projeto

- `accounts/`: usuario customizado, autenticacao e RBAC
- `products/`: catalogo, variacoes, dosagens, bulas e restricoes
- `config/`: configuracoes centrais do Django e roteamento

## Setup rapido (desenvolvimento)

### 1) Criar e ativar ambiente virtual

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2) Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

### 3) Configurar variaveis de ambiente

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 4) Aplicar migracoes e subir servidor

```bash
python manage.py migrate
python manage.py runserver
```

Healthcheck:

- `GET /health/`

Documentacao da API:

- `GET /api/schema/` (OpenAPI)
- `GET /api/docs/swagger/` (Swagger UI)
- `GET /api/docs/redoc/` (ReDoc)

## Qualidade e contribuicao

Dependencias de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

Habilitar hooks de pre-commit:

```bash
pre-commit install
```

Validacoes locais:

```bash
pre-commit run --all-files
python manage.py check
python manage.py test
```

Padroes adotados:

- formatter: `black`
- organizacao de imports: `isort`
- lint: `flake8`
- seguranca estatica: `bandit`
- commits: Conventional Commits (ver `CONTRIBUTING.md`)

## Autenticacao e usuarios

### Modelo de usuario customizado

Perfis suportados:

- `PATIENT`
- `DOCTOR`
- `PROVIDER`
- `ADMIN`

### Endpoints de autenticacao

Base: `/api/auth/`

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/verify/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

Endpoints de RBAC para validacao:

- `GET /api/auth/rbac/admin-only/`
- `GET /api/auth/rbac/provider-or-admin/`

Payload exemplo para login:

```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

## Catalogo de produtos

Base: `/api/`

Recursos principais:

- `categories`
- `products`
- `variations`
- `dosages`
- `package-inserts`
- `sales-restrictions`

Observacoes:

- as rotas sao expostas via DRF Router
- produto possui suporte a campos regulatorios (ex.: prescricao, principio ativo, classe controlada)
- CRUD administrativo protegido por permissoes no backend

## Banco de dados por ambiente

Desenvolvimento:

- SQLite (arquivo local)

Producao (`DJANGO_ENV=production`):

- `DATABASE_URL` obrigatorio
- `SECRET_KEY` obrigatorio

Exemplo:

```text
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
```

## Observacao importante sobre usuario customizado

Se o banco SQLite local estiver inconsistente por mudancas iniciais no modelo de usuario, recrie o banco:

Windows PowerShell:

```powershell
Remove-Item .\db.sqlite3 -Force
python manage.py migrate
python manage.py createsuperuser
```

Linux/macOS:

```bash
rm -f db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Status por sprint

### Sprint 0 (entregue)

- fundacao de qualidade (pre-commit, lint, seguranca, testes)
- pipeline de CI no GitHub Actions
- guia de contribuicao e padrao de commits

### Sprint 01 (entregue)

- setup inicial Django com env e banco por ambiente
- DRF + JWT
- usuario customizado com perfis de negocio
- endpoints de auth e RBAC
- auditoria de autenticacao (login/logout) com sanitizacao de dados sensiveis

### Sprint 02 (entregue)

- modelagem do catalogo (categorias, produtos e variacoes)
- expansao de saude/regulatorio (dosagens, bulas, restricoes)
- endpoints REST para recursos de catalogo

### Sprint 03 (entregue)

- documentacao de request/response dos endpoints principais
- matriz de permissoes por perfil com base nas rules reais do backend
- colecao versionada de testes de API para smoke e validacao funcional

### Sprint 04 (entregue)

- OpenAPI/Swagger/ReDoc habilitados para documentacao da API
- cobertura de RBAC ampliada para cenarios de escrita administrativa no catalogo
- colecao Bruno versionada para execucao de fluxos de auth, RBAC e catalogo

### Sprint 05 (entregue)

- fluxo de upload e auditoria de receitas medicas para produtos controlados
- endpoint de aprovacao/rejeicao de receita por admin
- trilha de auditoria LGPD para acesso a receitas

### Sprint 06 (entregue)

- integração de gateway de pagamento com provider configuravel (`mock` e `stripe`)
- criação de customer (comprador) no gateway
- criação de connected account (fornecedor) para split
- criação de payment intent no checkout com retorno de token (`client_secret`) e link (`checkout_url`)

Endpoint novo de checkout/pagamento:

- `POST /api/orders/{id}/payment-intent/`
  - payload opcional: `provider_user_id`, `currency`

## Proximos passos sugeridos

- adicionar exemplos OpenAPI mais detalhados por endpoint (request/response e erros)
- expandir cenarios de smoke para fluxos negativos de autenticacao e autorizacao
- fortalecer cobertura de testes de integracao para regras regulatorias do catalogo

## Artefatos da Sprint 03

- referencia de endpoints (request/response): `docs/sprint-03-api-reference.md`
- matriz de permissoes por perfil: `docs/sprint-03-rbac-matrix.md`
- colecao de testes de API (Postman): `api-tests/postman/ihealthbrasil-sprint03.postman_collection.json`

### Como usar a colecao Postman

1. importar o arquivo da colecao no Postman
2. ajustar variaveis da colecao:
  - `base_url` (padrao local: `http://127.0.0.1:8000`)
  - `username` e `password`
  - `product_slug` para testar endpoints por slug
3. executar na ordem:
  - `01 - Auth > Token obtain pair` (preenche `access` e `refresh` automaticamente)
  - `02 - RBAC`
  - `03 - Catalogo`

## Artefatos da Sprint 04

- OpenAPI Schema: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc: `/api/docs/redoc/`
- colecao Bruno versionada: `api-tests/bruno/ihealthbrasil-sprint04/`

### Como usar a colecao Bruno

1. abrir no Bruno a pasta `api-tests/bruno/ihealthbrasil-sprint04/`
2. selecionar o ambiente `local`
3. executar `auth/token-obtain-pair.bru`
4. preencher variaveis `access` e `refresh` no ambiente
5. executar requests de `rbac/` e `catalog/`

