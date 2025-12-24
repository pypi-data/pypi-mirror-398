import { z } from 'zod';
import { insertWorkerSchema, insertJobSchema, workers, jobs, users } from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
  unauthorized: z.object({
    message: z.string(),
  }),
};

export const api = {
  auth: {
    me: {
      method: 'GET' as const,
      path: '/api/user',
      responses: {
        200: z.custom<typeof users.$inferSelect>(),
        401: errorSchemas.unauthorized,
      },
    },
  },
  workers: {
    list: {
      method: 'GET' as const,
      path: '/api/workers',
      responses: {
        200: z.array(z.custom<typeof workers.$inferSelect>()),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/workers',
      input: insertWorkerSchema,
      responses: {
        201: z.custom<typeof workers.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    heartbeat: {
      method: 'POST' as const,
      path: '/api/workers/:id/heartbeat',
      responses: {
        200: z.object({ status: z.string() }),
      },
    }
  },
  jobs: {
    list: {
      method: 'GET' as const,
      path: '/api/jobs',
      responses: {
        200: z.array(z.custom<typeof jobs.$inferSelect>()),
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/jobs',
      input: insertJobSchema,
      responses: {
        201: z.custom<typeof jobs.$inferSelect>(),
        400: errorSchemas.validation,
        402: z.object({ message: z.string() }), // Payment required
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/jobs/:id',
      responses: {
        200: z.custom<typeof jobs.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    }
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
