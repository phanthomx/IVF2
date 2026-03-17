<template>
  <div class="dashboard">

    <!-- Header -->
    <header class="header">
      <div>
        <p class="eyebrow">Patient Portal</p>
        <h1>Welcome, <span class="accent">{{ profile.name?.split(' ')[0] }}</span></h1>
        <p class="service-id mono muted" v-if="profile.service_id">{{ profile.service_id }}</p>
      </div>
      <div class="header-actions">
        <button @click="activeTab = 'overview'"  :class="['tab-btn', activeTab === 'overview'  ? 'active' : '']">Overview</button>
        <button @click="activeTab = 'history'"   :class="['tab-btn', activeTab === 'history'   ? 'active' : '']">Visit History</button>
        <button @click="activeTab = 'invoices'"  :class="['tab-btn', activeTab === 'invoices'  ? 'active' : '']">Invoices</button>
        <button @click="activeTab = 'book'"      :class="['tab-btn', activeTab === 'book'      ? 'active' : '']">Book Appointment</button>
      </div>
    </header>

    <!-- ── OVERVIEW TAB ── -->
    <div v-if="activeTab === 'overview'">
      <div class="overview-grid">

        <!-- Profile card -->
        <div class="card profile-card">
          <div class="avatar">{{ profile.name?.charAt(0) }}</div>
          <div class="profile-info">
            <div class="patient-name">{{ profile.name }}</div>
            <div class="mono muted sm">{{ profile.email }}</div>
          </div>
          <div class="vitals-grid">
            <div class="vital-item"><label>Age</label><span>{{ profile.age || '—' }}</span></div>
            <div class="vital-item"><label>Height</label><span>{{ profile.height_cm ? profile.height_cm + ' cm' : '—' }}</span></div>
            <div class="vital-item"><label>Weight</label><span>{{ profile.weight_kg ? profile.weight_kg + ' kg' : '—' }}</span></div>
            <div class="vital-item"><label>Blood</label><span>{{ profile.blood_type || '—' }}</span></div>
          </div>
        </div>

        <!-- IVF Stage tracker -->
        <div class="card stage-card">
          <h3>IVF Cycle Progress</h3>
          <div class="stage-tracker">
            <div v-for="(stage, idx) in profile.stages" :key="stage" :class="['stage-step', getStageClass(idx)]">
              <div class="step-indicator">
                <div class="step-dot">
                  <span v-if="idx < profile.stage_index">✓</span>
                  <span v-else-if="idx === profile.stage_index">●</span>
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <div v-if="idx < profile.stages?.length - 1" :class="['step-line', idx < profile.stage_index ? 'done' : '']"></div>
              </div>
              <div class="step-label">
                <span :class="idx === profile.stage_index ? 'active-label' : ''">{{ stage }}</span>
                <span v-if="idx === profile.stage_index" class="current-badge">Current</span>
                <span v-else-if="idx < profile.stage_index" class="done-badge">Done</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Upcoming appointments -->
      <section class="section">
        <div class="section-header">
          <h2>Upcoming Appointments</h2>
          <span class="badge">{{ upcoming.length }}</span>
        </div>
        <div v-if="upcoming.length === 0" class="empty">
          No upcoming appointments.
          <button @click="activeTab = 'book'" class="link-btn">Book one →</button>
        </div>
        <div v-else class="upcoming-grid">
          <div v-for="appt in upcoming" :key="appt.appointment_id" class="upcoming-card">
            <div class="upcoming-date">
              <div class="date-day">{{ formatDay(appt.date) }}</div>
              <div class="date-month">{{ formatMonth(appt.date) }}</div>
            </div>
            <div class="upcoming-info">
              <div class="bold">Dr. {{ appt.doctor_name }}</div>
              <div class="sm muted">{{ appt.specialization }}</div>
              <div class="sm mono">{{ appt.start_time }} – {{ appt.end_time }}</div>
              <div class="sm muted mono">{{ appt.date }}</div>
            </div>
            <div class="upcoming-right">
              <span :class="['status-tag', appt.status]">{{ appt.status }}</span>
              <span class="stage-tag sm">{{ appt.stage }}</span>
              <button
                v-if="appt.can_cancel"
                @click="cancelAppointment(appt)"
                class="cancel-appt-btn"
              >
                Cancel
              </button>
              <span v-else-if="appt.status === 'in-session'" class="in-session-note">In Progress</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- ── HISTORY TAB ── -->
    <section v-if="activeTab === 'history'" class="section">
      <div class="section-header">
        <h2>Visit History</h2>
        <span class="badge">{{ history.length }}</span>
      </div>
      <div v-if="loadingHistory" class="empty">Loading history...</div>
      <div v-else-if="history.length === 0" class="empty">No visits recorded yet.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Doctor</th>
            <th>Stage</th>
            <th>Status</th>
            <th>Prescription</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="visit in history" :key="visit.appointment_id">
            <td class="mono sm bold">{{ visit.date }}</td>
            <td class="mono sm muted">{{ visit.start_time }}</td>
            <td>
              <div class="bold">Dr. {{ visit.doctor_name }}</div>
              <div class="sm muted">{{ visit.specialization }}</div>
            </td>
            <td><span class="stage-tag">{{ visit.stage || '—' }}</span></td>
            <td><span :class="['status-tag', visit.status]">{{ visit.status }}</span></td>
            <td>
              <button
                v-if="visit.has_prescription"
                @click="viewPrescription(visit.appointment_id)"
                class="rx-btn"
              >
                View Rx
              </button>
              <span v-else class="muted sm">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── INVOICES TAB ── -->
    <section v-if="activeTab === 'invoices'" class="section">
      <div class="invoice-summary">
        <div class="inv-stat">
          <label>Total Billed</label>
          <div class="inv-value blue">₹{{ invoiceSummary.total_billed?.toLocaleString() || 0 }}</div>
        </div>
        <div class="inv-stat">
          <label>Paid</label>
          <div class="inv-value green">₹{{ invoiceSummary.paid_total?.toLocaleString() || 0 }}</div>
        </div>
        <div class="inv-stat">
          <label>Pending</label>
          <div class="inv-value yellow">₹{{ invoiceSummary.pending_total?.toLocaleString() || 0 }}</div>
        </div>
      </div>

      <div class="section-header" style="margin-top:1.5rem">
        <h2>Invoice History</h2>
        <div style="display:flex;align-items:center;gap:0.5rem">
          <span class="badge">{{ invoices.length }}</span>
          <button v-if="invoices.length > 0" @click="downloadAllInvoices" class="dl-all-btn">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download All
          </button>
        </div>
      </div>

      <div v-if="loadingInvoices" class="empty">Loading invoices...</div>
      <div v-else-if="invoices.length === 0" class="empty">No invoices found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Visit Date</th>
            <th>Service Code</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Paid Via</th>
            <th>Date Paid</th>
            <th>Receipt</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in invoices" :key="inv.invoice_id">
            <td class="mono sm">{{ inv.visit_date || inv.date_generated }}</td>
            <td><span class="code-tag">{{ inv.service_code }}</span></td>
            <td class="bold">₹{{ inv.amount?.toLocaleString() }}</td>
            <td><span :class="['pay-tag', inv.status]">{{ inv.status }}</span></td>
            <td class="sm muted">{{ inv.payment_source ? inv.payment_source.replace('_', ' ') : '—' }}</td>
            <td class="mono sm muted">{{ inv.date_paid || '—' }}</td>
            <td>
              <button @click="downloadInvoice(inv)" class="dl-btn">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                PDF
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="pay-note">💬 To make a payment, please visit the front desk or contact your clinic.</p>
    </section>

    <!-- ── BOOK APPOINTMENT TAB ── -->
    <section v-if="activeTab === 'book'" class="section">
      <div class="section-header">
        <h2>Book an Appointment</h2>
      </div>
      <p class="hint">Appointments can be booked up to 7 days in advance.</p>

      <div class="book-layout">
        <!-- Step 1: Pick doctor -->
        <div class="book-step">
          <div class="step-num">1</div>
          <div class="step-body">
            <h3>Select Doctor</h3>
            <div class="doctor-grid">
              <div
                v-for="doc in doctors"
                :key="doc.id"
                :class="['doctor-card', bookForm.doctor_id === doc.id ? 'selected' : '']"
                @click="selectDoctor(doc)"
              >
                <div class="doc-avatar">{{ doc.name.charAt(0) }}</div>
                <div>
                  <div class="bold sm">Dr. {{ doc.name }}</div>
                  <div class="muted sm">{{ doc.specialization }}</div>
                  <div class="avail-days">
                    <span v-for="d in doc.available_days" :key="d" class="day-chip">{{ dayNames[d] }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Pick date -->
        <div class="book-step" v-if="bookForm.doctor_id">
          <div class="step-num">2</div>
          <div class="step-body">
            <h3>Select Date</h3>
            <input type="date" v-model="bookForm.date" :min="today" :max="maxDate" @change="fetchSlots" class="date-input" />
          </div>
        </div>

        <!-- Step 3: Pick slot -->
        <div class="book-step" v-if="bookForm.date && bookForm.doctor_id">
          <div class="step-num">3</div>
          <div class="step-body">
            <h3>Select Time Slot</h3>
            <div v-if="loadingSlots" class="empty-sm">Loading slots...</div>
            <div v-else-if="slots.length === 0" class="empty-sm">No availability on this date.</div>
            <div v-else class="slots-grid">
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
        </div>

        <!-- Step 4: Confirm -->
        <div class="book-step" v-if="bookForm.start_time">
          <div class="step-num">4</div>
          <div class="step-body">
            <h3>Confirm Booking</h3>
            <div class="confirm-box">
              <div class="confirm-row"><span class="muted">Doctor</span><span class="bold">Dr. {{ selectedDoctorName }}</span></div>
              <div class="confirm-row"><span class="muted">Date</span><span class="bold mono">{{ bookForm.date }}</span></div>
              <div class="confirm-row"><span class="muted">Time</span><span class="bold mono">{{ bookForm.start_time }}</span></div>
              <div class="confirm-row"><span class="muted">Stage</span><span class="stage-tag">{{ profile.current_cycle_stage }}</span></div>
            </div>
            <button @click="handleBooking" class="add-btn" :disabled="isSubmitting">
              {{ isSubmitting ? 'Booking...' : 'Confirm Appointment' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Prescription Modal ── -->
    <div v-if="showRx" class="overlay" @click.self="closeRx">
      <div class="modal rx-modal">
        <div class="modal-head">
          <div>
            <h2>Prescription</h2>
            <span class="mono muted sm" v-if="rxData">{{ rxData.visit_date }} · Dr. {{ rxData.doctor_name }}</span>
          </div>
          <div style="display:flex;align-items:center;gap:0.6rem">
            <button v-if="rxData" @click="downloadPrescription" class="dl-btn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download PDF
            </button>
            <button @click="closeRx" class="close">×</button>
          </div>
        </div>
        <div v-if="loadingRx" class="empty">Loading prescription...</div>
        <div v-else-if="rxData" class="rx-body">
          <div class="rx-meta">
            <div class="rx-meta-item">
              <label>Visit Date</label>
              <span class="mono sm">{{ rxData.visit_date }}</span>
            </div>
            <div class="rx-meta-item">
              <label>Doctor</label>
              <span>Dr. {{ rxData.doctor_name }}</span>
            </div>
            <div class="rx-meta-item">
              <label>Stage</label>
              <span class="stage-tag">{{ rxData.stage }}</span>
            </div>
          </div>
          <div class="rx-content">
            <label>Prescription / Protocol</label>
            <pre class="rx-text">{{ rxData.content }}</pre>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';

const authStore    = useAuthStore();
const messageStore = useMessageStore();
const BASE         = authStore.getBackendServerURL();

// ── State ──────────────────────────────────────────────────────────────────
const activeTab      = ref('overview');
const profile        = ref({});
const upcoming       = ref([]);
const history        = ref([]);
const invoices       = ref([]);
const invoiceSummary = ref({});
const doctors        = ref([]);
const slots          = ref([]);
const loadingHistory  = ref(false);
const loadingInvoices = ref(false);
const loadingSlots    = ref(false);
const isSubmitting    = ref(false);

const showRx    = ref(false);
const rxData    = ref(null);
const loadingRx = ref(false);

// ✅ IST-aware today and maxDate
const getISTDateString = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
};

const today   = getISTDateString(0);
const maxDate = computed(() => getISTDateString(7));

const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const bookForm = ref({ doctor_id: null, date: '', start_time: '' });

const selectedDoctorName = computed(() => {
  const d = doctors.value.find(d => d.id === bookForm.value.doctor_id);
  return d ? d.name : '';
});

// ── Stage helpers ──────────────────────────────────────────────────────────
const getStageClass = (idx) => {
  if (idx < profile.value.stage_index)   return 'completed';
  if (idx === profile.value.stage_index) return 'active';
  return 'pending';
};

// ── Date helpers (IST-aware) ───────────────────────────────────────────────
const formatDay = (dateStr) => {
  const [, , day] = dateStr.split('-');
  return parseInt(day);
};

const formatMonth = (dateStr) => {
  const [_year, month] = dateStr.split('-');
  return new Date(_year, month - 1, 1).toLocaleString('default', { month: 'short' });
};

// ── Fetch Profile ──────────────────────────────────────────────────────────
const fetchProfile = async () => {
  try {
    const res      = await axios.get(`${BASE}/api/v1/patient/profile`);
    profile.value  = res.data.profile;
    upcoming.value = res.data.upcoming;
  } catch {
    messageStore.setFlashMessage("Failed to load profile.");
  }
};

// ── Fetch History ──────────────────────────────────────────────────────────
const fetchHistory = async () => {
  loadingHistory.value = true;
  try {
    const res     = await axios.get(`${BASE}/api/v1/patient/history`);
    history.value = res.data.history;
  } catch {
    messageStore.setFlashMessage("Failed to load history.");
  } finally {
    loadingHistory.value = false;
  }
};

// ── Fetch Invoices ─────────────────────────────────────────────────────────
const fetchInvoices = async () => {
  loadingInvoices.value = true;
  try {
    const res        = await axios.get(`${BASE}/api/v1/patient/invoices`);
    invoices.value   = res.data.invoices;
    invoiceSummary.value = {
      total_billed:  res.data.total_billed,
      paid_total:    res.data.paid_total,
      pending_total: res.data.pending_total
    };
  } catch {
    messageStore.setFlashMessage("Failed to load invoices.");
  } finally {
    loadingInvoices.value = false;
  }
};

// ── Fetch Doctors ──────────────────────────────────────────────────────────
const fetchDoctors = async () => {
  try {
    const res     = await axios.get(`${BASE}/api/v1/patient/doctors`);
    doctors.value = res.data.doctors;
  } catch { /* silent */ }
};

// ── Slots ──────────────────────────────────────────────────────────────────
const fetchSlots = async () => {
  if (!bookForm.value.doctor_id || !bookForm.value.date) return;
  loadingSlots.value        = true;
  slots.value               = [];
  bookForm.value.start_time = '';
  try {
    const res   = await axios.get(`${BASE}/api/v1/patient/slots/${bookForm.value.doctor_id}/${bookForm.value.date}`);
    slots.value = res.data.slots;
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load slots.");
  } finally {
    loadingSlots.value = false;
  }
};

const selectDoctor = (doc) => {
  bookForm.value.doctor_id  = doc.id;
  bookForm.value.date       = '';
  bookForm.value.start_time = '';
  slots.value               = [];
};

// ── Book Appointment ───────────────────────────────────────────────────────
const handleBooking = async () => {
  isSubmitting.value = true;
  try {
    await axios.post(`${BASE}/api/v1/patient/book-appointment`, bookForm.value);
    messageStore.setFlashMessage("Appointment booked successfully!");
    bookForm.value  = { doctor_id: null, date: '', start_time: '' };
    slots.value     = [];
    activeTab.value = 'overview';
    fetchProfile();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Booking failed.");
  } finally {
    isSubmitting.value = false;
  }
};

// ── Cancel Appointment ─────────────────────────────────────────────────────
const cancelAppointment = async (appt) => {
  if (!confirm(`Cancel appointment with Dr. ${appt.doctor_name} on ${appt.date} at ${appt.start_time}?\nThe slot will become available again.`)) return;
  try {
    await axios.patch(`${BASE}/api/v1/patient/appointment/${appt.appointment_id}/cancel`);
    messageStore.setFlashMessage("Appointment cancelled successfully.");
    fetchProfile();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to cancel.");
  }
};

// ── View Prescription ──────────────────────────────────────────────────────
const viewPrescription = async (appointmentId) => {
  showRx.value    = true;
  rxData.value    = null;
  loadingRx.value = true;
  try {
    const res    = await axios.get(`${BASE}/api/v1/patient/prescription/${appointmentId}`);
    rxData.value = res.data.prescription;
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Prescription not available.");
    showRx.value = false;
  } finally {
    loadingRx.value = false;
  }
};

// ── Download Invoice / Receipt ─────────────────────────────────────────────
const buildReceiptHTML = (inv) => {
  const statusColor  = inv.status === 'paid' ? '#059669' : '#d97706';
  const statusBg     = inv.status === 'paid' ? '#f0fdf4' : '#fffbeb';
  const statusBorder = inv.status === 'paid' ? '#a7f3d0' : '#fde68a';

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Receipt – ${inv.service_code}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'DM Sans',sans-serif; background:#fff; color:#1a2535; padding:48px; max-width:680px; margin:auto; }
    .clinic-header { display:flex; justify-content:space-between; align-items:flex-start; padding-bottom:24px; border-bottom:2px solid #0a7ea4; margin-bottom:28px; }
    .clinic-name { font-size:22px; font-weight:700; color:#0a7ea4; }
    .clinic-sub { font-size:11px; color:#94a3b8; margin-top:3px; letter-spacing:0.08em; text-transform:uppercase; }
    .receipt-label { font-size:11px; color:#94a3b8; letter-spacing:0.1em; text-transform:uppercase; }
    .receipt-num { font-size:18px; font-weight:700; color:#1a2535; font-family:monospace; }
    .section-title { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; margin-bottom:12px; }
    .info-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:20px; margin-bottom:24px; }
    .info-item label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#94a3b8; display:block; margin-bottom:4px; }
    .info-item span { font-size:14px; font-weight:600; }
    .amount-box { background:#0a7ea4; border-radius:10px; padding:24px; text-align:center; margin-bottom:24px; }
    .amount-label { font-size:11px; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:0.1em; }
    .amount-value { font-size:40px; font-weight:700; color:#fff; margin-top:4px; }
    .status-pill { display:inline-block; background:${statusBg}; color:${statusColor}; border:1px solid ${statusBorder}; padding:4px 14px; border-radius:20px; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; }
    .footer { text-align:center; font-size:11px; color:#94a3b8; border-top:1px solid #e2e8f0; padding-top:20px; margin-top:8px; line-height:1.6; }
    @media print { body { padding:32px; } }
  </style>
</head>
<body>
  <div class="clinic-header">
    <div>
      <div class="clinic-name">Ivy Clinic</div>
      <div class="clinic-sub">IVF &amp; Reproductive Medicine</div>
    </div>
    <div style="text-align:right">
      <div class="receipt-label">Invoice / Receipt</div>
      <div class="receipt-num">#INV-${String(inv.invoice_id).padStart(5,'0')}</div>
    </div>
  </div>

  <div class="section-title">Service Details</div>
  <div class="info-grid">
    <div class="info-item"><label>Patient</label><span>${profile.value.name || '—'}</span></div>
    <div class="info-item"><label>Service ID</label><span style="font-family:monospace">${profile.value.service_id || '—'}</span></div>
    <div class="info-item"><label>Visit Date</label><span style="font-family:monospace">${inv.visit_date || inv.date_generated}</span></div>
    <div class="info-item"><label>Service Code</label><span style="font-family:monospace;color:#7c3aed">${inv.service_code}</span></div>
    <div class="info-item"><label>Payment Method</label><span>${inv.payment_source ? inv.payment_source.replace('_',' ') : 'Pending'}</span></div>
    <div class="info-item"><label>Date Paid</label><span style="font-family:monospace">${inv.date_paid || '—'}</span></div>
  </div>

  <div class="amount-box">
    <div class="amount-label">Amount</div>
    <div class="amount-value">₹${inv.amount?.toLocaleString('en-IN')}</div>
    <div style="margin-top:12px"><span class="status-pill">${inv.status}</span></div>
  </div>

  <div class="footer">
    Generated on ${new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'long', year:'numeric' })} &nbsp;·&nbsp;
    Ivy Platform &nbsp;·&nbsp; This is a computer-generated receipt and does not require a signature.
  </div>
</body>
</html>`;
};

const downloadInvoice = (inv) => {
  const html = buildReceiptHTML(inv);
  const win  = window.open('', '_blank');
  win.document.write(html);
  win.document.close();
  // Give fonts a moment to load, then trigger print dialog
  setTimeout(() => { win.print(); }, 600);
};

const downloadAllInvoices = () => {
  // Build one combined page with page-breaks between each receipt
  const pages = invoices.value.map(inv => buildReceiptHTML(inv)
    .replace('</body></html>', '<div style="page-break-after:always"></div></body></html>')
  ).join('\n');
  const win = window.open('', '_blank');
  win.document.write(pages);
  win.document.close();
  setTimeout(() => { win.print(); }, 800);
};

const closeRx = () => {
  showRx.value = false;
  rxData.value = null;
};

// ── Download Prescription ──────────────────────────────────────────────────
const downloadPrescription = () => {
  if (!rxData.value) return;
  const rx = rxData.value;

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Prescription – ${rx.visit_date}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'DM Sans',sans-serif; background:#fff; color:#1a2535; padding:48px; max-width:680px; margin:auto; }

    .header { display:flex; justify-content:space-between; align-items:flex-start; padding-bottom:20px; border-bottom:2px solid #7c3aed; margin-bottom:28px; }
    .clinic-name { font-size:22px; font-weight:700; color:#7c3aed; }
    .clinic-sub  { font-size:11px; color:#94a3b8; margin-top:3px; letter-spacing:0.08em; text-transform:uppercase; }
    .rx-label    { font-size:11px; color:#94a3b8; letter-spacing:0.1em; text-transform:uppercase; text-align:right; }
    .rx-symbol   { font-size:36px; font-weight:700; color:#7c3aed; line-height:1; }

    .meta-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:18px; margin-bottom:24px; }
    .meta-item label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#94a3b8; display:block; margin-bottom:3px; }
    .meta-item span  { font-size:13px; font-weight:600; }

    .rx-box { background:#faf5ff; border:1px solid #ddd6fe; border-radius:10px; padding:24px; margin-bottom:28px; }
    .rx-box-label { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#7c3aed; margin-bottom:14px; display:flex; align-items:center; gap:6px; }
    .rx-content { font-size:14px; line-height:1.85; white-space:pre-wrap; color:#1a2535; }

    .stage-pill { display:inline-block; background:#eff9fc; color:#0a7ea4; border:1px solid #bae6fd; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:600; }

    .sig-row { display:flex; justify-content:flex-end; margin-top:32px; padding-top:20px; border-top:1px solid #e2e8f0; }
    .sig-box  { text-align:center; }
    .sig-line { width:180px; border-bottom:1px solid #1a2535; margin-bottom:6px; height:40px; }
    .sig-name { font-size:12px; font-weight:600; }
    .sig-sub  { font-size:10px; color:#94a3b8; }

    .footer { text-align:center; font-size:11px; color:#94a3b8; margin-top:24px; line-height:1.6; }
    @media print { body { padding:32px; } }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <div class="clinic-name">Ivy Clinic</div>
      <div class="clinic-sub">IVF &amp; Reproductive Medicine</div>
    </div>
    <div>
      <div class="rx-label">Prescription</div>
      <div class="rx-symbol">℞</div>
    </div>
  </div>

  <div class="meta-grid">
    <div class="meta-item">
      <label>Patient</label>
      <span>${profile.value.name || '—'}</span>
    </div>
    <div class="meta-item">
      <label>Service ID</label>
      <span style="font-family:monospace">${profile.value.service_id || '—'}</span>
    </div>
    <div class="meta-item">
      <label>Visit Date</label>
      <span style="font-family:monospace">${rx.visit_date}</span>
    </div>
    <div class="meta-item">
      <label>Prescribing Doctor</label>
      <span>Dr. ${rx.doctor_name}</span>
    </div>
    <div class="meta-item">
      <label>IVF Stage</label>
      <span class="stage-pill">${rx.stage || '—'}</span>
    </div>
  </div>

  <div class="rx-box">
    <div class="rx-box-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>
      Medications &amp; Protocol
    </div>
    <div class="rx-content">${rx.content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
  </div>

  <div class="sig-row">
    <div class="sig-box">
      <div class="sig-line"></div>
      <div class="sig-name">Dr. ${rx.doctor_name}</div>
      <div class="sig-sub">Authorised Signature</div>
    </div>
  </div>

  <div class="footer">
    Issued on ${new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'long', year:'numeric' })} &nbsp;·&nbsp;
    Ivy Platform &nbsp;·&nbsp; This is a computer-generated prescription. Valid only when issued by a registered medical practitioner.
  </div>

</body>
</html>`;

  const win = window.open('', '_blank');
  win.document.write(html);
  win.document.close();
  setTimeout(() => { win.print(); }, 600);
};

// ── Tab watch ──────────────────────────────────────────────────────────────
watch(activeTab, (tab) => {
  if (tab === 'history')  fetchHistory();
  if (tab === 'invoices') fetchInvoices();
  if (tab === 'book')     fetchDoctors();
});

// ── Browser Notification Reminder ─────────────────────────────────────────
// Asks for permission once, then checks every 5 min whether any upcoming
// appointment is within the next 55–65 minutes and fires a notification.
let _notifInterval = null;
const _notifiedIds  = new Set();

const requestNotificationPermission = async () => {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'default') {
    await Notification.requestPermission();
  }
};

const checkUpcomingNotifications = () => {
  if (Notification.permission !== 'granted') return;
  if (!upcoming.value.length) return;

  const now      = new Date();
  const windowLo = new Date(now.getTime() + 55 * 60 * 1000);
  const windowHi = new Date(now.getTime() + 65 * 60 * 1000);

  for (const appt of upcoming.value) {
    if (_notifiedIds.has(appt.appointment_id)) continue;

    const apptTime = new Date(`${appt.date}T${appt.start_time}:00`);
    if (apptTime >= windowLo && apptTime <= windowHi) {
      new Notification('⏰ Ivy Clinic — Appointment Reminder', {
        body: `Your appointment with Dr. ${appt.doctor_name} is in 1 hour (${appt.start_time}).`,
        icon: '/favicon.ico',
        tag:  `appt-${appt.appointment_id}`   // prevents duplicate popups
      });
      _notifiedIds.add(appt.appointment_id);
    }
  }
};

onMounted(async () => {
  fetchProfile();
  await requestNotificationPermission();
  // Fire once immediately, then every 5 minutes
  checkUpcomingNotifications();
  _notifInterval = setInterval(checkUpcomingNotifications, 5 * 60 * 1000);
});

onUnmounted(() => {
  if (_notifInterval) clearInterval(_notifInterval);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');

.dashboard { font-family: 'DM Sans', sans-serif; background: #f0f5f9; min-height: 100vh; padding: 2rem 2.5rem; color: #1a2535; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; padding-bottom: 1.25rem; border-bottom: 1px solid #dde6f0; }
.header h1 { font-size: 1.6rem; font-weight: 700; margin: 0; }
.eyebrow { font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #94a3b8; margin: 0 0 0.3rem; }
.service-id { font-size: 0.78rem; margin: 0.25rem 0 0; }
.accent { color: #0a7ea4; }
.header-actions { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.tab-btn { background: #fff; border: 1px solid #dde6f0; color: #64748b; padding: 0.55rem 1rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.tab-btn.active { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.tab-btn:hover:not(.active) { border-color: #94a3b8; }

/* Overview grid */
.overview-grid { display: grid; grid-template-columns: 320px 1fr; gap: 1rem; margin-bottom: 2rem; }
.card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* Profile card */
.profile-card { display: flex; flex-direction: column; gap: 1rem; }
.avatar { width: 52px; height: 52px; background: #eff9fc; border: 2px solid #bae6fd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; font-weight: 700; color: #0a7ea4; }
.patient-name { font-size: 1rem; font-weight: 700; color: #1a2535; }
.vitals-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.5rem; }
.vital-item { display: flex; flex-direction: column; gap: 0.15rem; }
.vital-item label { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; }
.vital-item span { font-size: 0.84rem; font-weight: 600; color: #1a2535; }

/* Stage card */
.stage-card h3 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0 0 1rem; }
.stage-tracker { display: flex; align-items: flex-start; overflow-x: auto; padding-bottom: 0.5rem; }
.stage-step { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 80px; }
.step-indicator { display: flex; align-items: center; width: 100%; }
.step-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; border: 2px solid #e2e8f0; background: #fff; color: #94a3b8; z-index: 1; }
.step-line { flex: 1; height: 2px; background: #e2e8f0; }
.step-line.done { background: #059669; }
.stage-step.completed .step-dot { background: #059669; border-color: #059669; color: #fff; }
.stage-step.active .step-dot { background: #0a7ea4; border-color: #0a7ea4; color: #fff; box-shadow: 0 0 0 4px rgba(10,126,164,0.15); }
.step-label { text-align: center; margin-top: 0.5rem; font-size: 0.68rem; color: #94a3b8; line-height: 1.3; }
.stage-step.completed .step-label { color: #059669; }
.stage-step.active .step-label { color: #0a7ea4; font-weight: 700; }
.active-label { font-weight: 700; }
.current-badge { display: block; font-size: 0.6rem; background: #eff9fc; color: #0a7ea4; border: 1px solid #bae6fd; border-radius: 3px; padding: 0.1rem 0.3rem; margin-top: 0.2rem; text-align: center; }
.done-badge { display: block; font-size: 0.6rem; color: #059669; margin-top: 0.2rem; text-align: center; }

/* Upcoming */
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.section-header h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin: 0; }
.badge { background: #e2e8f0; color: #64748b; font-size: 0.68rem; font-family: 'IBM Plex Mono', monospace; padding: 0.1rem 0.5rem; border-radius: 20px; }
.upcoming-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.upcoming-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1rem 1.25rem; display: flex; align-items: center; gap: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.upcoming-date { background: #eff9fc; border: 1px solid #bae6fd; border-radius: 8px; padding: 0.5rem 0.75rem; text-align: center; min-width: 52px; flex-shrink: 0; }
.date-day { font-size: 1.4rem; font-weight: 700; color: #0a7ea4; line-height: 1; }
.date-month { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: #64748b; }
.upcoming-info { flex: 1; display: flex; flex-direction: column; gap: 0.2rem; }
.upcoming-right { display: flex; flex-direction: column; gap: 0.4rem; align-items: flex-end; }
.link-btn { background: none; border: none; color: #0a7ea4; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; font-weight: 600; cursor: pointer; text-decoration: underline; }

/* Cancel + in-session */
.cancel-appt-btn { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; padding: 0.28rem 0.7rem; border-radius: 5px; font-size: 0.73rem; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.cancel-appt-btn:hover { background: #e11d48; color: #fff; }
.in-session-note { font-size: 0.72rem; color: #2563eb; font-weight: 600; }

/* Invoice summary */
.invoice-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.inv-stat { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.inv-stat label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.4rem; }
.inv-value { font-size: 1.8rem; font-weight: 700; }
.inv-value.blue   { color: #2563eb; }
.inv-value.green  { color: #059669; }
.inv-value.yellow { color: #d97706; }
.pay-note { font-size: 0.78rem; color: #94a3b8; margin-top: 1rem; text-align: center; background: #f8fafc; padding: 0.75rem; border-radius: 8px; border: 1px solid #e2e8f0; }

/* Tags */
.status-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; text-transform: capitalize; }
.status-tag.waiting    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.status-tag.in-session { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.status-tag.completed  { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.status-tag.cancelled  { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.pay-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; text-transform: capitalize; }
.pay-tag.pending { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.pay-tag.paid    { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.stage-tag { font-size: 0.72rem; color: #0a7ea4; background: #eff9fc; border: 1px solid #bae6fd; padding: 0.18rem 0.5rem; border-radius: 4px; white-space: nowrap; }
.rx-tag    { font-size: 0.72rem; color: #059669; background: #f0fdf4; border: 1px solid #a7f3d0; padding: 0.18rem 0.5rem; border-radius: 4px; }
.code-tag  { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #7c3aed; background: #f5f3ff; border: 1px solid #ddd6fe; padding: 0.18rem 0.5rem; border-radius: 4px; }

/* Prescription button */
.rx-btn { background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; padding: 0.28rem 0.75rem; border-radius: 5px; font-size: 0.73rem; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.rx-btn:hover { background: #7c3aed; color: #fff; }

/* Table */
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #dde6f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.table th { text-align: left; padding: 0.7rem 1rem; background: #f8fafc; color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.table td { padding: 0.8rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.84rem; vertical-align: middle; }
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }

/* Booking */
.hint { font-size: 0.78rem; color: #94a3b8; margin: -0.25rem 0 1.5rem; }
.book-layout { display: flex; flex-direction: column; gap: 1.5rem; }
.book-step { display: flex; gap: 1rem; align-items: flex-start; }
.step-num { width: 32px; height: 32px; background: #0a7ea4; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.84rem; flex-shrink: 0; margin-top: 0.1rem; }
.step-body { flex: 1; background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.25rem; }
.step-body h3 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0 0 1rem; }
.doctor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; }
.doctor-card { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.9rem; border: 1px solid #dde6f0; border-radius: 8px; cursor: pointer; transition: all 0.15s; }
.doctor-card:hover { border-color: #0a7ea4; background: #f8fdff; }
.doctor-card.selected { border-color: #0a7ea4; background: #eff9fc; box-shadow: 0 0 0 2px rgba(10,126,164,0.15); }
.doc-avatar { width: 36px; height: 36px; background: #eff9fc; border: 1px solid #bae6fd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #0a7ea4; font-size: 0.9rem; flex-shrink: 0; }
.avail-days { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.4rem; }
.day-chip { font-size: 0.6rem; background: #f1f5f9; color: #64748b; padding: 0.1rem 0.35rem; border-radius: 3px; font-family: 'IBM Plex Mono', monospace; }
.date-input { background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.65rem 0.85rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; }
.date-input:focus { outline: none; border-color: #0a7ea4; }
.slots-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.slot-btn { padding: 0.45rem 0.9rem; border-radius: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 500; border: 1px solid #bae6fd; background: #eff9fc; color: #0a7ea4; cursor: pointer; transition: all 0.15s; }
.slot-btn:hover:not(.taken) { background: #0a7ea4; color: #fff; }
.slot-btn.selected { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.slot-btn.taken { background: #f1f5f9; color: #cbd5e1; border-color: #e2e8f0; cursor: not-allowed; text-decoration: line-through; }
.confirm-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.6rem; }
.confirm-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.84rem; }
.add-btn { background: #0a7ea4; color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: opacity 0.15s; }
.add-btn:hover { opacity: 0.88; }
.add-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Modal */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.4); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.modal { background: #fff; border-top: 3px solid #7c3aed; border-radius: 12px; width: 600px; max-width: 95vw; max-height: 90vh; overflow-y: auto; padding: 1.75rem; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }
.modal-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; }
.modal-head h2 { font-size: 1.05rem; font-weight: 700; margin: 0 0 0.2rem; }
.close { background: none; border: none; font-size: 1.4rem; color: #94a3b8; cursor: pointer; line-height: 1; flex-shrink: 0; }

/* Prescription modal */
.rx-modal { border-top-color: #7c3aed; }
.rx-body { display: flex; flex-direction: column; gap: 1.25rem; }
.rx-meta { display: flex; gap: 2rem; flex-wrap: wrap; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; }
.rx-meta-item { display: flex; flex-direction: column; gap: 0.25rem; }
.rx-meta-item label { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; }
.rx-meta-item span { font-size: 0.84rem; font-weight: 500; }
.rx-content { display: flex; flex-direction: column; gap: 0.5rem; }
.rx-content label { font-size: 0.67rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; }
.rx-text { background: #faf5ff; border: 1px solid #ddd6fe; border-radius: 8px; padding: 1rem 1.25rem; font-family: 'DM Sans', sans-serif; font-size: 0.88rem; line-height: 1.7; white-space: pre-wrap; color: #1a2535; margin: 0; }

/* Download buttons */
.dl-btn { display:inline-flex; align-items:center; gap:0.35rem; background:#f0fdf4; color:#059669; border:1px solid #a7f3d0; padding:0.28rem 0.65rem; border-radius:5px; font-size:0.72rem; font-weight:600; cursor:pointer; transition:all 0.15s; white-space:nowrap; font-family:'DM Sans',sans-serif; }
.dl-btn:hover { background:#059669; color:#fff; }
.dl-all-btn { display:inline-flex; align-items:center; gap:0.35rem; background:#0a7ea4; color:#fff; border:none; padding:0.32rem 0.8rem; border-radius:6px; font-size:0.75rem; font-weight:600; cursor:pointer; transition:opacity 0.15s; font-family:'DM Sans',sans-serif; }
.dl-all-btn:hover { opacity:0.88; }

.empty { padding: 2rem; text-align: center; color: #94a3b8; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.84rem; }
.empty-sm { padding: 0.75rem; text-align: center; color: #94a3b8; font-size: 0.8rem; }
.mono  { font-family: 'IBM Plex Mono', monospace; }
.bold  { font-weight: 600; }
.muted { color: #94a3b8; }
.sm    { font-size: 0.76rem; }
</style>