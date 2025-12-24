// server/passport.ts - COMPLETE FIX
import passport from 'passport';
import { Strategy as LocalStrategy } from 'passport-local';
import { login } from './auth';
import { db } from './db';
import { users } from '@shared/schema';
import { eq } from 'drizzle-orm';

export function setupPassport() {
  passport.use(
    new LocalStrategy(
      {
        usernameField: 'email',
        passwordField: 'password',
      },
      async (email, password, done) => {
        try {
          const user = await login(email, password);
          console.log('✅ Passport authenticated user:', {
            id: user.id,
            apiKey: user.apiKey ? 'Present' : 'MISSING'
          });
          return done(null, user);
        } catch (error) {
          return done(null, false, { message: (error as Error).message });
        }
      }
    )
  );

  passport.serializeUser((user, done) => {
    console.log('📝 Serializing user:', user.id);
    done(null, user.id);
  });

  passport.deserializeUser(async (id: string, done) => {
    try {
      console.log('🔍 Deserializing user:', id);
      
      // Use Drizzle ORM select
      const [user] = await db
        .select({
          id: users.id,
          email: users.email,
          username: users.username,
          role: users.role,
          apiKey: users.apiKey, // Auto-mapped from api_key
        })
        .from(users)
        .where(eq(users.id, id))
        .limit(1);
      
      if (!user) {
        console.error('❌ User not found:', id);
        return done(new Error('User not found'));
      }
      
      console.log('✅ Deserialized user:', {
        id: user.id,
        email: user.email,
        hasApiKey: !!user.apiKey,
        apiKeyPreview: user.apiKey ? `${user.apiKey.slice(0, 15)}...` : 'NONE'
      });
      
      done(null, user);
    } catch (error) {
      console.error('❌ Deserialize error:', error);
      done(error);
    }
  });
}
