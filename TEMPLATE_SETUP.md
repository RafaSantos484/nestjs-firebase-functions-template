# Template Setup Guide

This guide will help you configure this template for your new project.

## 🔧 Initial Setup Steps

### 1. Update Project Information

Edit `package.json`:
```json
{
  "name": "your-project-name",
  "version": "1.0.0",
  "description": "Your project description",
  "author": "Your Name <your.email@example.com>",
  "license": "MIT"
}
```

### 2. Configure Firebase Project

#### Option A: Use Existing Project
```bash
firebase use --add
```
Select your project and give it an alias (e.g., "default", "staging", "production").

#### Option B: Create New Project
```bash
# Create project in Firebase Console first
# Then link it:
firebase use --add
```

Update `.firebaserc`:
```json
{
  "projects": {
    "default": "your-project-id",
    "staging": "your-project-staging",
    "production": "your-project-prod"
  }
}
```

### 3. Configure Environment Files

Copy and customize environment files:

```bash
# Development environment
cp .env.dev.example .env.dev

# Production environment
cp .env.production.example .env.production
```

**`.env.dev`** - For local development:
```env
PORT=5001
CORS_ORIGIN=*
SKIP_AUTH=true
NODE_ENV=development
```

**`.env.production`** - For production deployment:
```env
PORT=5001
CORS_ORIGIN=https://yourdomain.com,https://app.yourdomain.com
SKIP_AUTH=false
NODE_ENV=production
```

### 3.1 Configure Firebase Service Account Credentials (Optional)

If your application needs to interact with Firebase services (Firestore, Auth, etc.), set up credentials:

