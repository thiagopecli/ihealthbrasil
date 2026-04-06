# Sprint 8: Integrações Externas - Guia de Implementação

## Visão Geral

Sprint 8 completou 100% de suas funcionalidades com as seguintes entrega:

1. **Integração Memed** - Validação externa de receitas médicas
2. **Celery Beat** - Scheduler para marcar receitas como expiradas
3. **Healthcheck Expandido** - Verificação de Redis/Broker
4. **Notificações por Email** - Aprovação/rejeição de receitas
5. **Admin Customizado** - Painel de gerenciamento de receitas

---

## 1. Integração Memed (Prescricoes Externas)

### Configuração

Adicionar variáveis ao `.env`:

```env
MEMED_ENABLED=True
MEMED_PROVIDER=mock  # mock para testes, memed para produção
MEMED_API_KEY=seu_api_key
MEMED_API_BASE_URL=https://api.memed.com.br/v1
```

### Arquitetura

```
products/notifications.py
  ├── BaseMemedProvider (interface)
  ├── MockMemedProvider (testes/dev)
  └── RealMemedProvider (produção com HTTP)
```

### Como Usar

#### Programaticamente

```python
from products.tasks import enqueue_prescription_to_memed

# Enfileira envio da receita para Memed
enqueue_prescription_to_memed(prescription_id=123)
```

#### Pelo Admin

1. Acesse `/admin/products/medicalprescription/`
2. Selecione uma ou mais receitas com arquivo
3. Na action dropdown, escolha "Enviar para validacao Memed"
4. Clique "Go"

Resultado:
- Receita é enviada para validação
- Resposta é armazenada em `prescription.verification_notes`
- Log de tentativa em `PrescriptionAccessAudit`

### Modelo de Resposta

```json
{
  "id": "memed_prescription_id",
  "status": "approved|rejected|pending",
  "confidence_score": 0.95,
  "validation_details": { ... }
}
```

### Tratamento de Erros

Se a integração falhar:
- Task retenta automaticamente (até 3 vezes)
- Log registrado em `PrescriptionAccessAudit` com detalhes do erro
- Sistema continua funcionando em modo fallback

---

## 2. Celery Beat - Expiração Automática de Receitas

### Configuração

Já vem configurado em `config/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    "mark-expired-prescriptions": {
        "task": "products.tasks.mark_expired_prescriptions",
        "schedule": crontab(hour=0, minute=0),  # Meia-noite UTC
        "options": {"queue": "default", "priority": 10},
    },
}
```

### Como Executar

**Desenvolvimento local:**

```bash
# Terminal 1: worker normal
celery -A config worker -l info

# Terminal 2: beat scheduler
celery -A config beat -l info
```

**Docker Compose:**

```yaml
# Já vem no docker-compose.yml
beat:
  image: ihealthbrasil:latest
  command: celery -A config beat -l info
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - DJANGO_ENV=production
```

### O que Faz

Diariamente à meia-noite UTC:
1. Busca receitas com status `SUBMITTED` e `expires_at < now()`
2. Marca como `EXPIRED`
3. Registra auditoria em `PrescriptionAccessAudit`

**Exemplo:**

```python
# Receita criada em 2026-04-01
# validity_days = 30
# expires_at = 2026-05-01 00:00:00 UTC
# 
# Beat executa 2026-05-01 00:00:00 UTC
# Status muda para EXPIRED
# Log criado com action=VERIFIED e details={"automatic_expiration": True}
```

### Monitoramento

Monitor via Redis:

```bash
redis-cli
> KEYS "*celery*"
> HGETALL celery-task-meta-<task-id>
```

---

## 3. Email de Notificações

### Configuração

Adicionar ao `.env`:

```env
EMAIL_ENABLED=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu_usuario@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_app  # Use App Password, não senha normal
EMAIL_USE_TLS=True
EMAIL_FROM_ADDRESS=noreply@ihealthbrasil.com.br
```

#### Para Gmail

