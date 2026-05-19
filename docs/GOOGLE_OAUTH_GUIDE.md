# Google OAuth - Guia Completo de Implementação

Este documento detalha como implementar e testar o login social com Google no iHealthBrasil.

## Status Atual

### ✅ Implementado no Backend
- Endpoint `/api/auth/google-oauth/` criado
- Validação de ID tokens do Google com biblioteca `google-auth`
- Criação/atualização automática de usuários
- Geração de JWT (access_token + refresh_token)
- Logging de eventos de autenticação
- Rate limiting configurado (20/hora)

### ✅ Implementado no Frontend
- Google OAuth SDK carregado dinamicamente
- Botões "Entrar com Google" e "Criar conta com Google"
- Captura de ID token do Google
- Envio de token para endpoint backend
- Armazenamento de tokens JWT em localStorage
- Redirecionamento para home após sucesso

### ⚙️ Configuração Necessária

#### 1. Obter Google Client ID

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto (ex: "iHealthBrasil")
3. Ative a "Google+ API"
4. Vá para "Credenciais" → "Criar Credencial" → "OAuth 2.0 Client ID" → "Web application"
5. Adicione Authorized JavaScript origins:
   - `http://127.0.0.1:5500` (desenvolvimento)
   - `http://localhost:5500` (desenvolvimento)
   - `https://seu-dominio.com` (produção)
6. Copie o "Client ID" gerado

#### 2. Configurar Frontend

```bash
# Navigate to frontend folder
cd frontend

# Create .env file with your credentials
echo "VITE_GOOGLE_CLIENT_ID=SEU_CLIENT_ID_AQUI.apps.googleusercontent.com" > .env
echo "VITE_API_URL=http://localhost:8000/api" >> .env

# Build
npm run build
```

#### 3. Configurar Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (se necessário)
python manage.py migrate

# Start development server
python manage.py runserver
```

#### 4. Servir Frontend

```bash
# Use Live Server extension in VS Code
# Open dist/index.html with Live Server
# Usually available at http://127.0.0.1:5500/
```

## Testando o Fluxo Completo

### Cenário 1: Novo Usuário via Google

1. Navegue para `http://127.0.0.1:5500/#/login`
2. Clique em "Entrar com Google"
3. Uma janela popup abrirá para autenticação do Google
4. Faça login com sua conta Google
5. Consentir com as permissões solicitadas
6. Frontend receberá ID token
7. Frontend enviará token para `POST /api/auth/google-oauth/`
8. Backend criará novo usuário com email/nome do Google
9. Backend retornará JWT tokens
10. Frontend armazenará tokens em localStorage
11. Página redirecionará para home com usuário autenticado

### Cenário 2: Usuário Existente via Google

1. Mesmo fluxo acima, mas usuário já existe no banco
2. Backend encontrará usuário existente e atualizará nome se necessário
3. Retornará JWT para usuário existente

### Cenário 3: Registrar via Google

1. Navegue para `http://127.0.0.1:5500/#/register`
2. Clique em "Criar conta com Google"
3. Mesmo fluxo de autenticação
4. Se bem-sucedido, nova conta criada ou usuário logado

## Testando com curl (Backend)

### Obter ID Token Válido

Você precisará de um ID token real do Google. Aqui está como simular para testes:

```bash
# 1. Fazer login via frontend para obter um token real
# 2. Ou usar Google OAuth Playground: https://developers.google.com/oauthplayground

# Uma vez com o token:
curl -X POST http://localhost:8000/api/auth/google-oauth/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "SEU_ID_TOKEN_AQUI",
    "client_id": "SEU_CLIENT_ID.apps.googleusercontent.com"
  }'
```

### Resposta Esperada (Sucesso)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "username": "usuario@gmail.com",
    "email": "usuario@gmail.com",
    "first_name": "João",
    "last_name": "Silva",
    "profile": "PATIENT",
    "phone_number": null,
    "is_active": true,
    "date_joined": "2025-02-01T10:00:00Z"
  }
}
```

### Resposta Esperada (Erro)

```json
{
  "id_token": ["Invalid token: Token expired or invalid signature"]
}
```

## Fluxo Técnico Detalhado

### Frontend → Backend

```
1. Usuário clica "Entrar com Google"
2. googleAuth.js inicializa token client com Client ID
3. Usuário faz login no popup do Google
4. Google retorna ID token + access token
5. Frontend envia POST /api/auth/google-oauth/ com ID token + Client ID
```

### Backend Processa

```
1. GoogleOAuthView recebe requisição
2. GoogleOAuthSerializer valida ID token com google.auth.transport.requests
3. Extrai claims: email, name, picture, etc
4. get_or_create User com email
5. Gera JWT tokens com RefreshToken.for_user(user)
6. Retorna {access, refresh, user} ao frontend
```

### Frontend Finaliza

```
1. Armazena tokens em localStorage
2. Armazena dados do usuário em localStorage
3. Redireciona para home (/)
4. Home renderiza com usuário autenticado
```

## Segurança

### Validações Implementadas

- ✅ ID token assinado pelo Google (verificado com google-auth)
- ✅ Audience do token valida Client ID
- ✅ Rate limiting: 20 requisições por hora
- ✅ Tokens JWT com expiration (access: 15min, refresh: 7 dias)
- ✅ Refresh tokens podem ser bloqueados (logout)
- ✅ HTTPS recomendado em produção

### Próximas Etapas para Segurança

- [ ] CSRF protection habilitado via Django middleware
- [ ] CORS configurado para domínios específicos
- [ ] HTTPS forçado em produção
- [ ] Audit logging de todos os logins Google
- [ ] Detecção de anomalias (múltiplos logins simultaneamente, etc)

## Troubleshooting

### Erro: "Não foi possível obter seus dados do Google"

**Causa**: `VITE_GOOGLE_CLIENT_ID` não configurado em `frontend/.env`

**Solução**: Crie `.env` com Client ID válido

### Erro: "Token audience mismatch"

**Causa**: Client ID no backend não bate com Client ID usado no frontend

**Solução**: Verificar que ambos têm o mesmo Client ID

### Erro: CORS (No 'Access-Control-Allow-Origin' header)

**Causa**: Frontend e backend em portas diferentes

**Solução**: Configurar CORS_ALLOWED_ORIGINS no Django ou adicionar middleware

```python
# config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]
```

### Pop-up Bloqueado

**Causa**: Navegador bloqueou o pop-up

**Solução**: Usuário precisa permitir pop-ups do site

## Próximos Passos

1. [ ] Testar com Google Client ID real
2. [ ] Implementar "Esqueci Minha Senha"
3. [ ] Adicionar outros provedores (Facebook, Microsoft)
4. [ ] Email verification para novos usuários
5. [ ] 2FA (autenticação de dois fatores)
6. [ ] Sincronização de perfil periodicamente

---

**Última atualização**: Fevereiro 2025
**Responsável**: Equipe Backend + Frontend
