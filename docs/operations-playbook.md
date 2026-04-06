# Playbook Operacional

Escopo:

- incidentes de producao
- alertas operacionais
- protecao LGPD
- sem front-end

## Objetivos

- reduzir tempo de deteccao
- reduzir tempo de restauracao
- evitar vazamento de dados sensiveis
- manter rastreabilidade por `correlation_id`

## Severidade

### SEV-1

- API indisponivel
- banco fora do ar
- fila Celery parada com impacto em pedidos ou webhooks
- prescricao sem download seguro
- indício de vazamento de dados

### SEV-2

- aumento de 5xx
- latencia acima do normal
- webhook rejeitando eventos validos
- falha parcial em SMS ou email

### SEV-3

- degradacao sem impacto direto no cliente
- alertas de capacidade
- job agendado atrasado

## Alertas Minimos

- taxa de erro HTTP acima de 5% em 5 minutos
- latencia p95 acima de 1s nas rotas criticas
- fila Celery com atraso acima de 5 minutos
- falha recorrente de webhook com assinatura valida
- aumento repentino de login falho
- erro de conexao com banco ou Redis

## Runbooks

### API fora do ar

1. Verificar healthcheck detalhado.
2. Confirmar banco e Redis.
3. Validar logs com `correlation_id` da ultima request afetada.
4. Reverter ultimo deploy se houver regressao.

### Webhook falhando

1. Conferir assinatura HMAC.
2. Verificar payload e `event_id`.
3. Checar logs da request e da task associada.
4. Validar idempotencia no banco.

### Fila Celery acumulada

1. Verificar worker e broker.
2. Conferir backlog por tipo de tarefa.
3. Reiniciar worker somente apos confirmar integridade do broker.
4. Reprocessar eventos pendentes se necessario.

### Suspita LGPD

1. Congelar a divulgacao do incidente.
2. Identificar usuarios, rotas e eventos afetados.
3. Preservar logs e `correlation_id`.
4. Revisar mascaramento de dados e acesso.
5. Acionar processo juridico/compliance.

## Regras de Log

- registrar `correlation_id`
- registrar usuario ou `anonymous`
- registrar rota e status HTTP
- registrar duracao da request
- nunca logar senha, token, CPF ou documento sensivel

## Revisao Periodica

- revisar alertas mensalmente
- revisar thresholds apos cada pico de uso
- testar restauracao de backup
- simular queda de Redis e de banco
