# Sprint 5: Gestão de Prescrições e Receitas (Crítica) - Validação Completa

## ✅ Status: IMPLEMENTADO E TESTADO

Data de Conclusão: 04/04/2026
Todos os 14 testes passaram com sucesso ✓

---

## 📋 Escopo Implementado

### 1. **Modelos de Dados** (products/models.py)

#### Order (Pedido)
- Status: PENDING, PAID, UNDER_MEDICAL_REVIEW, APPROVED, CANCELLED, FAILED
- Campos: user (FK), total_price, shipping_address, notes
- Índices: (user, status), (status, created_at)

#### OrderItem (Item do Pedido)
- Relacionamento: order (FK), product (FK), product_variation (FK)
- Campos: quantity, unit_price, total_price
- Rastreamento: created_at, updated_at

#### MedicalPrescription (Receita Médica)
- **Tipos**: ELECTRONIC, PRINTED, DIGITAL_PHOTO
- **Status**: PENDING, SUBMITTED, VERIFIED, REJECTED, EXPIRED
- **Campos**:
  - file: FileField com upload_to="prescriptions/%Y/%m/%d/"
  - file_size: BigIntegerField (permite NULL)
  - file_hash: CharField (SHA-256 para integridade, permite NULL)
  - prescriber_name, prescription_date, validity_days
  - expires_at: Calculado automaticamente
  - verification_notes: Para uso do admin
- **Auditoria**: OneToOne com Order, relacionamento reverso access_logs

#### PrescriptionAccessAudit (Auditoria LGPD)
- **Ações**: UPLOADED, DOWNLOADED, VIEWED, VERIFIED, REJECTED
- **Campos**:
  - prescription (FK)
  - user (FK, SET_NULL se deletado)
  - username_snapshot: Backup do nome de usuário
  - action: Choice field
  - ip_address, user_agent: Rastreamento de cliente
  - details: JSONField com dados sanitizados
  - created_at: Index para reporting
- **Índices**: (prescription, action, created_at), (user, action, created_at), (action, created_at)

---

## 🔌 Endpoints da API

### Gerenciamento de Pedidos (`/api/orders/`)

| Método | Endpoint | Permissão | Descrição |
|--------|----------|-----------|-----------|
| GET | `/api/orders/` | Autenticado | Listar (paciente vê só seus, admin vê todos) |
| POST | `/api/orders/` | Admin | Criar pedido |
| GET | `/api/orders/{id}/` | Autenticado | Detalhe com itens |
| POST | `/api/orders/{id}/approve_prescription/` | Admin | Aprovar receita |
| POST | `/api/orders/{id}/reject_prescription/` | Admin | Rejeitar receita |

**Resposta GET /orders:**
```json
{
  "count": 2,
  "next": null,
  "results": [
    {
      "id": 1,
      "user": "paciente@example.com",
      "status": "PENDING",
      "total_price": "150.00",
      "created_at": "2026-04-04T10:30:00Z",
      "updated_at": "2026-04-04T10:30:00Z"
    }
  ]
}
```

---

### Upload de Receitas (`/api/prescriptions/`)

| Método | Endpoint | Corpo | Descrição |
|--------|----------|-------|-----------|
| POST | `/api/prescriptions/` | multipart/form-data | Upload de receita |
| GET | `/api/prescriptions/{id}/` | - | Detalhe com logs |
| GET | `/api/prescriptions/{id}/download/` | - | Download com auditoria |
| GET | `/api/prescriptions/{id}/access_logs/` | - | Histórico de acessos |

**POST Payload (multipart/form-data):**
```python
order: 1
prescription_type: "DIGITAL_PHOTO"  # ou ELECTRONIC, PRINTED
file: <arquivo PDF>
prescriber_name: "Dr. Silva"
prescription_date: "2026-04-01"
```

**Resposta POST:**
```json
{
  "id": 42,
  "order": 1,
  "prescription_type": "DIGITAL_PHOTO",
  "status": "SUBMITTED",
  "file": "/media/prescriptions/2026/04/04/prescription_abc123.pdf",
  "file_size": 245632,
  "file_hash": "a1b2c3d4e5f6...",
  "prescriber_name": "Dr. Silva",
  "prescription_date": "2026-04-01",
  "expires_at": "2026-05-04T10:35:20Z",
  "access_logs": []
}
```

