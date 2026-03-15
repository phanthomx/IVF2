<template>
  <div class="dashboard">

    <!-- Header -->
    <header class="header">
      <div>
        <p class="eyebrow">Clinical Command Center</p>
        <h1>Doctor <span class="accent">Dashboard</span></h1>
      </div>
      <div class="header-actions">
        <input type="date" v-model="selectedDate" class="date-input" />
        <button @click="activeTab = 'queue'" :class="['tab-btn', activeTab === 'queue' ? 'active' : '']">Queue</button>
        <button @click="activeTab = 'history'" :class="['tab-btn', activeTab === 'history' ? 'active' : '']">History</button>
        <button @click="activeTab = 'availability'" :class="['tab-btn', activeTab === 'availability' ? 'active' : '']">Availability</button>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <label>Today's Patients</label>
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
    </div>

    <!-- QUEUE TAB -->
    <section v-if="activeTab === 'queue'" class="section">
      <div class="section-header">
        <h2>Patient Queue — {{ selectedDate }}</h2>
        <span class="badge">{{ queue.length }}</span>
      </div>
      <div v-if="loadingQueue" class="empty">Loading queue...</div>
      <div v-else-if="queue.length === 0" class="empty">No patients scheduled for this date.</div>
      <div v-else class="queue-grid">
        <div
          v-for="entry in queue"
          :key="entry.appointment_id"
          class="patient-card"
          @click="openConsultation(entry)"
        >
          <div class="card-top">
            <div>
              <div class="patient-name">{{ entry.patient_name }}</div>
              <div class="mono muted sm">{{ entry.service_id }}</div>
            </div>
            <span :class="['status-tag', entry.status]">{{ entry.status }}</span>
          </div>
          <div class="card-meta">
            <span class="meta-item">{{ entry.start_time }} – {{ entry.end_time }}</span>
            <span class="meta-item">Day {{ entry.cycle_day }}</span>
            <span v-if="entry.is_walkin" class="meta-item walkin-tag">Walk-in</span>
          </div>
          <div class="card-stage">
            <span class="stage-tag">{{ entry.current_stage }}</span>
          </div>
          <div class="card-vitals" v-if="entry.age || entry.blood_type">
            <span v-if="entry.age" class="vital">Age {{ entry.age }}</span>
            <span v-if="entry.blood_type" class="vital">{{ entry.blood_type }}</span>
          </div>
          <div class="card-footer">
            <button class="notes-peek-btn" @click.stop="openQueueVisitDetail(entry)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              View Notes &amp; Prescription
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- HISTORY TAB -->
    <section v-if="activeTab === 'history'" class="section">
      <div class="section-header">
        <h2>Patient History</h2>
      </div>
      <div class="search-row">
        <input
          v-model="historySearch"
          placeholder="Search patient by name or service ID..."
          class="search-input"
          @input="filterHistoryPatients"
        />
      </div>
      <div v-if="filteredHistoryPatients.length && historySearch && !selectedHistoryPatient" class="dropdown standalone">
        <div v-for="p in filteredHistoryPatients" :key="p.id" class="dropdown-item" @click="loadPatientHistory(p)">
          <span class="bold">{{ p.name }}</span>
          <span class="mono muted sm">{{ p.service_id }}</span>
        </div>
      </div>
      <div v-if="historyLoading" class="empty">Loading...</div>
      <div v-else-if="patientHistory" class="history-panel">
        <div class="profile-card">
          <div class="profile-left">
            <div class="avatar">{{ patientHistory.patient.name.charAt(0) }}</div>
            <div>
              <div class="patient-name">{{ patientHistory.patient.name }}</div>
              <div class="mono muted sm">{{ patientHistory.patient.service_id }}</div>
            </div>
          </div>
          <div class="profile-stats">
            <div class="p-stat"><label>Age</label><span>{{ patientHistory.patient.age || '—' }}</span></div>
            <div class="p-stat"><label>Height</label><span>{{ patientHistory.patient.height_cm ? patientHistory.patient.height_cm + ' cm' : '—' }}</span></div>
            <div class="p-stat"><label>Weight</label><span>{{ patientHistory.patient.weight_kg ? patientHistory.patient.weight_kg + ' kg' : '—' }}</span></div>
            <div class="p-stat"><label>Blood</label><span>{{ patientHistory.patient.blood_type || '—' }}</span></div>
            <div class="p-stat"><label>Stage</label><span class="accent">{{ patientHistory.patient.current_cycle_stage }}</span></div>
          </div>
        </div>

        <div class="section-header" style="margin-top:1.5rem">
          <h2>Visit History</h2>
          <span class="badge">{{ patientHistory.history.length }}</span>
        </div>
        <div v-if="patientHistory.history.length === 0" class="empty">No visits recorded.</div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Date</th><th>Time</th><th>Stage</th><th>Status</th><th>Notes</th><th>Prescription</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="visit in patientHistory.history" :key="visit.appointment_id" class="clickable-row" @click="openVisitDetail(visit)">
              <td class="mono sm">{{ visit.date }}</td>
              <td class="mono sm muted">{{ visit.start_time }}</td>
              <td><span class="stage-tag">{{ visit.stage || '—' }}</span></td>
              <td><span :class="['status-tag', visit.status]">{{ visit.status }}</span></td>
              <td class="notes-cell">{{ visit.clinical_notes || '—' }}</td>
              <td>
                <button v-if="visit.prescription || visit.clinical_notes" class="view-btn" @click.stop="openVisitDetail(visit)">View</button>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!historySearch" class="empty">Search for a patient above to view their history.</div>
    </section>

    <!-- AVAILABILITY TAB -->
    <section v-if="activeTab === 'availability'" class="section">
      <div class="section-header">
        <h2>Weekly Availability</h2>
        <button @click="saveAvailability" class="add-btn sm-btn">Save Schedule</button>
      </div>
      <p class="hint">Set your working hours for each day. Weekends are off by default.</p>
      <div class="avail-grid">
        <div v-for="day in weekDays" :key="day.value" :class="['avail-card', day.value >= 5 ? 'weekend' : '', availForm[day.value].enabled ? 'enabled' : '']">
          <div class="avail-top">
            <span class="day-name">{{ day.label }}</span>
            <div :class="['toggle', availForm[day.value].enabled ? 'on' : '']" @click="toggleDay(day.value)">
              <div class="toggle-knob"></div>
            </div>
          </div>
          <div v-if="availForm[day.value].enabled" class="avail-times">
            <div class="field">
              <label>Start</label>
              <input type="time" v-model="availForm[day.value].start_time" />
            </div>
            <div class="field">
              <label>End</label>
              <input type="time" v-model="availForm[day.value].end_time" />
            </div>
            <div class="field">
              <label>Slot (min)</label>
              <select v-model.number="availForm[day.value].slot_duration_minutes">
                <option :value="15">15</option>
                <option :value="20">20</option>
                <option :value="30">30</option>
                <option :value="45">45</option>
                <option :value="60">60</option>
              </select>
            </div>
          </div>
          <div v-else class="avail-off">Off</div>
        </div>
      </div>
    </section>

    <!-- CONSULTATION MODAL -->
    <div v-if="showConsultation" class="overlay" @click.self="showConsultation = false">
      <div class="modal consult-modal">
        <div class="modal-head">
          <div>
            <h2>{{ consultation.patient_name }}</h2>
            <span class="mono muted sm">{{ consultation.service_id }} · Day {{ consultation.cycle_day }}</span>
          </div>
          <div class="head-right">
            <span :class="['status-tag', consultation.status]">{{ consultation.status }}</span>
            <button @click="showConsultation = false" class="close">×</button>
          </div>
        </div>

        <div class="consult-body">
          <!-- Left: Stage tracker + actions -->
          <div class="consult-left">
            <h3>IVF Stage Progress</h3>
            <div class="stage-tracker">
              <div
                v-for="(stage, idx) in ivfStages"
                :key="stage"
                :class="['stage-step', getStageClass(stage, idx)]"
              >
                <div class="step-dot">
                  <span v-if="isStageCompleted(idx)">✓</span>
                  <span v-else-if="isStageActive(stage)">●</span>
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <div class="step-label">{{ stage }}</div>
              </div>
            </div>

            <div class="session-controls">
              <button
                v-if="consultation.status === 'waiting'"
                @click="startSession"
                class="start-btn"
                :disabled="sessionLoading"
              >
                {{ sessionLoading ? 'Starting...' : 'Start Session' }}
              </button>
              <button
                v-if="consultation.status === 'in-session'"
                @click="completeSession"
                class="complete-btn"
                :disabled="sessionLoading"
              >
                {{ sessionLoading ? 'Saving...' : 'Complete & Trigger Billing' }}
              </button>
              <div v-if="consultation.status === 'completed'" class="completed-banner">
                Session Completed
              </div>
            </div>
          </div>

          <!-- Right: Notes + Prescription -->
          <div class="consult-right">
            <div class="notes-section">
              <h3>Clinical Notes</h3>
              <textarea
                v-model="consultForm.clinical_notes"
                placeholder="Enter clinical observations, findings, and notes..."
                class="notes-area"
                :disabled="consultation.status === 'completed'"
                rows="6"
              ></textarea>
            </div>

            <div class="notes-section">
              <div class="rx-header">
                <h3>Prescription / Protocol</h3>
                <button
                  v-if="consultation.status !== 'completed'"
                  @click="runAICheck"
                  :disabled="aiChecking || !consultForm.prescription.trim()"
                  class="ai-check-btn"
                >
                  <svg v-if="!aiChecking" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 8v4l3 3"/><circle cx="18" cy="6" r="3" fill="currentColor" stroke="none"/></svg>
                  <span v-if="aiChecking" class="ai-spinner"></span>
                  {{ aiChecking ? 'Checking...' : 'AI Check' }}
                </button>
              </div>

              <div class="rx-split" :class="{ 'has-suggestion': aiSuggestion }">
                <!-- Doctor's draft -->
                <textarea
                  v-model="consultForm.prescription"
                  placeholder="Enter medications, dosages, and protocols..."
                  class="notes-area"
                  :disabled="consultation.status === 'completed'"
                  rows="6"
                ></textarea>

                <!-- AI suggestion panel -->
                <transition name="slide-in">
                  <div v-if="aiSuggestion" class="ai-panel">
                    <div class="ai-panel-head">
                      <div class="ai-panel-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
                        AI Suggestions
                        <span class="ai-count">{{ aiSuggestion.suggestions.length }}</span>
                      </div>
                      <button @click="dismissAI" class="ai-dismiss">✕</button>
                    </div>

                    <div v-if="!aiSuggestion.has_suggestions" class="ai-clean">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      Prescription looks good — no errors found.
                    </div>

                    <div v-else>
                      <div
                        v-for="(s, i) in aiSuggestion.suggestions"
                        :key="i"
                        class="ai-suggestion-item"
                        :class="{ dismissed: dismissedSuggestions.has(i) }"
                      >
                        <div v-if="!dismissedSuggestions.has(i)">
                          <div class="suggestion-diff">
                            <span class="diff-old">{{ s.original }}</span>
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                            <span class="diff-new">{{ s.corrected }}</span>
                          </div>
                          <div class="suggestion-reason">{{ s.reason }}</div>
                          <div class="suggestion-actions">
                            <button @click="acceptSuggestion(i, s)" class="accept-btn">
                              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                              Accept
                            </button>
                            <button @click="rejectSuggestion(i)" class="reject-btn">
                              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                              Reject
                            </button>
                          </div>
                        </div>
                        <div v-else class="dismissed-label">
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                          Suggestion rejected
                        </div>
                      </div>

                      <button
                        v-if="pendingSuggestions.length > 0"
                        @click="acceptAllSuggestions"
                        class="accept-all-btn"
                      >
                        Accept All ({{ pendingSuggestions.length }})
                      </button>
                    </div>
                  </div>
                </transition>
              </div>
              <div v-if="aiError" class="ai-error">{{ aiError }}</div>
            </div>

            <div class="advance-toggle">
              <label class="toggle-label">
                <div :class="['toggle', consultForm.advance_stage ? 'on' : '']" @click="consultForm.advance_stage = !consultForm.advance_stage">
                  <div class="toggle-knob"></div>
                </div>
                Advance patient to next IVF stage on completion
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VISIT DETAIL MODAL -->
    <div v-if="showVisitDetail" class="overlay" @click.self="showVisitDetail = false">
      <div class="modal visit-modal">
        <div class="modal-head">
          <div>
            <h2>{{ selectedVisit.patient_name || 'Visit Record' }}</h2>
            <div class="visit-meta-row">
              <span v-if="selectedVisit.date" class="visit-meta-chip">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                {{ selectedVisit.date }}
              </span>
              <span v-if="selectedVisit.start_time" class="visit-meta-chip">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ selectedVisit.start_time }}
              </span>
              <span v-if="selectedVisit.stage || selectedVisit.current_stage" class="stage-tag">
                {{ selectedVisit.stage || selectedVisit.current_stage }}
              </span>
            </div>
          </div>
          <div class="head-right">
            <span v-if="selectedVisit.status" :class="['status-tag', selectedVisit.status]">{{ selectedVisit.status }}</span>
            <button @click="showVisitDetail = false" class="close">×</button>
          </div>
        </div>

        <div class="visit-body">
          <!-- Clinical Notes -->
          <div class="visit-section">
            <div class="visit-section-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0a7ea4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              Clinical Notes
            </div>
            <div v-if="selectedVisit.clinical_notes" class="visit-content">{{ selectedVisit.clinical_notes }}</div>
            <div v-else class="visit-empty">No clinical notes recorded for this visit.</div>
          </div>

          <!-- Prescription -->
          <div class="visit-section">
            <div class="visit-section-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>
              Prescription / Protocol
              <span v-if="selectedVisit.is_finalized" class="finalized-badge">Finalized</span>
            </div>
            <div v-if="selectedVisit.prescription" class="visit-content rx-content">{{ selectedVisit.prescription }}</div>
            <div v-else class="visit-empty">No prescription issued for this visit.</div>
          </div>
        </div>
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

