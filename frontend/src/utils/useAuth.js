// /frontend/src/utils/useAuth.js
// MIGRATED: Now uses custom auth client instead of Supabase
import { useEffect, useState } from 'react';
import { authClient } from './authClient';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // get current session on load
    authClient.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setChecking(false);
    });

    // listen for changes (sign in / out)
    const { subscription } = authClient.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return { user, checking };
}
