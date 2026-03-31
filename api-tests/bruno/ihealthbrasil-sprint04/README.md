# Colecao Bruno - Sprint 04

Colecao versionada para validacao de auth, RBAC e catalogo.

## Estrutura

- `auth/`: login, perfil autenticado e logout
- `rbac/`: endpoints de validacao por perfil
- `catalog/`: consultas principais de catalogo
- `environments/local.bru`: variaveis locais

## Como executar

1. Abrir a pasta `api-tests/bruno/ihealthbrasil-sprint04` no Bruno.
2. Selecionar o ambiente `local`.
3. Executar primeiro `auth/token-obtain-pair.bru`.
4. Copiar `access` e `refresh` para as variaveis de ambiente.
5. Executar os demais endpoints de `auth/`, `rbac/` e `catalog/`.