// ── Auth headers ───────────────────────────────────────────────────────────
const getAuthHeaders = () => ({
  withCredentials: true,
  headers: {
    'Authentication-Token': authStore.getToken(),
    'Content-Type': 'application/json'
  }
});

// ── State ──────────────────────────────────────────────────────────────────
const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
const selectedDate   = ref(today);
const activeTab      = ref('queue');
const queue          = ref([]);
const loadingQueue   = ref(false);
const sessionLoading = ref(false);

// History
const historySearch           = ref('');
const allPatients             = ref([]);
const filteredHistoryPatients = ref([]);
const selectedHistoryPatient  = ref(null);
const patientHistory          = ref(null);
const historyLoading          = ref(false);

// Consultation modal
const showConsultation = ref(false);
const consultation     = ref({});
const consultForm      = ref({ clinical_notes: '', prescription: '', advance_stage: true });

// AI prescription check
const aiChecking          = ref(false);
const aiSuggestion        = ref(null);   // { has_suggestions, corrected_text, suggestions[] }
const aiError             = ref('');
const dismissedSuggestions = ref(new Set());

// Visit detail modal
const showVisitDetail = ref(false);
const selectedVisit   = ref({});

const ivfStages = [
  'Onboarding',
  'Baseline Assessment',
  'Stimulation Protocol',
  'Mid-Cycle Monitoring',
  'Trigger Administration',
  'Retrieval Procedure',
  'Transfer Procedure'
];

