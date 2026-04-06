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
- Celery + Redis (tarefas assíncronas)
- Gunicorn (servidor WSGI para produção)
- Docker + Docker Compose (deploy básico)
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

Para processar tarefas assincronas (Sprint 8), execute tambem o worker Celery em outro terminal:

```bash
celery -A config worker -l info
```

Healthcheck:

- `GET /health/`

Documentacao da API:

- `GET /api/schema/` (OpenAPI)
- `GET /api/docs/swagger/` (Swagger UI)
- `GET /api/docs/redoc/` (ReDoc)

## Deploy basico com Docker

### 1) Ajustar `.env` para ambiente de container

- `DJANGO_ENV=production`
- `DEBUG=False`
- `ALLOWED_HOSTS=127.0.0.1,localhost`
- `CSRF_TRUSTED_ORIGINS` com os domínios HTTPS do ambiente
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`

### 2) Subir API + worker + Redis

```bash
docker compose up --build
```

Serviços:

- `web`: Django + Gunicorn em `http://127.0.0.1:8000`
- `worker`: Celery worker
- `redis`: broker/result backend para tarefas assíncronas

## Sprint 8: Integrações Externas

### SMS via Twilio

Configurar variáveis de ambiente:

```env
SMS_ENABLED=True
SMS_PROVIDER=twilio  # ou 'mock' para testes
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
```

### Prescrições com Memed

Para validação externa de receitas:

```env
MEMED_ENABLED=True
MEMED_PROVIDER=memed  # ou 'mock' para testes
MEMED_API_KEY=your_api_key
MEMED_API_BASE_URL=https://api.memed.com.br/v1
```

No admin, após submeter um receita, use o action "Enviar para validacao Memed".

### Email de Notificações

Configurar provider de email:

```env
EMAIL_ENABLED=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
EMAIL_FROM_ADDRESS=noreply@ihealthbrasil.com.br
```

Or usar console em desenvolvimento:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Celery Beat: Tarefas Agendadas

Para marcar receitas como expiradas automaticamente (diariamente à meia-noite UTC):

```bash
celery -A config beat -l info
```

Em produção (Docker), considere usar `worker-pool-restarts` ou `Kubernetes CronJob`.

### Healthcheck Expandido

```bash
GET /health/           # status básico
GET /health/?detailed=true  # inclui Redis/broker
```

Resposta exemplo:

```json
{
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok"
  }
}
```

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

## Status por sprint (backend)

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

- i18n funcional na API por `Accept-Language` com `LocaleMiddleware`
- bulas com resolucao automatica por idioma (pt_BR, en_US, es_ES) e fallback
- traducao de mensagens principais de validacao para pt/en/es
- modelo de precificacao multimoeda por pais/moeda (`ProductPrice`)
- resposta de catalogo com preco contextual (`price`, `price_currency`, `price_country`, `price_is_fallback`)

Headers e query params suportados na resolucao de idioma/moeda:

- `Accept-Language` para idioma da resposta e selecao de bula
- `X-Country` ou `country` para pais de precificacao
- `X-Currency` ou `currency` para moeda de precificacao

Endpoint novo:

- `GET/POST /api/product-prices/` (admin para escrita)

### Sprint 04 (entregue)

- modelos `Order` e `OrderItem` implementados
- endpoints de pedidos com listagem e detalhe
- carrinho persistente com `Cart` e `CartItem`
- endpoints de carrinho: adicionar, atualizar, remover, limpar e consultar carrinho do usuario
- checkout completo do carrinho para `Order` e `OrderItem` com recalculo consolidado
- base de checkout para pagamento via `payment-intent`

### Sprint 05 (entregue)

- fluxo de upload e auditoria de receitas medicas para produtos controlados
- endpoint de aprovacao/rejeicao de receita por admin
- trilha de auditoria LGPD para acesso a receitas
- armazenamento privado de receitas fora de `/media` publico
- URL assinada temporaria para download seguro de receita

### Sprint 06 (entregue)

- integração de gateway de pagamento com provider configuravel (`mock` e `stripe`)
- criação de customer (comprador) no gateway
- criação de connected account (fornecedor) para split
- criação de payment intent no checkout com retorno de token (`client_secret`) e link (`checkout_url`)
- validação operacional completa com o gateway real escolhido

Endpoint novo de checkout/pagamento:

- `POST /api/orders/{id}/payment-intent/`
  - payload opcional: `provider_user_id`, `currency`

### Sprint 07 (entregue)

- webhook de pagamento com validacao de assinatura
- processamento idempotente de eventos do gateway
- atualizacao automatica de status do pedido

Endpoint novo:

- `POST /api/payments/webhooks/gateway/`

### Sprint 08 (entregue)

- integracao de SMS por provider configuravel (`mock` e `twilio`)
- disparo assíncrono de notificacao por mudanca de status do pedido
- fallback seguro para execucao local quando broker estiver indisponivel
- auditoria de notificacoes externas em `ExternalNotification`

### Sprint 09 (entregue)

- endpoints de gestao do fornecedor com restricao por ownership
- extrato financeiro de split para parceiro
- resumo agregado para dashboard financeiro

### Sprint 10 (entregue)

- otimização de querysets em endpoints críticos para reduzir N+1
- documentação OpenAPI enriquecida com exemplos de payload em endpoints de pagamento
- hardening de segurança para produção (HSTS, cookies seguros, SSL redirect)
- Dockerização do backend com `Dockerfile` e `docker-compose.yml`
- CI com validação de build de imagem Docker

## Proximos passos sugeridos (foco producao)

- concluir i18n na API e precificacao multimoeda
- adicionar expiracao automatica de receitas via tarefa agendada
- elevar observabilidade com `correlation_id`, metricas e alertas
- expandir testes de integracao para fluxos criticos (checkout, webhook, prescricao)

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

