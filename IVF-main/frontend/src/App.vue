<template>
  <div id="app-layout">
    <nav class="navbar">
      <RouterLink :to="isAuthenticated ? `/${user.role}` : '/'" class="brand">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="28" height="28">
          <defs>
            <radialGradient id="g" cx="50%" cy="60%" r="50%">
              <stop offset="0%" stop-color="#f9a8d4"/>
              <stop offset="100%" stop-color="#a855f7"/>
            </radialGradient>
          </defs>
          <ellipse cx="50" cy="35" rx="10" ry="22" fill="url(#g)" opacity="0.95"/>
          <ellipse cx="50" cy="35" rx="10" ry="22" fill="url(#g)" opacity="0.85" transform="rotate(-45 50 60)"/>
          <ellipse cx="50" cy="35" rx="10" ry="22" fill="url(#g)" opacity="0.85" transform="rotate(-90 50 60)"/>
          <ellipse cx="50" cy="35" rx="10" ry="22" fill="url(#g)" opacity="0.85" transform="rotate(45 50 60)"/>
          <ellipse cx="50" cy="35" rx="10" ry="22" fill="url(#g)" opacity="0.85" transform="rotate(90 50 60)"/>
          <circle cx="50" cy="60" r="7" fill="#fde68a"/>
          <path d="M50 67 Q45 80 42 90" stroke="#22c55e" stroke-width="3" fill="none" stroke-linecap="round"/>
          <path d="M50 75 Q55 72 60 74" stroke="#22c55e" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        </svg>
        IVF Care
      </RouterLink>

      <div class="nav-links">
        <template v-if="!isAuthenticated">
          <RouterLink to="/login" class="nav-btn">Sign In</RouterLink>
        </template>
        <template v-else>
          <span class="user-text">
            {{ user?.name }}
            <small v-if="user?.role">{{ user.role }}</small>
          </span>
          <button @click="logout" class="logout-btn">Logout</button>
        </template>
      </div>
    </nav>

    <div v-if="message" class="flash">
      {{ message }}
      <button class="flash-close" @click="messageStore.clearFlashMessage()">×</button>
    </div>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import axios from 'axios';
import { useMessageStore } from './stores/message_store';
import { useAuthStore } from './stores/auth_store';

const messageStore = useMessageStore();
const authStore = useAuthStore();
const router = useRouter();

const message = computed(() => messageStore.getFlashMessage());
const user = computed(() => authStore.getUserData());
const isAuthenticated = computed(() => authStore.isAuthenticated);

async function logout() {
  try {
    await axios.post(`${authStore.getBackendServerURL()}/api/v1/logout`);
  } catch (error) {
    console.warn("Logout request failed:", error);
  } finally {
    authStore.removeAuthUser();
    messageStore.setFlashMessage("You have been logged out.");
    router.push('/login');
  }
}

axios.interceptors.request.use(config => {
  const token = authStore.getToken();
  if (token) config.headers['Authentication-Token'] = token;
  return config;
});

axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 && authStore.isAuthenticated) {
      messageStore.setFlashMessage('Session expired. Please log in again.');
      authStore.removeAuthUser();
      router.push('/login');
    }
    return Promise.reject(err);
  }
);
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

#app-layout { min-height: 100vh; font-family: 'DM Sans', sans-serif; background: #f0f5f9; }

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 0 2.5rem;
  height: 62px;
  border-bottom: 1px solid #dde6f0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.2rem;
  font-weight: 700;
  text-decoration: none;
  color: #1a2535;
}

.nav-links { display: flex; align-items: center; gap: 1rem; }

.user-text {
  font-size: 0.82rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.user-text small {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
}

.nav-btn {
  text-decoration: none;
  background: #0a7ea4;
  color: #fff;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  font-size: 0.84rem;
  font-weight: 600;
  transition: opacity 0.15s;
}
.nav-btn:hover { opacity: 0.88; }

.logout-btn {
  background: #fff1f2;
  color: #e11d48;
  border: 1px solid #fecdd3;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.logout-btn:hover { background: #e11d48; color: #fff; }

.flash {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 1.5rem;
  background: #f0fdf4;
  color: #059669;
  border-bottom: 1px solid #a7f3d0;
  font-size: 0.84rem;
  font-weight: 500;
}
.flash-close { background: none; border: none; font-size: 1.1rem; color: #059669; cursor: pointer; line-height: 1; }

.content { padding: 0; }
</style>