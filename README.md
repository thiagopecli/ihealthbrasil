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

- Blacklist de refresh token apos rotacao habilitada

### Variaveis de ambiente JWT (opcionais)

```env
```

### Migracoes necessarias

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

- Campo `profile` no usuario com `choices` e indice no banco
- Registro no Django Admin com exibicao e filtro por perfil

### Importante sobre banco local (SQLite)


Windows PowerShell:

```powershell
Remove-Item .\db.sqlite3 -Force
python manage.py migrate
python manage.py createsuperuser
```

Linux/macOS:

rm -f db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Sprint 01 - Quarta tarefa concluida

API de autenticacao entregue com endpoints de registro, login, logout e renovacao de token usando DRF + JWT.

### Endpoints de autenticacao

- `POST /api/auth/register/` -> registro de usuario
### RBAC basico por perfil

### Exemplo de logout

Envie o refresh token no corpo da requisicao:
```

### Banco por ambiente
- Ambiente producao (`DJANGO_ENV=production`):
	- `DATABASE_URL` obrigatorio (PostgreSQL).
	- `SECRET_KEY` obrigatorio.

```text
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_do_banco
```

## Objetivo do projeto

- operacao com split de pagamento entre marketplace e fornecedor;
- suporte nativo a multiplos idiomas e moedas.


- Back-end: Python + Django + Django REST Framework
- Banco producao: PostgreSQL
- Banco local desenvolvimento: SQLite
- Fila assicrona: Celery + Redis
- Armazenamento de arquivos: S3 compativel
- Observabilidade: Sentry + OpenTelemetry + logs estruturados JSON


- Seguranca por padrao (security by default)
- Compliance by design (LGPD e trilhas de auditoria desde o inicio)
- Dominios desacoplados por app Django
- Integracoes externas encapsuladas por gateways/adapters
- Processos criticos assicronos com retentativa e idempotencia

## Estrutura inicial de dominios (apps Django)

- accounts: usuarios, papeis, permissoes, MFA, consentimentos
- catalog: produtos, categorias, composicao, bula, restricoes de uso
- prescriptions: upload/validacao de receita, status, auditoria
- cart_checkout: carrinho, checkout, regras de elegibilidade
- orders: pedidos, itens, ciclo de vida e rastreio
- payments: transacoes, split, repasses, conciliacao
- providers: cadastro de fornecedores e compliance do seller
- international: idioma, pais, moeda, conversao
- audit: trilha imutavel de eventos sensiveis

- Prescription
- PaymentSplit
- Payout
- CurrencyRate
- Product 1:N ProductRegulatoryRule
- Order 1:N OrderItem
- Order 1:N PaymentSplit
- requires_prescription (bool)
- active_ingredient
- dosage
- controlled_substance_class

## Sprint 02 - Primeira tarefa concluida

Criacao dos modelos de catálogo de produtos com suporte a variações.

### Modelos criados

- **Category**: Categoria de produtos
  - `name`: Nome único da categoria
  - `description`: Descrição (opcional)
  - `slug`: Slug único para URLs
  - Índices: `slug`

- **Product**: Produto do marketplace
  - `category`: ForeignKey para Category
  - `name`: Nome do produto
  - `description`: Descrição completa
  - `price`: Preço decimal com 2 casas
  - `requires_prescription`: Flag para produtos que requerem prescrição
  - `stock`: Quantidade em estoque
  - `sku`: SKU único para inventário
  - `slug`: Slug para URLs
  - `is_active`: Flag de ativação (índice)
  - Índices: `slug`, `is_active`, `sku`, `(category, is_active)`

- **ProductVariation**: Variações de um produto (tamanho, cor, concentração, etc)
  - `product`: ForeignKey para Product
  - `name`: Nome da variação (ex: "Tamanho", "Cor", "Concentração")
  - `value`: Valor específico (ex: "P", "M", "G" ou "Azul", "Vermelho")
  - `sku_suffix`: Sufixo para completar SKU único
  - `price_modifier`: Adicional ao preço base
  - `stock`: Estoque específico desta variação
  - Propriedade calculada: `final_price` (price do product + price_modifier)
  - Unique constraint: `(product, name, value)`
  - Índices: `product`, `(product, name)`

### API REST endpoints

- `GET /api/categories/` -> lista categorias
- `POST /api/categories/` -> criar categoria (admin only)
- `GET /api/categories/{slug}/` -> detalhes da categoria
- `PUT/PATCH /api/categories/{slug}/` -> atualizar categoria (admin)
- `DELETE /api/categories/{slug}/` -> deletar categoria (admin)

- `GET /api/products/` -> lista produtos ativos (com filtro por categoria)
- `POST /api/products/` -> criar produto (admin only)
- `GET /api/products/{slug}/` -> detalhes do produto com variações
- `PUT/PATCH /api/products/{slug}/` -> atualizar produto (admin)
- `DELETE /api/products/{slug}/` -> deletar produto (admin)
- `GET /api/products/requires_prescription/` -> lista produtos com prescrição
- `GET /api/products/{slug}/variations/` -> lista variações de um produto

- `GET /api/variations/` -> lista variações (com filtro por product)
- `POST /api/variations/` -> criar variação (admin only)
- `GET /api/variations/{id}/` -> detalhes da variação
- `PUT/PATCH /api/variations/{id}/` -> atualizar variação (admin)
- `DELETE /api/variations/{id}/` -> deletar variação (admin)

### Serializers

- `CategorySerializer`: Criação/listagem de categorias
- `ProductListSerializer`: Listagem simplificada de produtos
- `ProductDetailSerializer`: Detalhes completos com variações
- `ProductCreateUpdateSerializer`: Criação/atualização de produtos
- `ProductVariationSerializer`: CRUD de variações

### Admin Django

- Registro de Category, Product e ProductVariation
- Inline para adicionar variações direto na tela de edição de produto
- Filtros por: categoria, prescrição, ativação, data
- Busca por: nome, SKU, slug

### Validações e configurações

- `max-line-length = 120` para flake8 (arquivo `.flake8`)
- Admin em português (verbose_name, verbose_name_plural)
- Pre-commit e CI completamente funcional para o novo app

## Sprint 02 - Segunda tarefa concluida

Campos específicos para a área da saúde: dosagem, bulas e restrições de venda.

### Campos expandidos no Product

- `active_ingredient`: Princípio ativo (texto)
- `controlled_substance_class`: Classificação de substância controlada (ex: C1, C4)
- `min_age_required`: Idade mínima permitida para compra (0 = sem restrição)
- `max_age_allowed`: Idade máxima permitida para compra (0 = sem restrição)

### Novos modelos criados

- **ProductDosage**: Informações de dosagem para um produto
  - `product`: ForeignKey para Product
  - `strength`: Força/concentração (ex: 500mg, 10mg/5mL, 2%)
  - `unit`: Unidade de medida (mg, mcg, g, %)
  - `frequency_recommendation`: Frequência recomendada (ex: 2x ao dia)
  - `is_default`: Flag para dosagem padrão
  - Unique constraint: `(product, strength, unit)`
  - Índices: `product`, `(product, is_default)`

- **ProductPackageInsert**: Bula/Insert de embalagem (documento PDF)
  - `product`: ForeignKey para Product
  - `language`: Idioma (pt_BR, en_US, es_ES)
  - `title`: Título da bula (opcional)
  - `content`: Conteúdo em HTML ou texto
  - `file_url`: URL de arquivo PDF
  - `requires_prescription_note`: Flag se marca "Venda sob prescrição"
  - Unique constraint: `(product, language)`
  - Índices: `product`, `language`

- **SalesRestriction**: Restrições de venda para um produto
  - `product`: ForeignKey para Product
  - `restriction_type`: Tipo de restrição (age_min, age_max, region, professional_required, license_required, custom)
  - `description`: Descrição humanizada da restrição
  - `detail`: Detalhes técnicos/completos (opcional)
  - `is_active`: Flag de ativação
  - Índices: `product`, `restriction_type`, `(product, is_active)`

### API REST endpoints

- `GET /api/dosages/` -> lista dosagens (filtro por product)
- `POST /api/dosages/` -> criar dosagem (admin only)
- `GET /api/dosages/{id}/` -> detalhes dosagem
- `PUT/PATCH /api/dosages/{id}/` -> atualizar dosagem (admin)
- `DELETE /api/dosages/{id}/` -> deletar dosagem (admin)

- `GET /api/package-inserts/` -> lista bulas (filtro por product)
- `POST /api/package-inserts/` -> criar bula (admin only)
- `GET /api/package-inserts/{id}/` -> detalhes bula
- `PUT/PATCH /api/package-inserts/{id}/` -> atualizar bula (admin)
- `DELETE /api/package-inserts/{id}/` -> deletar bula (admin)

- `GET /api/sales-restrictions/` -> lista restrições (filtro por product)
- `POST /api/sales-restrictions/` -> criar restrição (admin only)
- `GET /api/sales-restrictions/{id}/` -> detalhes restrição
- `PUT/PATCH /api/sales-restrictions/{id}/` -> atualizar restrição (admin)
- `DELETE /api/sales-restrictions/{id}/` -> deletar restrição (admin)

### Serializers adicionados

- `ProductDosageSerializer`: CRUD de dosagens
- `ProductPackageInsertSerializer`: CRUD de bulas
- `SalesRestrictionSerializer`: CRUD de restrições
- `ProductDetailSerializer` atualizado: inclui dosages, package_inserts, sales_restrictions
- `ProductCreateUpdateSerializer` atualizado: novos campos de health

### Admin Django expandido

- Inlines para adicionar dosagens, bulas e restrições direto da tela de produto
- Novo admin para ProductDosage com filtros por unit e is_default
- Novo admin para ProductPackageInsert com filtros por language e restrição de prescrição
- Novo admin para SalesRestriction com filtros por tipo e ativação
- Busca expandida: agora inclui active_ingredient



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
