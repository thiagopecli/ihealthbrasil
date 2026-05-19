# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Google OAuth (frontend + backend)

Para implementar login social com Google:

### 1. Criar Credenciais no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou use um existente
3. Ative a API de Google+
4. Acesse "Credenciais" > "Criar Credencial" > "OAuth 2.0 - ID de Cliente" > "Aplicação da Web"
5. Adicione as origens JavaScript autorizadas:
   - `http://127.0.0.1:5500` (desenvolvimento local)
   - `http://localhost:5500`
   - `https://seu-dominio.com` (produção)
6. Copie o "Client ID"

### 2. Configurar Frontend

1. Crie o arquivo `frontend/.env` com base em `.env.example`:
```bash
VITE_GOOGLE_CLIENT_ID=SEU_CLIENT_ID.apps.googleusercontent.com
VITE_API_URL=http://localhost:8000/api
```

### 3. Configurar Backend

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. O endpoint `/api/auth/google-oauth/` já está disponível automaticamente

3. Teste o fluxo:
   - Clique em "Entrar com Google" ou "Criar conta com Google"
   - O usuário é criado/autenticado automaticamente com JWT retornado

### Fluxo Completo

- **Frontend**: Coleta `id_token` do Google OAuth
- **Backend**: Valida o `id_token` com `google-auth` library
- **Backend**: Cria/busca usuário no banco
- **Backend**: Retorna `access_token` e `refresh_token` JWT
- **Frontend**: Armazena tokens no `localStorage`
- **Frontend**: Redireciona para home autenticado
