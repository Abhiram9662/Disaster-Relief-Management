/**
 * Disaster Relief Coordination Dashboard Application.
 */

class ReliefApp {
  constructor() {
    this.currentTab = 'dashboard';
    this.isSimulatedOffline = false;
    this.lastHlc = 0;
    this.mapData = null;
    this.init();
  }

  async init() {
    this.setupTabs();
    this.setupActions();
    this.setupSMS();
    this.setupMatching();
    this.setupBenchmarks();
    this.setupSync();
    await this.refreshAll();

    // Periodic poll every 5 seconds if online
    setInterval(() => {
      if (!this.isSimulatedOffline) {
        this.fetchSummary();
      }
    }, 5000);
  }

  setupTabs() {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        const target = tab.dataset.target;
        this.currentTab = target;
        document.getElementById(target).classList.add('active');

        if (target === 'dashboard' && this.mapData) {
          this.renderMap(this.mapData);
        }
      });
    });
  }

  setupActions() {
    // Seed demo button
    const seedBtn = document.getElementById('seedDemoBtn');
    if (seedBtn) {
      seedBtn.addEventListener('click', async () => {
        const scenario = document.getElementById('seedScenarioSelect').value || 'S1';
        seedBtn.disabled = true;
        seedBtn.innerText = 'Seeding...';
        try {
          const res = await fetch(`/api/simulation/seed-demo?scenario=${scenario}`, { method: 'POST' });
          const data = await res.json();
          this.showToast(`Seeded ${data.scenario}: ${data.volunteers_count} volunteers, ${data.needs_count} needs (${data.total_slots} slots).`);
          await this.refreshAll();
        } catch (err) {
          this.showToast('Failed to seed scenario: ' + err.message, 'error');
        } finally {
          seedBtn.disabled = false;
          seedBtn.innerText = 'Seed Scenario';
        }
      });
    }

    // Toggle offline simulation
    const offlineToggle = document.getElementById('offlineToggleBtn');
    if (offlineToggle) {
      offlineToggle.addEventListener('click', () => {
        this.isSimulatedOffline = !this.isSimulatedOffline;
        const statusBadge = document.getElementById('nodeStatusBadge');
        if (this.isSimulatedOffline) {
          offlineToggle.classList.add('btn-danger');
          offlineToggle.innerText = 'Go Online';
          statusBadge.className = 'status-pill offline';
          statusBadge.innerText = '● Offline Camp Node Replica';
          this.showToast('Node in Offline Mode. Using local replica & queued writes.', 'warning');
        } else {
          offlineToggle.classList.remove('btn-danger');
          offlineToggle.innerText = 'Simulate Offline';
          statusBadge.className = 'status-pill online';
          statusBadge.innerText = '● Online (Connected)';
          this.showToast('Node Connected. Synchronizing with cloud/peers...', 'success');
          if (window.pwaStore) window.pwaStore.flushQueue();
          this.refreshAll();
        }
      });
    }
  }

  async refreshAll() {
    await Promise.all([
      this.fetchSummary(),
      this.fetchVolunteers(),
      this.fetchNeeds(),
      this.fetchMapData()
    ]);
  }

  async fetchSummary() {
    try {
      const res = await fetch('/api/dashboard/summary');
      const data = await res.json();
      this.updateSummaryUI(data);
    } catch (err) {
      console.warn('Summary fetch failed:', err);
    }
  }

  updateSummaryUI(data) {
    document.getElementById('statTotalVols').innerText = data.total_volunteers;
    document.getElementById('statAvailVols').innerText = data.available_volunteers;
    document.getElementById('statAssignedVols').innerText = data.assigned_volunteers;

    document.getElementById('statTotalNeeds').innerText = data.total_needs;
    document.getElementById('statOpenNeeds').innerText = data.open_needs;
    document.getElementById('statCriticalNeeds').innerText = data.critical_needs_count;

    document.getElementById('statTotalSlots').innerText = data.total_slots;
    document.getElementById('statFilledSlots').innerText = data.filled_slots;
    document.getElementById('statCoverageRate').innerText = `${data.coverage_rate}%`;

    // Category breakdowns
    const cb = data.category_breakdown || {};
    for (const [cat, stats] of Object.entries(cb)) {
      const elV = document.getElementById(`cat_${cat}_vols`);
      const elN = document.getElementById(`cat_${cat}_needs`);
      const elBar = document.getElementById(`cat_${cat}_bar`);
      if (elV) elV.innerText = `${stats.volunteers_available} ready`;
      if (elN) elN.innerText = `${stats.slots_filled}/${stats.slots_required} slots filled`;
      if (elBar) {
        const pct = stats.slots_required > 0 ? (stats.slots_filled / stats.slots_required) * 100 : 0;
        elBar.style.width = `${Math.min(100, pct)}%`;
      }
    }
  }

  async fetchVolunteers() {
    try {
      const res = await fetch('/api/volunteers');
      const vols = await res.json();
      const listEl = document.getElementById('volunteersTableBody');
      if (!listEl) return;
      listEl.innerHTML = vols.slice(0, 15).map(v => `
        <tr>
          <td><strong>${v.id}</strong></td>
          <td>${v.name}</td>
          <td>${v.skills.map(s => `<span class="tag tag-${s}">${s}</span>`).join(' ')}</td>
          <td>${v.languages.join(', ')}</td>
          <td>(${v.latitude.toFixed(2)}, ${v.longitude.toFixed(2)})</td>
          <td>${v.start_time}:00 - ${v.end_time}:00</td>
          <td><span class="status-badge status-${v.status}">${v.status}</span></td>
        </tr>
      `).join('');
      if (vols.length > 15) {
        listEl.innerHTML += `<tr><td colspan="7" class="text-center text-muted">...and ${vols.length - 15} more registered volunteers</td></tr>`;
      }
    } catch (err) {
      console.warn('Volunteers fetch error:', err);
    }
  }

  async fetchNeeds() {
    try {
      const res = await fetch('/api/needs');
      const needs = await res.json();
      const listEl = document.getElementById('needsTableBody');
      if (!listEl) return;
      listEl.innerHTML = needs.slice(0, 15).map(n => `
        <tr>
          <td><strong>${n.id}</strong></td>
          <td>${n.title}</td>
          <td><span class="tag tag-${n.category}">${n.category}</span></td>
          <td><span class="urgency-badge urgency-${n.urgency}">Level ${n.urgency}</span></td>
          <td>${n.filled_slots} / ${n.required_head_count}</td>
          <td>${n.required_language}</td>
          <td><span class="status-badge status-${n.status}">${n.status}</span></td>
        </tr>
      `).join('');
      if (needs.length > 15) {
        listEl.innerHTML += `<tr><td colspan="7" class="text-center text-muted">...and ${needs.length - 15} more open need requests</td></tr>`;
      }
    } catch (err) {
      console.warn('Needs fetch error:', err);
    }
  }

  async fetchMapData() {
    try {
      const res = await fetch('/api/dashboard/map');
      this.mapData = await res.json();
      this.renderMap(this.mapData);
    } catch (err) {
      console.warn('Map fetch error:', err);
    }
  }

  renderMap(data) {
    const canvas = document.getElementById('disasterMapCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    // Background grid
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    const step = width / 10;
    for (let x = 0; x <= width; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let y = 0; y <= height; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // Coordinate conversion function (maps 0-50 km or 31.0-31.5 lat to canvas)
    let minX = 0, maxX = 50, minY = 0, maxY = 50;
    // Check if coordinates are geographic lat/long
    if (data.volunteers.length > 0 && data.volunteers[0].lat > 25.0) {
      minX = 31.0; maxX = 31.5; minY = 75.5; maxY = 76.0;
    }

    const toCanvasX = (lat) => ((lat - minX) / (maxX - minX)) * (width - 40) + 20;
    const toCanvasY = (lon) => ((lon - minY) / (maxY - minY)) * (height - 40) + 20;

    // Draw Camps
    data.camps.forEach(c => {
      const cx = toCanvasX(c.lat);
      const cy = toCanvasY(c.lon);

      // Camp radius zone
      ctx.beginPath();
      ctx.arc(cx, cy, 35, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(59, 130, 246, 0.12)';
      ctx.fill();
      ctx.strokeStyle = '#3b82f6';
      ctx.stroke();

      // Camp icon
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(cx, cy, 8, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#e2e8f0';
      ctx.font = '10px Inter, sans-serif';
      ctx.fillText(`⛺ ${c.name}`, cx - 25, cy - 12);
    });

    // Draw Volunteers
    data.volunteers.forEach(v => {
      const vx = toCanvasX(v.lat);
      const vy = toCanvasY(v.lon);
      ctx.beginPath();
      ctx.arc(vx, vy, 4, 0, Math.PI * 2);
      ctx.fillStyle = v.status === 'assigned' ? '#10b981' : '#38bdf8';
      ctx.fill();
    });

    // Draw Needs
    data.needs.forEach(n => {
      const nx = toCanvasX(n.lat);
      const ny = toCanvasY(n.lon);

      ctx.fillStyle = n.urgency === 4 ? '#ef4444' : (n.urgency === 3 ? '#f97316' : '#eab308');
      ctx.fillRect(nx - 4, ny - 4, 8, 8);

      if (n.urgency >= 3) {
        ctx.strokeStyle = ctx.fillStyle;
        ctx.beginPath();
        ctx.arc(nx, ny, 10, 0, Math.PI * 2);
        ctx.stroke();
      }
    });

    // Legend
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.fillRect(10, height - 35, width - 20, 25);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.fillText('● Blue: Available Vol   ● Green: Assigned Vol   ■ Red/Orange: Urgent Need   ⛺ Blue Ring: Relief Camp', 20, height - 18);
  }

  // --- Matching Console ---
  setupMatching() {
    const runBtn = document.getElementById('runMatchingBtn');
    if (!runBtn) return;

    // Synchronize slider values
    ['alpha', 'beta', 'gamma', 'eta', 'rmax'].forEach(param => {
      const slider = document.getElementById(`slider_${param}`);
      const valDisplay = document.getElementById(`val_${param}`);
      if (slider && valDisplay) {
        slider.addEventListener('input', () => {
          valDisplay.innerText = slider.value;
        });
      }
    });

    runBtn.addEventListener('click', async () => {
      const algo = document.getElementById('matchingAlgoSelect').value;
      const alpha = parseFloat(document.getElementById('slider_alpha').value);
      const beta = parseFloat(document.getElementById('slider_beta').value);
      const gamma = parseFloat(document.getElementById('slider_gamma').value);
      const eta = parseFloat(document.getElementById('slider_eta').value);
      const r_max_km = parseFloat(document.getElementById('slider_rmax').value);

      runBtn.disabled = true;
      runBtn.innerText = 'Solving Assignment...';

      try {
        const res = await fetch('/api/match', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            algorithm: algo,
            alpha: alpha,
            beta: beta,
            gamma: gamma,
            eta: eta,
            r_max_km: r_max_km
          })
        });
        const data = await res.json();
        this.renderMatchingResults(data);
        this.showToast(`Matching complete via ${algo.toUpperCase()}: ${data.assignments.length} assignments proposed.`);
        await this.refreshAll();
      } catch (err) {
        this.showToast('Matching failed: ' + err.message, 'error');
      } finally {
        runBtn.disabled = false;
        runBtn.innerText = 'Execute Matching Engine';
      }
    });
  }

  renderMatchingResults(data) {
    document.getElementById('matchStatCoverage').innerText = `${data.qualified_coverage_percent}%`;
    document.getElementById('matchStatPrecision').innerText = `${data.skill_precision_percent}%`;
    document.getElementById('matchStatDistance').innerText = `${data.mean_distance_km} km`;
    document.getElementById('matchStatUtility').innerText = data.total_utility;
    document.getElementById('matchStatRuntime').innerText = `${data.runtime_ms} ms`;

    const tbody = document.getElementById('assignmentsTableBody');
    if (!tbody) return;

    if (!data.assignments || data.assignments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No feasible assignments found for current constraints.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.assignments.map(a => {
      const b = a.breakdown || {};
      const breakdownText = `S:${b.skill_match || 1} P:${(b.proximity || 0).toFixed(2)} (${(b.distance_km || 0).toFixed(1)}km) A:${(b.availability_coverage || 0).toFixed(2)} L:${b.language_match || 0}`;
      return `
        <tr>
          <td><strong>${a.assignment_id}</strong></td>
          <td>${a.volunteer_name} <span class="text-muted">(${a.volunteer_id})</span></td>
          <td>${a.need_id} <span class="text-muted">(${a.slot_id})</span></td>
          <td><span class="tag tag-${a.category}">${a.category}</span></td>
          <td><strong>${a.score.toFixed(3)}</strong></td>
          <td><small class="text-muted">${breakdownText}</small></td>
          <td>
            ${a.status === 'confirmed'
              ? '<span class="status-badge status-assigned">Locked</span>'
              : `<button class="btn btn-sm btn-primary confirm-btn" data-id="${a.assignment_id}">Confirm & Lock</button>`
            }
          </td>
        </tr>
      `;
    }).join('');

    // Attach confirm event listeners
    tbody.querySelectorAll('.confirm-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const asgnId = btn.dataset.id;
        btn.disabled = true;
        btn.innerText = 'Locking...';
        try {
          const res = await fetch(`/api/assignments/${asgnId}/confirm`, { method: 'POST' });
          if (res.ok) {
            btn.parentElement.innerHTML = '<span class="status-badge status-assigned">Locked</span>';
            this.showToast(`Assignment ${asgnId} confirmed & locked!`);
            await this.refreshAll();
          }
        } catch (err) {
          this.showToast('Confirmation failed: ' + err.message, 'error');
          btn.disabled = false;
        }
      });
    });
  }

  // --- SMS Gateway Simulator ---
  setupSMS() {
    const input = document.getElementById('smsInputText');
    const sendBtn = document.getElementById('smsSendBtn');
    const byteCounter = document.getElementById('smsByteCount');
    const logContainer = document.getElementById('smsChatLog');

    if (!input || !sendBtn) return;

    input.addEventListener('input', () => {
      const len = new TextEncoder().encode(input.value).length;
      byteCounter.innerText = `${len} / 160 bytes`;
      if (len > 160) {
        byteCounter.style.color = '#ef4444';
      } else {
        byteCounter.style.color = '#94a3b8';
      }
    });

    sendBtn.addEventListener('click', async () => {
      const text = input.value.trim();
      if (!text) return;

      const sender = document.getElementById('smsSenderPhone').value || '+919876543210';

      // Render outgoing message
      const outDiv = document.createElement('div');
      outDiv.className = 'sms-bubble sms-out';
      outDiv.innerHTML = `<div class="sms-sender">From: ${sender}</div><div>${this.escapeHtml(text)}</div><div class="sms-meta">${text.length} chars (${new TextEncoder().encode(text).length} bytes)</div>`;
      logContainer.appendChild(outDiv);
      logContainer.scrollTop = logContainer.scrollHeight;

      try {
        const res = await fetch('/api/sms', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sender: sender, message: text })
        });
        const data = await res.json();

        // Render incoming reply
        const inDiv = document.createElement('div');
        inDiv.className = 'sms-bubble sms-in';
        inDiv.innerHTML = `<div class="sms-sender">Gateway Response (${data.parsed_type})</div><div>${this.escapeHtml(data.response_sms)}</div><div class="sms-meta">${data.response_sms.length} chars (${new TextEncoder().encode(data.response_sms).length} bytes)</div>`;
        logContainer.appendChild(inDiv);
        logContainer.scrollTop = logContainer.scrollHeight;

        this.showToast(`SMS processed: ${data.parsed_type}`);
        await this.refreshAll();
      } catch (err) {
        this.showToast('SMS transmission error: ' + err.message, 'error');
      }
    });

    // SMS Sample Templates
    document.querySelectorAll('.sms-sample-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        input.value = btn.dataset.sms;
        input.dispatchEvent(new Event('input'));
      });
    });
  }

  // --- Research Benchmarks Runner (Table 2, 3, 4) ---
  setupBenchmarks() {
    const runBtn = document.getElementById('runResearchBenchmarksBtn');
    if (!runBtn) return;

    runBtn.addEventListener('click', async () => {
      const seeds = parseInt(document.getElementById('benchSeedsSelect').value || '10');
      runBtn.disabled = true;
      runBtn.innerText = `Running ${seeds} seeds benchmark...`;

      try {
        const res = await fetch(`/api/simulation/run-benchmarks?seeds=${seeds}`);
        const data = await res.json();
        this.renderTable2(data.table2_matching);
        this.renderTable3(data.table3_bandwidth);
        this.renderTable4(data.table4_translation);
        this.showToast(`Benchmark reproduction complete over ${seeds} random seeds!`, 'success');
      } catch (err) {
        this.showToast('Benchmark run failed: ' + err.message, 'error');
      } finally {
        runBtn.disabled = false;
        runBtn.innerText = 'Run Research Benchmark Suite';
      }
    });
  }

  renderTable2(rows) {
    const tbody = document.getElementById('benchTable2Body');
    if (!tbody) return;
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td><strong>${r.Scenario}</strong></td>
        <td><span class="badge ${r.Method === 'Proposed' ? 'badge-success' : 'badge-info'}">${r.Method}</span></td>
        <td><strong>${r['Qualified coverage (%)']}</strong></td>
        <td>${r['Skill precision (%)']}%</td>
        <td>${r['Distance (km)']} km</td>
        <td>${r['Utility ratio (%)']}%</td>
        <td>${r['Runtime (ms)']} ms</td>
      </tr>
    `).join('');
  }

  renderTable3(rows) {
    const tbody = document.getElementById('benchTable3Body');
    if (!tbody) return;
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.Payload}</td>
        <td><strong>${r['Raw size (bytes)']}</strong></td>
        <td>${r['Compressed (bytes)']}</td>
      </tr>
    `).join('');
  }

  renderTable4(rows) {
    const tbody = document.getElementById('benchTable4Body');
    if (!tbody) return;
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td><strong>${r['Language pair']}</strong></td>
        <td>${r.BLEU}</td>
        <td>${r['chrF++']}</td>
        <td>${r.COMET}</td>
        <td>${r['Adequacy (1–5)']}</td>
        <td><strong class="text-success">${r['Critical-content preserved (%)']}</strong></td>
      </tr>
    `).join('');
  }

  // --- Sync Inspector ---
  setupSync() {
    const exportBtn = document.getElementById('exportDeltaBtn');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', async () => {
      try {
        const res = await fetch(`/api/sync/delta?from_hlc=${this.lastHlc}`);
        const data = await res.json();
        document.getElementById('syncDeltaRawSize').innerText = `${data.raw_size_bytes} bytes`;
        document.getElementById('syncDeltaCompSize').innerText = `${data.compressed_size_bytes} bytes`;
        document.getElementById('syncDeltaRatio').innerText = `${data.compression_ratio}x`;
        document.getElementById('syncDeltaJsonView').innerText = JSON.stringify(data.delta, null, 2);
        this.lastHlc = data.delta.to_hlc;
        this.showToast(`Delta exported: ${data.compressed_size_bytes} bytes transferred (zlib level 9).`);
      } catch (err) {
        this.showToast('Delta export failed: ' + err.message, 'error');
      }
    });
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
      }, 3500);
    }, 10);
  }

  escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.appDashboard = new ReliefApp();
});
