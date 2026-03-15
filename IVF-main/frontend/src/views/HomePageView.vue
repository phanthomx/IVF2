<template>
  <div class="app">

    <!-- LANDING PAGE -->
    <main class="landing">
      <div class="badge">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        IVF Clinic Management System
      </div>

      <h1 class="headline">
        Compassionate Care,
        <span class="powered"> Powered</span><br/>
        <span class="precision">by Precision</span>
      </h1>

      <p class="subtext">
        A secure, all-in-one platform for managing IVF treatments,
        patient records, billing, and clinic operations.
      </p>

    </main>

  </div>
</template>

<script setup>
// No authentication or modal logic required
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.app {
  font-family: 'Inter', sans-serif;
  background: #f0f4f5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.app::before {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(
    ellipse 80% 60% at 50% 40%,
    rgba(255,255,255,.7) 0%,
    transparent 70%
  );
  pointer-events: none;
  z-index: 0;
}

/* LANDING */
.landing {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 24px 120px;
  position: relative;
  z-index: 1;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 18px;
  border-radius: 100px;
  border: 1.5px solid #c8ddd8;
  background: rgba(255,255,255,.7);
  color: #2a9d8f;
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: .04em;
  margin-bottom: 44px;
  backdrop-filter: blur(4px);
}

.badge svg {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

.headline {
  font-size: clamp(40px, 6vw, 68px);
  font-weight: 800;
  line-height: 1.12;
  color: #1a2b4a;
  letter-spacing: -.02em;
  max-width: 760px;
  margin-bottom: 28px;
}

.headline .powered { color: #2e5fa3; }
.headline .precision { color: #2a9d8f; }

.subtext {
  font-size: clamp(15px, 1.8vw, 18px);
  color: #7a8fa6;
  line-height: 1.7;
  max-width: 500px;
  margin-bottom: 48px;
}
</style>