/**
 * Multimodal Attendance & Engagement Agent - Frontend Client Controller
 * Manages live Camera, Web Audio, Face Detection Overlay, WebSockets, and UI Sync.
 */

let socket = null;
let webcamStream = null;
let audioContext = null;
let audioAnalyser = null;
let audioDataArray = null;
let isStreaming = false;
let simulationMode = false;
let simulationTimer = null;

// Tracked client-side telemetry state
let clientState = {
  assignedStudentId: "STU-1001",
  assignedStudentName: "Alex Chen",
  headPose: { yaw: 0.0, pitch: 0.0, roll: 0.0 },
  expression: "focused",
  motionLevel: 18.0,
  audioLevel: 35.0,
  isSpeech: false,
  faces: []
};

// Canvas references
const videoElem = document.getElementById('webcamVideo');
const canvasElem = document.getElementById('overlayCanvas');
let canvasCtx = null;

document.addEventListener('DOMContentLoaded', () => {
  if (canvasElem) {
    canvasCtx = canvasElem.getContext('2d');
  }
  initCharts();
  connectWebSocket();
  setupEventListeners();
});

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/stream`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    updateConnectionStatus(true);
    console.log("[WebSocket] Connected to Multimodal Classroom Intelligence Stream.");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'telemetry_response') {
        handleTelemetryResponse(data);
      }
    } catch (err) {
      console.error("[WebSocket] Parse error:", err);
    }
  };

  socket.onclose = () => {
    updateConnectionStatus(false);
    // Auto-reconnect after 2 seconds
    setTimeout(connectWebSocket, 2000);
  };

  socket.onerror = (err) => {
    console.warn("[WebSocket] Error:", err);
  };
}

function updateConnectionStatus(connected) {
  const badge = document.getElementById('connectionBadge');
  const dot = document.getElementById('connectionDot');
  const text = document.getElementById('connectionText');

  if (!badge) return;

  if (connected) {
    dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
    text.innerText = "STREAM ONLINE";
    badge.className = "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  } else {
    dot.className = "w-2.5 h-2.5 rounded-full bg-rose-400";
    text.innerText = "RECONNECTING...";
    badge.className = "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20";
  }
}

function setupEventListeners() {
  const btnStartCam = document.getElementById('btnStartCamera');
  const btnStopCam = document.getElementById('btnStopCamera');
  const btnSimulate = document.getElementById('btnToggleSimulation');
  const studentSelect = document.getElementById('studentProfileSelect');

  if (btnStartCam) {
    btnStartCam.addEventListener('click', startWebcam);
  }
  if (btnStopCam) {
    btnStopCam.addEventListener('click', stopWebcam);
  }
  if (btnSimulate) {
    btnSimulate.addEventListener('click', toggleSimulation);
  }
  if (studentSelect) {
    studentSelect.addEventListener('change', (e) => {
      clientState.assignedStudentId = e.target.value;
      const opt = e.target.options[e.target.selectedIndex];
      clientState.assignedStudentName = opt.text.split('(')[0].trim();
    });
  }

  // Quick scenario test buttons
  const btnScenario1 = document.getElementById('btnScenario1');
  const btnScenario2 = document.getElementById('btnScenario2');
  const btnScenario3 = document.getElementById('btnScenario3');

  if (btnScenario1) btnScenario1.addEventListener('click', runScenario1SustainedPresence);
  if (btnScenario2) btnScenario2.addEventListener('click', runScenario2AttentionDrop);
  if (btnScenario3) btnScenario3.addEventListener('click', runScenario3TeachingPrompt);
}

// --- Webcam & Audio Capture ---

async function startWebcam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: true
    });
    webcamStream = stream;
    videoElem.srcObject = stream;
    await videoElem.play();

    initAudioAnalysis(stream);
    isStreaming = true;
    simulationMode = false;

    document.getElementById('btnStartCamera').classList.add('hidden');
    document.getElementById('btnStopCamera').classList.remove('hidden');
    document.getElementById('cameraStatusBadge').innerText = "LIVE WEBCAM";
    document.getElementById('cameraStatusBadge').className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";

    // Start video processing loop
    requestAnimationFrame(processVideoFrame);
  } catch (err) {
    console.warn("Webcam access denied or unavailable, switching to Demo Simulation Mode:", err);
    toggleSimulation();
  }
}

function stopWebcam() {
  if (webcamStream) {
    webcamStream.getTracks().forEach(track => track.stop());
    webcamStream = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  isStreaming = false;

  document.getElementById('btnStartCamera').classList.remove('hidden');
  document.getElementById('btnStopCamera').classList.add('hidden');
  document.getElementById('cameraStatusBadge').innerText = "CAMERA OFF";
  document.getElementById('cameraStatusBadge').className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-slate-700 text-slate-300";

  if (canvasCtx) {
    canvasCtx.clearRect(0, 0, canvasElem.width, canvasElem.height);
  }
}

function initAudioAnalysis(stream) {
  try {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    audioAnalyser = audioContext.createAnalyser();
    audioAnalyser.fftSize = 256;
    source.connect(audioAnalyser);
    audioDataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
  } catch (e) {
    console.warn("Audio Context error:", e);
  }
}

function sampleAudioLevel() {
  if (!audioAnalyser || !audioDataArray) return { level: 25.0, isSpeech: false };
  audioAnalyser.getByteFrequencyData(audioDataArray);
  let sum = 0;
  for (let i = 0; i < audioDataArray.length; i++) {
    sum += audioDataArray[i];
  }
  const avg = sum / audioDataArray.length;
  const level = Math.min(100, (avg / 128.0) * 100);
  const isSpeech = level > 28.0;
  return { level, isSpeech };
}

// --- Video Processing & Overlays ---

let lastSendTime = 0;

async function processVideoFrame(timestamp) {
  if (!isStreaming) return;

  if (canvasElem && videoElem.videoWidth) {
    canvasElem.width = videoElem.videoWidth;
    canvasElem.height = videoElem.videoHeight;
    canvasCtx.clearRect(0, 0, canvasElem.width, canvasElem.height);

    // Primary detected participant box
    const boxW = 200;
    const boxH = 240;
    const boxX = (canvasElem.width - boxW) / 2;
    const boxY = (canvasElem.height - boxH) / 2 - 20;

    // Build face detection object
    clientState.faces = [{
      student_id: clientState.assignedStudentId,
      bbox: [boxX, boxY, boxW, boxH],
      confidence: 0.94
    }];

    // Sample audio
    const audioData = sampleAudioLevel();
    clientState.audioLevel = audioData.level;
    clientState.isSpeech = audioData.isSpeech;

    // Draw futuristic HUD on canvas
    drawFaceHUD(boxX, boxY, boxW, boxH);

    // Send packet via WebSocket at ~4Hz
    if (timestamp - lastSendTime > 250) {
      sendTelemetry();
      lastSendTime = timestamp;
    }
  }

  requestAnimationFrame(processVideoFrame);
}

function drawFaceHUD(x, y, w, h) {
  if (!canvasCtx) return;

  // Bounding bracket box
  canvasCtx.strokeStyle = '#6366f1';
  canvasCtx.lineWidth = 2.5;

  const bracketLength = 25;
  // Top-Left
  canvasCtx.beginPath();
  canvasCtx.moveTo(x, y + bracketLength);
  canvasCtx.lineTo(x, y);
  canvasCtx.lineTo(x + bracketLength, y);
  canvasCtx.stroke();

  // Top-Right
  canvasCtx.beginPath();
  canvasCtx.moveTo(x + w - bracketLength, y);
  canvasCtx.lineTo(x + w, y);
  canvasCtx.lineTo(x + w, y + bracketLength);
  canvasCtx.stroke();

  // Bottom-Left
  canvasCtx.beginPath();
  canvasCtx.moveTo(x, y + h - bracketLength);
  canvasCtx.lineTo(x, y + h);
  canvasCtx.lineTo(x + bracketLength, y + h);
  canvasCtx.stroke();

  // Bottom-Right
  canvasCtx.beginPath();
  canvasCtx.moveTo(x + w - bracketLength, y + h);
  canvasCtx.lineTo(x + w, y + h);
  canvasCtx.lineTo(x + w, y + h - bracketLength);
  canvasCtx.stroke();

  // Label tag above face
  canvasCtx.fillStyle = 'rgba(15, 23, 42, 0.85)';
  canvasCtx.fillRect(x, y - 48, w, 42);
  canvasCtx.strokeStyle = 'rgba(99, 102, 241, 0.4)';
  canvasCtx.strokeRect(x, y - 48, w, 42);

  canvasCtx.fillStyle = '#f8fafc';
  canvasCtx.font = 'bold 12px Inter, sans-serif';
  canvasCtx.fillText(`👤 ${clientState.assignedStudentName}`, x + 8, y - 28);

  canvasCtx.fillStyle = '#38bdf8';
  canvasCtx.font = '10px Inter, sans-serif';
  canvasCtx.fillText(`ID: ${clientState.assignedStudentId} • 94% Match`, x + 8, y - 12);
}

function sendTelemetry() {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  const packet = {
    type: "telemetry",
    faces: clientState.faces,
    assigned_student_id: clientState.assignedStudentId,
    audio_level: clientState.audioLevel,
    is_speech: clientState.isSpeech,
    head_pose: clientState.headPose,
    expression: clientState.expression,
    motion: clientState.motionLevel
  };

  socket.send(JSON.stringify(packet));
}

// --- Simulation Mode for Automated Demonstration ---

function toggleSimulation() {
  simulationMode = !simulationMode;
  const badge = document.getElementById('cameraStatusBadge');
  const btn = document.getElementById('btnToggleSimulation');

  if (simulationMode) {
    if (isStreaming) stopWebcam();
    btn.innerHTML = `<span class="flex items-center gap-1.5"><svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg> Stop Simulation</span>`;
    badge.innerText = "SIMULATED SESSION";
    badge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30";

    drawSimulatedVideo();

    simulationTimer = setInterval(() => {
      // Natural fluctuation around active state
      clientState.faces = [{
        student_id: clientState.assignedStudentId,
        bbox: [120, 80, 200, 240],
        confidence: 0.92
      }];
      clientState.audioLevel = 35 + (Math.random() * 25);
      clientState.isSpeech = Math.random() > 0.4;
      clientState.motionLevel = 15 + (Math.random() * 15);
      sendTelemetry();
    }, 400);

  } else {
    clearInterval(simulationTimer);
    btn.innerHTML = `<span class="flex items-center gap-1.5"><svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Simulate Classroom Stream</span>`;
    badge.innerText = "STANDBY";
    badge.className = "px-2.5 py-0.5 rounded text-xs font-semibold bg-slate-700 text-slate-300";
    if (canvasCtx) canvasCtx.clearRect(0, 0, canvasElem.width, canvasElem.height);
  }
}

function drawSimulatedVideo() {
  if (!canvasElem || !canvasCtx) return;
  canvasElem.width = 640;
  canvasElem.height = 420;

  // Render simulated classroom video backdrop
  const grad = canvasCtx.createLinearGradient(0, 0, 640, 420);
  grad.addColorStop(0, '#0f172a');
  grad.addColorStop(0.5, '#1e293b');
  grad.addColorStop(1, '#0f172a');
  canvasCtx.fillStyle = grad;
  canvasCtx.fillRect(0, 0, 640, 420);

  // Classroom student silhouette avatar
  canvasCtx.fillStyle = '#334155';
  canvasCtx.beginPath();
  canvasCtx.arc(320, 180, 60, 0, Math.PI * 2);
  canvasCtx.fill();

  canvasCtx.beginPath();
  canvasCtx.ellipse(320, 310, 110, 80, 0, 0, Math.PI * 2);
  canvasCtx.fill();

  drawFaceHUD(220, 100, 200, 240);
}

// --- Scenarios Automation for Mentor Demo ---

function runScenario1SustainedPresence() {
  // Scenario 1: Demonstrates Sustained Presence Attendance Tracking
  if (!simulationMode && !isStreaming) toggleSimulation();
  
  // Show notification
  showToast("Scenario 1 Activated", "Simulating continuous presence for Alex Chen (5s threshold)...", "emerald");
  
  // Ensure sustained presence for 6 seconds
  clientState.headPose = { yaw: 0, pitch: 0, roll: 0 };
  clientState.expression = "focused";
  clientState.motionLevel = 18.0;
}

function runScenario2AttentionDrop() {
  // Scenario 2: Engagement and Session Dynamics Analysis
  if (!simulationMode && !isStreaming) toggleSimulation();

  showToast("Scenario 2 Activated", "Simulating Attention Drop (Looking down at phone, prolonged silence)...", "amber");

  clientState.headPose = { yaw: -5, pitch: -28, roll: 0 }; // Looking down
  clientState.expression = "bored";
  clientState.audioLevel = 8.0;
  clientState.isSpeech = false;
  clientState.motionLevel = 4.0;
}

function runScenario3TeachingPrompt() {
  // Scenario 3: AI-Driven Teaching Suggestions
  if (!simulationMode && !isStreaming) toggleSimulation();

  showToast("Scenario 3 Activated", "Forcing pedagogical drop to trigger AI Teaching Suggestion Agent...", "indigo");

  clientState.headPose = { yaw: 32, pitch: -22, roll: 0 };
  clientState.expression = "distracted";
  clientState.audioLevel = 5.0;
  clientState.isSpeech = false;
  clientState.motionLevel = 2.0;
}

// --- WebSocket Telemetry Response Handler ---

function handleTelemetryResponse(data) {
  const fusion = data.fusion;
  const visual = data.visual;
  const audio = data.audio;
  const attendance = data.attendance;
  const suggestion = data.suggestion;

  // 1. Update Composite Score Gauge
  const scoreElem = document.getElementById('compositeScoreValue');
  const scoreStateElem = document.getElementById('compositeStateLabel');
  const scorePill = document.getElementById('compositeStatePill');

  if (scoreElem && fusion) {
    scoreElem.innerText = Math.round(fusion.overall_score);
    scoreStateElem.innerText = fusion.state_label;
    
    // Status color
    if (fusion.overall_score >= 75) {
      scorePill.className = "px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    } else if (fusion.overall_score >= 50) {
      scorePill.className = "px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30";
    } else if (fusion.overall_score >= 35) {
      scorePill.className = "px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30";
    } else {
      scorePill.className = "px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse";
    }
  }

  // 2. Update Metric Sliders / Bars
  if (visual) {
    updateMetricProgress('visualAttentionBar', 'visualAttentionVal', visual.visual_attention_score, visual.head_pose_label);
    updateMetricProgress('facialValenceBar', 'facialValenceVal', visual.facial_expression_score, visual.facial_expression_label);
    updateMetricProgress('motionDynamicsBar', 'motionDynamicsVal', visual.motion_score, visual.motion_label);
  }
  if (audio) {
    updateMetricProgress('audioActivityBar', 'audioActivityVal', audio.audio_engagement_score, audio.acoustic_state);
  }

  // 3. Update Chart.js Timeline
  if (fusion && visual && audio) {
    updateEngagementTimeline(fusion.overall_score, visual.visual_attention_score, audio.audio_engagement_score);
  }

  // 4. Update Attendance Table Roster
  if (attendance && attendance.roster) {
    updateAttendanceRosterUI(attendance);
  }

  // 5. Update AI Teaching Suggestions
  if (suggestion) {
    prependSuggestionCard(suggestion);
  }
}

function updateMetricProgress(barId, valId, score, label) {
  const bar = document.getElementById(barId);
  const val = document.getElementById(valId);
  if (bar) bar.style.width = `${Math.min(100, Math.max(0, score))}%`;
  if (val) val.innerText = `${Math.round(score)}% • ${label}`;
}

function updateAttendanceRosterUI(attendance) {
  const countPresent = document.getElementById('countPresent');
  const countTotal = document.getElementById('countTotal');
  if (countPresent) countPresent.innerText = attendance.total_present;
  if (countTotal) countTotal.innerText = attendance.total_enrolled;

  const tbody = document.getElementById('attendanceTableBody');
  if (!tbody) return;

  tbody.innerHTML = attendance.roster.map(stu => {
    let statusBadge = '';
    if (stu.status === 'PRESENT') {
      statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"><svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg> PRESENT</span>`;
    } else if (stu.status === 'PARTIAL') {
      statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">PARTIAL</span>`;
    } else {
      statusBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/60 text-slate-400 border border-slate-600/30">ABSENT</span>`;
    }

    const durationSec = stu.sustained_duration_seconds || 0.0;
    const progressPct = Math.min(100, (durationSec / 5.0) * 100);

    return `
      <tr class="border-b border-slate-700/50 hover:bg-slate-800/40 transition">
        <td class="py-2.5 px-3">
          <div class="font-medium text-slate-200">${stu.name}</div>
          <div class="text-xs text-slate-400">${stu.student_id} • ${stu.roll_no}</div>
        </td>
        <td class="py-2.5 px-3">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-slate-700 h-2 rounded-full overflow-hidden">
              <div class="bg-indigo-500 h-full rounded-full transition-all duration-300" style="width: ${progressPct}%"></div>
            </div>
            <span class="text-xs font-mono text-slate-300">${durationSec.toFixed(1)}s</span>
          </div>
        </td>
        <td class="py-2.5 px-3 text-right">
          ${statusBadge}
        </td>
      </tr>
    `;
  }).join('');
}

