# Guia de Contribuicao

## Fluxo de branch

- Branch principal: `main`
- Branches de trabalho: `feature/<descricao-curta>`
- Todo merge deve ser via requisicao de pull request

Obs.: protecao da `main` (revisao obrigatoria e validacoes de status) deve ser configurada no GitHub.

## Convencao de commits

Padrao: Commits Convencionais (Conventional Commits)

Exemplos:

- `feat(auth): adiciona endpoint de logout com blacklist`
- `fix(accounts): corrige validacao de perfil no registro`
- `chore(ci): adiciona workflow de lint e testes`
- `docs(readme): atualiza instrucoes de setup`

Tipos recomendados:

- `feat`
- `fix`
- `chore`
- `docs`
- `refactor`
- `test`

## Qualidade local (Sprint 0)

1. Instale dependencias de desenvolvimento:

```bash
python -m pip install -r requirements-dev.txt
```

2. Ative hooks de pre-commit:

```bash
pre-commit install
```

3. Rode validacoes manualmente (opcional):

```bash
pre-commit run --all-files
python manage.py check
python manage.py test
```