1. Habilite [Two-Factor Authentication](https://myaccount.google.com/security)
2. Gere [App Password](https://myaccount.google.com/apppasswords)
3. Use o app password em `EMAIL_HOST_PASSWORD`

#### Para Desenvolvimento

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Emails aparecem no console ao invés de serem enviados.

### Como Usar

#### Programaticamente

```python
from products.tasks import enqueue_prescription_notification_email

# Notify aprovação
enqueue_prescription_notification_email(
    prescription_id=123,
    notification_type="verified"
)

# Notify rejeição
enqueue_prescription_notification_email(
    prescription_id=123,
    notification_type="rejected"
)
```

#### Pelo Admin

1. Acesse `/admin/products/medicalprescription/`
2. Selecione receitas com status `SUBMITTED`
3. Escolha action:
   - "Verificar receitas selecionadas (aprovar)" → envia email de aprovação
   - "Rejeitar receitas selecionadas" → envia email de rejeição
4. Clique "Go"

### Template de Email

**Aprovação:**

```
Olá <first_name ou username>,

Sua receita foi verificada e aprovada!
Seu pedido #<order_id> pode ser processado normalmente.

Obrigado!
iHealth Brasil
```

**Rejeição:**

```
Olá <first_name ou username>,

Sua receita foi verificada e rejeitada.
Motivo: <verification_notes>

Por favor, envie uma nova receita válida.

iHealth Brasil
```

### Auditoria

Cada email enfileirado cria log em `PrescriptionAccessAudit`:

```json
{
  "notification_type": "verified|rejected",
  "email_sent": true,
  "recipient": "user@example.com"
}
```

---

## 4. Healthcheck Expandido

### Endpoints

```bash
# Status básico
GET /health/
# {"status": "ok"}

# Status detalhado com Redis
GET /health/?detailed=true
# {
#   "status": "ok",
#   "components": {
#     "database": "ok",
#     "redis": "ok"
#   }
# }
```

### HTTP Status Codes

- `200 OK` - Tudo ok
- `200 OK (degraded)` - Redis indisponível, DB ok
- `503 Service Unavailable` - DB indisponível

### Uso em Kubernetes/Docker

```yaml
livenessProbe:
  httpGet:
    path: /health/?detailed=true
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

---

## 5. Admin Customizado - Receitas

### Acesso

`GET /admin/products/medicalprescription/`

### Features

#### Filtros Quick

- Status (PENDING, SUBMITTED, VERIFIED, REJECTED, EXPIRED)
- Tipo de receita (ELECTRONIC, PRINTED, DIGITAL_PHOTO)
- Data de criação
- Data de expiração

#### Actions em Lote

1. **Verificar receitas selecionadas (aprovar)**
   - Muda status para VERIFIED
   - Enfileira email de aprovação
   
2. **Rejeitar receitas selecionadas**
   - Muda status para REJECTED
   - Enfileira email de rejeição

3. **Enviar para validacao Memed**
   - Enfileira envio para Memed
   - Requer `MEMED_ENABLED=True`

#### Detalhes da Receita

- **Pedido e Receita**: ordem associada, tipo, prescritor, data
- **Arquivo**: link para download (assinado), hash SHA-256, tamanho
- **Validação**: status colorido, notas, dias restantes até expiração
- **Auditoria**: inline com todos os acessos registrados

#### Status com Cores

- 🟠 PENDING (orange) - aguardando upload
- 🔵 SUBMITTED (blue) - enviada, aguardando verificação
- 🟢 VERIFIED (green) - aprovada
- 🔴 REJECTED (red) - rejeitada
- ⚫ EXPIRED (gray) - expirada

### Auditoria de Acesso

`GET /admin/products/prescriptionaccessaudit/`

Registra todas as ações em receitas:

```
UPLOADED - arquivo foi enviado
DOWNLOADED - usuário baixou arquivo
VIEWED - usuário visualizou receita
VERIFIED - admin aprovou ou scheduler expirou
REJECTED - admin rejeitou
```

Inclui:
- Usuário (com snapshot se deletado)
- IP address
- User-agent
- Timestamp
- Details customizados (motivos, status, etc)

---

## Fluxo Completo: De Pedido a Aprovação

```
1. Cliente faz pedido com prescrição necessária
   ↓
2. Sistema cria MedicalPrescription (status=PENDING)
   ↓
3. Cliente faz upload do arquivo
   MedicalPrescription.status = SUBMITTED
   ↓
4. [OPCIONAL] Sistema envia para Memed se MEMED_ENABLED=True
   (Background task, até 3 retries)
   ↓
5. Admin verifica manualmente
   → Action "Verificar receitas selecionadas"
   ↓
6. Sistema:
   - Muda status para VERIFIED
   - Registra auditoria (action=VERIFIED, details={...})
   - Enfileira envio de email (task assíncrona)
   ↓
7. Task envia email ao cliente
   - "Receita Aprovada - Pedido #123"
   - Registra resultado em auditoria
   ↓
8. Pedido segue para processamento de pagamento/entrega
```

---

## Variáveis de Ambiente Completas (Sprint 8)

```env
# Core
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=seu_secret_aqui

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Celery/Redis
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_TASK_ALWAYS_EAGER=False

# Sprint 8: SMS
SMS_ENABLED=True
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=seu_sid
TWILIO_AUTH_TOKEN=seu_token
TWILIO_FROM_NUMBER=+5511987654321

# Sprint 8: Memed
MEMED_ENABLED=True
MEMED_PROVIDER=memed
MEMED_API_KEY=seu_api_key
MEMED_API_BASE_URL=https://api.memed.com.br/v1

# Sprint 8: Email
EMAIL_ENABLED=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=seu_app_password
EMAIL_USE_TLS=True
EMAIL_FROM_ADDRESS=noreply@ihealthbrasil.com.br
```

---

## Troubleshooting

### Email não está sendo enviado

1. Verificar `EMAIL_ENABLED=True`
2. Verificar credenciais de SMTP
3. Se Gmail, usar App Password (não senha normal)
4. Verificar logs:
   ```bash
   python manage.py shell
   from django.core.mail import send_mail
   send_mail("test", "test", "noreply@ihealthbrasil.com.br", ["seu_email@gmail.com"])
   ```

### Memed não está respondendo

1. Verificar `MEMED_ENABLED=True`
2. Verificar `MEMED_API_KEY` e `MEMED_API_BASE_URL`
3. Testar com `MEMED_PROVIDER=mock` first
4. Verificar logs em `PrescriptionAccessAudit`

### Beat não está executando

1. Verificar se `celery beat` está rodando
2. Verificar Redis: `redis-cli ping` → deve retornar `PONG`
3. Verificar logs: `celery -A config beat -l debug`
4. Certificar que há um worker também: `celery -A config worker`

### Receitas não estão expirando

1. Verificar se beat está ativo
2. Verificar se há receitas com `status=SUBMITTED` e `expires_at < now()`
3. Executar manualmente:
   ```bash
   python manage.py shell
   from products.tasks import mark_expired_prescriptions
   mark_expired_prescriptions()
   ```

---

## Testes

```bash
# Testar task de SMS
python manage.py test products.tests.TestOrderStatusSms

# Testar task de Memed (mock)
python manage.py test products.tests.TestMemedProvider

# Testar scheduler de expiração
python manage.py test products.tests.TestMarkExpiredPrescriptions

# Testar email
python manage.py test products.tests.TestPrescriptionNotificationEmail

# Rodar todos os testes de Sprint 8
python manage.py test products.tests -k sprint8
```

---

## Próximas Melhorias (Sugestões)

- Webhook de receipt para confirmar delivery de email
- Rate limiting em endpoints de receita
- OCR automático para validação de receita
- Integração com mais providers (Telegram, WhatsApp)
- Relatório de SLA (tempo médio de aprovação)
- Dashboard do fornecedor mostrando receitas pendentes