function prependSuggestionCard(suggestion) {
  const container = document.getElementById('suggestionsFeed');
  if (!container) return;

  // Check if card with same title already visible
  if (document.getElementById(`sugg-${suggestion.id}`)) return;

  const priorityColor = suggestion.priority === 'HIGH' 
    ? 'border-rose-500/40 bg-rose-950/20 text-rose-300'
    : (suggestion.priority === 'MEDIUM' ? 'border-amber-500/40 bg-amber-950/20 text-amber-300' : 'border-indigo-500/40 bg-indigo-950/20 text-indigo-300');

  const cardHtml = `
    <div id="sugg-${suggestion.id}" class="p-4 rounded-xl border ${priorityColor} mb-3 backdrop-blur-md transition-all duration-300 hover:shadow-lg">
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-white/10">
          ${suggestion.priority} PRIORITY • ${suggestion.type}
        </span>
        <button onclick="dismissSuggestion(${suggestion.id})" class="text-slate-400 hover:text-slate-200 text-sm">✕</button>
      </div>
      <h4 class="text-sm font-semibold text-white mb-1">${suggestion.title}</h4>
      <p class="text-xs text-slate-300 leading-relaxed mb-3">${suggestion.description}</p>
      <div class="flex items-center justify-between">
        <button onclick="applySuggestionAction('${suggestion.action}')" class="px-3 py-1 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition">
          ⚡ ${suggestion.action || 'Apply Recommendation'}
        </button>
        <span class="text-[10px] text-slate-400">Just now</span>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('afterbegin', cardHtml);
}

function dismissSuggestion(id) {
  const el = document.getElementById(`sugg-${id}`);
  if (el) el.remove();
  fetch(`/api/suggestions/${id}/dismiss`, { method: 'POST' }).catch(() => {});
}

function applySuggestionAction(actionName) {
  showToast("Pedagogical Action Triggered", `Instructor applied: "${actionName}"`, "indigo");
}

function showToast(title, message, color = "indigo") {
  const toast = document.createElement('div');
  toast.className = `fixed bottom-6 right-6 z-50 p-4 rounded-xl glass-panel border border-${color}-500/40 bg-slate-900/90 text-white shadow-2xl flex items-start gap-3 max-w-md animate-bounce`;
  toast.innerHTML = `
    <div class="p-2 rounded-lg bg-${color}-500/20 text-${color}-400">🔔</div>
    <div>
      <div class="text-sm font-semibold text-white">${title}</div>
      <div class="text-xs text-slate-300 mt-0.5">${message}</div>
    </div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}
