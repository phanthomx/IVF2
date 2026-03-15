<template>
  <div class="dashboard">

    <!-- Header -->
    <header class="header">
      <div>
        <p class="eyebrow">Finance & Billing</p>
        <h1>Accountant <span class="accent">Hub</span></h1>
      </div>
      <div class="header-actions">
        <button @click="setTab('queue')"   :class="['tab-btn', activeTab === 'queue'   ? 'active' : '']">Billing Queue</button>
        <button @click="setTab('ledger')"  :class="['tab-btn', activeTab === 'ledger'  ? 'active' : '']">Invoice Ledger</button>
        <button @click="setTab('reports')" :class="['tab-btn', activeTab === 'reports' ? 'active' : '']">Reports</button>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <label>Total Billed</label>
        <div class="value blue">₹{{ fmt(ledgerSummary.total_billed) }}</div>
        <div class="stat-sub">All time</div>
      </div>
      <div class="stat-card">
        <label>Collected Revenue</label>
        <div class="value green">₹{{ fmt(ledgerSummary.total_revenue) }}</div>
        <div class="stat-sub">Paid invoices</div>
      </div>
      <div class="stat-card">
        <label>Outstanding</label>
        <div class="value yellow">₹{{ fmt(ledgerSummary.total_pending) }}</div>
        <div class="stat-sub">Awaiting payment</div>
      </div>
      <div class="stat-card">
        <label>Pending Action</label>
        <div class="value red">{{ billingQueue.length }}</div>
        <div class="stat-sub">Need bill generation</div>
      </div>
    </div>

    <!-- ── BILLING QUEUE TAB ── -->
    <section v-if="activeTab === 'queue'" class="section">
      <div class="section-header">
        <h2>Pending Billing Queue</h2>
        <span class="badge">{{ billingQueue.length }}</span>
      </div>
      <div class="hipaa-notice">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        HIPAA Compliant — Patient identities masked. Service codes only.
      </div>

      <div v-if="loadingQueue" class="empty">Loading queue...</div>
      <div v-else-if="billingQueue.length === 0" class="empty">No pending bills. All sessions are billed.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Service ID</th>
            <th>Procedure</th>
            <th>Visit Date</th>
            <th>Generated</th>
            <th>Amount (₹)</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in billingQueue" :key="inv.invoice_id">
            <td class="mono muted sm">#{{ inv.invoice_id }}</td>
            <td class="mono sm svc-id">{{ inv.service_id }}</td>
            <td><span class="code-tag">{{ inv.service_code }}</span></td>
            <td class="mono sm muted">{{ inv.visit_date || '—' }}</td>
            <td class="mono sm muted">{{ inv.date_generated }}</td>
            <td>
              <div class="amount-cell">
                <span class="bold">{{ inv.amount?.toLocaleString() }}</span>
                <button class="edit-amt-btn" @click.stop="openEditAmount(inv)" title="Edit amount">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
              </div>
            </td>
            <td><span :class="['pay-tag', inv.status]">{{ inv.status }}</span></td>
            <td>
              <div class="action-group">
                <button @click="generateBill(inv.invoice_id)" class="gen-btn" :disabled="processing === inv.invoice_id">
                  {{ processing === inv.invoice_id ? '...' : 'Confirm Bill' }}
                </button>

              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── INVOICE LEDGER TAB ── -->
    <section v-if="activeTab === 'ledger'" class="section">
      <div class="section-header">
        <h2>Invoice Ledger</h2>
        <span class="badge">{{ allInvoices.length }}</span>
        <div class="ledger-filters">
          <button @click="ledgerFilter = 'all'"     :class="['filter-btn', ledgerFilter === 'all'     ? 'active' : '']">All</button>
          <button @click="ledgerFilter = 'pending'" :class="['filter-btn', ledgerFilter === 'pending' ? 'active' : '']">Pending</button>
          <button @click="ledgerFilter = 'paid'"    :class="['filter-btn', ledgerFilter === 'paid'    ? 'active' : '']">Paid</button>
        </div>
      </div>
      <div v-if="loadingLedger" class="empty">Loading ledger...</div>
      <div v-else-if="filteredInvoices.length === 0" class="empty">No invoices found.</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Invoice</th>
            <th>Service ID</th>
            <th>Procedure</th>
            <th>Visit Date</th>
            <th>Amount (₹)</th>
            <th>Status</th>
            <th>Payment Method</th>
            <th>Date Paid</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in filteredInvoices" :key="inv.invoice_id">
            <td class="mono muted sm">#{{ inv.invoice_id }}</td>
            <td class="mono sm svc-id">{{ inv.service_id }}</td>
            <td><span class="code-tag">{{ inv.service_code }}</span></td>
            <td class="mono sm muted">{{ inv.visit_date || '—' }}</td>
            <td class="bold">{{ inv.amount?.toLocaleString() }}</td>
            <td><span :class="['pay-tag', inv.status]">{{ inv.status }}</span></td>
            <td>
              <span v-if="inv.payment_source" class="source-tag">{{ inv.payment_source.replace('_', ' ') }}</span>
              <span v-else class="muted">—</span>
            </td>
            <td class="mono sm muted">{{ inv.date_paid || '—' }}</td>
