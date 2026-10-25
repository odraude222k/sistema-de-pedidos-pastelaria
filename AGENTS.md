# AGENTS.md

Estas instruções se aplicam a todo o repositório.

## Visão geral do projeto

Monorepo de um sistema full stack de pedidos para pastelaria:

- `backend/`: API em FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Psycopg, Pydantic Settings, Poetry com `package-mode = false` e Python 3.12.
- `frontend/`: aplicação em React 19 com JavaScript/JSX, Vite 8, Tailwind CSS 4, Vitest, Testing Library, Oxlint e Node.js 24.
- `compose.yaml`: orquestra os serviços locais com Docker Compose.
- `.github/workflows/`: executa lint, testes e builds do backend e do frontend na integração contínua.

Documentação, mensagens de commit e mensagens HTTP devem ser escritas em PT-BR. Identificadores de código podem permanecer em inglês quando isso preservar os padrões das bibliotecas e do projeto.

## Fluxo Git obrigatório

- Nunca crie nem altere arquivos diretamente na branch `main`.
- Antes de qualquer alteração, confirme a branch atual e crie uma branch de trabalho com nome descritivo. Para trabalho feito pelo Codex, use o prefixo `codex/`.
- Faça commits pequenos, coesos e com mensagens em PT-BR na branch de trabalho.
- Nunca adicione linha de atribuição a IA (`Co-Authored-By`, `Generated with...` ou equivalente) em commits, pull requests ou descrições, mesmo que alguma ferramenta faça isso por padrão.
- Não reescreva o histórico, não force push e não descarte alterações do usuário sem autorização explícita.

## Regras para alterações

- Procure um padrão equivalente no projeto antes de criar arquivos ou abstrações; preserve a arquitetura existente.
- Faça alterações pequenas e focadas. Não mexa em arquivos fora do escopo e não adicione dependências sem justificar a necessidade.
- Se o comportamento mudar, adicione ou atualize testes. Não silencie, pule nem remova testes apenas para fazer a suíte passar.
- Uma alteração em modelos persistidos exige uma migration do Alembic. Revise tanto o upgrade quanto o downgrade.
- Não confie em IDs, papéis ou permissões enviados pelo cliente; valide autorização no servidor.
- Senhas devem ser tratadas exclusivamente pelas funções centralizadas em `backend/app/core/security.py` quando esse módulo existir; nunca implemente hashing ou comparação de senha de forma dispersa.
- Não exponha stack traces, credenciais, SQL ou detalhes internos do banco nas respostas da API.
- Nunca versione segredos ou valores reais do arquivo `.env`; mantenha exemplos seguros em `.env.example`.

## Comandos do Makefile

Execute os comandos a partir da raiz do repositório:

- `make help`: lista os comandos disponíveis.
- `make up`: constrói e inicia os serviços com Docker Compose.
- `make down`: encerra os serviços.
- `make logs`: acompanha os logs dos serviços.
- `make ps`: mostra o estado dos serviços.
- `make install-frontend`: instala as dependências do frontend com `npm ci`.
- `make lint-backend`: executa Ruff (`check` e `format --check`).
- `make test-backend`: executa os testes do backend com Pytest.
- `make lint-frontend`: executa o lint do frontend com Oxlint.
- `make test-frontend`: executa os testes do frontend com Vitest.
- `make build-frontend`: valida o build de produção do frontend.

## Verificação antes de concluir

Rode as verificações proporcionais ao escopo da mudança e informe claramente o resultado:

- Backend: `make lint-backend` e `make test-backend`.
- Frontend: `make lint-frontend`, `make test-frontend` e `make build-frontend`.
- Full stack: execute todos os comandos de backend e frontend acima.
- Fluxos cobertos por E2E: execute os testes E2E relevantes quando essa suíte existir no projeto.

Se algum comando não puder ser executado por limitação do ambiente, dependência ausente ou serviço indisponível, não o trate como aprovado: registre qual comando faltou e o motivo.
