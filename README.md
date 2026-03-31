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

## Proximos passos sugeridos

- documentar exemplos de request/response para cada endpoint
- adicionar tabela de permissoes por perfil
- incluir colecao de testes de API (Postman/Bruno) versionada
