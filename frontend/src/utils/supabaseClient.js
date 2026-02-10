// /frontend/src/utils/supabaseClient.js
// MIGRATED: Now uses custom auth client instead of Supabase
// This file is kept for backward compatibility

import { authClient, auth } from './authClient';

// Export auth client with backward-compatible name
export const supabase = {
  auth,
  // Add any other commonly used methods here for compatibility
};

export { authClient };
export default supabase;