<td></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ── REPORTS TAB ── -->
    <section v-if="activeTab === 'reports'" class="section">
      <div class="section-header">
        <h2>Business Intelligence</h2>
        <div class="report-tabs">
          <button @click="reportPeriod = 'daily'"   :class="['report-tab', reportPeriod === 'daily'   ? 'active' : '']">Daily</button>
          <button @click="reportPeriod = 'weekly'"  :class="['report-tab', reportPeriod === 'weekly'  ? 'active' : '']">Weekly</button>
          <button @click="reportPeriod = 'monthly'" :class="['report-tab', reportPeriod === 'monthly' ? 'active' : '']">Monthly</button>
        </div>
      </div>

      <div v-if="loadingReport" class="empty">Loading report...</div>
      <div v-else class="report-layout">
        <div class="report-summary">
          <div class="rsumm-card">
            <label>Period Revenue</label>
            <div class="rsumm-value green">₹{{ periodRevenue.toLocaleString() }}</div>
          </div>
          <div class="rsumm-card">
            <label>Period Pending</label>
            <div class="rsumm-value yellow">₹{{ periodPending.toLocaleString() }}</div>
          </div>
          <div class="rsumm-card">
            <label>Collection Rate</label>
            <div class="rsumm-value blue">
              {{ periodRevenue + periodPending > 0 ? Math.round((periodRevenue / (periodRevenue + periodPending)) * 100) : 0 }}%
            </div>
          </div>
          <div class="rsumm-card">
            <label>Total Sessions</label>
            <div class="rsumm-value teal">{{ periodCount }}</div>
          </div>
        </div>
        <div class="chart-card">
          <canvas ref="chartCanvas" height="300"></canvas>
        </div>
      </div>
    </section>

    <!-- ── EDIT AMOUNT MODAL ── -->
    <div v-if="showEditAmount" class="overlay" @click.self="showEditAmount = false">
      <div class="modal sm-modal">
        <div class="modal-head">
          <div>
            <h2>Edit Invoice Amount</h2>
            <span class="mono muted sm">Invoice #{{ activeInvoice?.invoice_id }}</span>
          </div>
          <button @click="showEditAmount = false" class="close">×</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label>Amount (₹)</label>
            <input v-model.number="editedAmount" type="number" min="0" step="100" class="amt-input" />
          </div>
          <p class="hint-sm">Default flat fee is ₹{{ FLAT_FEE.toLocaleString() }}. Only update if this procedure requires a different rate.</p>
        </div>
        <div class="modal-foot">
          <button @click="showEditAmount = false" class="cancel-btn">Cancel</button>
          <button @click="confirmEditAmount" class="gen-btn confirm-w">Update & Confirm Bill</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';
