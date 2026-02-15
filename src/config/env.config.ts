/**
 * Centraliza o acesso as variaveis de ambiente com tipos e defaults.
 */

export type CorsOrigin = '*' | string[];

type BooleanLike = string | undefined;

export class Env {
  static get nodeEnv(): string | undefined {
    return process.env.NODE_ENV;
  }

  static get skipAuth(): boolean {
    return Env.parseBoolean(process.env.SKIP_AUTH, false);
  }

  static get corsOrigin(): CorsOrigin {
    const raw = process.env.CORS_ORIGIN;
    if (!raw) return ['http://localhost:3000'];

    if (raw.trim() === '*') return '*';

    const items = raw
      .split(',')
      .map((value) => value.trim())
      .filter((value) => value.length > 0);

    return items.length > 0 ? items : ['http://localhost:3000'];
  }

  static get port(): number {
    return Env.parseInt(process.env.PORT, 5001);
  }

  private static parseBoolean(value: BooleanLike, fallback: boolean): boolean {
    if (value === undefined) return fallback;
    return value.trim().toLowerCase() === 'true';
  }

  private static parseInt(value: string | undefined, fallback: number): number {
    if (value === undefined || value.trim() === '') return fallback;
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
  }
}
