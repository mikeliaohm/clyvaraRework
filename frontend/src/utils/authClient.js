// Custom authentication client to replace Supabase
// Uses backend JWT authentication

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AuthClient {
  constructor() {
    this.token = localStorage.getItem('auth_token');
    this.user = this.loadUser();
  }

  loadUser() {
    const userStr = localStorage.getItem('auth_user');
    return userStr ? JSON.parse(userStr) : null;
  }

  saveAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem('auth_token', token);
    localStorage.setItem('auth_user', JSON.stringify(user));
  }

  clearAuth() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }

  async signup({ email, password, full_name, username, specialty, graduation_year, institution }) {
    try {
      const response = await fetch(`${API_URL}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name,
          username,
          specialty,
          graduation_year,
          institution,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      const data = await response.json();
      this.saveAuth(data.access_token, data.user);

      return { data: { user: data.user }, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  async login({ email, password }) {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      this.saveAuth(data.access_token, data.user);

      return { data: { user: data.user }, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  async logout() {
    this.clearAuth();
    return { error: null };
  }

  async getSession() {
    if (!this.token) {
      return { data: { session: null }, error: null };
    }

    try {
      // Verify token is still valid by fetching user info
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        // Token is invalid, clear auth
        this.clearAuth();
        return { data: { session: null }, error: null };
      }

      const user = await response.json();
      this.user = user;
      localStorage.setItem('auth_user', JSON.stringify(user));

      return {
        data: {
          session: {
            user,
            access_token: this.token,
          },
        },
        error: null,
      };
    } catch (error) {
      this.clearAuth();
      return { data: { session: null }, error };
    }
  }

  getUser() {
    return {
      data: { user: this.user },
      error: null,
    };
  }

  getToken() {
    return this.token;
  }

  // Auth state change listeners
  _listeners = [];

  onAuthStateChange(callback) {
    this._listeners.push(callback);

    // Return unsubscribe function
    return {
      subscription: {
        unsubscribe: () => {
          this._listeners = this._listeners.filter((cb) => cb !== callback);
        },
      },
    };
  }

  _notifyListeners(event, session) {
    this._listeners.forEach((callback) => {
      callback(event, session);
    });
  }

  // Helper to get headers with auth token
  getAuthHeaders() {
    if (!this.token) {
      return {};
    }
    return {
      'Authorization': `Bearer ${this.token}`,
    };
  }
}

// Create singleton instance
export const authClient = new AuthClient();

// Export a compatible interface similar to Supabase
export const auth = {
  async signUp(credentials) {
    return authClient.signup(credentials);
  },

  async signInWithPassword({ email, password }) {
    return authClient.login({ email, password });
  },

  async signOut() {
    const result = await authClient.logout();
    authClient._notifyListeners('SIGNED_OUT', null);
    return result;
  },

  async getSession() {
    return authClient.getSession();
  },

  getUser() {
    return authClient.getUser();
  },

  onAuthStateChange(callback) {
    return authClient.onAuthStateChange(callback);
  },
};

export default authClient;