import Chart from 'chart.js/auto';

const authStore    = useAuthStore();
const messageStore = useMessageStore();
const BASE         = authStore.getBackendServerURL();
const FLAT_FEE     = 5000;

// ── Auth Headers ───────────────────────────────────────────────────────────
const getAuthHeaders = () => ({
  withCredentials: true,
  headers: {
    'Authentication-Token': authStore.getToken(),
    'Content-Type': 'application/json'
  }
});

// ── Helpers ────────────────────────────────────────────────────────────────
const fmt = (val) => val ? Number(val).toLocaleString() : '0';

// ── State ──────────────────────────────────────────────────────────────────
const activeTab     = ref('queue');
const reportPeriod  = ref('monthly');
const billingQueue  = ref([]);
const allInvoices   = ref([]);
const ledgerSummary = ref({});
const reportData    = ref([]);
const ledgerFilter  = ref('all');

const loadingQueue  = ref(false);
const loadingLedger = ref(false);
const loadingReport = ref(false);
const processing    = ref(null);

// Modals
const showEditAmount  = ref(false);
const activeInvoice   = ref(null);
const editedAmount    = ref(0);

const chartCanvas   = ref(null);
let   chartInstance = null;

// ── Computed ───────────────────────────────────────────────────────────────
const periodRevenue = computed(() => reportData.value.reduce((s, d) => s + d.revenue, 0));
const periodPending = computed(() => reportData.value.reduce((s, d) => s + d.pending, 0));
const periodCount   = computed(() => reportData.value.reduce((s, d) => s + d.count, 0));

const filteredInvoices = computed(() => {
  if (ledgerFilter.value === 'all') return allInvoices.value;
  return allInvoices.value.filter(i => i.status === ledgerFilter.value);
});

// ── Tab Switch ─────────────────────────────────────────────────────────────
const setTab = (tab) => {
  activeTab.value = tab;
  if (tab === 'queue')   fetchQueue();
  if (tab === 'ledger')  fetchLedger();
  if (tab === 'reports') fetchReport();
};

// ── Fetch Queue ────────────────────────────────────────────────────────────
const fetchQueue = async () => {
  loadingQueue.value = true;
  try {
    const res          = await axios.get(`${BASE}/api/v1/accountant/billing-queue`, getAuthHeaders());
    billingQueue.value = res.data.queue ?? [];
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load billing queue.");
  } finally {
    loadingQueue.value = false;
  }
};

// ── Fetch Ledger ───────────────────────────────────────────────────────────
const fetchLedger = async () => {
  loadingLedger.value = true;
  try {
    const res           = await axios.get(`${BASE}/api/v1/accountant/invoices`, getAuthHeaders());
    allInvoices.value   = res.data.invoices ?? [];
    ledgerSummary.value = {
      total_billed:  res.data.total_billed  ?? 0,
      total_revenue: res.data.total_revenue ?? 0,
      total_pending: res.data.total_pending ?? 0
    };
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load ledger.");
  } finally {
    loadingLedger.value = false;
  }
};

// ── Generate / Confirm Bill ────────────────────────────────────────────────
const generateBill = async (invoiceId, amount = null) => {
  processing.value = invoiceId;
  try {
    const payload = amount !== null ? { amount } : {};
    await axios.post(`${BASE}/api/v1/accountant/invoice/${invoiceId}/generate`, payload, getAuthHeaders());
    messageStore.setFlashMessage(`Bill confirmed for invoice #${invoiceId}`);
    fetchQueue();
    fetchLedger();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to confirm bill.");
  } finally {
    processing.value = null;
  }
};

// ── Edit Amount ────────────────────────────────────────────────────────────
const openEditAmount = (inv) => {
  activeInvoice.value  = inv;
  editedAmount.value   = inv.amount;
  showEditAmount.value = true;
};

