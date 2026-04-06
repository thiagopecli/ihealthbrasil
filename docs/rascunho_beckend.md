# Projecao de Backend iHealth Brasil

Escopo deste documento:

- somente back-end
- sem itens de front-end
- foco em status real do que ja foi feito e no que ainda falta para producao

## Visao executiva

O backend ja entrega o nucleo do produto:

- autenticacao com JWT e RBAC
- catalogo regulatorio de produtos de saude
- prescricoes com auditoria LGPD
- pagamentos com split e webhook
- notificacoes assicronas por SMS
- painel do fornecedor e relatorios financeiros
- CI, pre-commit, Docker e documentacao OpenAPI

O que ainda impede considerar o sistema pronto para producao total:

- i18n funcional na API com Accept-Language
- precificacao multimoeda por pais/moeda
- expiracao automatica de receitas com tarefa agendada
- integracao externa de prescricao, se esta ainda for requisito de negocio
- tracing distribuido completo com stack externa, se o ambiente exigir
- alertas formais integrados ao monitoramento real

## Tabela resumo por sprint

| Sprint | Status | Conclusao estimada | O que ja esta pronto | Principal pendencia |
|---|---|---:|---|---|
| Sprint 0 | Concluida | 100% | CI, pre-commit, convencao de commits e base de qualidade | Proteger a main no GitHub |
| Sprint 1 | Concluida | 100% | Auth JWT, RBAC, usuario customizado e auditoria de login/logout | Reset de senha e reforcos opcionais |
| Sprint 2 | Concluida | 100% | Catalogo regulatorio, filtros e CRUD do backend | Imagem de produto e controle transacional de estoque |
| Sprint 3 | Concluida | 100% | i18n por Accept-Language, bulas com fallback e multimoeda por pais/moeda | Nenhuma pendencia aberta |
| Sprint 4 | Concluida | 100% | Carrinho persistente (Cart/CartItem), endpoints de carrinho e checkout completo carrinho -> pedido | Nenhuma pendencia aberta |
| Sprint 5 | Concluida | 100% | Upload, auditoria, aprovacao/rejeicao, storage privado e URL assinada temporaria | Nenhuma pendencia aberta |
| Sprint 6 | Concluida | 100% | Gateway, customer, connected account e payment intent | Validacao operacional do gateway real |
| Sprint 7 | Concluida | 100% | Webhook seguro, idempotencia e split | Nenhuma pendencia aberta |
| Sprint 8 | Concluida | 100% | Celery, SMS assíncrono, auditoria de notificacao, Memed, Celery Beat e email | Nenhuma pendencia aberta |
| Sprint 9 | Concluida | 100% | Painel do fornecedor e extrato financeiro | Exportacoes e filtros extras, se precisar |
| Sprint 10 | Concluida com gaps | 95% | OpenAPI, Docker, otimizações e hardening basico | tracing distribuido completo e alertas formais |

Leitura rapida da tabela:

- acima de 90%: pronto para operar com ajustes menores
- entre 70% e 89%: funcional, mas ainda nao considero fechado para producao total
- abaixo de 70%: ainda precisa de entrega estrutural

## Status por sprint

### Sprint 0 - Infra, qualidade e processo

Status: concluida.

Ja foi feito:

- padrao de branch e fluxo com PR
- Conventional Commits documentado
- pre-commit com black, isort, flake8 e bandit
- CI em GitHub Actions com lint, testes e build Docker

Falta para producao:

- protecao da main e regras obrigatorias de PR precisam existir no GitHub
- isso nao fica resolvido só no repositório local

### Sprint 1 - Fundacao, auth e LGPD base

Status: concluida.

Ja foi feito:

- projeto Django e DRF configurados
- autenticação JWT completa com login, refresh, logout e blacklist
- usuario customizado com perfis PATIENT, DOCTOR, PROVIDER e ADMIN
- RBAC básico em endpoints de validação
- auditoria de login e logout com sanitizacao de dados sensiveis

Falta para producao:

- reset de senha por e-mail
- 2FA ou outro reforco de autenticacao, se for requisito
- SSO/OAuth, se houver necessidade futura

### Sprint 2 - Catalogo e regras de saude

Status: concluida.

Ja foi feito:

- Category, Product e ProductVariation
- ProductDosage, ProductPackageInsert e SalesRestriction
- filtros por categoria, prescricao e idade
- CRUD administrativo do catalogo
- ownership de produto para fornecedor no painel

Falta para producao:

- nao ha imagem/media de produto modelada
- estoque transacional com bloqueio concorrente ainda nao foi explicitamente tratado

### Sprint 3 - i18n e precificacao multimoeda

Status: concluida.

Ja foi feito:

- i18n funcional na API com Accept-Language (LocaleMiddleware ativo)
- bulas com selecao por idioma e fallback para pt_BR
- traducao de mensagens principais de validacao para pt/en/es
- modelo ProductPrice por produto/pais/moeda
- catalogo retornando preco contextual por cabecalho/query params
- endpoint para gestao de precos multimoeda: /api/product-prices/

### Sprint 4 - Carrinho e pedido

Status: concluida.

Ja foi feito:

- modelo Order
- modelo OrderItem
- modelo Cart persistente por usuario
- modelo CartItem persistente
- endpoints de carrinho: me, add item, update item, remove item e clear
- checkout completo carrinho -> pedido com criacao de Order e OrderItem
- recálculo consolidado de total no backend
- status de pedido: PENDING, PAID, UNDER_MEDICAL_REVIEW, APPROVED, CANCELLED e FAILED
- detalhe de pedido com itens

