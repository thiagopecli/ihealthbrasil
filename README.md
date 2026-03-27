# ihealthbrasil

Marketplace healthtech para saude mental e produtos com exigencias regulatorias (incluindo itens com prescricao).

## Sprint 0 - Entregue

Fundacao de engenharia para qualidade e processo:

- Pre-commit com `black`, `isort`, `flake8` e `bandit`
- Pipeline CI em GitHub Actions com lint, seguranca e testes
- Convencao de commits (Conventional Commits) e fluxo de branch documentados

Arquivos da Sprint 0:

- `.pre-commit-config.yaml`
- `pyproject.toml`
- `requirements-dev.txt`
- `.github/workflows/ci.yml`
- `CONTRIBUTING.md`

### Como usar localmente

```bash
python -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
python manage.py check
python manage.py test
```

## Sprint 01 - Primeira tarefa concluida

Setup inicial do projeto Django com configuracao de variaveis de ambiente e banco de dados:

- Desenvolvimento local: SQLite (padrao)
- Producao: PostgreSQL via `DATABASE_URL`

### Estrutura criada

- `manage.py`
- `config/settings.py`
- `config/urls.py`
- `config/asgi.py`
- `config/wsgi.py`
- `.env.example`
- `requirements.txt`

### Como rodar localmente

1. Crie e ative um ambiente virtual Python:

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

2. Instale dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

No Windows PowerShell (alternativa):

```powershell
Copy-Item .env.example .env
```

4. Rode migracoes e servidor:

```bash
python manage.py migrate
python manage.py runserver
```

API de healthcheck disponivel em `/health/`.

## Sprint 01 - Segunda tarefa concluida

Configuracao do Django REST Framework (DRF) e JWT com `djangorestframework-simplejwt`.

### Endpoints de autenticacao JWT

- `POST /api/auth/token/` -> login (retorna access e refresh)
- `POST /api/auth/token/refresh/` -> gera novo access token
- `POST /api/auth/token/verify/` -> valida token

Exemplo de payload para login:

```json
{
	"username": "seu_usuario",
	"password": "sua_senha"
}
```

### Configuracao de seguranca aplicada

- DRF com autenticacao padrao via JWT
- Permissao padrao global: `IsAuthenticated`
- Rotacao de refresh token habilitada
- Blacklist de refresh token apos rotacao habilitada

### Variaveis de ambiente JWT (opcionais)

```env
JWT_ACCESS_MINUTES=15
JWT_REFRESH_DAYS=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True
```

### Migracoes necessarias

Como o blacklist foi habilitado, execute migracoes antes de rodar o servidor:

```bash
python manage.py migrate
python manage.py runserver
```

## Sprint 01 - Terceira tarefa concluida

Criacao de modelo de usuario customizado no app `accounts`, separado por perfis de negocio:

- `PATIENT` (Paciente)
- `DOCTOR` (Medico)
- `PROVIDER` (Parceiro/Fornecedor)
- `ADMIN` (Admin)

Configuracao aplicada:

- `AUTH_USER_MODEL = "accounts.User"`
- Campo `profile` no usuario com `choices` e indice no banco
- Registro no Django Admin com exibicao e filtro por perfil

### Importante sobre banco local (SQLite)

Como este projeto ja tinha migracoes aplicadas com o usuario padrao do Django, ao trocar para `AUTH_USER_MODEL` customizado e necessario recriar o banco local de desenvolvimento.

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

## Sprint 01 - Quarta tarefa concluida

API de autenticacao entregue com endpoints de registro, login, logout e renovacao de token usando DRF + JWT.

### Endpoints de autenticacao

- `POST /api/auth/register/` -> registro de usuario
- `POST /api/auth/token/` -> login (obtem access/refresh)
- `POST /api/auth/token/refresh/` -> renova access token
- `POST /api/auth/logout/` -> invalida refresh token (blacklist)
- `GET /api/auth/me/` -> dados do usuario autenticado

### RBAC basico por perfil

Perfis no usuario customizado:

- `PATIENT`
- `DOCTOR`
- `PROVIDER`
- `ADMIN`

Regras de permissao implementadas:

- `GET /api/auth/rbac/admin-only/` -> somente `ADMIN`
- `GET /api/auth/rbac/provider-or-admin/` -> `PROVIDER` ou `ADMIN`

### Exemplo de logout

Envie o refresh token no corpo da requisicao:

```json
{
	"refresh": "<refresh_token>"
}
```

### Banco por ambiente

- Ambiente local (`DJANGO_ENV=development`):
	- Se `DATABASE_URL` estiver vazio, usa SQLite automaticamente (`db.sqlite3`).

- Ambiente producao (`DJANGO_ENV=production`):
	- `DATABASE_URL` obrigatorio (PostgreSQL).
	- `SECRET_KEY` obrigatorio.
	- `DEBUG=False` recomendado.

Exemplo de URL PostgreSQL:

```text
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
```

## Objetivo do projeto

Construir um marketplace robusto, seguro e escalavel para:

- venda de produtos de saude mental e terapias;
- controle de produtos com exigencia de prescricao medica;
- operacao com split de pagamento entre marketplace e fornecedor;
- suporte nativo a multiplos idiomas e moedas.

## Stack proposta

- Back-end: Python + Django + Django REST Framework
- Banco producao: PostgreSQL
- Banco local desenvolvimento: SQLite
- Fila assicrona: Celery + Redis
- Armazenamento de arquivos: S3 compativel
- Observabilidade: Sentry + OpenTelemetry + logs estruturados JSON

## Principios de arquitetura

