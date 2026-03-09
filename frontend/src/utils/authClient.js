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
      const response = await fetch(`${API_URL}/api/fau/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name, username, specialty, graduation_year, institution }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Signup failed');
      }

      // Registration returns user data but no token — auto-login to get one
      return this.login({ email, password });
    } catch (error) {
      return { data: null, error };
    }
  }

  async login({ email, password }) {
    try {
      // fastapi-users login uses OAuth2 form data (username field = email)
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const tokenResponse = await fetch(`${API_URL}/api/fau/auth/jwt/login`, {
        method: 'POST',
        body: formData,
      });

      if (!tokenResponse.ok) {
        const error = await tokenResponse.json();
        throw new Error(error.detail || 'Login failed');
      }

      const { access_token } = await tokenResponse.json();

      // Fetch user profile with the new token
      const userResponse = await fetch(`${API_URL}/api/fau/users/me`, {
        headers: { 'Authorization': `Bearer ${access_token}` },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const user = await userResponse.json();
      this.saveAuth(access_token, user);

      return { data: { user }, error: null };
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
      const response = await fetch(`${API_URL}/api/fau/users/me`, {
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
