# Sprint 03 - Matriz de permissoes por perfil

Legenda:

- OK: permitido
- NO: nao permitido
- AUTH: exige autenticacao

## Auth e RBAC

| Endpoint | Metodo | PATIENT | DOCTOR | PROVIDER | ADMIN | Regra aplicada |
|---|---|---|---|---|---|---|
| /api/auth/register/ | POST | OK | OK | OK | NO | Registro publico, mas perfil ADMIN bloqueado |
| /api/auth/token/ | POST | OK | OK | OK | OK | Login com credenciais validas |
| /api/auth/token/refresh/ | POST | OK | OK | OK | OK | Exige refresh valido |
| /api/auth/token/verify/ | POST | OK | OK | OK | OK | Exige token JWT para verificar |
| /api/auth/logout/ | POST | AUTH | AUTH | AUTH | AUTH | IsAuthenticated |
| /api/auth/me/ | GET | AUTH | AUTH | AUTH | AUTH | IsAuthenticated |
| /api/auth/rbac/admin-only/ | GET | NO | NO | NO | OK | IsAuthenticated + HasAnyProfile([ADMIN]) |
| /api/auth/rbac/provider-or-admin/ | GET | NO | NO | OK | OK | IsAuthenticated + HasAnyProfile([PROVIDER, ADMIN]) |

## Catalogo (resources do DRF router)

A regra abaixo vale para:

- /api/categories/
- /api/products/
- /api/variations/
- /api/dosages/
- /api/package-inserts/
- /api/sales-restrictions/
- actions de product (requires_prescription, variations, dosages, package_inserts, restrictions)

| Metodo | PATIENT | DOCTOR | PROVIDER | ADMIN | Regra aplicada |
|---|---|---|---|---|---|
| GET/HEAD/OPTIONS | OK | OK | OK | OK | IsAdminOrReadOnly (leitura publica) |
| POST/PUT/PATCH/DELETE | NO | NO | NO | OK* | IsAdminOrReadOnly (escrita exige is_staff=true) |

* Observacao importante:

No codigo atual a escrita administrativa depende de `request.user.is_staff`. Isso significa que apenas o valor do campo `profile` nao basta; o usuario precisa estar com `is_staff=true` (tipicamente admin/superuser).

## Arquivos-fonte das regras

- accounts/permissions.py
- accounts/views.py
- products/permissions.py
- products/views.py