// Availability
const weekDays = [
  { label: 'Monday',    value: 0 },
  { label: 'Tuesday',   value: 1 },
  { label: 'Wednesday', value: 2 },
  { label: 'Thursday',  value: 3 },
  { label: 'Friday',    value: 4 },
  { label: 'Saturday',  value: 5 },
  { label: 'Sunday',    value: 6 },
];

const defaultAvail = () => ({
  enabled: false, start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30
});

const availForm = ref({
  0: { enabled: true,  start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30 },
  1: { enabled: true,  start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30 },
  2: { enabled: true,  start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30 },
  3: { enabled: true,  start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30 },
  4: { enabled: true,  start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30 },
  5: defaultAvail(),
  6: defaultAvail(),
});

// ── Queue ──────────────────────────────────────────────────────────────────
const fetchQueue = async () => {
  loadingQueue.value = true;
  try {
    const res   = await axios.get(`${BASE}/api/v1/doctor/queue/${selectedDate.value}`, getAuthHeaders());
    queue.value = res.data.queue ?? [];
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load queue.");
  } finally {
    loadingQueue.value = false;
  }
};

// ── Stage helpers ──────────────────────────────────────────────────────────
const getStageClass = (stage, idx) => {
  const currentIdx = ivfStages.indexOf(consultation.value.current_stage);
  if (idx < currentIdx) return 'completed';
  if (stage === consultation.value.current_stage) return 'active';
  return 'pending';
};

