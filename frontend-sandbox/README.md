# iHealth Brasil - Frontend Sandbox

Versão isolada do front-end para testar funcionalidades sem alterar o projeto principal.

Requisitos:
- Node 18+ / npm

Como executar:

```bash
cd frontend-sandbox
npm install
# defina a variável de ambiente VITE_API_BASE se quiser apontar para a API do backend
# Ex: VITE_API_BASE="http://localhost:8000"
npm run dev
```

Observações:
- O sandbox usa Vite, React e React Router.
- A identidade visual segue o frontend original: Montserrat, azul petróleo, azul ciano e cards brancos.
- O catálogo e o checkout funcionam com API real ou fallback mock local.
- O carrinho fica salvo no navegador em localStorage.
- Os endpoints de API estão centralizados em `src/api.js`.
- Se a porta 5173 já estiver em uso, o Vite pode subir em 5174 automaticamente.

Fluxo sugerido:
1. Abrir a tela de login.
2. Navegar para o catálogo e aplicar filtros.
3. Adicionar produtos ao carrinho.
4. Ir ao checkout para validar o layout e simular a conclusão do pedido.
