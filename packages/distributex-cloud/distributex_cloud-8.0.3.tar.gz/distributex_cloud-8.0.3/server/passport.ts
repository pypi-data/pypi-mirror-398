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
          return done(null, user);
        } catch (error) {
          return done(null, false, { message: (error as Error).message });
        }
      }
    )
  );

  passport.serializeUser((user, done) => {
    done(null, user.id);
  });

  passport.deserializeUser(async (id: string, done) => {
    try {
      const [user] = await db.select({
        id: users.id,
        email: users.email,
        username: users.username,
        credits: users.credits,
      }).from(users).where(eq(users.id, id)).limit(1);
      
      if (!user) {
        return done(new Error('User not found'));
      }
      
      done(null, user);
    } catch (error) {
      done(error);
    }
  });
}