const confirmEditAmount = async () => {
  showEditAmount.value = false;
  await generateBill(activeInvoice.value.invoice_id, editedAmount.value);
};

// ── Fetch Report ───────────────────────────────────────────────────────────
const fetchReport = async () => {
  loadingReport.value = true;
  try {
    const res        = await axios.get(`${BASE}/api/v1/accountant/report/${reportPeriod.value}`, getAuthHeaders());
    reportData.value = res.data[reportPeriod.value] ?? [];
    await nextTick();
    renderChart();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load report.");
  } finally {
    loadingReport.value = false;
  }
};

// ── Chart ──────────────────────────────────────────────────────────────────
const renderChart = () => {
  if (!chartCanvas.value) return;
  if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

  const labels  = reportData.value.map(d => d.label);
  const revenue = reportData.value.map(d => d.revenue);
  const pending = reportData.value.map(d => d.pending);

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label:           'Revenue (Paid)',
          data:            revenue,
          backgroundColor: 'rgba(5,150,105,0.75)',
          borderColor:     '#059669',
          borderWidth:     1,
          borderRadius:    4,
        },
        {
          label:           'Pending',
          data:            pending,
          backgroundColor: 'rgba(217,119,6,0.55)',
          borderColor:     '#d97706',
          borderWidth:     1,
          borderRadius:    4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#64748b', font: { family: 'DM Sans', size: 12 } } },
        tooltip: { callbacks: { label: (ctx) => ` ₹${ctx.parsed.y.toLocaleString()}` } }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'IBM Plex Mono', size: 11 } },
          grid:  { color: '#f1f5f9' }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font:  { family: 'IBM Plex Mono', size: 11 },
            callback: (val) => `₹${val.toLocaleString()}`
          },
          grid: { color: '#f1f5f9' }
        }
      }
    }
  });
};

watch(reportPeriod, () => { if (activeTab.value === 'reports') fetchReport(); });

