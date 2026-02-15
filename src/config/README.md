# Configuração de Ambiente

Esta pasta contém as configurações centralizadas da aplicação, seguindo os princípios da arquitetura hexagonal.

## Env.config.ts

Classe responsável por centralizar o acesso às variáveis de ambiente com tipos e valores padrão.

### Variáveis Disponíveis

#### `nodeEnv: string | undefined`

Retorna o ambiente de execução da aplicação (development, production, etc).

```typescript
const env = Env.nodeEnv; // 'development', 'production', etc
```

#### `port: number`

Porta onde a aplicação será executada. Padrão: `5001`

```typescript
const port = Env.port; // 5001
```

#### `corsOrigin: CorsOrigin`

Configuração de origens permitidas para CORS. Pode ser `"*"` ou um array de URLs.
Padrão: `['http://localhost:3000']`

```typescript
const origins = Env.corsOrigin; // '*' ou ['http://localhost:3000', 'https://example.com']
```

#### `skipAuth: boolean`

Flag para pular a validação de autenticação. Padrão: `false`

⚠️ **ATENÇÃO**: Nunca defina como `true` em produção!

```typescript
const skipAuth = Env.skipAuth; // true ou false
```

### Uso

```typescript
import { Env } from './config/env.config';

// Usar no código
const port = Env.port;
const corsOrigin = Env.corsOrigin;
```

### Testes

Os testes unitários da classe Env estão localizados em `test/config/env.config.spec.ts` e cobrem todos os cenários de uso.
