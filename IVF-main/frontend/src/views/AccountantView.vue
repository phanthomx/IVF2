<template>
  <div class="shell">

    <!-- ── SIDEBAR ─────────────────────────────────────────── -->
    <aside class="sidebar">
      <nav class="nav">
        <button @click="setTab('queue')"   :class="['nav-item', activeTab==='queue'   ? 'active' : '']">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          <span>Billing Queue</span>
          <span v-if="billingQueue.length" class="nav-badge">{{ billingQueue.length }}</span>
        </button>
        <button @click="setTab('ledger')"  :class="['nav-item', activeTab==='ledger'  ? 'active' : '']">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <span>Invoice Ledger</span>
        </button>
        <button @click="setTab('reports')" :class="['nav-item', activeTab==='reports' ? 'active' : '']">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <span>Reports</span>
        </button>
        <button @click="setTab('doctors')" :class="['nav-item', activeTab==='doctors' ? 'active' : '']">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <span>Doctor Analysis</span>
        </button>
      </nav>

      <!-- Sidebar KPIs -->
      <div class="side-kpis">
        <div class="side-kpi">
          <span class="side-kpi-label">Total Billed</span>
          <span class="side-kpi-val blue">₹{{ fmtK(ledgerSummary.total_billed) }}</span>
        </div>
        <div class="side-kpi">
          <span class="side-kpi-label">Collected</span>
          <span class="side-kpi-val green">₹{{ fmtK(ledgerSummary.total_revenue) }}</span>
        </div>
        <div class="side-kpi">
          <span class="side-kpi-label">Outstanding</span>
          <span class="side-kpi-val amber">₹{{ fmtK(ledgerSummary.total_pending) }}</span>
        </div>
      </div>

      <div class="hipaa-pill">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        HIPAA Compliant
      </div>
    </aside>

    <!-- ── MAIN CONTENT ────────────────────────────────────── -->
    <main class="main">

      <!-- ── BILLING QUEUE ── -->
      <div v-if="activeTab === 'queue'" class="pane">
        <div class="pane-head">
          <div>
            <h1 class="pane-title">Billing Queue</h1>
            <p class="pane-sub">Sessions awaiting bill confirmation</p>
          </div>
          <span class="chip amber">{{ billingQueue.length }} pending</span>
        </div>
        <div v-if="loadingQueue" class="empty-state">Loading…</div>
        <div v-else-if="billingQueue.length === 0" class="empty-state">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          All sessions billed
        </div>
        <div v-else class="scroll-table-wrap">
          <table class="dtable">
            <thead><tr>
              <th>Invoice</th><th>Service ID</th><th>Code</th>
              <th>Visit</th><th>Generated</th><th>Amount</th>
              <th>Status</th><th>Action</th>
            </tr></thead>
            <tbody>
              <tr v-for="inv in billingQueue" :key="inv.invoice_id">
                <td class="mono dim">#{{ inv.invoice_id }}</td>
                <td class="mono accent-blue">{{ inv.service_id }}</td>
                <td><span class="code-pill">{{ inv.service_code }}</span></td>
                <td class="mono dim sm">{{ inv.visit_date || '—' }}</td>
                <td class="mono dim sm">{{ inv.date_generated }}</td>
                <td>
                  <div class="amt-wrap">
                    <span class="bold">{{ inv.amount?.toLocaleString() }}</span>
                    <button class="icon-btn" @click.stop="openEditAmount(inv)" title="Edit">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                  </div>
                </td>
                <td><span :class="['status-chip', inv.status]">{{ inv.status }}</span></td>
                <td>
                  <button @click="generateBill(inv.invoice_id)" class="confirm-btn" :disabled="processing===inv.invoice_id">
                    {{ processing===inv.invoice_id ? '…' : 'Confirm' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── INVOICE LEDGER ── -->
      <div v-if="activeTab === 'ledger'" class="pane">
        <div class="pane-head">
          <div>
            <h1 class="pane-title">Invoice Ledger</h1>
            <p class="pane-sub">Complete billing history</p>
          </div>
          <div class="filter-row">
            <button @click="ledgerFilter='all'"     :class="['flt-btn', ledgerFilter==='all'     ? 'active':'']">All</button>
            <button @click="ledgerFilter='pending'" :class="['flt-btn', ledgerFilter==='pending' ? 'active':'']">Pending</button>
            <button @click="ledgerFilter='paid'"    :class="['flt-btn', ledgerFilter==='paid'    ? 'active':'']">Paid</button>
          </div>
        </div>
        <div v-if="loadingLedger" class="empty-state">Loading…</div>
        <div v-else-if="filteredInvoices.length===0" class="empty-state">No invoices found.</div>
        <div v-else class="scroll-table-wrap">
          <table class="dtable">
            <thead><tr>
              <th>Invoice</th><th>Service ID</th><th>Code</th>
              <th>Visit</th><th>Amount</th><th>Status</th>
              <th>Payment</th><th>Paid On</th>
            </tr></thead>
            <tbody>
              <tr v-for="inv in filteredInvoices" :key="inv.invoice_id">
                <td class="mono dim">#{{ inv.invoice_id }}</td>
                <td class="mono accent-blue">{{ inv.service_id }}</td>
                <td><span class="code-pill">{{ inv.service_code }}</span></td>
                <td class="mono dim sm">{{ inv.visit_date || '—' }}</td>
                <td class="bold">{{ inv.amount?.toLocaleString() }}</td>
                <td><span :class="['status-chip', inv.status]">{{ inv.status }}</span></td>
                <td><span v-if="inv.payment_source" class="pay-src">{{ inv.payment_source.replace('_',' ') }}</span><span v-else class="dim">—</span></td>
                <td class="mono dim sm">{{ inv.date_paid || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── REPORTS ── -->
      <div v-show="activeTab === 'reports'" class="pane">
        <div class="pane-head">
          <div>
            <h1 class="pane-title">Business Intelligence</h1>
            <p class="pane-sub">Revenue analytics &amp; trends</p>
          </div>
          <div class="filter-row">
            <button @click="reportPeriod='daily'"   :class="['flt-btn', reportPeriod==='daily'   ? 'active':'']">Daily</button>
            <button @click="reportPeriod='weekly'"  :class="['flt-btn', reportPeriod==='weekly'  ? 'active':'']">Weekly</button>
            <button @click="reportPeriod='monthly'" :class="['flt-btn', reportPeriod==='monthly' ? 'active':'']">Monthly</button>
          </div>
        </div>

        <div v-if="loadingReport" class="empty-state">Loading…</div>
        <div v-show="!loadingReport" class="reports-body">
          <div class="kpi-strip">
            <div class="kpi-card">
              <span class="kpi-label">Period Revenue</span>
              <span class="kpi-val green">₹{{ fmt(chartPayload.kpi?.period_revenue) }}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Period Pending</span>
              <span class="kpi-val amber">₹{{ fmt(chartPayload.kpi?.period_pending) }}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Collection Rate</span>
              <span class="kpi-val blue">{{ chartPayload.kpi?.collection_rate ?? 0 }}%</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Sessions</span>
              <span class="kpi-val teal">{{ chartPayload.kpi?.period_count ?? 0 }}</span>
            </div>
          </div>

          <div class="chart-grid">
            <div class="chart-box">
              <div class="chart-box-head"><span class="chart-box-title">Revenue vs Pending</span><span class="chart-box-sub">{{ reportPeriod }}</span></div>
              <canvas ref="barCanvas"></canvas>
            </div>
            <div class="chart-box">
              <div class="chart-box-head"><span class="chart-box-title">Revenue Trend</span><span class="chart-box-sub">collected vs billed</span></div>
              <canvas ref="lineCanvas"></canvas>
            </div>
            <div class="chart-box">
              <div class="chart-box-head"><span class="chart-box-title">Collection Split</span><span class="chart-box-sub">paid vs pending</span></div>
              <div class="donut-wrap">
                <canvas ref="donutCanvas"></canvas>
                <div class="donut-center">
                  <span class="donut-pct">{{ chartPayload.kpi?.collection_rate ?? 0 }}%</span>
                  <span class="donut-lbl">collected</span>
                </div>
              </div>
            </div>
            <div class="chart-box">
              <div class="chart-box-head"><span class="chart-box-title">Service Codes</span><span class="chart-box-sub">all time</span></div>
              <canvas ref="serviceCanvas"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- ── DOCTOR ANALYSIS ── -->
      <div v-show="activeTab === 'doctors'" class="pane">
        <div class="pane-head">
          <div>
            <h1 class="pane-title">Doctor Analysis</h1>
            <p class="pane-sub">Revenue breakdown by physician</p>
          </div>
          <div class="filter-row">
            <button @click="doctorPeriod='all'"     :class="['flt-btn', doctorPeriod==='all'     ? 'active':'']">All Time</button>
            <button @click="doctorPeriod='monthly'" :class="['flt-btn', doctorPeriod==='monthly' ? 'active':'']">12 Mo</button>
            <button @click="doctorPeriod='weekly'"  :class="['flt-btn', doctorPeriod==='weekly'  ? 'active':'']">12 Wk</button>
            <button @click="doctorPeriod='daily'"   :class="['flt-btn', doctorPeriod==='daily'   ? 'active':'']">30 Days</button>
          </div>
        </div>

        <div v-if="loadingDoctor" class="empty-state">Loading…</div>
        <div v-else-if="doctorData.length===0" class="empty-state">No doctor data for this period.</div>
        <div v-else class="doctor-body">

          <div class="kpi-strip">
            <div class="kpi-card">
              <span class="kpi-label">Active Doctors</span>
              <span class="kpi-val teal">{{ doctorData.length }}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Total Sessions</span>
              <span class="kpi-val blue">{{ doctorData.reduce((s,d)=>s+d.session_count,0) }}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Total Revenue</span>
              <span class="kpi-val green">₹{{ fmt(doctorData.reduce((s,d)=>s+d.revenue,0)) }}</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Top Earner</span>
              <span class="kpi-val violet">{{ doctorData[0]?.doctor_name?.split(' ').slice(0,2).join(' ') ?? '—' }}</span>
            </div>
          </div>

          <div class="doc-two-col">
            <div class="chart-box">
              <div class="chart-box-head"><span class="chart-box-title">Revenue vs Pending</span><span class="chart-box-sub">by doctor</span></div>
              <canvas ref="docBarCanvas"></canvas>
            </div>
            <div class="chart-box rate-box">
              <div class="chart-box-head"><span class="chart-box-title">Collection Rates</span><span class="chart-box-sub">% billed collected</span></div>
              <div class="rate-list">
                <div v-for="doc in doctorData" :key="'r'+doc.doctor_id" class="rate-item">
                  <div class="rate-meta">
                    <div class="doc-ava">{{ doc.doctor_name.charAt(0) }}</div>
                    <div class="rate-info">
                      <span class="rate-name">{{ doc.doctor_name }}</span>
                      <span class="rate-spec">{{ doc.specialization }}</span>
                    </div>
                  </div>
                  <div class="rate-bar-row">
                    <div class="rate-track">
                      <div class="rate-fill" :style="{
                        width: doc.collection_rate+'%',
                        background: doc.collection_rate>=75
                          ? 'linear-gradient(90deg,#059669,#34d399)'
                          : doc.collection_rate>=40
                          ? 'linear-gradient(90deg,#d97706,#fbbf24)'
                          : 'linear-gradient(90deg,#e11d48,#fb7185)'
                      }"></div>
                    </div>
                    <span class="rate-pct mono" :style="{color: doc.collection_rate>=75?'#34d399':doc.collection_rate>=40?'#fbbf24':'#fb7185'}">
                      {{ doc.collection_rate }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="scroll-table-wrap" style="flex-shrink:0; max-height: 260px;">
            <table class="dtable">
              <thead><tr>
                <th>#</th><th>Doctor</th><th>Specialization</th>
                <th>Sessions</th><th>Total Billed</th>
                <th>Revenue</th><th>Pending</th><th>Rate</th>
              </tr></thead>
              <tbody>
                <tr v-for="(doc,i) in doctorData" :key="doc.doctor_id">
                  <td class="mono dim sm">{{ i+1 }}</td>
                  <td>
                    <div class="doc-cell">
                      <div class="doc-ava sm-ava">{{ doc.doctor_name.charAt(0) }}</div>
                      <span class="bold">{{ doc.doctor_name }}</span>
                    </div>
                  </td>
                  <td><span class="pay-src">{{ doc.specialization }}</span></td>
                  <td class="mono sm">{{ doc.session_count }}</td>
                  <td class="mono">{{ doc.total_billed.toLocaleString() }}</td>
                  <td class="mono" style="color:#059669;font-weight:600;">{{ doc.revenue.toLocaleString() }}</td>
                  <td class="mono" style="color:#d97706;font-weight:600;">{{ doc.pending.toLocaleString() }}</td>
                  <td>
                    <div class="inline-rate">
                      <div class="inline-track">
                        <div class="inline-fill" :style="{
                          width:doc.collection_rate+'%',
                          background:doc.collection_rate>=75?'#34d399':doc.collection_rate>=40?'#fbbf24':'#fb7185'
                        }"></div>
                      </div>
                      <span class="mono sm" :style="{color:doc.collection_rate>=75?'#34d399':doc.collection_rate>=40?'#fbbf24':'#fb7185',fontWeight:600}">
                        {{ doc.collection_rate }}%
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="tfoot-row">
                  <td colspan="3" class="sm dim bold">TOTALS</td>
                  <td class="mono bold">{{ doctorData.reduce((s,d)=>s+d.session_count,0) }}</td>
                  <td class="mono bold">{{ doctorData.reduce((s,d)=>s+d.total_billed,0).toLocaleString() }}</td>
                  <td class="mono bold" style="color:#059669;">{{ doctorData.reduce((s,d)=>s+d.revenue,0).toLocaleString() }}</td>
                  <td class="mono bold" style="color:#d97706;">{{ doctorData.reduce((s,d)=>s+d.pending,0).toLocaleString() }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>

        </div>
      </div>

    </main>

    <!-- ── EDIT AMOUNT MODAL ── -->
    <div v-if="showEditAmount" class="overlay" @click.self="showEditAmount=false">
      <div class="modal">
        <div class="modal-head">
          <div>
            <h2>Edit Invoice Amount</h2>
            <span class="mono dim sm">Invoice #{{ activeInvoice?.invoice_id }}</span>
          </div>
          <button @click="showEditAmount=false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <label class="field-label">Amount (₹)</label>
          <input v-model.number="editedAmount" type="number" min="0" step="100" class="amt-input" />
          <p class="hint">Default flat fee ₹{{ FLAT_FEE.toLocaleString() }}. Edit only if procedure rate differs.</p>
        </div>
        <div class="modal-foot">
          <button @click="showEditAmount=false" class="ghost-btn">Cancel</button>
          <button @click="confirmEditAmount" class="confirm-btn wide">Update &amp; Confirm</button>
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

const getAuthHeaders = () => ({
  withCredentials: true,
  headers: {
    'Authentication-Token': authStore.getToken(),
    'Content-Type': 'application/json'
  }
});

const fmt  = (val) => val ? Number(val).toLocaleString() : '0';
const fmtK = (val) => {
  if (!val) return '0';
  const n = Number(val);
  if (n >= 100000) return (n / 100000).toFixed(1) + 'L';
  if (n >= 1000)   return (n / 1000).toFixed(1) + 'k';
  return n.toLocaleString();
};

const activeTab     = ref('queue');
const reportPeriod  = ref('monthly');
const doctorPeriod  = ref('all');
const billingQueue  = ref([]);
const allInvoices   = ref([]);
const ledgerSummary = ref({});
const ledgerFilter  = ref('all');
const chartPayload  = ref({ kpi: null, timeseries: [], donut: null, service_codes: null });
const doctorData    = ref([]);

const loadingQueue  = ref(false);
const loadingLedger = ref(false);
const loadingReport = ref(false);
const loadingDoctor = ref(false);
const processing    = ref(null);

const showEditAmount = ref(false);
const activeInvoice  = ref(null);
const editedAmount   = ref(0);

const barCanvas     = ref(null);
const lineCanvas    = ref(null);
const donutCanvas   = ref(null);
const serviceCanvas = ref(null);
const docBarCanvas  = ref(null);

let barInstance = null, lineInstance = null, donutInstance = null,
    serviceInstance = null, docBarInstance = null;

const filteredInvoices = computed(() => {
  if (ledgerFilter.value === 'all') return allInvoices.value;
  return allInvoices.value.filter(i => i.status === ledgerFilter.value);
});

const setTab = (tab) => {
  activeTab.value = tab;
  if (tab === 'queue')   fetchQueue();
  if (tab === 'ledger')  fetchLedger();
  if (tab === 'reports') fetchCharts();
  if (tab === 'doctors') fetchDoctorAnalysis();
};

const fetchQueue = async () => {
  loadingQueue.value = true;
  try {
    const res = await axios.get(`${BASE}/api/v1/accountant/billing-queue`, getAuthHeaders());
    billingQueue.value = res.data.queue ?? [];
  } catch (e) { messageStore.setFlashMessage(e.response?.data?.message || "Failed to load queue."); }
  finally { loadingQueue.value = false; }
};

const fetchLedger = async () => {
  loadingLedger.value = true;
  try {
    const res = await axios.get(`${BASE}/api/v1/accountant/invoices`, getAuthHeaders());
    allInvoices.value   = res.data.invoices ?? [];
    ledgerSummary.value = {
      total_billed:  res.data.total_billed  ?? 0,
      total_revenue: res.data.total_revenue ?? 0,
      total_pending: res.data.total_pending ?? 0,
    };
  } catch (e) { messageStore.setFlashMessage(e.response?.data?.message || "Failed to load ledger."); }
  finally { loadingLedger.value = false; }
};

const fetchCharts = async () => {
  loadingReport.value = true;
  try {
    const res = await axios.get(`${BASE}/api/v1/accountant/charts/${reportPeriod.value}`, getAuthHeaders());
    chartPayload.value = res.data;
    await nextTick(); await nextTick();
    renderAllCharts();
  } catch (e) { messageStore.setFlashMessage(e.response?.data?.message || "Failed to load charts."); }
  finally { loadingReport.value = false; }
};

const fetchDoctorAnalysis = async () => {
  loadingDoctor.value = true;
  try {
    const res = await axios.get(`${BASE}/api/v1/accountant/charts/doctors?period=${doctorPeriod.value}`, getAuthHeaders());
    doctorData.value = res.data.doctors ?? [];
    await nextTick(); await nextTick();
    renderDoctorBar();
  } catch (e) { messageStore.setFlashMessage(e.response?.data?.message || "Failed to load doctor data."); }
  finally { loadingDoctor.value = false; }
};

const generateBill = async (invoiceId, amount = null) => {
  processing.value = invoiceId;
  try {
    const payload = amount !== null ? { amount } : {};
    await axios.post(`${BASE}/api/v1/accountant/invoice/${invoiceId}/generate`, payload, getAuthHeaders());
    messageStore.setFlashMessage(`Bill confirmed for invoice #${invoiceId}`);
    fetchQueue(); fetchLedger();
  } catch (e) { messageStore.setFlashMessage(e.response?.data?.message || "Failed to confirm bill."); }
  finally { processing.value = null; }
};

const openEditAmount = (inv) => { activeInvoice.value = inv; editedAmount.value = inv.amount; showEditAmount.value = true; };
const confirmEditAmount = async () => { showEditAmount.value = false; await generateBill(activeInvoice.value.invoice_id, editedAmount.value); };

const kill = (i) => { if (i) i.destroy(); return null; };

const TT = { backgroundColor:'#1e293b', titleColor:'#94a3b8', bodyColor:'#f1f5f9', padding:10, cornerRadius:6 };
const TX = { color:'#94a3b8', font:{ family:'JetBrains Mono', size:10 } };
const GR = { color:'rgba(0,0,0,0.06)' };
const RU = { ...TX, callback: v => `₹${(v/1000).toFixed(0)}k` };
const LG = { labels:{ color:'#64748b', font:{ family:'Outfit', size:11 }, boxWidth:10 } };

const renderAllCharts = () => { renderBar(); renderLine(); renderDonut(); renderService(); };

const renderBar = () => {
  if (!barCanvas.value) return;
  barInstance = kill(barInstance);
  const ts = chartPayload.value.timeseries ?? [];
  barInstance = new Chart(barCanvas.value, {
    type:'bar',
    data:{ labels:ts.map(d=>d.label), datasets:[
      { label:'Revenue', data:ts.map(d=>d.revenue), backgroundColor:'rgba(52,211,153,0.75)', borderRadius:4, borderSkipped:false },
      { label:'Pending', data:ts.map(d=>d.pending), backgroundColor:'rgba(251,191,36,0.45)', borderRadius:4, borderSkipped:false },
    ]},
    options:{ responsive:true, maintainAspectRatio:false,
      interaction:{ mode:'index', intersect:false },
      plugins:{ legend:LG, tooltip:{ ...TT, callbacks:{ label:c=>` ₹${c.parsed.y.toLocaleString()}` }}},
      scales:{ x:{ ticks:TX, grid:{ display:false }}, y:{ ticks:RU, grid:GR }}}
  });
};

const renderLine = () => {
  if (!lineCanvas.value) return;
  lineInstance = kill(lineInstance);
  const ts = chartPayload.value.timeseries ?? [];
  lineInstance = new Chart(lineCanvas.value, {
    type:'line',
    data:{ labels:ts.map(d=>d.label), datasets:[
      { label:'Collected', data:ts.map(d=>d.revenue), borderColor:'#34d399', backgroundColor:'rgba(52,211,153,0.07)', borderWidth:2, pointRadius:2, tension:0.4, fill:true },
      { label:'Billed',    data:ts.map(d=>d.total),   borderColor:'#38bdf8', backgroundColor:'rgba(56,189,248,0.04)', borderWidth:1.5, pointRadius:2, tension:0.4, fill:true, borderDash:[4,3] },
    ]},
    options:{ responsive:true, maintainAspectRatio:false,
      interaction:{ mode:'index', intersect:false },
      plugins:{ legend:{ ...LG, labels:{...LG.labels, usePointStyle:true }}, tooltip:{ ...TT, callbacks:{ label:c=>` ₹${c.parsed.y.toLocaleString()}` }}},
      scales:{ x:{ ticks:TX, grid:{ display:false }}, y:{ ticks:RU, grid:GR }}}
  });
};

const renderDonut = () => {
  if (!donutCanvas.value) return;
  donutInstance = kill(donutInstance);
  const d = chartPayload.value.donut ?? { labels:[], values:[] };
  donutInstance = new Chart(donutCanvas.value, {
    type:'doughnut',
    data:{ labels:d.labels, datasets:[{ data:d.values,
      backgroundColor:['rgba(52,211,153,0.8)','rgba(251,191,36,0.5)'],
      borderColor:['#34d399','#fbbf24'], borderWidth:1.5, hoverOffset:5 }]},
    options:{ responsive:true, maintainAspectRatio:false, cutout:'72%',
      plugins:{ legend:{ position:'bottom', labels:{ color:'#475569', font:{ family:'Outfit', size:11 }, boxWidth:9, padding:14 }},
        tooltip:{ ...TT, callbacks:{ label:c=>` ₹${c.parsed.toLocaleString()}` }}}}
  });
};

const renderService = () => {
  if (!serviceCanvas.value) return;
  serviceInstance = kill(serviceInstance);
  const sc = chartPayload.value.service_codes ?? { labels:[], revenue:[], pending:[] };
  serviceInstance = new Chart(serviceCanvas.value, {
    type:'bar',
    data:{ labels:sc.labels, datasets:[
      { label:'Revenue', data:sc.revenue, backgroundColor:'rgba(52,211,153,0.75)', borderRadius:3, borderSkipped:false },
      { label:'Pending', data:sc.pending, backgroundColor:'rgba(251,191,36,0.45)', borderRadius:3, borderSkipped:false },
    ]},
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      interaction:{ mode:'index', intersect:false },
      plugins:{ legend:LG, tooltip:{ ...TT, callbacks:{ label:c=>` ₹${c.parsed.x.toLocaleString()}` }}},
      scales:{ x:{ ticks:RU, grid:GR }, y:{ ticks:{ color:'#818cf8', font:{ family:'JetBrains Mono', size:10 }}, grid:{ display:false }}}}
  });
};

const renderDoctorBar = () => {
  if (!docBarCanvas.value) return;
  docBarInstance = kill(docBarInstance);
  const rows = doctorData.value;
  docBarInstance = new Chart(docBarCanvas.value, {
    type:'bar',
    data:{ labels:rows.map(d=>d.doctor_name), datasets:[
      { label:'Revenue', data:rows.map(d=>d.revenue), backgroundColor:'rgba(52,211,153,0.75)', borderRadius:4, borderSkipped:false },
      { label:'Pending', data:rows.map(d=>d.pending), backgroundColor:'rgba(251,191,36,0.45)', borderRadius:4, borderSkipped:false },
    ]},
    options:{ responsive:true, maintainAspectRatio:false,
      interaction:{ mode:'index', intersect:false },
      plugins:{ legend:LG, tooltip:{ ...TT, callbacks:{ label:c=>` ₹${c.parsed.y.toLocaleString()}` }}},
      scales:{ x:{ ticks:TX, grid:{ display:false }}, y:{ ticks:RU, grid:GR }}}
  });
};

watch(reportPeriod, () => { if (activeTab.value==='reports') fetchCharts(); });
watch(doctorPeriod, () => { if (activeTab.value==='doctors') fetchDoctorAnalysis(); });

onMounted(() => { fetchQueue(); fetchLedger(); fetchCharts(); fetchDoctorAnalysis(); });
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f1f5f9;
  font-family: 'Outfit', sans-serif;
  color: #1e293b;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  padding: 1.25rem 0.75rem;
  gap: 0.5rem;
}

.nav { display: flex; flex-direction: column; gap: 0.2rem; }
.nav-item {
  display: flex; align-items: center; gap: 0.6rem;
  width: 100%; padding: 0.55rem 0.75rem;
  background: none; border: none;
  color: #64748b; font-family: 'Outfit', sans-serif;
  font-size: 0.82rem; font-weight: 500;
  border-radius: 8px; cursor: pointer;
  transition: all 0.15s; text-align: left;
}
.nav-item:hover { background: #f1f5f9; color: #334155; }
.nav-item.active { background: #e0f2fe; color: #0a7ea4; border: 1px solid #bae6fd; }
.nav-badge {
  margin-left: auto;
  background: #e11d4820; color: #ef4444;
  font-size: 0.62rem; font-family: 'JetBrains Mono', monospace;
  padding: 0.1rem 0.4rem; border-radius: 99px;
  border: 1px solid #e11d4830;
}

.side-kpis { margin-top: auto; display: flex; flex-direction: column; gap: 0.35rem; padding: 0.75rem 0.5rem; border-top: 1px solid #e2e8f0; }
.side-kpi  { display: flex; justify-content: space-between; align-items: center; }
.side-kpi-label { font-size: 0.68rem; color: #94a3b8; }
.side-kpi-val   { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 600; }
.side-kpi-val.blue  { color: #0a7ea4; }
.side-kpi-val.green { color: #059669; }
.side-kpi-val.amber { color: #d97706; }

.hipaa-pill {
  display: flex; align-items: center; gap: 0.4rem;
  font-size: 0.62rem; color: #d97706; background: #d9770610;
  border: 1px solid #d9770625; padding: 0.35rem 0.65rem;
  border-radius: 6px; margin: 0 0.25rem 0.25rem;
}

.main { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 1.5rem 1.75rem; gap: 1rem; }
.pane-head { display: flex; align-items: flex-start; justify-content: space-between; flex-shrink: 0; }
.pane-title { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0 0 0.15rem; }
.pane-sub   { font-size: 0.74rem; color: #64748b; margin: 0; }

.chip       { font-size: 0.68rem; font-weight: 700; padding: 0.25rem 0.65rem; border-radius: 99px; font-family: 'JetBrains Mono', monospace; }
.chip.amber { background: #fbbf2415; color: #d97706; border: 1px solid #fbbf2430; }

.filter-row { display: flex; gap: 0.3rem; }
.flt-btn {
  background: #ffffff; border: 1px solid #e2e8f0; color: #64748b;
  padding: 0.3rem 0.7rem; border-radius: 6px;
  font-family: 'Outfit', sans-serif; font-size: 0.74rem; font-weight: 600;
  cursor: pointer; transition: all 0.15s;
}
.flt-btn:hover  { border-color: #64748b; color: #64748b; }
.flt-btn.active { background: #0a7ea415; color: #0a7ea4; border-color: #0a7ea440; }

.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.75rem; color: #94a3b8; font-size: 0.84rem; }

.kpi-strip { display: grid; grid-template-columns: repeat(4,1fr); gap: 0.75rem; flex-shrink: 0; }
.kpi-card  { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.85rem 1rem; display: flex; flex-direction: column; gap: 0.2rem; }
.kpi-label { font-size: 0.63rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.09em; color: #94a3b8; }
.kpi-val   { font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1.1; }
.kpi-val.green  { color: #059669; }
.kpi-val.amber  { color: #d97706; }
.kpi-val.blue   { color: #0a7ea4; }
.kpi-val.teal   { color: #0d9488; }
.kpi-val.violet { color: #7c3aed; font-size: 0.95rem; }

.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 0.75rem;
  flex: 1;
  min-height: 0;
}

.chart-box {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 0.9rem 1.1rem 1rem; display: flex; flex-direction: column;
  min-height: 0; overflow: hidden;
}
.chart-box canvas { flex: 1; min-height: 0; }
.chart-box-head   { display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.6rem; flex-shrink: 0; }
.chart-box-title  { font-size: 0.78rem; font-weight: 700; color: #64748b; }
.chart-box-sub    { font-size: 0.64rem; color: #94a3b8; }

.donut-wrap   { position: relative; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }
.donut-wrap canvas { max-height: 100%; }
.donut-center { position: absolute; top: 42%; transform: translateY(-50%); text-align: center; pointer-events: none; }
.donut-pct    { display: block; font-size: 1.3rem; font-weight: 700; color: #059669; font-family: 'JetBrains Mono', monospace; line-height: 1; }
.donut-lbl    { font-size: 0.58rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }

.reports-body { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 0.75rem; overflow: hidden; }

.doctor-body { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 0.75rem; overflow: hidden; }
.doc-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; height: 260px; flex-shrink: 0; }

.rate-box  { overflow: hidden; }
.rate-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.7rem; padding-right: 0.25rem; }
.rate-item { display: flex; flex-direction: column; gap: 0.35rem; }
.rate-meta { display: flex; align-items: center; gap: 0.5rem; }
.rate-info { display: flex; flex-direction: column; }
.rate-name { font-size: 0.78rem; font-weight: 600; color: #64748b; }
.rate-spec { font-size: 0.63rem; color: #94a3b8; }
.rate-bar-row { display: flex; align-items: center; gap: 0.5rem; }
.rate-track { flex: 1; height: 6px; background: #f8fafc; border-radius: 99px; overflow: hidden; }
.rate-fill  { height: 100%; border-radius: 99px; transition: width 0.5s ease; }
.rate-pct   { font-size: 0.7rem; font-weight: 700; min-width: 38px; text-align: right; }

.doc-ava    { width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0; background: linear-gradient(135deg,#7c3aed,#0a7ea4); color:#fff; font-size:0.68rem; font-weight:700; display:flex; align-items:center; justify-content:center; }
.sm-ava     { width: 22px; height: 22px; font-size: 0.62rem; }
.doc-cell   { display: flex; align-items: center; gap: 0.5rem; }

.inline-rate  { display: flex; align-items: center; gap: 0.4rem; min-width: 100px; }
.inline-track { flex: 1; height: 5px; background: #f8fafc; border-radius: 99px; overflow: hidden; }
.inline-fill  { height: 100%; border-radius: 99px; transition: width 0.4s; }

.scroll-table-wrap { flex: 1; overflow: auto; border-radius: 10px; border: 1px solid #e2e8f0; }
.dtable { width: 100%; border-collapse: collapse; background: #ffffff; }
.dtable th { position: sticky; top: 0; z-index: 1; text-align: left; padding: 0.6rem 0.9rem; background: #f8fafc; color: #94a3b8; font-size: 0.62rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.dtable td { padding: 0.6rem 0.9rem; border-bottom: 1px solid #f1f5f9; font-size: 0.8rem; vertical-align: middle; }
.dtable tbody tr:last-child td { border-bottom: none; }
.dtable tbody tr:hover { background: #f8fafc; }
.tfoot-row td { padding: 0.65rem 0.9rem; background: #f8fafc; border-top: 1px solid #e2e8f0; font-size: 0.8rem; }

.status-chip { display:inline-block; padding:0.18rem 0.55rem; border-radius:5px; font-size:0.65rem; font-weight:700; text-transform:capitalize; }
.status-chip.pending { background:#fbbf2410; color:#d97706; border:1px solid #fbbf2425; }
.status-chip.paid    { background:#34d39910; color:#059669; border:1px solid #34d39925; }
.code-pill { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#7c3aed; background:#a78bfa10; border:1px solid #a78bfa25; padding:0.15rem 0.45rem; border-radius:4px; }
.pay-src   { font-size:0.68rem; color:#64748b; background:#f8fafc; padding:0.15rem 0.45rem; border-radius:4px; }

.confirm-btn { background:#e0f2fe; color:#0a7ea4; border:1px solid #bae6fd; padding:0.28rem 0.7rem; border-radius:5px; font-family:'Outfit',sans-serif; font-size:0.72rem; font-weight:600; cursor:pointer; transition:all 0.15s; white-space:nowrap; }
.confirm-btn:hover { background:#0a7ea4; color:#fff; }
.confirm-btn:disabled { opacity:0.35; cursor:not-allowed; }
.confirm-btn.wide { width:100%; padding:0.65rem; font-size:0.82rem; }
.ghost-btn { background:transparent; color:#64748b; border:1px solid #e2e8f0; padding:0.6rem 1.1rem; border-radius:6px; font-family:'Outfit',sans-serif; font-size:0.8rem; font-weight:600; cursor:pointer; }
.ghost-btn:hover { border-color:#64748b; }
.icon-btn { background:none; border:none; color:#94a3b8; cursor:pointer; padding:0.2rem; border-radius:3px; display:flex; align-items:center; transition:color 0.15s; }
.icon-btn:hover { color:#0a7ea4; }
.amt-wrap { display:flex; align-items:center; gap:0.4rem; }

.overlay { position:fixed; inset:0; background:rgba(0,0,0,0.65); backdrop-filter:blur(6px); display:flex; align-items:center; justify-content:center; z-index:2000; }
.modal { background:#ffffff; border:1px solid #e2e8f0; border-top:2px solid #0a7ea4; border-radius:12px; width:420px; padding:1.5rem; box-shadow:0 8px 30px rgba(0,0,0,0.12); }
.modal-head { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.1rem; padding-bottom:0.85rem; border-bottom:1px solid #e2e8f0; }
.modal-head h2 { font-size:0.95rem; font-weight:700; color:#0f172a; margin:0 0 0.15rem; }
.close-btn { background:none; border:none; font-size:1.3rem; color:#94a3b8; cursor:pointer; }
.modal-body { display:flex; flex-direction:column; gap:0.6rem; margin-bottom:1.1rem; }
.modal-foot { display:flex; justify-content:flex-end; gap:0.5rem; padding-top:0.85rem; border-top:1px solid #e2e8f0; }
.field-label { font-size:0.68rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; }
.amt-input { background:#f1f5f9; border:1px solid #e2e8f0; color:#0f172a; padding:0.6rem 0.8rem; border-radius:6px; font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:600; width:100%; box-sizing:border-box; }
.amt-input:focus { outline:none; border-color:#0a7ea4; }
.hint { font-size:0.7rem; color:#94a3b8; margin:0; }

.mono        { font-family: 'JetBrains Mono', monospace; }
.bold        { font-weight: 600; }
.dim         { color: #94a3b8; }
.sm          { font-size: 0.72rem; }
.accent-blue { color: #0a7ea4; }

::-webkit-scrollbar       { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>