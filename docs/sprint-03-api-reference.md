# Sprint 03 - API reference (request/response)

Este documento consolida exemplos de request/response para os endpoints principais da API.

## Convencoes

- Base URL local: `http://127.0.0.1:8000`
- Prefixo auth: `/api/auth/`
- Prefixo catalogo: `/api/`
- Auth JWT: `Authorization: Bearer <access_token>`

## Auth e usuarios

### POST /api/auth/register/

Request:

```json
{
  "username": "patient_demo",
  "email": "patient_demo@example.com",
  "password": "SenhaForte123",
  "first_name": "Paciente",
  "last_name": "Demo",
  "profile": "PATIENT"
}
```

Response 201 (sucesso):

```json
{
  "username": "patient_demo",
  "email": "patient_demo@example.com",
  "first_name": "Paciente",
  "last_name": "Demo",
  "profile": "PATIENT"
}
```

Response 400 (erro comum):

```json
{
  "profile": [
    "Perfil ADMIN nao pode ser definido no registro publico."
  ]
}
```

### POST /api/auth/token/

Request:

```json
{
  "username": "patient_demo",
  "password": "SenhaForte123"
}
```

Response 200:

```json
{
  "refresh": "<jwt_refresh>",
  "access": "<jwt_access>"
}
```

Response 401:

```json
{
  "detail": "No active account found with the given credentials"
}
```

### POST /api/auth/token/refresh/

Request:

```json
{
  "refresh": "<jwt_refresh>"
}
```

Response 200:

```json
{
  "access": "<novo_jwt_access>"
}
```

### POST /api/auth/token/verify/

Request:

```json
{
  "token": "<jwt_access>"
}
```

Response 200:

```json
{}
```

Response 401:

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

### POST /api/auth/logout/

Header:

- `Authorization: Bearer <access_token>`

Request:

```json
{
  "refresh": "<jwt_refresh>"
}
```

Response 205:

```json
{}
```

Response 400:

```json
{
  "detail": "Refresh token invalido ou expirado."
}
```

### GET /api/auth/me/

Header:

- `Authorization: Bearer <access_token>`

Response 200:

```json
{
  "id": 10,
  "username": "patient_demo",
  "email": "patient_demo@example.com",
  "first_name": "Paciente",
  "last_name": "Demo",
  "profile": "PATIENT",
  "is_active": true,
  "date_joined": "2026-03-30T12:00:00Z"
}
```

Response 401:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### GET /api/auth/rbac/admin-only/

Header:

- `Authorization: Bearer <access_token>`

Response 200:

```json
{
  "detail": "Acesso permitido para ADMIN."
}
```

Response 403:

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### GET /api/auth/rbac/provider-or-admin/

Header:

- `Authorization: Bearer <access_token>`

Response 200:

```json
{
  "detail": "Acesso permitido para PROVIDER ou ADMIN."
}
```

## Catalogo

### GET /api/categories/

Response 200 (paginado):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Analgésicos",
      "description": "Produtos para dor",
      "slug": "analgesicos",
      "created_at": "2026-03-30T12:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

### POST /api/categories/

Header:

- `Authorization: Bearer <access_token_admin>`

Request:

```json
{
  "name": "Vitaminas",
  "description": "Suplementacao"
}
```

Response 201:

```json
{
  "id": 2,
  "name": "Vitaminas",
  "description": "Suplementacao",
  "slug": "vitaminas",
  "created_at": "2026-03-30T12:05:00Z",
  "updated_at": "2026-03-30T12:05:00Z"
}
```

Response 401/403 sem permissao de escrita.

### GET /api/products/

Exemplo com filtros:

`/api/products/?search=dipirona&category_slug=analgesicos&ordering=price&page=1&page_size=10`

Response 200 (listagem resumida):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "name": "Dipirona 500mg",
      "slug": "dipirona-500mg",
      "price": "12.90",
      "requires_prescription": false,
      "stock": 100,
      "is_active": true,
      "category": 1,
      "category_name": "Analgésicos"
    }
  ]
}
```

### GET /api/products/{slug}/

Response 200 (detalhado): campos do produto + variacoes + dosagens + bulas + restricoes.

### GET /api/products/requires_prescription/

Response 200:

- Mesmo formato paginado de listagem.
- Retorna apenas produtos com `requires_prescription=true`.

### GET /api/products/{slug}/variations/

Response 200:

```json
{
  "product_slug": "dipirona-500mg",
  "variations": [
    {
      "id": 1,
      "name": "Caixa",
      "value": "20 comprimidos",
      "sku_suffix": "CX20",
      "price_modifier": "0.00",
      "stock": 30,
      "final_price": 12.9,
      "created_at": "2026-03-30T12:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

### GET /api/products/{slug}/dosages/

Response 200:

```json
{
  "product_slug": "dipirona-500mg",
  "dosages": [
    {
      "id": 1,
      "strength": "500",
      "unit": "mg",
      "frequency_recommendation": "A cada 8h",
      "is_default": true,
      "created_at": "2026-03-30T12:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

### GET /api/products/{slug}/package_inserts/

Response 200:

```json
{
  "product_slug": "dipirona-500mg",
  "package_inserts": [
    {
      "id": 1,
      "language": "pt-BR",
      "language_display": "Portugues (Brasil)",
      "title": "Bula Dipirona",
      "content": "Conteudo da bula",
      "file_url": "",
      "requires_prescription_note": false,
      "created_at": "2026-03-30T12:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

### GET /api/products/{slug}/restrictions/

Response 200:

```json
{
  "product_slug": "dipirona-500mg",
  "restrictions": [
    {
      "id": 1,
      "restriction_type": "AGE",
      "restriction_type_display": "Faixa etaria",
      "description": "Nao recomendado para menores de 12 anos",
      "detail": "Consultar medico",
      "is_active": true,
      "created_at": "2026-03-30T12:00:00Z",
      "updated_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

## Observacoes de permissao para catalogo

- Leitura (GET/HEAD/OPTIONS): publica.
- Escrita (POST/PUT/PATCH/DELETE): exige usuario `is_staff=true`.
- Em geral, no projeto atual, usuario ADMIN e superuser devem ser usados para escrita administrativa.
