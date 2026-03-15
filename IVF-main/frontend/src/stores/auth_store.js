// stores/auth_store.js
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    setToken(token) {
      this.token = token;
      localStorage.setItem('token', token); // ← persists across navigation
    },
    setUserData(user) {
      this.user = user;
      localStorage.setItem('user', JSON.stringify(user)); // ← persists across navigation
    },
    getUserData() { return this.user; },
    getToken() { return this.token; },
    getBackendServerURL() { return 'http://localhost:5001'; },
    removeAuthUser() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }
});