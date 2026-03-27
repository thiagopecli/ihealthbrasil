# Projecao de Sprints - Back-end iHealth Brasil

## Versao organizada para Trello (copiar e colar)

Sugestao de listas no board:

- Product Backlog
- Sprint Backlog
- Em Desenvolvimento
- Em Code Review
- Em QA/Homologacao
- Concluido

Padrao de card no Trello (usar em todas as sprints):

- Titulo: [Sprint X] Nome curto da entrega
- Descricao: objetivo da sprint + impacto no negocio
- Checklist 1: Escopo tecnico
- Checklist 2: Compliance LGPD
- Checklist 3: Testes e qualidade
- Checklist 4: Observabilidade
- Critero de aceite: o que precisa estar funcionando para mover para Concluido

### Sprint 0 - Infra, Qualidade e Processo (3-5 dias)

Objetivo: criar base de engenharia para escalar sem divida tecnica.

Cards:

1. [Sprint 0] Padrao de branch e protecao da main
- Definir fluxo de branch (feature/*)
- Habilitar regras de protecao da main
- Exigir pull request para merge

2. [Sprint 0] Convencao de commits
- Adotar Conventional Commits
- Publicar guia rapido para o time

3. [Sprint 0] Pre-commit e padrao de codigo
- Configurar black
- Configurar isort
- Configurar flake8
- Configurar bandit

4. [Sprint 0] CI minimo
- Rodar lint no pipeline
- Rodar testes no pipeline
- Falhar pipeline em vulnerabilidade critica

Criterio de aceite da sprint:
- Nenhum PR mergeia sem passar no CI.

### Sprint 1 - Fundacao, Auth e LGPD Base

Objetivo: API inicial segura com autenticacao e papeis.

Cards:

1. [Sprint 1] Bootstrap Django + DRF
- Estruturar projeto Django
- Configurar variaveis de ambiente
- Configurar SQLite local e PostgreSQL para producao

2. [Sprint 1] JWT completo
- Login
- Refresh token
- Logout
- Revogacao basica de token

3. [Sprint 1] Usuario customizado e perfis
- Criar User custom
- Perfis: Paciente, Medico, Fornecedor, Admin
- Permissoes basicas por papel (RBAC)

4. [Sprint 1] Compliance e auditoria base
- Registrar eventos de login/logout
- Nao logar dados sensiveis

Criterio de aceite da sprint:
- Endpoints de auth funcionando com RBAC basico.

### Sprint 2 - Catalogo e Regras de Saude

Objetivo: modelar produtos de saude com regras regulatorias.

Cards:

1. [Sprint 2] Modelos de catalogo
- Categoria
- Produto
- Variacao

2. [Sprint 2] Campos regulatorios
- exige_prescricao
- dosagem
- bula
- restricao de venda

3. [Sprint 2] CRUD de catalogo
- Criar produto
- Editar produto
- Listar produto
- Remover produto

4. [Sprint 2] Filtros do front-end
- Filtro por categoria
- Filtro por exige receita

Criterio de aceite da sprint:
- Front-end consegue listar e filtrar produtos com regras de saude.

### Sprint 3 - i18n e Precificacao Multimoeda

Objetivo: preparar catalogo para operacao global.

Cards:

1. [Sprint 3] i18n na API
- Configurar idiomas pt-BR, en-US, es-ES, fr-FR
- Traduzir mensagens de erro principais

2. [Sprint 3] Modelo de precos por pais/moeda
- Tabela de preco por moeda
- Conversao controlada por regra de negocio

3. [Sprint 3] Resposta por Accept-Language
- Retornar conteudo traduzido
- Retornar moeda adequada por contexto

Criterio de aceite da sprint:
- Catalogo retorna idioma e moeda corretos por cabecalho.

### Sprint 4 - Carrinho e Pedido

Objetivo: habilitar jornada de compra ate pedido pendente.

Cards:

1. [Sprint 4] Carrinho e itens
- Criar carrinho
- Adicionar item
- Remover item

2. [Sprint 4] Pedido e status
- Modelar Order
- Status: Pendente, Pago, Em Analise Medica, Cancelado

3. [Sprint 4] Checkout inicial
- Converter carrinho em pedido
- Persistir totais e itens

Criterio de aceite da sprint:
- Fluxo carrinho -> pedido pendente funcionando no banco.

### Sprint 5 - Prescricoes e Receitas (critico)

Objetivo: fluxo seguro para produtos controlados.

Cards:

1. [Sprint 5] Modelo de receita vinculada ao pedido
- Upload de arquivo
- Viculo com pedido e paciente

2. [Sprint 5] Armazenamento seguro
- Integrar S3 privado
- Gerar URL assinada temporaria

3. [Sprint 5] Auditoria de acesso a receita
- Registrar quem acessou
- Registrar quando acessou
- Registrar origem da acao

Criterio de aceite da sprint:
- Receita enviada no checkout com acesso controlado e auditavel.

### Sprint 6 - Pagamento e Split (parte 1)

Objetivo: conectar gateway e preparar entidades financeiras.

Cards:

1. [Sprint 6] SDK do gateway
- Instalar e configurar credenciais seguras

2. [Sprint 6] Customer e conta conectada
- Criar comprador no gateway
- Criar fornecedor para split

3. [Sprint 6] Intencao de pagamento
- Gerar payment intent / token / link

Criterio de aceite da sprint:
- Back-end gera intencao de pagamento valida no checkout.

### Sprint 7 - Webhooks e automacao de status (parte 2)

Objetivo: fechar ciclo financeiro real.

Cards:

1. [Sprint 7] Regra matematica de split
- Calcular comissao iHealth
- Calcular valor do fornecedor

2. [Sprint 7] Endpoint de webhook seguro
- Validar assinatura do webhook
- Processar eventos de pagamento

3. [Sprint 7] Atualizacao automatica de pedido
- Pago
- Falha
- Expirado

Criterio de aceite da sprint:
- Pedido muda de status com base na confirmacao do gateway.

### Sprint 8 - Integracoes externas (Memed / SMS)

Objetivo: conectar ecossistema externo sem travar API.

Cards:

1. [Sprint 8] Integracao API de receita ou SMS
- Memed (prescricao) ou Twilio/Zenvia (mensageria)

2. [Sprint 8] Processamento assincrono
- Configurar Celery + Redis
- Mover tarefas de terceiros para fila

3. [Sprint 8] Acoplamento com status do pedido
- Enviar notificacoes por evento de pedido

Criterio de aceite da sprint:
- Integracao externa funcionando com tarefas assincronas.

### Sprint 9 - Painel do Fornecedor e Relatorios

Objetivo: autonomia do parceiro dentro do marketplace.

Cards:

1. [Sprint 9] Endpoints de gestao do fornecedor
- CRUD de produtos do proprio fornecedor
- Restricao por ownership

2. [Sprint 9] Dashboard financeiro
- Total vendido
- Extrato de split
- Filtros por periodo

Criterio de aceite da sprint:
- API do parceiro funcional para operacao diaria.

### Sprint 10 - Refatoracao, Docs e Deploy

Objetivo: hardening final para producao.

Cards:

1. [Sprint 10] Performance e N+1
- Revisar queries com select_related
- Revisar queries com prefetch_related

2. [Sprint 10] Documentacao OpenAPI
- Swagger/drf-yasg atualizado
- Exemplos de payload de endpoints criticos

3. [Sprint 10] Deploy e seguranca final
- Dockerizacao
- CI/CD basico
- Revisao final de seguranca

Criterio de aceite da sprint:
- Sistema documentado, otimizado e pronto para release.

## Cards fixos de governanca (criar em toda sprint)

1. [Governanca] Checklist Compliance da Sprint
- Permissao explicita em endpoint novo
- Sem log sensivel (CPF, token, dados medicos)
- Auditoria para acesso a receita
- Politica de retencao para dados sensiveis

2. [Governanca] Checklist NFR da Sprint
- p95 endpoint critico menor que 500ms
- Taxa de erro dentro do alvo
- Verificacao de disponibilidade

3. [Governanca] Checklist Observabilidade da Sprint
- Logs estruturados ativos
- correlation_id presente
- Dashboard/alerta atualizado para feature nova

## Sprint 0: Infraestrutura, Qualidade e Ritual de Time (3-5 dias)

Foco: Criar base tecnica para acelerar as sprints sem gerar divida tecnica.

- Definicao de estrategia de branch (main protegida + feature branches).
- Convencao de commits (Conventional Commits: feat, fix, chore, docs, refactor).
- Configuracao de pre-commit com black, isort, flake8 e bandit.
- Pipeline CI inicial com passos: lint, testes unitarios e scanner de seguranca.
- Estrutura base de testes (pytest + factory_boy ou fixtures simples).

Entregavel da semana: Esteira minima de qualidade rodando em toda pull request, com bloqueio de merge em caso de falha.

## Sprint 1: Fundacao, Autenticacao e LGPD Base

Foco: Preparar o terreno e garantir o controle de acesso seguro.

- Setup inicial do projeto Django, configuracao de variaveis de ambiente e banco de dados (SQLite local / PostgreSQL producao).
- Configuracao do Django Rest Framework (DRF) e JWT (JSON Web Tokens) para autenticacao.
- Criacao de um modelo de Usuario customizado, separando os perfis (Paciente, Medico, Parceiro/Fornecedor, Admin).

Entregavel da semana: API rodando com endpoints de registro, login, logout e renovacao de token, com permissoes basicas baseadas em papeis (Role-Based Access Control).

## Sprint 2: Catalogo de Produtos e Regras de Saude

Foco: Modelagem do core business da iHealth.

- Criacao dos modelos de Categoria, Produto e Variacoes.
- Implementacao de campos especificos para a area da saude: flags para "exige prescricao", dosagem, bulas e restricoes de venda.
- Criacao dos endpoints CRUD (Create, Read, Update, Delete) para o catalogo.

Entregavel da semana: Endpoints do catalogo prontos para o front-end listar os produtos, com filtros por categoria e exigencia de receita.

## Sprint 3: Internacionalizacao (i18n) e Precificacao

Foco: Preparar o terreno para a expansao global (Portugues, Ingles, Espanhol, Frances).

- Configuracao do sistema de traducao nativo do Django para mensagens de erro e respostas da API.
- Modelagem da estrutura de precos com suporte a multiplas moedas (Tabela de Precos por pais/moeda).

Entregavel da semana: Endpoints de catalogo retornando dados no idioma e na moeda corretos com base no cabecalho da requisicao (Accept-Language).

## Sprint 4: Gestao de Carrinho e Pedidos

Foco: A jornada de compra do usuario.

- Modelagem do Carrinho de Compras e Itens do Carrinho.
- Modelagem do Pedido (Order) e seus status (Pendente, Pago, Em Analise Medica, Cancelado).
- Endpoints para adicionar/remover itens e fechar o pedido (checkout inicial).

Entregavel da semana: Fluxo completo de criacao de carrinho e conversao para um pedido pendente no banco de dados.

## Sprint 5: Gestao de Prescricoes e Receitas (Critico)

Foco: O diferencial de saude mental e produtos controlados (LGPD nivel maximo).

- Criacao do modelo para upload e vinculo de receitas medicas ao Pedido.
- Configuracao de armazenamento seguro na nuvem (ex: AWS S3 com URLs assinadas temporarias) para garantir que os arquivos nao fiquem expostos publicamente.
- Logs de auditoria: registrar no banco qual usuario acessou qual receita e quando.

Entregavel da semana: Fluxo seguro de envio de receita pelo paciente no checkout e endpoint de auditoria para o painel admin.

## Sprint 6: Integracao de Pagamento e Split (Parte 1)

Foco: Preparacao do gateway de pagamento (Stripe, Pagar.me, etc.).

- Instalacao e configuracao do SDK do gateway escolhido.
- Criacao das logicas de "Customer" (comprador) e "Connected Account" (vendedores/fornecedores) no gateway para permitir o split.
- Geracao da intencao de pagamento no fechamento do carrinho.

Entregavel da semana: Comunicacao back-end com o gateway estabelecida e geracao de links/tokens de pagamento.

## Sprint 7: Integracao de Pagamento e Webhooks (Parte 2)

Foco: Fechar o ciclo financeiro e automatizar os status.

- Criacao da logica matematica do Split: separar o valor do fornecedor e a comissao da iHealth.
- Desenvolvimento do endpoint de Webhook para escutar as atualizacoes do gateway (ex: "Pagamento Aprovado", "Boleto Vencido").

Entregavel da semana: Pedidos mudando de status automaticamente no banco de dados com base na confirmacao real do pagamento.

## Sprint 8: Integracoes Externas (Memed / SMS)

Foco: Comunicacao com sistemas de saude e mensageria.

- Integracao com API externa de prescricao (como Memed) ou provedor de SMS (como Twilio/Zenvia) para envio de links.
- Criacao de rotinas assincronas (usando Celery + Redis, se necessario) para nao travar a API durante requisicoes a terceiros.

Entregavel da semana: Disparo de SMS automatizado ou validacao de receita externa funcionando acoplada ao status do pedido.

## Sprint 9: Painel do Parceiro e Relatorios

Foco: Dar autonomia para os fornecedores do marketplace.

- Endpoints para os fornecedores gerenciarem seus proprios produtos.
- Endpoints de dashboard financeiro: quanto o fornecedor vendeu, extrato do split de pagamento.

Entregavel da semana: API do painel de controle do vendedor 100% funcional.

## Sprint 10: Refatoracao, Documentacao e Deploy

Foco: Polimento final e entrega.

- Otimizacao de queries no banco (uso de select_related e prefetch_related do Django para evitar o problema de N+1 queries).
- Geracao da documentacao da API (Swagger / drf-yasg).
- Revisao final de seguranca e auxilio na configuracao do deploy (Dockerizacao e CI/CD basicos).

Entregavel da semana: Codigo documentado, otimizado e pronto para producao.

## NFRs Minimos (obrigatorios desde Sprint 1)

- Performance: p95 de endpoints criticos menor que 500ms em carga normal.
- Disponibilidade: alvo inicial de 99.5% em ambiente de producao.
- Confiabilidade: retentativa com backoff para integracoes externas criticas.
- Recuperacao: RPO de 15 minutos e RTO de 1 hora.
- Seguranca: 0 vulnerabilidades criticas abertas antes de deploy de release.

## Checkpoint de Compliance por Sprint (LGPD + Saude)

Checklist obrigatorio no fechamento de cada sprint:

- Todos os endpoints novos possuem permissao explicita (deny by default).
- Nenhum log novo expõe CPF, dados medicos, token ou documento bruto.
- Acesso a receita medica gera evento de auditoria (quem, quando, acao, origem).
- Campos sensiveis possuem politica de retencao definida.
- Histories com dado sensivel possuem base legal e trilha de consentimento quando aplicavel.

## Plano de Observabilidade (implementacao progressiva)

Sprint 1 a 2:

- Logs estruturados JSON em toda API.
- correlation_id por requisicao para rastreio ponta a ponta.

Sprint 3 a 5:

- Metricas tecnicas (latencia, erro 4xx/5xx, throughput).
- Dashboard inicial para endpoints criticos.

Sprint 6 a 8:

- Metricas de negocio: conversao checkout, taxa de falha de pagamento, tempo medio de validacao de receita.
- Alertas para indisponibilidade de gateways (pagamento, SMS, prescricao).

Sprint 9 a 10:

- Tracing distribuido para diagnostico de gargalos entre API, fila e servicos externos.
- Playbook de incidentes com procedimentos de resposta e escalonamento.

## Definicao de Pronto Expandida (DoD)

Uma historia so e considerada concluida quando:

- Codigo revisado e aprovado em pull request.
- Testes da feature aprovados no CI.
- Checkpoint de compliance validado.
- Metricas e logs da feature validados em ambiente de homologacao.
- Documentacao tecnica atualizada.