const isStageCompleted = (idx) => {
  const currentIdx = ivfStages.indexOf(consultation.value.current_stage);
  return idx < currentIdx;
};

const isStageActive = (stage) => stage === consultation.value.current_stage;

// ── Consultation ───────────────────────────────────────────────────────────
const openConsultation = (entry) => {
  consultation.value      = { ...entry };
  consultForm.value       = { clinical_notes: '', prescription: '', advance_stage: true };
  aiSuggestion.value      = null;
  aiError.value           = '';
  dismissedSuggestions.value = new Set();
  showConsultation.value  = true;
};

const openQueueVisitDetail = async (entry) => {
  // For queue cards, fetch the patient's last completed visit notes
  try {
    const res = await axios.get(`${BASE}/api/v1/doctor/patient/${entry.patient_id}`, getAuthHeaders());
    const history = res.data.history ?? [];
    // Find most recent completed visit with notes or prescription
    const lastVisit = history.find(v => v.clinical_notes || v.prescription) || history[0];
    if (lastVisit) {
      selectedVisit.value = {
        ...lastVisit,
        patient_name:  entry.patient_name,
        current_stage: entry.current_stage,
      };
    } else {
      selectedVisit.value = {
        patient_name:   entry.patient_name,
        date:           selectedDate.value,
        start_time:     entry.start_time,
        stage:          entry.current_stage,
        current_stage:  entry.current_stage,
        status:         entry.status,
        clinical_notes: null,
        prescription:   null,
      };
    }
    showVisitDetail.value = true;
  } catch {
    messageStore.setFlashMessage("Could not load visit details.");
  }
};

const openVisitDetail = (visit) => {
  selectedVisit.value   = { ...visit };
  showVisitDetail.value = true;
};

// ── AI Prescription Check ──────────────────────────────────────────────────
const pendingSuggestions = computed(() =>
  (aiSuggestion.value?.suggestions || []).filter((_, i) => !dismissedSuggestions.value.has(i))
);

const runAICheck = async () => {
  if (!consultForm.value.prescription.trim()) return;
  aiChecking.value = true;
  aiError.value    = '';
  aiSuggestion.value = null;
  dismissedSuggestions.value = new Set();

  try {
    const res = await axios.post(
      `${BASE}/api/v1/doctor/prescription/ai-check`,
      {
        prescription_text: consultForm.value.prescription,
        patient_context: {
          age:        consultation.value.age,
          stage:      consultation.value.current_stage,
          blood_type: consultation.value.blood_type,
        }
      },
      getAuthHeaders()
    );
    aiSuggestion.value = res.data;
  } catch (err) {
    aiError.value = err.response?.data?.message || "AI check failed. Please try again.";
  } finally {
    aiChecking.value = false;
  }
};

const acceptSuggestion = (index, suggestion) => {
  // Replace the specific fragment in the draft
  consultForm.value.prescription = consultForm.value.prescription.replace(
    suggestion.original,
    suggestion.corrected
  );
  dismissedSuggestions.value = new Set([...dismissedSuggestions.value, index]);
};

