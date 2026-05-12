// ============================================================
// AI Text Analyzer
// Lambda Function URL 
// ============================================================
const API_URL = 'https://fqsvppzcm7mlft55l7jb6d5zru0muoci.lambda-url.us-east-1.on.aws/';

// ===== Character Counter =====
const textInput = document.getElementById('textInput');
const charCount = document.getElementById('charCount');

textInput.addEventListener('input', () => {
  const len = textInput.value.length;
  charCount.textContent = `${len} character${len !== 1 ? 's' : ''}`;
});

// ===== Allow Ctrl+Enter to submit =====
textInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && e.ctrlKey) analyzeText();
});

// ===== Main Analyze Function =====
async function analyzeText() {
  const text = textInput.value.trim();

  if (!text) {
    showError('Please enter some text to analyze.');
    return;
  }

  if (text.length < 10) {
    showError('Please enter at least 10 characters for a meaningful analysis.');
    return;
  }

  setLoading(true);
  hideResults();
  hideError();

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data = await response.json();

    // CA's Lambda returns body as a JSON string inside the response
    let result = data;
    if (typeof data.body === 'string') {
      result = JSON.parse(data.body);
    } else if (data.body && typeof data.body === 'object') {
      result = data.body;
    }

    displayResults(result);

  } catch (err) {
    console.error('Analysis error:', err);
    showError('Could not connect to the analysis backend. Details: ' + err.message);
  } finally {
    setLoading(false);
  }
}

// ===== Display Results =====
// CA's Lambda response structure:
// result.sentiment      -> { overall, confidence, scores: { Positive, Negative, Neutral, Mixed }, positiveWords, negativeWords }
// result.entities       -> [ { text, type, position, confidence } ]
// result.keyPhrases     -> [ { text, confidence } ]
// result.textStatistics -> { wordCount, sentenceCount, avgWordsPerSentence, readabilityScore, readabilityLevel }

function displayResults(result) {

  // ── Sentiment ──────────────────────────────────────────
  const sentiment = result.sentiment || {};
  const overall = sentiment.overall || 'NEUTRAL';
  const confidence = sentiment.confidence || '';
  const scores = sentiment.scores || {};

  document.getElementById('sentimentValue').textContent = capitalize(overall);
  document.getElementById('sentimentConfidence').textContent = confidence ? `Confidence: ${confidence}` : '';

  // Color the badge
  const badge = document.getElementById('sentimentValue');
  if (overall === 'POSITIVE') badge.style.color = 'var(--pos-color)';
  else if (overall === 'NEGATIVE') badge.style.color = 'var(--neg-color)';
  else if (overall === 'MIXED') badge.style.color = 'var(--mix-color)';
  else badge.style.color = 'var(--neu-color)';

  // Scores come as strings like "45.5%" — parse them
  setBarFromString('posBar', 'posScore', scores.Positive || '0%');
  setBarFromString('neuBar', 'neuScore', scores.Neutral  || '0%');
  setBarFromString('negBar', 'negScore', scores.Negative || '0%');
  setBarFromString('mixBar', 'mixScore', scores.Mixed    || '0%');

  // ── Readability ────────────────────────────────────────
  const stats = result.textStatistics || {};
  const score = Math.round(stats.readabilityScore || 0);

  document.getElementById('readScore').textContent = score;
  document.getElementById('readLevel').textContent = stats.readabilityLevel || '—';
  document.getElementById('wordCount').textContent = stats.wordCount || '—';
  document.getElementById('sentCount').textContent = stats.sentenceCount || '—';
  document.getElementById('avgWps').textContent    = stats.avgWordsPerSentence || '—';

  // Donut chart — circumference = 2π×32 ≈ 201
  const circ = 201;
  const filled = (score / 100) * circ;
  document.getElementById('donutCircle').setAttribute('stroke-dasharray', `${filled} ${circ - filled}`);

  // ── Entities ───────────────────────────────────────────
  const entities = result.entities || [];
  renderEntities(entities);

  // ── Key Phrases ────────────────────────────────────────
  const phrases = result.keyPhrases || [];
  renderPhrases(phrases);

  // Show results section
  document.getElementById('results').classList.remove('hidden');
}

// ===== Render Entities =====
function renderEntities(entities) {
  const container = document.getElementById('entitiesList');
  container.innerHTML = '';

  if (!entities || entities.length === 0) {
    container.innerHTML = '<span class="empty-msg">No entities detected</span>';
    return;
  }

  entities.forEach((e, i) => {
    const text = e.text || '';
    const type = e.type || 'OTHER';

    const tag = document.createElement('span');
    tag.className = `tag tag-${type}`;
    tag.style.animationDelay = `${i * 0.05}s`;
    tag.title = `${type} · ${e.confidence || ''}`;

    const dot = document.createElement('span');
    dot.className = 'tag-dot';
    dot.style.background = dotColor(type);

    const label = document.createElement('span');
    label.textContent = text;

    tag.appendChild(dot);
    tag.appendChild(label);
    container.appendChild(tag);
  });
}

// ===== Render Key Phrases =====
function renderPhrases(phrases) {
  const container = document.getElementById('phrasesList');
  container.innerHTML = '';

  if (!phrases || phrases.length === 0) {
    container.innerHTML = '<span class="empty-msg">No key phrases detected</span>';
    return;
  }

  phrases.forEach((p, i) => {
    // CA's format: { text: "...", confidence: "85%" }
    const text = typeof p === 'string' ? p : (p.text || '');
    const conf = typeof p === 'object' ? (p.confidence || '') : '';

    const tag = document.createElement('span');
    tag.className = 'tag tag-phrase';
    tag.style.animationDelay = `${i * 0.05}s`;
    if (conf) tag.title = `Confidence: ${conf}`;
    tag.textContent = text;
    container.appendChild(tag);
  });
}

// ===== Reset =====
function resetForm() {
  textInput.value = '';
  charCount.textContent = '0 characters';
  hideResults();
  hideError();
  textInput.focus();
}

// ===== Helpers =====
function setLoading(on) {
  document.getElementById('loadingState').classList.toggle('hidden', !on);
  document.getElementById('analyzeBtn').disabled = on;
}

function hideResults() {
  document.getElementById('results').classList.add('hidden');
}

function showError(msg) {
  document.getElementById('errorMsg').textContent = msg;
  document.getElementById('errorState').classList.remove('hidden');
}

function hideError() {
  document.getElementById('errorState').classList.add('hidden');
}

// Parse score strings like "45.5%" and set bar width + label
function setBarFromString(barId, pctId, pctStr) {
  const val = parseFloat(pctStr) || 0;
  document.getElementById(barId).style.width = `${val}%`;
  document.getElementById(pctId).textContent = `${val}%`;
}

function capitalize(str) {
  if (!str) return '—';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function dotColor(type) {
  const map = {
    PERSON: '#2D7A4F',
    ORGANIZATION: '#2C5FA3',
    LOCATION: '#8A5E1A',
    DATE: '#6E3A8A',
    EMAIL: '#1A6A7A',
    URL: '#3A6A1A',
    NUMBER: '#7A5A00',
  };
  return map[type] || '#A8A59E';
}