1. Go to [Firebase Console](https://console.firebase.google.com/) → Your Project → Settings ⚙️ → Service Accounts
2. Click **"Generate New Private Key"**
3. Copy the downloaded `credentials.json` to your project root:

```bash
cp ~/Downloads/credentials.json .
```

4. Update `credentials.json.example` with placeholder values (safe to commit):

```json
{
  "type": "service_account",
  "project_id": "your-firebase-project-id",
  "private_key_id": "key_id_here",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com",
  "client_id": "client_id_here",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxx%40your-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

⚠️ **Important:** 
- `credentials.json` is in `.gitignore` - never commit it!
- Only commit `credentials.json.example` with placeholder values
- For production, use Cloud Secret Manager or secure environment variables

For detailed setup instructions, see [FIREBASE_CREDENTIALS.md](./FIREBASE_CREDENTIALS.md).

### 4. Update Application Entry Point (Optional)

If you want to change the Firebase Function name from `api` to something else, edit `src/main.ts`:

```typescript
// Change from:
export const api = onRequest(async (req, res) => { /* ... */ });

// To:
export const myfunction = onRequest(async (req, res) => { /* ... */ });
```

### 5. Configure Firebase Function Settings (Optional)

Edit `src/main.ts` to add Firebase Function settings:

```typescript
import { onRequest } from 'firebase-functions/v2/https';

export const api = onRequest(
  {
    region: 'us-central1',           // Choose your region
    maxInstances: 100,                // Max concurrent instances
    minInstances: 0,                  // Min instances (0 = scale to zero)
    timeoutSeconds: 60,               // Timeout (default: 60s, max: 540s)
    memory: '256MiB',                 // Memory allocation
    cors: true,                       // Enable CORS (we handle it in code)
  },
  async (req, res) => {
    await createNestApplication();
    expressApp(req, res);
  }
);
```

### 6. Add Your Business Logic

The template provides a basic structure. Add your features:

#### Generate New Resources
```bash
# Generate a new module with controller and service
nest generate resource users

# Or individually:
nest generate module products
nest generate controller products
nest generate service products
```

#### Organize by Feature
```
src/
├── config/
├── users/
│   ├── users.controller.ts
│   ├── users.service.ts
│   ├── users.module.ts
│   └── dto/
│       ├── create-user.dto.ts
│       └── update-user.dto.ts
├── products/
│   ├── products.controller.ts
│   ├── products.service.ts
│   └── products.module.ts
└── main.ts
```

### 7. Configure Database (If Needed)

#### Firestore Example
```bash
npm install @google-cloud/firestore
```

```typescript
// src/config/firestore.config.ts
import { Firestore } from '@google-cloud/firestore';

export const firestore = new Firestore({
  projectId: Env.firebaseProjectId,
});
```

#### Other Databases
Install appropriate packages:
- PostgreSQL: `npm install @nestjs/typeorm typeorm pg`
- MongoDB: `npm install @nestjs/mongoose mongoose`
- MySQL: `npm install @nestjs/typeorm typeorm mysql2`

### 8. Add Authentication (If Needed)

#### Firebase Auth Guard Example

Create `src/guards/firebase-auth.guard.ts`:
```typescript
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import * as admin from 'firebase-admin';
import { Env } from '../config/env.config';

@Injectable()
export class FirebaseAuthGuard implements CanActivate {
  async canActivate(context: ExecutionContext): Promise<boolean> {
    if (Env.skipAuth) return true; // Skip in development

    const request = context.switchToHttp().getRequest();
    const token = this.extractToken(request);

    if (!token) return false;

    try {
      const decodedToken = await admin.auth().verifyIdToken(token);
      request.user = decodedToken;
      return true;
    } catch (error) {
      return false;
    }
  }

  private extractToken(request: any): string | null {
    const authHeader = request.headers.authorization;
    if (!authHeader) return null;
    return authHeader.replace('Bearer ', '');
  }
}
```

Use in controllers:
```typescript
@Controller('users')
@UseGuards(FirebaseAuthGuard)
export class UsersController {
  // Protected routes
}
```

## 🚀 Development Workflow

### Local Development
```bash
npm run start:dev     # Hot reload
```

### Testing
```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

### Firebase Emulator
```bash
npm run serve         # Test with Firebase emulators
```

### Deploy
```bash
npm run deploy        # Deploy to Firebase
```

## 📝 Best Practices

### 1. Environment Variables
- Never commit `.env` files (only `.env.*.example`)
- Always provide defaults in `src/config/env.config.ts`
- Document new variables in README.md

### 2. Error Handling
```typescript
import { HttpException, HttpStatus } from '@nestjs/common';

throw new HttpException('User not found', HttpStatus.NOT_FOUND);
```

### 3. Validation
```bash
npm install class-validator class-transformer
```

```typescript
// dto/create-user.dto.ts
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(3)
  name: string;
}
```

Enable in `main.ts`:
```typescript
import { ValidationPipe } from '@nestjs/common';

app.useGlobalPipes(new ValidationPipe());
```

### 4. Logging
```typescript
import { Logger } from '@nestjs/common';

export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  async findAll() {
    this.logger.log('Finding all users');
    // ...
  }
}
```

## 🔐 Security Checklist

- [ ] Set `SKIP_AUTH=false` in production
- [ ] Configure proper CORS origins (no `*` in production)
- [ ] Add rate limiting (consider `@nestjs/throttler`)
- [ ] Validate all inputs with class-validator
- [ ] Use environment variables for secrets
- [ ] Enable Firebase App Check for production
- [ ] Review Firebase Security Rules
- [ ] Set up proper IAM roles

## 📊 Monitoring

### Firebase Console
- View logs: `npm run logs`
- Monitor performance in Firebase Console
- Set up alerts for errors

### Cloud Logging
```typescript
import { Logger } from '@nestjs/common';

const logger = new Logger('MyService');
logger.log('Info message');
logger.warn('Warning message');
logger.error('Error message');
```

## 🎯 Next Steps

1. ✅ Complete this setup guide
2. ✅ Update README.md with project-specific info
3. ✅ Configure CI/CD (GitHub Actions, GitLab CI, etc.)
4. ✅ Set up staging environment
5. ✅ Add monitoring and alerts
6. ✅ Configure backup strategy
7. ✅ Document API endpoints (consider Swagger/OpenAPI)

## 📚 Additional Resources

- [NestJS Documentation](https://docs.nestjs.com)
- [Firebase Functions v2](https://firebase.google.com/docs/functions/2nd-gen)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Firebase Security Best Practices](https://firebase.google.com/docs/rules/security)

---

**Ready to build something awesome!** 🚀