onMounted(() => {
  fetchQueue();
  fetchLedger();
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
.header-actions { display: flex; align-items: center; gap: 0.6rem; }
.tab-btn { background: #fff; border: 1px solid #dde6f0; color: #64748b; padding: 0.55rem 1rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.tab-btn.active { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.tab-btn:hover:not(.active) { border-color: #94a3b8; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.stat-card label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.3rem; }
.stat-sub { font-size: 0.7rem; color: #94a3b8; margin-top: 0.25rem; }
.value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.value.blue   { color: #2563eb; }
.value.green  { color: #059669; }
.value.yellow { color: #d97706; }
.value.red    { color: #e11d48; }

/* Section */
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.section-header h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin: 0; }
.badge { background: #e2e8f0; color: #64748b; font-size: 0.68rem; font-family: 'IBM Plex Mono', monospace; padding: 0.1rem 0.5rem; border-radius: 20px; }

/* HIPAA notice */
.hipaa-notice { display: flex; align-items: center; gap: 0.5rem; font-size: 0.74rem; color: #92400e; background: #fffbeb; border: 1px solid #fde68a; padding: 0.55rem 0.9rem; border-radius: 7px; margin-bottom: 1rem; font-weight: 500; }

/* Ledger filters */
.ledger-filters { display: flex; gap: 0.35rem; margin-left: auto; }
.filter-btn { background: #fff; border: 1px solid #e2e8f0; color: #64748b; padding: 0.28rem 0.75rem; border-radius: 5px; font-family: 'DM Sans', sans-serif; font-size: 0.73rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.filter-btn.active { background: #1a2535; color: #fff; border-color: #1a2535; }

/* Table */
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #dde6f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.table th { text-align: left; padding: 0.7rem 1rem; background: #f8fafc; color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.table td { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.84rem; vertical-align: middle; }
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }

/* Service ID — masked look */
.svc-id { color: #0a7ea4; letter-spacing: 0.03em; }

/* Amount cell */
.amount-cell { display: flex; align-items: center; gap: 0.4rem; }
.edit-amt-btn { background: none; border: none; color: #94a3b8; cursor: pointer; padding: 0.2rem; border-radius: 3px; display: flex; align-items: center; transition: color 0.15s; }
.edit-amt-btn:hover { color: #0a7ea4; }

/* Action group */
.action-group { display: flex; gap: 0.4rem; }

/* Tags */
.pay-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; text-transform: capitalize; }
.pay-tag.pending { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.pay-tag.paid    { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.code-tag { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #7c3aed; background: #f5f3ff; border: 1px solid #ddd6fe; padding: 0.18rem 0.5rem; border-radius: 4px; }
.source-tag { font-size: 0.72rem; color: #64748b; background: #f1f5f9; padding: 0.15rem 0.45rem; border-radius: 4px; text-transform: capitalize; }

/* Buttons */
.gen-btn { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 0.3rem 0.75rem; border-radius: 5px; font-family: 'DM Sans', sans-serif; font-size: 0.72rem; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.gen-btn:hover { background: #2563eb; color: #fff; }
.gen-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.sm-btn { padding: 0.22rem 0.55rem; font-size: 0.68rem; }
.confirm-w { width: 100%; justify-content: center; padding: 0.7rem; font-size: 0.84rem; }
.cancel-btn { background: transparent; color: #64748b; border: 1px solid #e2e8f0; padding: 0.65rem 1.2rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.cancel-btn:hover { border-color: #94a3b8; }

/* Reports */
.report-tabs { display: flex; gap: 0.4rem; margin-left: auto; }
.report-tab { background: #fff; border: 1px solid #dde6f0; color: #64748b; padding: 0.35rem 0.8rem; border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.76rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.report-tab.active { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.report-tab:hover:not(.active) { border-color: #94a3b8; }
.report-layout { display: flex; flex-direction: column; gap: 1rem; }
.report-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.rsumm-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rsumm-card label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.3rem; }
.rsumm-value { font-size: 1.6rem; font-weight: 700; }
.rsumm-value.green  { color: #059669; }
.rsumm-value.yellow { color: #d97706; }
.rsumm-value.blue   { color: #2563eb; }
.rsumm-value.teal   { color: #0a7ea4; }
.chart-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); height: 340px; }

/* Modal */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 1rem; }
.modal { background: #fff; border-top: 3px solid #0a7ea4; border-radius: 12px; width: 100%; padding: 1.75rem; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }
.sm-modal { max-width: 440px; }
.modal-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9; }
.modal-head h2 { font-size: 1.05rem; font-weight: 700; margin: 0 0 0.2rem; }
.close { background: none; border: none; font-size: 1.4rem; color: #94a3b8; cursor: pointer; }
.modal-body { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.25rem; }
.modal-foot { display: flex; justify-content: flex-end; gap: 0.6rem; padding-top: 1rem; border-top: 1px solid #f1f5f9; }

/* Invoice summary in modal */
.invoice-summary { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.65rem; }
.inv-row { display: flex; justify-content: space-between; align-items: center; }
.inv-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8; }
.inv-amount { font-size: 1.2rem; font-weight: 700; color: #059669; font-family: 'IBM Plex Mono', monospace; }

/* Amount input */
.amt-input { background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.65rem 0.85rem; border-radius: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 600; width: 100%; box-sizing: border-box; }
.amt-input:focus { outline: none; border-color: #0a7ea4; }
.hint-sm { font-size: 0.74rem; color: #94a3b8; margin: 0; }

/* Empty */
.empty { padding: 2rem; text-align: center; color: #94a3b8; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.84rem; }
.mono  { font-family: 'IBM Plex Mono', monospace; }
.bold  { font-weight: 600; }
.muted { color: #94a3b8; }
.sm    { font-size: 0.76rem; }
</style>