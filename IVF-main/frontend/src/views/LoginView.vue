
<template>
  <div class="login-container">
    <h2>IVF Portal Login</h2>
    
    <div v-if="messageStore.getFlashMessage()" class="alert">
      {{ messageStore.getFlashMessage() }}
    </div>

    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>Email ID:</label>
        <input v-model="email" type="email" required placeholder="Enter your email" />
      </div>

      <div class="form-group">
        <label>Password:</label>
        <input v-model="password" type="password" required placeholder="Enter password" />
      </div>

      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';
import axios from 'axios';

const email = ref('');
const password = ref('');
const isLoading = ref(false);

const authStore = useAuthStore();
const messageStore = useMessageStore();
const router = useRouter();

const handleLogin = async () => {
  isLoading.value = true;
  try {
    // 1. Send request to Flask (Port 5001)
    const response = await axios.post(`${authStore.getBackendServerURL()}/api/v1/login`, {
      email: email.value,
      password: password.value
    });

    // 2. Update Pinia stores
    authStore.setToken(response.data.token);
    authStore.setUserData(response.data.user);
    
    messageStore.setFlashMessage("Login successful!");

    // 3. CORRECTED Redirection Logic
    const userRole = response.data.user.role;
    
    // Using exact path matches from your router/index.js
    if (userRole === 'admin') {
      router.push('/admin'); // Matches path: '/admin'
    } else if (userRole === 'receptionist') {
      router.push('/receptionist'); 
    } else if (userRole === 'doctor') {
      router.push('/doctor'); 
    } else if (userRole === 'patient') {
      router.push('/patient'); 
    } else if (userRole === 'accountant')   router.push('/accountant');
    else {
      router.push('/'); // Fallback to home if no role matches
    }

  } catch (error) {
    const errorMsg = error.response?.data?.message || "Invalid credentials";
    messageStore.setFlashMessage(errorMsg);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>

.login-container { 
  max-width: 420px; 
  margin: 80px auto; 
  padding: 2.5rem; 
  border: 1px solid #dce6ec; 
  border-radius: 16px; 
  background-color: #ffffff;
  box-shadow: 0 20px 60px rgba(20,35,60,.12);
  font-family: 'Inter', sans-serif;
}

/* TITLE */

h2{
  text-align:center;
  margin-bottom:26px;
  color:#1a2b4a;
  font-weight:700;
  letter-spacing:-0.02em;
}

/* FORM */

.form-group { 
  margin-bottom: 1.4rem; 
}

label { 
  display: block; 
  margin-bottom: 6px; 
  font-weight: 600; 
  color: #4a5b6b; 
  font-size:14px;
}

/* INPUTS */

input { 
  width: 100%; 
  padding: 12px; 
  border: 1.5px solid #dce6ec; 
  border-radius: 10px; 
  box-sizing: border-box; 
  background:#f8fafc;
  font-size:14px;
  transition: all .2s;
}

input::placeholder{
  color:#9aa8b6;
}

input:focus { 
  border-color: #1E7A94; 
  outline: none;
  background:#ffffff;
  box-shadow:0 0 0 3px rgba(30,122,148,.1);
}

/* ALERT MESSAGE */

.alert { 
  padding: 12px; 
  background-color: #e6f4f2; 
  color: #1E7A94; 
  margin-bottom: 1.5rem; 
  border-radius: 8px; 
  text-align: center;
  font-weight:500;
}

/* BUTTON */

button { 
  width: 100%; 
  padding: 14px; 
  margin-top:10px;
  background-color: #1E7A94;
  color: white; 
  border: none; 
  border-radius: 12px;
  cursor: pointer; 
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: .4px;
  transition: all .18s ease;
}

button:hover { 
  background-color: #16677d;
  transform: translateY(-1px);
}

button:active{
  transform:translateY(0px);
}

button:disabled { 
  background-color: #b9d4dc; 
  cursor: not-allowed; 
  transform:none;
}

</style>