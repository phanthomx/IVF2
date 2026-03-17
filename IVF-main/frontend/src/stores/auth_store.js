// stores/auth_store.js
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: sessionStorage.getItem('token') || null,
    user: JSON.parse(sessionStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    setToken(token) {
      this.token = token;
      sessionStorage.setItem('token', token);
    },
    setUserData(user) {
      this.user = user;
      sessionStorage.setItem('user', JSON.stringify(user));
    },
    getUserData() { return this.user; },
    getToken() { return this.token; },
    getBackendServerURL() { return 'http://localhost:5001'; },
    removeAuthUser() {
      this.token = null;
      this.user = null;
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
    }
  }
});