---

### Auditoria de Acesso (`/api/prescription-audit/`)

| Método | Endpoint | Query Params | Descrição |
|--------|----------|--------------|-----------|
| GET | `/api/prescription-audit/` | - | Todos logs (admin only) |
| GET | `/api/prescription-audit/?action=DOWNLOADED` | action, prescription | Filtrar por ação |
| GET | `/api/prescription-audit/by_prescription/?prescription_id=42` | prescription_id | Logs de uma receita |
| GET | `/api/prescription-audit/by_user/?user_id=5` | user_id | Logs de um usuário |

**Resposta GET /prescription-audit/:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "prescription": 42,
      "user": "paciente@example.com",
      "username_snapshot": "paciente@example.com",
      "action": "UPLOADED",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "details": {
        "file_name": "prescription_abc123.pdf",
        "file_format": "[REDACTED]"
      },
      "created_at": "2026-04-04T10:35:20Z"
    },
    {
      "id": 2,
      "prescription": 42,
      "user": "admin@example.com",
      "username_snapshot": "admin@example.com",
      "action": "VERIFIED",
      "ip_address": "192.168.1.50",
      "user_agent": "Chrome...",
      "details": {
        "verified_by": "admin@example.com"
      },
      "created_at": "2026-04-04T11:00:00Z"
    }
  ]
}
```

---

## 🔐 Permissões e RBAC

### Controle de Acesso

| Recurso | Paciente | Admin | Anonimo |
|---------|----------|-------|---------|
| Listar seus pedidos | ✓ | ✓ (todos) | ✗ |
| Ver detalhe do pedido | ✓ (próprio) | ✓ | ✗ |
| Upload de receita | ✓ | ✓ | ✗ |
| Download de receita | ✓ (própria) | ✓ | ✗ |
| Ver logs da receita | ✓ (própria) | ✓ | ✗ |
| Aprovar receita | ✗ | ✓ | ✗ |
| Rejeitar receita | ✗ | ✓ | ✗ |
| Acessar auditoria completa | ✗ | ✓ | ✗ |

---

## 🛡️ Auditoria LGPD

### Sanitização de Dados

Todos os logs sanitizam campos sensíveis:
- `password`, `token`, `refresh`, `authorization`, `secret`, `api_key`
- `cpf`, `medical_record`

Grandes payloads são truncados a 500 caracteres.

### Registro de Acesso

Cada ação sobre receita cria log com:

| Campo | Descrição |
|-------|-----------|
| prescription | ID da receita |
| user | Usuário autenticado (FK, SET_NULL se deletado) |
| username_snapshot | Backup do username (compliance) |
| action | UPLOADED, DOWNLOADED, VIEWED, VERIFIED, REJECTED |
| ip_address | IP do cliente (via X-Forwarded-For ou REMOTE_ADDR) |
| user_agent | Browser/cliente |
| details | JSONField com contexto (sanitizado) |
| created_at | Timestamp automático |

---

## ⚙️ Configuração para Produção

### 1. Django Settings (config/settings.py)

```python
# Media files (já configurado)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Validação de upload
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

### 2. URLs (config/urls.py)

```python
# Em desenvolvimento, media files são servidos automaticamente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 3. AWS S3 (Recomendado para Produção)

Para integração com S3, instale:
```bash
pip install boto3 django-storages
```

Configure em `settings.py`:
```python
if USE_S3:  # Variável de ambiente
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region_name': os.getenv('AWS_S3_REGION_NAME', 'us-east-1'),
                'endpoint_url': os.getenv('AWS_S3_ENDPOINT_URL'),
            }
        }
    }

# URLs assinadas com expiration (14 dias)
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 86400 * 14
```

URLs assinadas são geradas automaticamente via `prescription.file.url` no download endpoint.

---

## 🧪 Testes Unitários

Todos os 14 testes passaram:

```bash
# Testes de Pedidos (3 testes)
✓ Patient can list own orders only
✓ Admin can list all orders
✓ Unauthenticated cannot access orders

