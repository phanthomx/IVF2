import { createRouter, createWebHistory } from 'vue-router';

import LoginView from '../views/LoginView.vue';
import AdminView from '../views/AdminView.vue';
import DoctorView from '@/views/DoctorView.vue';
import AccountantView from '@/views/AccountantView.vue';
import ReceptionistView from '@/views/ReceptionistView.vue';
import PatientView from '@/views/PatientView.vue';
import HomePageView from '@/views/HomePageView.vue';

import { useAuthStore } from '@/stores/auth_store';

const routes = [
  
  { path: '/login', name: 'login', component: LoginView },
  { path: '/', name: 'homepage', component: HomePageView},
  { 
    path: '/admin', 
    name: 'admin', 
    component: AdminView,
    meta: { requiresAuth: true, role: 'admin' }
  },
  { 
  path: '/receptionist', 
  name: 'receptionist', 
  component: ReceptionistView,
  meta: { requiresAuth: true, role: 'receptionist' }
},
{ 
  path: '/doctor', 
  name: 'doctor', 
  component: DoctorView,
  meta: { requiresAuth: true, role: 'doctor' }
},
{ 
  path: '/patient', 
  name: 'patient', 
  component: PatientView,
  meta: { requiresAuth: true, role: 'patient' }
},
{ 
  path: '/accountant', 
  name: 'accountant', 
  component: AccountantView,
  meta: { requiresAuth: true, role: 'accountant' }
},

];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;   // ✅ uses exposed computed
  const userRole = authStore.getUserData()?.role;      // ✅ uses exposed action

  // 1. If route requires auth and user isn't logged in → send to login
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/login');
  }

  // 2. If route requires a specific role and user's role doesn't match → send to login
  if (to.meta.requiresAuth && to.meta.role && userRole !== to.meta.role) {
    return next('/login');
  }

  next();
});

export default router;