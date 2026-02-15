import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';
import { INestApplication } from '@nestjs/common';
import { AppModule } from './app.module';
import { Env } from './config/env.config';
import express from 'express';
import { onRequest } from 'firebase-functions/v2/https';

const expressApp = express();
let cachedApp: INestApplication | null = null;

async function createNestApplication(): Promise<INestApplication> {
  if (cachedApp) {
    return cachedApp;
  }

  const app = await NestFactory.create(
    AppModule,
    new ExpressAdapter(expressApp),
    { logger: ['error', 'warn', 'log'] },
  );

  // Configuração CORS
  app.enableCors({
    origin: Env.corsOrigin,
    credentials: true,
  });

  await app.init();

  cachedApp = app;
  return app;
}

// Firebase Function export
export const api = onRequest({ cors: true }, async (req, res) => {
  await createNestApplication();
  expressApp(req, res);
});

// Desenvolvimento local
if (Env.nodeEnv === 'dev') {
  void createNestApplication().then(() => {
    const port = Env.port;
    expressApp.listen(port, () => {
      console.log(`🚀 Server is running on http://localhost:${port}`);
    });
  });
}