# Testes de Receitas (4 testes)
✓ Patient can upload prescription
✓ Only admin can verify prescription
✓ Prescription access audit log created on download
✓ Prescription access logs endpoint admin only

# Testes de Catálogo (7 testes - não afetados)
✓ Category list public and create requires admin
✓ Products list supports search, filter, ordering, pagination
✓ Requires prescription endpoint
✓ Nested product endpoints
✓ Variations dosages package inserts and restrictions filter by product slug
✓ Catalog write requires admin for all resources
✓ Category and product create allowed for admin
```

**Rodar testes:**
```bash
python manage.py test products.tests -v 2
```

---

## 📊 Estrutura de Dados

### Diagrama (Simplificado)

```
User
  ↓
Order (1:N)
  ├─ OrderItem (1:N)
  │   ├─ Product (N:1)
  │   └─ ProductVariation (N:1)
  └─ MedicalPrescription (1:1)
      └─ PrescriptionAccessAudit (1:N)
         └─ User [snapshot]
```

### Fluxo de Receita

1. **Upload (Patient)**
   - POST `/api/prescriptions/` com file
   - Status: PENDING → SUBMITTED
   - Log: UPLOADED criado
   - Hash SHA-256 calculado

2. **Verificação (Admin)**
   - POST `/api/orders/{id}/approve_prescription/`
   - Status: SUBMITTED → VERIFIED
   - Log: VERIFIED criado com notes

3. **Download (Patient/Admin)**
   - GET `/api/prescriptions/{id}/download/`
   - Log: DOWNLOADED criado
   - URL assinada (S3) ou caminho local

4. **Rejeição (Admin)**
   - POST `/api/orders/{id}/reject_prescription/`
   - Status: SUBMITTED → REJECTED
   - Log: REJECTED criado com reason

---

## 🚀 Próximas Etapas

### Sprint 6: Integração de Pagamento (Parte 1)
- Instalar SDK do gateway (Stripe, Pagar.me, etc)
- Criar Customer e Connected Account
- Gerar payment intent no checkout

### Sprint 7: Webhooks e Automação (Parte 2)
- Endpoint seguro para webhooks
- Atualizar status automático
- Implementar split de pagamento

---

## 📝 Documentação de Desenvolvimento

### Imports Importantes

```python
# Models
from products.models import Order, OrderItem, MedicalPrescription, PrescriptionAccessAudit

# Serializers
from products.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    MedicalPrescriptionUploadSerializer,
    MedicalPrescriptionDetailSerializer,
    PrescriptionAccessAuditSerializer,
)

# Auditoria
from products.audit import log_prescription_access, get_prescription_access_logs

# Utilities
from products.utils import calculate_file_hash, calculate_prescription_expiry
```

### Exemplo de Uso em Views

```python
from rest_framework.decorators import action
from products.audit import log_prescription_access
from products.models import PrescriptionAccessAudit, MedicalPrescription

class MyViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['get'])
    def my_action(self, request, pk=None):
        prescription = MedicalPrescription.objects.get(pk=pk)
        
        # Registrar acesso
        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.DOWNLOADED,
            details={"format": "pdf"}
        )
        
        return Response({"status": "ok"})
```

---

## ✅ Checklist de Compliance

- [x] Modelo de Receita com upload seguro
- [x] Arquivo com hash SHA-256 para integridade
- [x] Expiration automática de receita
- [x] Logs de acesso (LGPD)
- [x] Sanitização de dados sensíveis
- [x] Endpoints com permissão (RBAC)
- [x] IP e User-Agent rastreados
- [x] Username snapshot (deletado depois)
- [x] Testes unitários 100%
- [x] Configuração S3 documentada
- [x] Criação automática de índices
- [x] Paginação de logs

---

## 📞 Suporte

Para dúvidas sobre a implementação, consulte:
- [products/models.py](products/models.py) - Estrutura de dados
- [products/views.py](products/views.py) - Endpoints
- [products/serializers.py](products/serializers.py) - Validação
- [products/audit.py](products/audit.py) - Auditoria LGPD
- [products/tests.py](products/tests.py) - Exemplos de uso
