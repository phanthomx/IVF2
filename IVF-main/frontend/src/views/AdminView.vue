<template>
  <div class="dashboard">
    <header class="header">
      <div class="header-left">
        <h1>Admin <span class="accent">Command Center</span></h1>
        <p class="subtitle">HIPAA-Compliant Management System</p>
      </div>
      <button @click="showModal = true" class="add-btn">+ Onboard Doctor</button>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon patients">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        </div>
        <div>
          <label>Total Patients</label>
          <div class="value blue">{{ stats.total_patients ?? 0 }}</div>
          <div class="sub">{{ stats.patient_growth ?? '—' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon doctors">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0a7ea4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        </div>
        <div>
          <label>Active Doctors</label>
          <div class="value teal">{{ stats.active_doctors ?? 0 }}</div>
          <div class="sub">{{ stats.online_now ?? '—' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon health">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <div>
          <label>System Health</label>
          <div class="value green">{{ stats.system_status ?? 'Checking...' }}</div>
          <div class="sub">{{ stats.uptime ? `Optimal • ${stats.uptime} uptime` : '—' }}</div>
        </div>
      </div>
    </div>

    <section class="section">
      <div class="section-header">
        <h2>Doctors &amp; Patients</h2>
        <span class="badge">{{ users.length }}</span>
      </div>
      <div v-if="loadingUsers" class="empty">Loading users...</div>
      <div v-else-if="users.length === 0" class="empty">No users found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Details</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td class="mono muted">#{{ user.id }}</td>
            <td class="bold">{{ user.name }}</td>
            <td class="muted sm">{{ user.email }}</td>
            <td><span :class="['role', user.role]">{{ user.role }}</span></td>
            <td class="muted sm">
              <span v-if="user.specialization && user.specialization !== '—'">{{ user.specialization }}</span>
              <span v-else-if="user.service_id && user.service_id !== '—'" class="mono">{{ user.service_id }}</span>
              <span v-else>—</span>
            </td>
            <td>
              <button v-if="user.role === 'doctor'" @click="removeDoctor(user.id, user.name)" class="rm-btn">Remove</button>
              <button v-else-if="user.role === 'patient'" @click="removePatient(user.id, user.name)" class="rm-btn">Remove</button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="section">
      <div class="section-header">
        <h2>Security Audit Log</h2>
        <span class="badge">{{ logs.length }}</span>
      </div>
      <div v-if="loadingLogs" class="empty">Loading logs...</div>
      <div v-else-if="logs.length === 0" class="empty">No audit logs found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Timestamp</th><th>User</th><th>IP Address</th><th>Endpoint</th><th>Method</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(log, i) in logs" :key="i">
            <td class="mono muted sm">{{ log.timestamp }}</td>
            <td class="mono accent">{{ log.user_id }}</td>
            <td class="mono muted sm">{{ log.ip_address }}</td>
            <td class="mono blue sm">{{ log.endpoint }}</td>
            <td><span :class="['method', (log.method || 'get').toLowerCase()]">{{ log.method || 'GET' }}</span></td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="showModal" class="overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-head">
          <h2>Register New Doctor</h2>
          <button @click="showModal = false" class="close">×</button>
        </div>
        <form @submit.prevent="handleOnboard">
          <div class="fields">
            <div class="field" v-for="f in formFields" :key="f.key">
              <label>{{ f.label }}</label>
              <input v-model="form[f.key]" :type="f.type || 'text'" :placeholder="f.placeholder" required />
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" @click="showModal = false" class="cancel-btn">Cancel</button>
            <button type="submit" class="add-btn" :disabled="isSubmitting">
              {{ isSubmitting ? 'Registering...' : 'Register Doctor' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';

const authStore = useAuthStore();
const messageStore = useMessageStore();

const stats       = ref({});
const logs        = ref([]);
const users       = ref([]);
const showModal   = ref(false);
const isSubmitting = ref(false);
const loadingUsers = ref(false);
const loadingLogs  = ref(false);

const form = ref({
  name: '',
  email: '',
  password: '',
  specialization: '',
  license_number: ''
});

const formFields = [
  { key: 'name',           label: 'Full Name',      placeholder: 'Dr. Jane Smith' },
  { key: 'email',          label: 'Email Address',  placeholder: 'dr.smith@ivfclinic.com', type: 'email' },
  { key: 'password',       label: 'Temp Password',  placeholder: 'Min. 8 characters',      type: 'password' },
  { key: 'specialization', label: 'Specialization', placeholder: 'e.g. Reproductive Endocrinology' },
  { key: 'license_number', label: 'License Number', placeholder: 'e.g. MCI-2024-001' },
];

// ✅ withCredentials included so auth token cookie is sent properly
const getAuthHeaders = () => ({
  withCredentials: true,
  headers: {
    'Authentication-Token': authStore.getToken(),
    'Content-Type': 'application/json'
  }
});

const fetchData = async () => {
  loadingLogs.value = true;
  try {
    const res = await axios.get(
      `${authStore.getBackendServerURL()}/api/v1/admin/dashboard`,
      getAuthHeaders()
    );
    stats.value = res.data.stats ?? {};
    logs.value  = res.data.logs  ?? [];
  } catch (err) {
    const msg = err.response?.data?.message || "Failed to load dashboard.";
    messageStore.setFlashMessage(msg);
  } finally {
    loadingLogs.value = false;
  }
};

const fetchUsers = async () => {
  loadingUsers.value = true;
  try {
    const res = await axios.get(
      `${authStore.getBackendServerURL()}/api/v1/admin/users`,
      getAuthHeaders()
    );
    users.value = res.data.users ?? [];
  } catch (err) {
    const msg = err.response?.data?.message || "Failed to load users.";
    messageStore.setFlashMessage(msg);
  } finally {
    loadingUsers.value = false;
  }
};

const handleOnboard = async () => {
  isSubmitting.value = true;
  try {
    await axios.post(
      `${authStore.getBackendServerURL()}/api/v1/admin/onboard-doctor`,
      form.value,
      getAuthHeaders()
    );
    messageStore.setFlashMessage("Doctor registered successfully!");
    showModal.value = false;
    form.value = { name: '', email: '', password: '', specialization: '', license_number: '' };
    fetchData();
    fetchUsers();
  } catch (err) {
    const msg = err.response?.data?.message || "Registration failed.";
    messageStore.setFlashMessage(msg);
  } finally {
    isSubmitting.value = false;
  }
};

const removeDoctor = async (id, name) => {
  if (!confirm(`Permanently remove Dr. ${name}?`)) return;
  try {
    await axios.delete(
      `${authStore.getBackendServerURL()}/api/v1/admin/remove-doctor/${id}`,
      getAuthHeaders()
    );
    messageStore.setFlashMessage(`Dr. ${name} removed.`);
    fetchData();
    fetchUsers();
  } catch (err) {
    const msg = err.response?.data?.message || "Failed to remove doctor.";
    messageStore.setFlashMessage(msg);
  }
};

const removePatient = async (id, name) => {
  if (!confirm(`Permanently remove ${name}?`)) return;
  try {
    await axios.delete(
      `${authStore.getBackendServerURL()}/api/v1/admin/remove-patient/${id}`,
      getAuthHeaders()
    );
    messageStore.setFlashMessage(`${name} removed.`);
    fetchData();
    fetchUsers();
  } catch (err) {
    const msg = err.response?.data?.message || "Failed to remove patient.";
    messageStore.setFlashMessage(msg);
  }
};

onMounted(() => {
  fetchData();
  fetchUsers();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');

.dashboard { font-family: 'DM Sans', sans-serif; background: #f0f5f9; min-height: 100vh; padding: 2rem 2.5rem; color: #1a2535; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1.25rem; border-bottom: 1px solid #dde6f0; }
.header h1 { font-size: 1.6rem; font-weight: 700; margin: 0; }
.accent { color: #0a7ea4; }
.subtitle { font-size: 0.72rem; color: #94a3b8; letter-spacing: 0.06em; margin: 0.2rem 0 0; text-transform: uppercase; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.25rem 1.5rem; display: flex; align-items: center; gap: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.stat-icon { font-size: 1.8rem; width: 48px; height: 48px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.stat-icon.patients { background: #eff6ff; }
.stat-icon.doctors  { background: #f0fdf4; }
.stat-icon.health   { background: #f0fdf4; }
label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.2rem; }
.value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
.value.blue  { color: #2563eb; }
.value.teal  { color: #0a7ea4; }
.value.green { color: #059669; }
.sub { font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem; }

/* Sections */
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.section-header h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin: 0; }
.badge { background: #e2e8f0; color: #64748b; font-size: 0.68rem; font-family: 'IBM Plex Mono', monospace; padding: 0.1rem 0.5rem; border-radius: 20px; }

/* Table */
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #dde6f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.table th { text-align: left; padding: 0.7rem 1rem; background: #f8fafc; color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.table td { padding: 0.8rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.84rem; vertical-align: middle; }
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }

.mono  { font-family: 'IBM Plex Mono', monospace; }
.bold  { font-weight: 600; }
.muted { color: #94a3b8; }
.sm    { font-size: 0.78rem; }
.blue  { color: #2563eb; }
.accent { color: #0a7ea4; }

/* Role tags */
.role { display: inline-block; padding: 0.18rem 0.55rem; border-radius: 5px; font-size: 0.67rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
.role.doctor  { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.role.patient { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }

/* Method tags */
.method { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 600; padding: 0.18rem 0.5rem; border-radius: 4px; }
.method.get    { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.method.post   { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.method.delete { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.method.put    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }

/* Buttons */
.add-btn { background: #0a7ea4; color: #fff; border: none; padding: 0.7rem 1.3rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.84rem; cursor: pointer; transition: opacity 0.15s; }
.add-btn:hover { opacity: 0.88; }
.add-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.rm-btn { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; padding: 0.28rem 0.7rem; border-radius: 5px; font-size: 0.73rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.rm-btn:hover { background: #e11d48; color: #fff; }
.cancel-btn { background: transparent; color: #64748b; border: 1px solid #e2e8f0; padding: 0.65rem 1.2rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.cancel-btn:hover { border-color: #94a3b8; }

/* Empty */
.empty { padding: 2rem; text-align: center; color: #94a3b8; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.84rem; }

/* Modal */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal { background: #fff; border-top: 3px solid #0a7ea4; border-radius: 12px; width: 460px; padding: 1.75rem; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
.modal-head h2 { font-size: 1.05rem; font-weight: 700; margin: 0; }
.close { background: none; border: none; font-size: 1.4rem; color: #94a3b8; cursor: pointer; line-height: 1; }
.fields { display: flex; flex-direction: column; gap: 0.85rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field label { font-size: 0.67rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
.field input { background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.65rem 0.85rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; transition: border-color 0.15s; }
.field input:focus { outline: none; border-color: #0a7ea4; background: #fff; }
.field input::placeholder { color: #cbd5e1; }
.modal-foot { display: flex; justify-content: flex-end; gap: 0.6rem; margin-top: 1.25rem; padding-top: 1.1rem; border-top: 1px solid #f1f5f9; }
</style>