### Sprint 5 - Prescricoes e receitas

Status: concluida.

Ja foi feito:

- MedicalPrescription vinculada ao pedido
- upload de arquivo da receita
- hash SHA-256 e tamanho do arquivo
- expiracao calculada
- auditoria de acesso com logs de upload, download, view, verify e reject
- aprovacao e rejeicao por admin
- sanitizacao de payloads sensiveis na auditoria
- armazenamento privado de receita fora de media publica
- URL assinada temporaria para download seguro

Falta para producao:

- job automatizado para marcar expiracao da receita
- integracao com OCR/validacao automatica, se for requisito
- notificacao por e-mail quando a receita for aprovada ou rejeitada

### Sprint 6 - Pagamento e split

Status: concluida.

Ja foi feito:

- gateway abstrato com mock e Stripe
- customer do comprador
- connected account do fornecedor
- payment intent com checkout_url e client_secret
- validacao operacional completa com o gateway real escolhido
- split calculado no momento da transacao

Falta para producao:

- cobertura adicional de cenarios de falha, reconciliacao e estorno

### Sprint 7 - Webhooks e automacao de status

Status: concluida (100%).

Ja foi feito:

- webhook com assinatura HMAC
- idempotencia por event_id
- atualizacao de status do pedido com base em evento do gateway
- calculo de split no processamento do evento
- transicao para UNDER_MEDICAL_REVIEW quando ha receita pendente

Falta para producao:

- nenhuma pendencia aberta

### Sprint 8 - Integracoes externas

Status: concluida (100%).

Ja foi feito:

- Celery configurado
- tarefa assíncrona para SMS por evento de pedido
- provider mock e provider Twilio
- fallback local quando o broker nao esta disponivel
- auditoria de notificacoes externas
- integracao Memed com providers mock e real para validacao de receitas
- Celery Beat com scheduler para marcar receitas como expiradas automaticamente
- healthcheck expandido com verificacao de Redis/broker
- tasks assincronas para envio de email de notificacao (aprovacao/rejeicao)
- admin customizado para MedicalPrescription com actions rapidas (verificar, rejeitar, enviar Memed)
- PrescriptionAccessAudit admin com rastreio completo de acessos

Falta para producao:

- nenhuma pendencia aberta

### Sprint 9 - Painel do fornecedor e relatorios

Status: concluida.

Ja foi feito:

- CRUD de produtos do proprio fornecedor
- restricao por ownership
- extrato financeiro de split
- resumo agregado de vendas

Falta para producao:

- exportacao CSV/PDF, se o parceiro precisar de relatorios externos
- mais filtros financeiros, se o negocio pedir

### Sprint 10 - refatoracao, docs e deploy

Status: concluida, com lacunas de hardening.

Ja foi feito:

- queries otimizadas com select_related e prefetch_related em pontos criticos
- OpenAPI/Swagger/ReDoc habilitados
- schema OpenAPI com nomes explicitamente definidos para enums de status no backend de products
- exemplos de payload em endpoints importantes
- Docker e Docker Compose
- hardening basico de producao no settings

Falta para producao:

- tracing distribuido completo com stack externa, se o ambiente exigir
- alertas formais integrados ao monitoramento real
- protecoes extras de borda, se houver API pública fora do gateway

### Sprint 11 - observabilidade e operacao

Status: concluida com necessidade de integracao externa para tracing completo.

Ja foi feito:

- `correlation_id` e `traceparent` propagados em requests, tasks e webhooks
- logs estruturados em JSON com campos mínimos de request
- hardening LGPD em auditoria: campos de contato sensíveis sanitizados e email mascarado em notificações
- métricas HTTP de latência, erro e throughput expostas em `/metrics/`
- rate limiting nas rotas públicas e críticas de autenticação, health e webhook
- playbook operacional com incidentes e alertas

Falta para producao:

- tracing distribuído completo, se a stack de infra já estiver disponível
- integração com alertas do monitoramento real

## O que ja esta pronto para producao

Se o criterio for manter o escopo atual do backend, o que ja esta pronto para subir com boa confianca e:

- auth e RBAC funcionando
- catalogo regulatorio funcional
- prescricoes auditadas
- pagamentos e webhook operando
- SMS assíncrono funcionando
- painel do fornecedor funcional
- CI e dockerizacao prontos

## O que ainda falta para liberar producao com mais seguranca

Prioridade alta:

- expiracao automatica de receitas
- i18n e multimoeda, se o roadmap continuar exigindo isso
- observabilidade com correlation_id e metricas

Prioridade media:

- export LGPD e politicas de retencao formalizadas no codigo
- webhooks com monitoramento e conciliacao
- healthcheck do Redis/broker
- cobertura de testes para os gaps acima

Prioridade baixa, mas recomendada:

- reset de senha por e-mail
- SSO/2FA
- relatorios exportaveis para fornecedor

## Checklist de aceite para mandar o backend para producao

- autenticacao e RBAC testados em CI
- catalogo validado com regras regulatorias
- prescricoes com armazenamento privado, URL assinada temporaria e auditoria completa
- pagamento aprovado, expirado e falho cobertos por teste
- notificacoes externas com fallback e rastreio
- observabilidade minima implementada
- documentacao tecnica atualizada
- revisao final de seguranca executada

## Observacao de governanca

O checklist abaixo deve ser mantido em toda entrega do backend:

- permissao explicita em endpoint novo
- sem log sensivel com CPF, token ou dados medicos brutos
- auditoria para acesso a receita
- politica de retencao para dados sensiveis
- teste para fluxo critico antes de merge