const rejectSuggestion = (index) => {
  dismissedSuggestions.value = new Set([...dismissedSuggestions.value, index]);
};

const acceptAllSuggestions = () => {
  if (!aiSuggestion.value) return;
  // Apply all non-dismissed suggestions in order
  let text = consultForm.value.prescription;
  aiSuggestion.value.suggestions.forEach((s, i) => {
    if (!dismissedSuggestions.value.has(i)) {
      text = text.replace(s.original, s.corrected);
    }
  });
  consultForm.value.prescription = text;
  // Dismiss all
  const allIndexes = aiSuggestion.value.suggestions.map((_, i) => i);
  dismissedSuggestions.value = new Set(allIndexes);
};

const dismissAI = () => {
  aiSuggestion.value = null;
  aiError.value = '';
};

const startSession = async () => {
  sessionLoading.value = true;
  try {
    await axios.post(
      `${BASE}/api/v1/doctor/appointment/${consultation.value.appointment_id}/start`,
      {},
      getAuthHeaders()
    );
    consultation.value.status = 'in-session';
    messageStore.setFlashMessage("Session started.");
    fetchQueue();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to start session.");
  } finally {
    sessionLoading.value = false;
  }
};

const completeSession = async () => {
  if (!consultForm.value.clinical_notes.trim()) {
    messageStore.setFlashMessage("Please add clinical notes before completing.");
    return;
  }
  sessionLoading.value = true;
  try {
    const res = await axios.post(
      `${BASE}/api/v1/doctor/appointment/${consultation.value.appointment_id}/complete`,
      consultForm.value,
      getAuthHeaders()
    );
    consultation.value.status = 'completed';
    messageStore.setFlashMessage(`Session complete — ${res.data.new_stage} stage. Invoice pushed.`);
    showConsultation.value = false;
    fetchQueue();
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to complete session.");
  } finally {
    sessionLoading.value = false;
  }
};

// ── History ────────────────────────────────────────────────────────────────
// ✅ Fixed: use the doctor's own patients endpoint instead of receptionist's
const fetchAllPatients = async () => {
  try {
    const res = await axios.get(`${BASE}/api/v1/doctor/patients`, getAuthHeaders());
    allPatients.value = res.data.patients ?? [];
  } catch {
    // Fallback: extract unique patients from the current queue
    allPatients.value = queue.value.map(q => ({
      id:         q.patient_id,
      name:       q.patient_name,
      service_id: q.service_id
    }));
  }
};

const filterHistoryPatients = () => {
  const q = historySearch.value.toLowerCase();
  if (!q) { filteredHistoryPatients.value = []; return; }
  filteredHistoryPatients.value = allPatients.value.filter(p =>
    p.name.toLowerCase().includes(q) || p.service_id.toLowerCase().includes(q)
  ).slice(0, 6);
};

const loadPatientHistory = async (patient) => {
  selectedHistoryPatient.value  = patient;
  historySearch.value           = `${patient.name} (${patient.service_id})`;
  filteredHistoryPatients.value = [];
  historyLoading.value          = true;
  try {
    const res            = await axios.get(`${BASE}/api/v1/doctor/patient/${patient.id}`, getAuthHeaders());
    patientHistory.value = res.data;
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to load patient history.");
  } finally {
    historyLoading.value = false;
  }
};

// ── Availability ───────────────────────────────────────────────────────────
const fetchAvailability = async () => {
  try {
    const res = await axios.get(`${BASE}/api/v1/doctor/availability`, getAuthHeaders());
    weekDays.forEach(d => { availForm.value[d.value] = defaultAvail(); });
    res.data.availability.forEach(a => {
      availForm.value[a.day_of_week] = {
        enabled:               true,
        start_time:            a.start_time,
        end_time:              a.end_time,
        slot_duration_minutes: a.slot_duration_minutes
      };
    });
  } catch { /* silent */ }
};

const toggleDay = (dayValue) => {
  if (dayValue >= 5 && !availForm.value[dayValue].enabled) {
    if (!confirm("Enable weekend availability?")) return;
  }
  availForm.value[dayValue].enabled = !availForm.value[dayValue].enabled;
};

const saveAvailability = async () => {
  const slots = weekDays
    .filter(d => availForm.value[d.value].enabled)
    .map(d => ({
      day_of_week:           d.value,
      start_time:            availForm.value[d.value].start_time,
      end_time:              availForm.value[d.value].end_time,
      slot_duration_minutes: availForm.value[d.value].slot_duration_minutes
    }));

  try {
    await axios.post(`${BASE}/api/v1/doctor/availability`, { slots }, getAuthHeaders());
    messageStore.setFlashMessage("Availability saved successfully!");
  } catch (err) {
    messageStore.setFlashMessage(err.response?.data?.message || "Failed to save availability.");
  }
};

watch(selectedDate, fetchQueue);
watch(activeTab, (tab) => {
  if (tab === 'history')      fetchAllPatients();
  if (tab === 'availability') fetchAvailability();
});

