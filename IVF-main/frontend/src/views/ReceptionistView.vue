
<template>
  <div class="dashboard">

    <!-- Header -->
    <header class="header">
      <div>
        <p class="eyebrow">Front Desk Hub</p>
        <h1>Receptionist <span class="accent">Dashboard</span></h1>
      </div>
      <div class="header-actions">
        <button @click="activeTab = 'queue'"    :class="['tab-btn', activeTab === 'queue'    ? 'active' : '']">Queue</button>
        <button @click="activeTab = 'bookings'" :class="['tab-btn', activeTab === 'bookings' ? 'active' : '']">Bookings</button>
        <button @click="activeTab = 'history'"  :class="['tab-btn', activeTab === 'history'  ? 'active' : '']">History</button>
        <button @click="openRegister" class="add-btn">+ Register Patient</button>
        <button @click="openBooking"  class="book-btn">+ Book Appointment</button>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <label>Today's Appointments</label>
        <div class="value blue">{{ queue.length }}</div>
      </div>
      <div class="stat-card">
        <label>Waiting</label>
        <div class="value yellow">{{ queue.filter(q => q.status === 'waiting').length }}</div>
      </div>
      <div class="stat-card">
        <label>In Session</label>
        <div class="value teal">{{ queue.filter(q => q.status === 'in-session').length }}</div>
      </div>
      <div class="stat-card">
        <label>Completed</label>
        <div class="value green">{{ queue.filter(q => q.status === 'completed').length }}</div>
      </div>
      <div class="stat-card">
        <label>Pending Payment</label>
        <div class="value red">{{ queue.filter(q => q.payment_status === 'pending').length }}</div>
      </div>
    </div>

    <!-- ── QUEUE TAB ── -->
    <section v-if="activeTab === 'queue'" class="section">
      <div class="section-header">
        <h2>Daily Queue</h2>
        <input type="date" v-model="selectedDate" class="date-input-sm" />
        <span class="badge">{{ queue.length }}</span>
      </div>
      <div v-if="loadingQueue" class="empty">Loading queue...</div>
      <div v-else-if="queue.length === 0" class="empty">No appointments scheduled for this date.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Patient</th>
            <th>Service ID</th>
            <th>Doctor</th>
            <th>Stage</th>
            <th>Status</th>
            <th>Payment</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in queue" :key="entry.appointment_id">
            <td class="mono sm">{{ entry.start_time }} – {{ entry.end_time }}</td>
            <td>
              <div class="bold">{{ entry.patient_name }}</div>
              <div class="sm muted" v-if="entry.is_walkin">🚶 Walk-in</div>
            </td>
            <td class="mono muted sm">{{ entry.service_id }}</td>
            <td class="sm">{{ entry.doctor_name }}</td>
            <td><span class="stage-tag">{{ entry.stage || '—' }}</span></td>
            <td><span :class="['status-tag', entry.status]">{{ entry.status }}</span></td>
            <td>
              <div v-if="entry.invoice_id" class="pay-toggle-row">
                <span :class="['pay-tag', entry.payment_status]">{{ entry.payment_status }}</span>
                <div
                  :class="['toggle', entry.payment_status === 'paid' ? 'on' : '']"
                  @click="togglePayment(entry)"
                  :title="entry.payment_status === 'paid' ? 'Mark as Pending' : 'Mark as Paid'"
                >
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <span v-else class="muted sm">No Invoice</span>
            </td>
            <td>
              <button
                v-if="entry.status === 'waiting'"
                @click="cancelAppointment(entry)"
                class="cancel-appt-btn"
              >
                Cancel
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── BOOKINGS TAB ── -->
    <section v-if="activeTab === 'bookings'" class="section">
      <div class="section-header">
        <h2>Upcoming Bookings</h2>
        <span class="badge">{{ upcomingBookings.length }}</span>
      </div>
      <div class="search-row">
        <input
          v-model="bookingsSearch"
          placeholder="Search by patient name or service ID..."
          class="search-input"
          @input="fetchBookings"
        />
      </div>
      <div v-if="loadingBookings" class="empty">Loading bookings...</div>
      <div v-else-if="upcomingBookings.length === 0" class="empty">No upcoming bookings found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Patient</th>
            <th>Service ID</th>
            <th>Doctor</th>
            <th>Stage</th>
            <th>Status</th>
            <th>Walk-in</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in upcomingBookings"
            :key="entry.appointment_id"
            :class="entry.status === 'in-session' ? 'row-active' : ''"
          >
            <td class="mono sm bold">{{ entry.date }}</td>
            <td class="mono sm muted">{{ entry.start_time }} – {{ entry.end_time }}</td>
            <td><div class="bold">{{ entry.patient_name }}</div></td>
            <td class="mono muted sm">{{ entry.service_id }}</td>
            <td class="sm">{{ entry.doctor_name }}</td>
            <td><span class="stage-tag">{{ entry.stage || '—' }}</span></td>
            <td><span :class="['status-tag', entry.status]">{{ entry.status }}</span></td>
            <td>
              <span v-if="entry.is_walkin" class="walkin-tag">🚶 Walk-in</span>
              <span v-else class="muted sm">—</span>
            </td>
            <td>
              <button
                v-if="entry.can_cancel"
                @click="cancelAppointment(entry)"
                class="cancel-appt-btn"
              >
                Cancel
              </button>
              <span v-else-if="entry.status === 'in-session'" class="in-session-note">In Progress</span>
              <span v-else class="muted sm">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── HISTORY TAB ── -->
    <section v-if="activeTab === 'history'" class="section">
      <div class="section-header">
        <h2>Appointment History</h2>
        <span class="badge">{{ appointmentHistory.length }}</span>
      </div>
      <div class="search-row">
        <input
          v-model="historySearch"
          placeholder="Search by patient name or service ID..."
          class="search-input"
          @input="fetchHistory"
        />
      </div>
      <div v-if="loadingHistory" class="empty">Loading history...</div>
      <div v-else-if="appointmentHistory.length === 0" class="empty">No past appointments found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Patient</th>
            <th>Service ID</th>
            <th>Doctor</th>
            <th>Stage</th>
            <th>Status</th>
            <th>Payment</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in appointmentHistory" :key="entry.appointment_id">
            <td class="mono sm bold">{{ entry.date }}</td>
            <td class="mono sm muted">{{ entry.start_time }} – {{ entry.end_time }}</td>
            <td>
              <div class="bold">{{ entry.patient_name }}</div>
              <div class="sm muted" v-if="entry.is_walkin">🚶 Walk-in</div>
            </td>
            <td class="mono muted sm">{{ entry.service_id }}</td>
            <td class="sm">{{ entry.doctor_name }}</td>
            <td><span class="stage-tag">{{ entry.stage || '—' }}</span></td>
            <td><span :class="['status-tag', entry.status]">{{ entry.status }}</span></td>
            <td>
              <div v-if="entry.invoice_id" class="pay-toggle-row">
                <span :class="['pay-tag', entry.payment_status]">{{ entry.payment_status }}</span>
                <div
                  :class="['toggle', entry.payment_status === 'paid' ? 'on' : '']"
                  @click="togglePayment(entry)"
                  :title="entry.payment_status === 'paid' ? 'Mark as Pending' : 'Mark as Paid'"
                >
                  <div class="toggle-knob"></div>
                </div>
              </div>
              <span v-else class="muted sm">No Invoice</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── Register Patient Modal ── -->
    <div v-if="showRegister" class="overlay" @click.self="showRegister = false">
      <div class="modal">
        <div class="modal-head">
          <h2>Register New Patient</h2>
          <button @click="showRegister = false" class="close">×</button>
        </div>
        <form @submit.prevent="handleRegister">
          <div class="fields">
            <div class="row2">
              <div class="field">
                <label>Full Name</label>
                <input v-model="regForm.name" placeholder="Jane Doe" required />
              </div>
              <div class="field">
                <label>Email</label>
                <input v-model="regForm.email" type="email" placeholder="jane@email.com" required />
              </div>
            </div>
            <div class="row2">
              <div class="field">
                <label>Temp Password</label>
                <input v-model="regForm.password" type="password" placeholder="Min 8 chars" required />
              </div>
              <div class="field">
                <label>Contact Number</label>
                <input v-model="regForm.contact_info" placeholder="9876543210" />
              </div>
            </div>
            <div class="row4">
              <div class="field">
                <label>Age</label>
                <input v-model.number="regForm.age" type="number" placeholder="28" />
              </div>
              <div class="field">
                <label>Height (cm)</label>
                <input v-model.number="regForm.height_cm" type="number" placeholder="165" />
              </div>
              <div class="field">
                <label>Weight (kg)</label>
                <input v-model.number="regForm.weight_kg" type="number" placeholder="62" />
              </div>
              <div class="field">
                <label>Blood Type</label>
                <select v-model="regForm.blood_type">
                  <option value="">Select</option>
                  <option v-for="bt in bloodTypes" :key="bt" :value="bt">{{ bt }}</option>
                </select>
              </div>
            </div>
          </div>
          <div class="modal-foot">
            <button type="button" @click="showRegister = false" class="cancel-btn">Cancel</button>
            <button type="submit" class="add-btn" :disabled="isSubmitting">
              {{ isSubmitting ? 'Registering...' : 'Register Patient' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ── Book Appointment Modal ── -->
    <div v-if="showBooking" class="overlay" @click.self="showBooking = false">
      <div class="modal">
        <div class="modal-head">
          <h2>Book Appointment</h2>
          <button @click="showBooking = false" class="close">×</button>
        </div>
        <form @submit.prevent="handleBooking">
          <div class="fields">
            <div class="field">
              <label>Patient</label>
              <input
                v-model="patientSearch"
                placeholder="Search by name or service ID..."
                @input="filterPatients"
              />
              <div v-if="filteredPatients.length && patientSearch && !bookForm.patient_id" class="dropdown">
                <div
                  v-for="p in filteredPatients"
                  :key="p.id"
                  class="dropdown-item"
                  @click="selectPatient(p)"
                >
                  <span class="bold">{{ p.name }}</span>
                  <span class="mono muted sm">{{ p.service_id }}</span>
                </div>
              </div>
              <div v-if="bookForm.patient_id" class="selected-tag">
                ✓ {{ patientSearch }}
                <button type="button" @click="clearPatient" class="clear">×</button>
              </div>
            </div>
            <div class="row2">
              <div class="field">
                <label>Doctor</label>
                <select v-model="bookForm.doctor_id" @change="clearSlots" required>
                  <option value="">Select doctor</option>
                  <option v-for="d in doctors" :key="d.id" :value="d.id">
                    {{ d.name }} — {{ d.specialization }}
                  </option>
                </select>
              </div>
              <div class="field">
                <label>Date</label>
                <input v-model="bookForm.date" type="date" :min="today" :max="maxDate" @change="fetchSlots" required />
              </div>
            </div>
            <div class="field toggle-row">
              <label>Walk-in Patient?</label>
              <div :class="['toggle', bookForm.is_walkin ? 'on' : '']" @click="bookForm.is_walkin = !bookForm.is_walkin">
                <div class="toggle-knob"></div>
              </div>
            </div>
            <div class="field" v-if="slots.length > 0">
              <label>Available Slots</label>
              <div class="slots-grid">
                <button
                  v-for="slot in slots"
                  :key="slot.start_time"
                  type="button"
                  :class="['slot-btn', slot.available ? '' : 'taken', bookForm.start_time === slot.start_time ? 'selected' : '']"
                  :disabled="!slot.available"
                  @click="bookForm.start_time = slot.start_time"
                >
                  {{ slot.start_time }}
                </button>
              </div>
            </div>
            <div v-else-if="bookForm.doctor_id && bookForm.date && !loadingSlots" class="empty-sm">
              No availability for this date.
            </div>
            <div v-if="loadingSlots" class="empty-sm">Loading slots...</div>
          </div>
          <div class="modal-foot">
            <button type="button" @click="showBooking = false" class="cancel-btn">Cancel</button>
            <button type="submit" class="add-btn" :disabled="isSubmitting || !bookForm.start_time || !bookForm.patient_id">
              {{ isSubmitting ? 'Booking...' : 'Confirm Booking' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';

const authStore    = useAuthStore();
const messageStore = useMessageStore();
const BASE         = authStore.getBackendServerURL();

// ✅ IST-aware date helper
const getISTDateString = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
};

const today   = getISTDateString(0);
const maxDate = computed(() => getISTDateString(7));

// ── State ──────────────────────────────────────────────────────────────────
const activeTab          = ref('queue');
const selectedDate       = ref(today);
const queue              = ref([]);
const upcomingBookings   = ref([]);
const appointmentHistory = ref([]);
const patients           = ref([]);
const doctors            = ref([]);
const slots              = ref([]);
const loadingQueue       = ref(false);
const loadingBookings    = ref(false);
const loadingHistory     = ref(false);
const loadingSlots       = ref(false);
const isSubmitting       = ref(false);
const showRegister       = ref(false);
const showBooking        = ref(false);
const patientSearch      = ref('');
const bookingsSearch     = ref('');
const historySearch      = ref('');
const filteredPatients   = ref([]);
const bloodTypes         = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const regForm = ref({
  name: '', email: '', password: '', contact_info: '',
  age: null, height_cm: null, weight_kg: null, blood_type: ''
});

const bookForm = ref({
  patient_id: null, doctor_id: '', date: '', start_time: '', is_walkin: false
});

// ── Fetch Queue ────────────────────────────────────────────────────────────
const fetchQueue = async () => {
  loadingQueue.value = true;
  try {
    const res   = await axios.get(`${BASE}/api/v1/receptionist/queue/${selectedDate.value}`);
    queue.value = res.data.queue;
  } catch {
    messageStore.setFlashMessage("Failed to load queue.");
  } finally {
    loadingQueue.value = false;
  }
};

// ── Fetch Bookings ─────────────────────────────────────────────────────────
const fetchBookings = async () => {
  loadingBookings.value = true;
  try {
    const params           = bookingsSearch.value ? `?patient=${bookingsSearch.value}` : '';
    const res              = await axios.get(`${BASE}/api/v1/receptionist/bookings${params}`);
    upcomingBookings.value = res.data.bookings;
  } catch {
    messageStore.setFlashMessage("Failed to load bookings.");
  } finally {
    loadingBookings.value = false;
  }
};

// ── Fetch History ──────────────────────────────────────────────────────────
const fetchHistory = async () => {
  loadingHistory.value = true;
  try {
    const params             = historySearch.value ? `?patient=${historySearch.value}` : '';
    const res                = await axios.get(`${BASE}/api/v1/receptionist/history${params}`);
    appointmentHistory.value = res.data.history;
  } catch {
    messageStore.setFlashMessage("Failed to load history.");
  } finally {
    loadingHistory.value = false;
  }
};

// ── Fetch Doctors + Patients ───────────────────────────────────────────────
const fetchDoctors = async () => {
  try {
    const res     = await axios.get(`${BASE}/api/v1/receptionist/doctors`);
    doctors.value = res.data.doctors;
  } catch { /* silent */ }
};

const fetchPatients = async () => {
  try {
    const res      = await axios.get(`${BASE}/api/v1/receptionist/patients`);
    patients.value = res.data.patients;
  } catch { /* silent */ }
};

// ── Patient Search ─────────────────────────────────────────────────────────
const filterPatients = () => {
  const q = patientSearch.value.toLowerCase();
  filteredPatients.value = patients.value.filter(p =>
    p.name.toLowerCase().includes(q) || p.service_id.toLowerCase().includes(q)
  ).slice(0, 6);
};

const selectPatient = (p) => {
  bookForm.value.patient_id = p.id;
  patientSearch.value       = `${p.name} (${p.service_id})`;
  filteredPatients.value    = [];
};

const clearPatient = () => {
  bookForm.value.patient_id = null;
  patientSearch.value       = '';
  filteredPatients.value    = [];
};

// ── Slots ──────────────────────────────────────────────────────────────────
const fetchSlots = async () => {
  if (!bookForm.value.doctor_id || !bookForm.value.date) return;
  loadingSlots.value        = true;
  slots.value               = [];
  bookForm.value.start_time = '';
  try {
    const res   = await axios.get(`${BASE}/api/v1/receptionist/slots/${bookForm.value.doctor_id}/${bookForm.value.date}`);
    slots.value = res.data.slots;
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load slots.");
  } finally {
    loadingSlots.value = false;
  }
};

const clearSlots = () => {
  slots.value               = [];
  bookForm.value.start_time = '';
  if (bookForm.value.date) fetchSlots();
};

// ── Register ───────────────────────────────────────────────────────────────
const openRegister = () => {
  regForm.value      = { name: '', email: '', password: '', contact_info: '', age: null, height_cm: null, weight_kg: null, blood_type: '' };
  showRegister.value = true;
};

const handleRegister = async () => {
  isSubmitting.value = true;
  try {
    const res = await axios.post(`${BASE}/api/v1/receptionist/register-patient`, regForm.value);
    messageStore.setFlashMessage(`Patient registered! Service ID: ${res.data.service_id}`);
    showRegister.value = false;
    fetchPatients();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Registration failed.");
  } finally {
    isSubmitting.value = false;
  }
};

// ── Book Appointment ───────────────────────────────────────────────────────
const openBooking = () => {
  bookForm.value      = { patient_id: null, doctor_id: '', date: '', start_time: '', is_walkin: false };
  patientSearch.value = '';
  slots.value         = [];
  showBooking.value   = true;
};

const handleBooking = async () => {
  isSubmitting.value = true;
  try {
    await axios.post(`${BASE}/api/v1/receptionist/book-appointment`, bookForm.value);
    messageStore.setFlashMessage("Appointment booked successfully!");
    showBooking.value = false;
    fetchQueue();
    fetchBookings();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Booking failed.");
  } finally {
    isSubmitting.value = false;
  }
};

// ── Cancel Appointment ─────────────────────────────────────────────────────
const cancelAppointment = async (entry) => {
  if (!confirm(`Cancel appointment for ${entry.patient_name} on ${entry.date} at ${entry.start_time}?\nThe slot will become available again.`)) return;
  try {
    await axios.patch(`${BASE}/api/v1/receptionist/appointment/${entry.appointment_id}/cancel`);
    messageStore.setFlashMessage("Appointment cancelled — slot is now available.");
    fetchQueue();
    fetchBookings();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to cancel.");
  }
};

// ── Toggle Payment ─────────────────────────────────────────────────────────
const togglePayment = async (entry) => {
  const action = entry.payment_status === 'paid' ? 'revert to Pending' : 'mark as Paid';
  if (!confirm(`${action} for ${entry.patient_name}?`)) return;
  try {
    const res            = await axios.patch(`${BASE}/api/v1/receptionist/invoice/${entry.invoice_id}/toggle-payment`);
    entry.payment_status = res.data.status;
    messageStore.setFlashMessage(`Payment status updated to: ${res.data.status}`);
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to update payment.");
  }
};

// ── Watchers ───────────────────────────────────────────────────────────────
watch(selectedDate, fetchQueue);
watch(activeTab, (tab) => {
  if (tab === 'bookings') fetchBookings();
  if (tab === 'history')  fetchHistory();
});

onMounted(() => {
  fetchQueue();
  fetchDoctors();
  fetchPatients();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');

.dashboard { font-family: 'DM Sans', sans-serif; background: #f0f5f9; min-height: 100vh; padding: 2rem 2.5rem; color: #1a2535; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; padding-bottom: 1.25rem; border-bottom: 1px solid #dde6f0; }
.header h1 { font-size: 1.6rem; font-weight: 700; margin: 0; }
.eyebrow { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #94a3b8; margin: 0 0 0.3rem; }
.accent { color: #0a7ea4; }
.header-actions { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }

/* Tab buttons */
.tab-btn { background: #fff; border: 1px solid #dde6f0; color: #64748b; padding: 0.55rem 1rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.tab-btn.active { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.tab-btn:hover:not(.active) { border-color: #94a3b8; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.stat-card label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.3rem; }
.value { font-size: 1.9rem; font-weight: 700; line-height: 1; }
.value.blue   { color: #2563eb; }
.value.yellow { color: #d97706; }
.value.teal   { color: #0a7ea4; }
.value.green  { color: #059669; }
.value.red    { color: #e11d48; }

/* Section */
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.section-header h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin: 0; }
.badge { background: #e2e8f0; color: #64748b; font-size: 0.68rem; font-family: 'IBM Plex Mono', monospace; padding: 0.1rem 0.5rem; border-radius: 20px; }
.date-input-sm { background: #fff; border: 1px solid #dde6f0; color: #1a2535; padding: 0.4rem 0.7rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.78rem; }

/* Search */
.search-row { margin-bottom: 0.75rem; }
.search-input { width: 100%; background: #fff; border: 1px solid #dde6f0; color: #1a2535; padding: 0.7rem 1rem; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; box-sizing: border-box; }
.search-input:focus { outline: none; border-color: #0a7ea4; }

/* Table */
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #dde6f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.table th { text-align: left; padding: 0.7rem 1rem; background: #f8fafc; color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.table td { padding: 0.8rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.84rem; vertical-align: middle; }
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }
.row-active { background: #eff6ff !important; }
.mono  { font-family: 'IBM Plex Mono', monospace; }
.bold  { font-weight: 600; }
.muted { color: #94a3b8; }
.sm    { font-size: 0.76rem; }

/* Tags */
.status-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; text-transform: capitalize; }
.status-tag.waiting    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.status-tag.in-session { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.status-tag.completed  { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.status-tag.cancelled  { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.pay-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; text-transform: capitalize; white-space: nowrap; }
.pay-tag.pending    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.pay-tag.paid       { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.pay-tag.no_invoice { background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; }
.stage-tag { font-size: 0.72rem; color: #0a7ea4; background: #eff9fc; border: 1px solid #bae6fd; padding: 0.18rem 0.5rem; border-radius: 4px; }
.walkin-tag { font-size: 0.72rem; color: #7c3aed; background: #f5f3ff; border: 1px solid #ddd6fe; padding: 0.18rem 0.5rem; border-radius: 4px; }
.in-session-note { font-size: 0.72rem; color: #2563eb; font-weight: 600; }

/* Payment toggle */
.pay-toggle-row { display: flex; align-items: center; gap: 0.5rem; }

/* Buttons */
.add-btn  { background: #0a7ea4; color: #fff; border: none; padding: 0.65rem 1.2rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.84rem; cursor: pointer; transition: opacity 0.15s; }
.add-btn:hover { opacity: 0.88; }
.add-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.book-btn { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; padding: 0.65rem 1.2rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.84rem; cursor: pointer; transition: all 0.15s; }
.book-btn:hover { background: #059669; color: #fff; }
.cancel-btn { background: transparent; color: #64748b; border: 1px solid #e2e8f0; padding: 0.65rem 1.2rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.cancel-btn:hover { border-color: #94a3b8; }
.cancel-appt-btn { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; padding: 0.28rem 0.7rem; border-radius: 5px; font-size: 0.73rem; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.cancel-appt-btn:hover { background: #e11d48; color: #fff; }

/* Toggle */
.toggle { width: 44px; height: 24px; background: #e2e8f0; border-radius: 12px; cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle.on { background: #059669; }
.toggle-knob { width: 18px; height: 18px; background: #fff; border-radius: 50%; position: absolute; top: 3px; left: 3px; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.toggle.on .toggle-knob { left: 23px; }
.toggle-row { flex-direction: row !important; align-items: center; gap: 1rem; }

/* Empty */
.empty    { padding: 2rem; text-align: center; color: #94a3b8; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.84rem; }
.empty-sm { padding: 0.75rem; text-align: center; color: #94a3b8; font-size: 0.8rem; }

/* Modal */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal { background: #fff; border-top: 3px solid #0a7ea4; border-radius: 12px; width: 580px; max-height: 90vh; overflow-y: auto; padding: 1.75rem; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
.modal-head h2 { font-size: 1.05rem; font-weight: 700; margin: 0; }
.close { background: none; border: none; font-size: 1.4rem; color: #94a3b8; cursor: pointer; }

/* Form */
.fields { display: flex; flex-direction: column; gap: 1rem; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.row4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; position: relative; }
.field label { font-size: 0.67rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
.field input, .field select { background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.65rem 0.85rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; transition: border-color 0.15s; }
.field input:focus, .field select:focus { outline: none; border-color: #0a7ea4; background: #fff; }
.field input::placeholder { color: #cbd5e1; }
.modal-foot { display: flex; justify-content: flex-end; gap: 0.6rem; margin-top: 1.25rem; padding-top: 1.1rem; border-top: 1px solid #f1f5f9; }

/* Dropdown */
.dropdown { position: absolute; top: 100%; background: #fff; border: 1px solid #dde6f0; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); z-index: 100; width: 100%; max-height: 200px; overflow-y: auto; margin-top: 0.25rem; }
.dropdown-item { display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 1rem; cursor: pointer; font-size: 0.84rem; }
.dropdown-item:hover { background: #f0f5f9; }
.selected-tag { display: flex; align-items: center; gap: 0.5rem; background: #eff9fc; border: 1px solid #bae6fd; color: #0a7ea4; padding: 0.4rem 0.75rem; border-radius: 6px; font-size: 0.82rem; font-weight: 600; margin-top: 0.3rem; }
.clear { background: none; border: none; color: #0a7ea4; font-size: 1rem; cursor: pointer; line-height: 1; }

/* Slots */
.slots-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.slot-btn { padding: 0.4rem 0.8rem; border-radius: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 500; border: 1px solid #bae6fd; background: #eff9fc; color: #0a7ea4; cursor: pointer; transition: all 0.15s; }
.slot-btn:hover:not(.taken) { background: #0a7ea4; color: #fff; }
.slot-btn.selected { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.slot-btn.taken { background: #f1f5f9; color: #cbd5e1; border-color: #e2e8f0; cursor: not-allowed; text-decoration: line-through; }
</style>
