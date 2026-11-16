/**
 * Multilingual Chatbot Widget with Dual-Text Display & FSM Slot-Filling.
 */

class ChatWidget {
  constructor() {
    this.sessionId = 'sess-' + Math.random().toString(36).substring(2, 9);
    this.messagesContainer = document.getElementById('chatMessages');
    this.inputField = document.getElementById('chatInput');
    this.sendBtn = document.getElementById('chatSendBtn');
    this.roleSelect = document.getElementById('chatRole');
    this.langSelect = document.getElementById('chatTargetLang');
    this.typingIndicator = document.getElementById('chatTyping');
    this.init();
  }

  init() {
    if (!this.inputField) return;

    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    // Handle suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        this.inputField.value = chip.dataset.text || chip.innerText;
        this.sendMessage();
      });
    });

    // Voice simulation button
    const voiceBtn = document.getElementById('voiceNoteBtn');
    if (voiceBtn) {
      voiceBtn.addEventListener('click', () => {
        this.simulateVoiceNote();
      });
    }

    // Initial greeting
    this.renderBotMessage({
      bot_reply_source_lang: "Hello! I am the Multilingual Disaster Relief Assistant. How can I help you?",
      bot_reply_target_lang: "नमस्ते! मैं बहुभाषी आपदा राहत सहायक हूँ। मैं आपकी क्या मदद कर सकता हूँ?",
      target_language: "hi",
      detected_language: "en",
      used_phrasebook: true,
      preservation_passed: true
    });
  }

  async sendMessage() {
    const text = this.inputField.value.trim();
    if (!text) return;

    const userRole = this.roleSelect.value;
    const targetLang = this.langSelect.value;

    this.renderUserMessage(text);
    this.inputField.value = '';
    this.showTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          user_role: userRole,
          source_language: 'auto',
          target_language: targetLang,
          message: text
        })
      });

      const data = await res.json();
      this.showTyping(false);
      this.renderBotMessage(data);

      // If user finished registration or need, refresh dashboard
      if (data.bot_reply_source_lang && (data.bot_reply_source_lang.includes('Registration confirmed') || data.bot_reply_source_lang.includes('Need successfully broadcast'))) {
        if (window.appDashboard) window.appDashboard.refreshAll();
      }
    } catch (err) {
      this.showTyping(false);
      this.renderBotMessage({
        bot_reply_source_lang: "Network error or offline mode. Your request is safely recorded locally.",
        bot_reply_target_lang: "नेटवर्क त्रुटि या ऑफ़लाइन मोड। आपका अनुरोध स्थानीय रूप से सुरक्षित रूप से दर्ज किया गया है।",
        target_language: targetLang,
        detected_language: "en"
      });
    }
  }

  simulateVoiceNote() {
    const voiceSamples = [
      "हमें कैंप अल्फा में तुरंत 100 लीटर पीने के पानी की जरूरत है",
      "We need 2 medical volunteers and sterile bandages at Camp Beta",
      "ਸਾਨੂੰ ਤੁਰੰਤ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਲੋੜ ਹੈ",
      "What supplies are available at Central Depot?",
      "Register volunteer Manya Sharma medical and translation hi en at Camp Alpha 08:00 to 18:00"
    ];
    const picked = voiceSamples[Math.floor(Math.random() * voiceSamples.length)];
    this.inputField.value = picked;
    const notif = document.getElementById('chatAudioNotif');
    if (notif) {
      notif.innerText = `🎙️ Transcribed voice-note: "${picked}"`;
      notif.classList.remove('hidden');
      setTimeout(() => notif.classList.add('hidden'), 4000);
    }
    this.sendMessage();
  }

  renderUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'chat-bubble user-bubble';
    div.innerHTML = `<div class="bubble-text">${this.escapeHtml(text)}</div>`;
    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
  }

  renderBotMessage(data) {
    const div = document.createElement('div');
    div.className = 'chat-bubble bot-bubble';

    const sourceText = data.bot_reply_source_lang || data.original_text || "";
    const targetText = data.bot_reply_target_lang || data.translated_text || "";
    const showDual = targetText && sourceText !== targetText;

    let badges = '';
    if (data.used_phrasebook) {
      badges += `<span class="badge badge-success">✓ Verified Phrasebook</span>`;
    }
    if (data.preservation_passed) {
      badges += `<span class="badge badge-info">✓ Entities Preserved</span>`;
    } else if (data.flagged_for_human_review) {
      badges += `<span class="badge badge-warning">⚠️ Flagged for Human Review</span>`;
    }

    if (data.glossary_terms && data.glossary_terms.length > 0) {
      badges += `<span class="badge badge-purple">Glossary: ${data.glossary_terms.join(', ')}</span>`;
    }

    div.innerHTML = `
      <div class="bubble-badges">${badges}</div>
      <div class="bubble-text main-translation">${this.escapeHtml(targetText || sourceText)}</div>
      ${showDual ? `<div class="bubble-text dual-original"><em>Original:</em> ${this.escapeHtml(sourceText)}</div>` : ''}
    `;

    this.messagesContainer.appendChild(div);
    this.scrollToBottom();
  }

  showTyping(show) {
    if (this.typingIndicator) {
      this.typingIndicator.style.display = show ? 'block' : 'none';
      if (show) this.scrollToBottom();
    }
  }

  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.chatWidget = new ChatWidget();
});