onMounted(() => { fetchQueue(); });
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
.date-input { background: #fff; border: 1px solid #dde6f0; color: #1a2535; padding: 0.6rem 0.9rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; }
.tab-btn { background: #fff; border: 1px solid #dde6f0; color: #64748b; padding: 0.55rem 1rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.tab-btn.active { background: #0a7ea4; color: #fff; border-color: #0a7ea4; }
.tab-btn:hover:not(.active) { border-color: #94a3b8; }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
.stat-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.1rem 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.stat-card label { font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; display: block; margin-bottom: 0.3rem; }
.value { font-size: 1.9rem; font-weight: 700; line-height: 1; }
.value.blue   { color: #2563eb; }
.value.yellow { color: #d97706; }
.value.teal   { color: #0a7ea4; }
.value.green  { color: #059669; }

/* Section */
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.section-header h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin: 0; }
.badge { background: #e2e8f0; color: #64748b; font-size: 0.68rem; font-family: 'IBM Plex Mono', monospace; padding: 0.1rem 0.5rem; border-radius: 20px; }
.hint { font-size: 0.78rem; color: #94a3b8; margin: -0.25rem 0 1rem; }

/* Queue Grid */
.queue-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.patient-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.25rem; cursor: pointer; transition: all 0.15s; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.patient-card:hover { border-color: #0a7ea4; box-shadow: 0 4px 12px rgba(10,126,164,0.1); transform: translateY(-1px); }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
.patient-name { font-weight: 700; font-size: 0.95rem; color: #1a2535; }
.card-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.6rem; }
.meta-item { font-size: 0.72rem; color: #64748b; }
.walkin-tag { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.68rem; font-weight: 600; }
.card-stage { margin-bottom: 0.5rem; }
.card-vitals { display: flex; gap: 0.5rem; }
.vital { font-size: 0.7rem; background: #f1f5f9; color: #64748b; padding: 0.15rem 0.5rem; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; }

/* Tags */
.status-tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 5px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; text-transform: capitalize; }
.status-tag.waiting    { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.status-tag.in-session { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.status-tag.completed  { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; }
.status-tag.cancelled  { background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
.stage-tag { font-size: 0.72rem; color: #0a7ea4; background: #eff9fc; border: 1px solid #bae6fd; padding: 0.18rem 0.5rem; border-radius: 4px; }
.rx-tag { font-size: 0.72rem; color: #059669; background: #f0fdf4; border: 1px solid #a7f3d0; padding: 0.18rem 0.5rem; border-radius: 4px; }

/* Table */
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; border: 1px solid #dde6f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.table th { text-align: left; padding: 0.7rem 1rem; background: #f8fafc; color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }
.table td { padding: 0.8rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.84rem; vertical-align: middle; }
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }
.notes-cell { max-width: 200px; font-size: 0.76rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* History */
.search-row { margin-bottom: 0.5rem; }
.search-input { width: 100%; background: #fff; border: 1px solid #dde6f0; color: #1a2535; padding: 0.7rem 1rem; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; box-sizing: border-box; }
.search-input:focus { outline: none; border-color: #0a7ea4; }
.dropdown.standalone { background: #fff; border: 1px solid #dde6f0; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); margin-bottom: 1rem; }
.dropdown-item { display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 1rem; cursor: pointer; font-size: 0.84rem; }
.dropdown-item:hover { background: #f0f5f9; }

/* Profile card */
.profile-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1.25rem 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.profile-left { display: flex; align-items: center; gap: 1rem; }
.avatar { width: 44px; height: 44px; background: #eff9fc; border: 2px solid #bae6fd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 700; color: #0a7ea4; }
.profile-stats { display: flex; gap: 1.5rem; }
.p-stat { display: flex; flex-direction: column; gap: 0.15rem; }
.p-stat label { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; }
.p-stat span { font-size: 0.84rem; font-weight: 600; color: #1a2535; }

/* Availability */
.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.75rem; }
.avail-card { background: #fff; border: 1px solid #dde6f0; border-radius: 10px; padding: 1rem; transition: all 0.15s; }
.avail-card.weekend { background: #f8fafc; border-style: dashed; }
.avail-card.enabled { border-color: #bae6fd; background: #f8fdff; }
.avail-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.day-name { font-size: 0.78rem; font-weight: 700; color: #1a2535; }
.avail-times { display: flex; flex-direction: column; gap: 0.5rem; }
.avail-off { font-size: 0.72rem; color: #cbd5e1; text-align: center; padding: 0.5rem 0; }

/* Toggle */
.toggle { width: 36px; height: 20px; background: #e2e8f0; border-radius: 10px; cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle.on { background: #0a7ea4; }
.toggle-knob { width: 14px; height: 14px; background: #fff; border-radius: 50%; position: absolute; top: 3px; left: 3px; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.toggle.on .toggle-knob { left: 19px; }
.advance-toggle { display: flex; align-items: center; margin-top: 0.5rem; }
.toggle-label { display: flex; align-items: center; gap: 0.75rem; font-size: 0.82rem; color: #64748b; cursor: pointer; }

/* Buttons */
.add-btn { background: #0a7ea4; color: #fff; border: none; padding: 0.65rem 1.2rem; border-radius: 7px; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.84rem; cursor: pointer; transition: opacity 0.15s; }
.add-btn:hover { opacity: 0.88; }
.sm-btn { padding: 0.45rem 1rem; font-size: 0.78rem; }

/* Empty */
.empty { padding: 2rem; text-align: center; color: #94a3b8; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 0.84rem; }

/* Modal */
.overlay { position: fixed; inset: 0; background: rgba(15,23,42,0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; padding: 1rem; }
.modal { background: #fff; border-top: 3px solid #0a7ea4; border-radius: 12px; width: 100%; max-width: 860px; max-height: 90vh; overflow-y: auto; padding: 1.75rem; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }
.modal-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9; }
.modal-head h2 { font-size: 1.1rem; font-weight: 700; margin: 0 0 0.2rem; }
.head-right { display: flex; align-items: center; gap: 0.75rem; }
.close { background: none; border: none; font-size: 1.4rem; color: #94a3b8; cursor: pointer; }

/* Consultation layout */
.consult-body { display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; }
.consult-left h3, .consult-right h3 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0 0 0.75rem; }

/* Stage tracker */
.stage-tracker { display: flex; flex-direction: column; gap: 0; margin-bottom: 1.5rem; }
.stage-step { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; position: relative; }
.stage-step:not(:last-child)::after { content: ''; position: absolute; left: 13px; top: 32px; width: 2px; height: 100%; background: #e2e8f0; z-index: 0; }
.stage-step.completed::after { background: #059669; }
.stage-step.active::after { background: #bae6fd; }
.step-dot { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; z-index: 1; border: 2px solid #e2e8f0; background: #fff; color: #94a3b8; }
.stage-step.completed .step-dot { background: #059669; border-color: #059669; color: #fff; }
.stage-step.active .step-dot { background: #0a7ea4; border-color: #0a7ea4; color: #fff; box-shadow: 0 0 0 4px rgba(10,126,164,0.15); }
.step-label { font-size: 0.8rem; color: #94a3b8; }
.stage-step.completed .step-label { color: #059669; font-weight: 600; }
.stage-step.active .step-label { color: #0a7ea4; font-weight: 700; }

/* Session controls */
.session-controls { margin-top: 1rem; }
.start-btn { width: 100%; background: #2563eb; color: #fff; border: none; padding: 0.8rem; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: opacity 0.15s; }
.start-btn:hover { opacity: 0.88; }
.start-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.complete-btn { width: 100%; background: #059669; color: #fff; border: none; padding: 0.8rem; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: opacity 0.15s; }
.complete-btn:hover { opacity: 0.88; }
.complete-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.completed-banner { background: #f0fdf4; border: 1px solid #a7f3d0; color: #059669; padding: 0.8rem; border-radius: 8px; text-align: center; font-weight: 700; font-size: 0.9rem; }

/* Notes */
.notes-section { margin-bottom: 1rem; }
.notes-area { width: 100%; background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.75rem; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 0.84rem; resize: vertical; transition: border-color 0.15s; box-sizing: border-box; }
.notes-area:focus { outline: none; border-color: #0a7ea4; background: #fff; }
.notes-area:disabled { background: #f1f5f9; color: #94a3b8; cursor: not-allowed; }

/* Form fields */
.field { display: flex; flex-direction: column; gap: 0.25rem; }
.field label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #94a3b8; }
.field input, .field select { background: #f8fafc; border: 1px solid #e2e8f0; color: #1a2535; padding: 0.4rem 0.5rem; border-radius: 5px; font-family: 'DM Sans', sans-serif; font-size: 0.78rem; }
.field input:focus, .field select:focus { outline: none; border-color: #0a7ea4; }

/* ── AI Prescription Check ─────────────────────────────────────────── */
.rx-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.rx-header h3 { margin: 0; }

.ai-check-btn {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: #f5f3ff; color: #7c3aed;
  border: 1px solid #ddd6fe; padding: 0.35rem 0.85rem;
  border-radius: 6px; font-family: 'DM Sans', sans-serif;
  font-size: 0.78rem; font-weight: 600; cursor: pointer;
  transition: all 0.15s;
}
.ai-check-btn:hover:not(:disabled) { background: #7c3aed; color: #fff; border-color: #7c3aed; }
.ai-check-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.ai-spinner {
  display: inline-block; width: 11px; height: 11px;
  border: 2px solid #ddd6fe; border-top-color: #7c3aed;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Split layout: textarea + AI panel side by side */
.rx-split { display: grid; grid-template-columns: 1fr; gap: 0.75rem; transition: grid-template-columns 0.25s ease; }
.rx-split.has-suggestion { grid-template-columns: 1fr 1fr; }

/* AI panel */
.ai-panel {
  background: #faf5ff; border: 1px solid #e9d5ff;
  border-radius: 8px; padding: 0.9rem; overflow-y: auto;
  max-height: 200px; display: flex; flex-direction: column; gap: 0.6rem;
}
.ai-panel-head { display: flex; justify-content: space-between; align-items: center; }
.ai-panel-title { display: flex; align-items: center; gap: 0.4rem; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #7c3aed; }
.ai-count { background: #7c3aed; color: #fff; font-size: 0.62rem; padding: 0.05rem 0.4rem; border-radius: 10px; }
.ai-dismiss { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 0.9rem; padding: 0; line-height: 1; }
.ai-dismiss:hover { color: #64748b; }

.ai-clean { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: #059669; font-weight: 600; }

.ai-suggestion-item {
  background: #fff; border: 1px solid #e9d5ff; border-radius: 7px;
  padding: 0.65rem 0.75rem; display: flex; flex-direction: column; gap: 0.4rem;
}
.ai-suggestion-item.dismissed { opacity: 0.5; }
.dismissed-label { font-size: 0.72rem; color: #94a3b8; display: flex; align-items: center; gap: 0.3rem; }

.suggestion-diff { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.diff-old { font-size: 0.78rem; color: #dc2626; background: #fef2f2; padding: 0.1rem 0.35rem; border-radius: 3px; text-decoration: line-through; font-family: 'IBM Plex Mono', monospace; }
.diff-new { font-size: 0.78rem; color: #059669; background: #f0fdf4; padding: 0.1rem 0.35rem; border-radius: 3px; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }
.suggestion-reason { font-size: 0.73rem; color: #64748b; line-height: 1.4; }

.suggestion-actions { display: flex; gap: 0.4rem; }
.accept-btn {
  display: inline-flex; align-items: center; gap: 0.3rem;
  background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0;
  padding: 0.25rem 0.6rem; border-radius: 5px;
  font-size: 0.72rem; font-weight: 600; cursor: pointer; font-family: 'DM Sans', sans-serif;
  transition: all 0.12s;
}
.accept-btn:hover { background: #059669; color: #fff; }
.reject-btn {
  display: inline-flex; align-items: center; gap: 0.3rem;
  background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3;
  padding: 0.25rem 0.6rem; border-radius: 5px;
  font-size: 0.72rem; font-weight: 600; cursor: pointer; font-family: 'DM Sans', sans-serif;
  transition: all 0.12s;
}
.reject-btn:hover { background: #e11d48; color: #fff; }

.accept-all-btn {
  width: 100%; margin-top: 0.25rem;
  background: #7c3aed; color: #fff; border: none;
  padding: 0.45rem; border-radius: 6px;
  font-family: 'DM Sans', sans-serif; font-size: 0.78rem; font-weight: 700;
  cursor: pointer; transition: opacity 0.15s;
}
.accept-all-btn:hover { opacity: 0.88; }

.ai-error { font-size: 0.76rem; color: #dc2626; margin-top: 0.35rem; }

/* Slide-in animation */
.slide-in-enter-active { animation: slideIn 0.2s ease; }
.slide-in-leave-active { animation: slideIn 0.15s ease reverse; }
@keyframes slideIn {
  from { opacity: 0; transform: translateX(8px); }
  to   { opacity: 1; transform: translateX(0); }
}


/* Visit detail modal */
.visit-modal { max-width: 640px; }
.visit-body { display: flex; flex-direction: column; gap: 1.25rem; }
.visit-section { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; }
.visit-section-label { display: flex; align-items: center; gap: 0.5rem; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 0.85rem; }
.visit-content { font-size: 0.88rem; color: #1a2535; line-height: 1.65; white-space: pre-wrap; background: #fff; border: 1px solid #e2e8f0; border-radius: 7px; padding: 1rem; }
.rx-content { border-color: #a7f3d0; background: #f0fdf4; color: #065f46; }
.visit-empty { font-size: 0.82rem; color: #94a3b8; font-style: italic; padding: 0.5rem 0; }
.finalized-badge { background: #f0fdf4; color: #059669; border: 1px solid #a7f3d0; font-size: 0.62rem; padding: 0.1rem 0.45rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.06em; margin-left: 0.4rem; }
.clickable-row { cursor: pointer; }
.card-footer { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #f1f5f9; }
.notes-peek-btn { display: flex; align-items: center; gap: 0.4rem; background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; padding: 0.35rem 0.75rem; border-radius: 5px; font-size: 0.72rem; font-weight: 600; cursor: pointer; transition: all 0.15s; font-family: 'DM Sans', sans-serif; width: 100%; justify-content: center; }
.notes-peek-btn:hover { background: #eff9fc; color: #0a7ea4; border-color: #bae6fd; }
.visit-meta-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.35rem; flex-wrap: wrap; }
.visit-meta-chip { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.72rem; color: #64748b; background: #f1f5f9; padding: 0.2rem 0.55rem; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; }
.view-btn { background: #eff9fc; color: #0a7ea4; border: 1px solid #bae6fd; padding: 0.25rem 0.65rem; border-radius: 5px; font-size: 0.72rem; font-weight: 600; cursor: pointer; transition: all 0.15s; font-family: 'DM Sans', sans-serif; }
.view-btn:hover { background: #0a7ea4; color: #fff; }
.bold  { font-weight: 600; }
.muted { color: #94a3b8; }
.sm    { font-size: 0.76rem; }
</style>