- Seguranca por padrao (security by default)
- Compliance by design (LGPD e trilhas de auditoria desde o inicio)
- Dominios desacoplados por app Django
- Integracoes externas encapsuladas por gateways/adapters
- Processos criticos assicronos com retentativa e idempotencia

## Estrutura inicial de dominios (apps Django)

- core: configuracoes comuns, utilitarios, classes base
- accounts: usuarios, papeis, permissoes, MFA, consentimentos
- catalog: produtos, categorias, composicao, bula, restricoes de uso
- prescriptions: upload/validacao de receita, status, auditoria
- cart_checkout: carrinho, checkout, regras de elegibilidade
- orders: pedidos, itens, ciclo de vida e rastreio
- payments: transacoes, split, repasses, conciliacao
- providers: cadastro de fornecedores e compliance do seller
- international: idioma, pais, moeda, conversao
- audit: trilha imutavel de eventos sensiveis
- notifications: email, SMS, webhooks

## Modelagem de dados (visao de alto nivel)

Entidades centrais:

- User
- PatientProfile
- ProviderProfile
- Product
- ProductRegulatoryRule
- Prescription
- PrescriptionValidation
- Cart
- Order
- OrderItem
- PaymentTransaction
- PaymentSplit
- Payout
- CurrencyRate
- LocalizedContent
- AuditEvent

Relacionamentos criticos:

- Product 1:N ProductRegulatoryRule
- Order 1:N OrderItem
- Order 1:N PaymentSplit
- Prescription 1:N PrescriptionValidation
- User 1:N AuditEvent

Campos importantes para produtos controlados:

- requires_prescription (bool)
- active_ingredient
- dosage
- controlled_substance_class
- regulatory_notes
- min_age
- contraindications (JSON)
- requires_medical_follow_up (bool)

## Fluxo de prescricao (resumo)

1. Usuario adiciona produto ao carrinho.
2. Checkout identifica itens que exigem prescricao.
3. Sistema bloqueia finalizacao sem receita valida.
4. Receita e enviada para validacao interna/externa (ex: Memed).
5. Status aprovado libera pagamento e emissao do pedido.
6. Todos os eventos sao registrados no modulo de auditoria.

## Seguranca e LGPD (nao negociavel)

Controles minimos obrigatorios:

- criptografia em repouso e em transito (TLS 1.2+)
- controle de acesso por papeis (RBAC) e escopo por recurso
- principio do menor privilegio para operadores internos
- mascaramento de dados sensiveis em logs
- trilha de auditoria imutavel para dados de saude e receitas
- base legal e consentimento versionado por finalidade
- politica de retencao e descarte seguro de dados
- mecanismo de atendimento a direitos do titular (LGPD)

Sugestoes tecnicas:

- campo sensivel com criptografia de aplicacao para documentos medicos
- assinaturas HMAC para validar integridade de callbacks/webhooks
- rotacao de chaves e secrets via cofre (Vault/Secrets Manager)

## Integracoes externas

### Receita medica

- gateway de prescricao com adaptador (MemedAdapter)
- fluxo assicrono para emissao, consulta e atualizacao de status
- fallback resiliente com fila de retentativa
- notificacao por SMS com provider desacoplado

### Pagamentos e split

Requisitos:

- split nativo no PSP (Stripe Connect, Pagar.me ou Mercado Pago)
- idempotencia por chave de requisicao
- conciliacao diaria automatica
- politica de estorno proporcional por participante do split

Modelo sugerido:

- PaymentTransaction (autorizacao/captura/estorno)
- PaymentSplit (percentual e valor por recebedor)
- Payout (repasse e status)
- LedgerEntry (razao contabil para rastreabilidade)

## Internacionalizacao e moedas

Idiomas de lancamento:

- pt-BR
- en-US
- es-ES
- fr-FR

Diretrizes:

- usar i18n nativo do Django para mensagens e validacoes
- armazenar conteudo traduzivel em LocalizedContent
- separar preco base de moeda de exibicao
- congelar taxa de cambio no momento da compra
- evitar float em valores monetarios (usar Decimal)

## Roadmap tecnico (90 dias)

### Fase 1 - Fundacao (semanas 1-3)

- bootstrap do projeto Django + DRF
- modelagem inicial de dominio (accounts, catalog, orders)
- setup de autenticacao, RBAC e auditoria base
- pipeline CI/CD e ambientes dev/stage/prod

### Fase 2 - Compliance e prescricao (semanas 4-6)

- modulo prescriptions completo
- upload seguro e validacao de receitas
- trilhas de auditoria detalhadas
- politicas LGPD operacionais

### Fase 3 - Pagamentos e split (semanas 7-9)

- integracao com PSP escolhido
- fluxo de cobranca com split
- conciliacao e tratamento de estornos
- monitoramento de eventos financeiros

### Fase 4 - Internacional e hardening (semanas 10-12)

- i18n completo (4 idiomas)
- suporte a moedas e taxa congelada
- testes de carga e seguranca
- readiness para go-live

## Qualidade e testes

- testes unitarios para regras de negocio criticas
- testes de integracao para APIs e gateways externos
- testes de contrato para webhooks e providers
- testes de permissao para recursos sensiveis
- SAST/DAST no CI

## Definicao de pronto (DoD) para features criticas

- regra de negocio coberta por testes
- trilha de auditoria implementada
- logs sem vazamento de dado sensivel
- autorizacao validada por perfil e escopo
- documentacao tecnica atualizada

## Proximo passo recomendado

Implementar agora o esqueleto do back-end com:

1. Projeto Django + DRF
2. Apps iniciais (core, accounts, catalog, prescriptions, orders, payments)
3. Modelo base de auditoria e RBAC
4. Docker Compose (app + postgres + redis)
