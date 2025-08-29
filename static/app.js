document.addEventListener("DOMContentLoaded", function () {
  // Global variables
  let sessionId =
    getSessionIdFromUrl() || window.SESSION_ID || generateSessionId();
  let currentAssistantText = ""; // For real-time chat history updates
  let selectedPersona = "developer"; // Default persona
  let currentStreamingMessage = null; // Track current streaming message in new UI
  let isConnecting = false; // Track connection state
  let isStreaming = false; // Track streaming state
  let allSessions = []; // Store all sessions
  let webSearchEnabled = false; // Track web search mode

  // DOM elements
  const toggleChatHistoryBtn = document.getElementById("toggleChatHistory");
  const chatHistoryContainer = document.getElementById("chatHistoryContainer");
  const personaSelect = document.getElementById("personaSelect");
  const webSearchToggle = document.getElementById("webSearchToggle");

  // New UI elements
  const chatMessages = document.getElementById("chatMessages");
  const personaName = document.getElementById("personaName");
  const personaAvatar = document.getElementById("personaAvatar");
  const newChatBtn = document.getElementById("newChatBtn");

  // Modal elements
  const conversationModal = document.getElementById("conversationModal");
  const closeModalBtn = document.getElementById("closeModal");
  const modalCloseBtn = document.getElementById("modalCloseBtn");
  const modalQuestionContent = document.getElementById("modalQuestionContent");
  const modalResponseContent = document.getElementById("modalResponseContent");

  // Audio streaming variables
  let audioStreamSocket;
  let audioStreamRecorder;
  let audioStreamStream;

  // Audio playback variables
  let audioContext = null;
  let audioChunks = [];
  let playheadTime = 0;
  let isPlaying = false;
  let wavHeaderSet = true;
  const SAMPLE_RATE = 44100;
  let audioBuffer = []; // Additional buffer for smoother playback
  let isBuffering = false;
  let minBufferSize = 2; // Minimum chunks to buffer before starting playback (reduced for lower latency)
  let currentAudioElement = null; // Track currently playing HTML5 Audio element

  const audioStreamBtn = document.getElementById("audioStreamBtn");
  const audioStreamStatus = document.getElementById("audioStreamStatus");
  const streamingStatusLog = document.getElementById("streamingStatusLog");
  const connectionStatus = document.getElementById("connectionStatus");
  const statusText = document.getElementById("statusText");
  const streamingSessionId = document.getElementById("streamingSessionId");

  // Initialize session
  initializeSession();

  // Load all sessions on startup
  loadAllSessions();

  // Add cleanup when page is closed or refreshed
  window.addEventListener('beforeunload', function(event) {
    // Clean up temporary audio files when page is closing
    cleanupTempAudioFiles();
    
    // Stop any active audio streaming
    if (isStreaming) {
      stopAudioStreaming();
    }

    // Stop any currently playing HTML5 Audio element
    if (currentAudioElement) {
      try {
        currentAudioElement.pause();
        currentAudioElement.currentTime = 0;
        console.log("🛑 Stopped HTML5 audio on page unload");
      } catch (error) {
        console.warn("Error stopping audio on page unload:", error);
      }
    }
  });

  // Event listeners for new UI
  if (newChatBtn) {
    newChatBtn.addEventListener("click", startNewChat);
  }

  // Web search toggle event listener
  if (webSearchToggle) {
    webSearchToggle.addEventListener("click", function () {
      webSearchEnabled = !webSearchEnabled;
      updateWebSearchToggle();

      // Send web search update to WebSocket if connected
      if (
        audioStreamSocket &&
        audioStreamSocket.readyState === WebSocket.OPEN
      ) {
        audioStreamSocket.send(
          JSON.stringify({
            type: "web_search_update",
            web_search_enabled: webSearchEnabled,
          })
        );
      }

      // Show notification
      showWebSearchNotification(webSearchEnabled);
    });
  }

  // Event listeners
  if (toggleChatHistoryBtn) {
    toggleChatHistoryBtn.addEventListener("click", toggleChatHistory);
  }

  // Persona selection event listener
  if (personaSelect) {
    personaSelect.addEventListener("change", function () {
      selectedPersona = personaSelect.value;
      updatePersonaDisplay();

      // Send persona update to WebSocket if connected
      if (
        audioStreamSocket &&
        audioStreamSocket.readyState === WebSocket.OPEN
      ) {
        audioStreamSocket.send(
          JSON.stringify({
            type: "persona_update",
            persona: selectedPersona,
          })
        );
      }

      // Update persona badge
      const personaBadge = document.getElementById("currentPersona");
      if (personaBadge) {
        personaBadge.textContent =
          getPersonaDisplayName(selectedPersona).split(" ")[0];
        personaBadge.setAttribute("data-persona", selectedPersona);
      }
    });
  }

  // Modal event listeners
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", closeModal);
  }
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener("click", closeModal);
  }

  // Close modal when clicking outside
  if (conversationModal) {
    conversationModal.addEventListener("click", function (e) {
      if (e.target === conversationModal) {
        closeModal();
      }
    });
  }

  // Settings modal event listeners
  const settingsBtn = document.getElementById("settingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const closeSettingsModal = document.getElementById("closeSettingsModal");
  const cancelSettings = document.getElementById("cancelSettings");
  const saveApiKeys = document.getElementById("saveApiKeys");
  const clearApiKeys = document.getElementById("clearApiKeys");
  const apiKeysAlert = document.getElementById("apiKeysAlert");
  const openSettingsFromAlert = document.getElementById(
    "openSettingsFromAlert"
  );

  if (settingsBtn) {
    settingsBtn.addEventListener("click", openSettings);
  }
  if (closeSettingsModal) {
    closeSettingsModal.addEventListener("click", closeSettings);
  }
  if (cancelSettings) {
    cancelSettings.addEventListener("click", closeSettings);
  }
  if (saveApiKeys) {
    saveApiKeys.addEventListener("click", saveApiKeysToStorage);
  }
  if (clearApiKeys) {
    clearApiKeys.addEventListener("click", clearAllApiKeys);
  }
  if (openSettingsFromAlert) {
    openSettingsFromAlert.addEventListener("click", function () {
      hideApiKeysAlert();
      openSettings();
    });
  }

  // Close settings modal when clicking outside
  if (settingsModal) {
    settingsModal.addEventListener("click", function (e) {
      if (e.target === settingsModal) {
        closeSettings();
      }
    });
  }

  // Close modal with Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      if (conversationModal && conversationModal.style.display !== "none") {
        closeModal();
      }
      if (settingsModal && settingsModal.style.display !== "none") {
        closeSettings();
      }
    }
  });

  // Initialize streaming mode
  initializeStreamingMode();

  // New UI Functions
  function updatePersonaDisplay() {
    const displayName = getPersonaDisplayName(selectedPersona);
    if (personaName) {
      personaName.textContent = displayName.split(" ")[0]; // Show just the first part
    }

    // Update avatar icon based on persona
    if (personaAvatar) {
      const icons = {
        developer: "fas fa-code",
        aizen: "fas fa-crown",
        luffy: "fas fa-anchor",
        politician: "fas fa-user-tie",
      };
      personaAvatar.innerHTML = `<i class="${
        icons[selectedPersona] || "fas fa-robot"
      }"></i>`;
    }

    document.title = `Voice Agent - ${displayName}`;
  }

  function addMessageToChat(content, isUser = false, isStreaming = false) {
    if (!chatMessages) return;

    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector(".welcome-message");
    if (welcomeMessage) {
      welcomeMessage.remove();
    }

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "message-avatar";

    if (isUser) {
      avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
    } else {
      const icons = {
        developer: "fas fa-code",
        aizen: "fas fa-crown",
        luffy: "fas fa-anchor",
        politician: "fas fa-user-tie",
      };
      avatarDiv.innerHTML = `<i class="${
        icons[selectedPersona] || "fas fa-robot"
      }"></i>`;
    }

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";

    if (isUser) {
      contentDiv.textContent = content;
    } else {
      // For assistant messages, parse markdown
      try {
        if (typeof marked !== "undefined" && content) {
          contentDiv.innerHTML = marked.parse(content);
          // Apply syntax highlighting if available
          if (typeof hljs !== "undefined") {
            contentDiv.querySelectorAll("pre code").forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          contentDiv.textContent = content;
        }
      } catch (error) {
        console.warn("Markdown parsing error:", error);
        contentDiv.textContent = content;
      }
    }

    if (isStreaming) {
      contentDiv.classList.add("streaming");
    }

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
  }

  function updateStreamingMessage(messageElement, content) {
    if (!messageElement) return;

    const contentDiv = messageElement.querySelector(".message-content");
    if (contentDiv) {
      try {
        if (typeof marked !== "undefined" && content) {
          contentDiv.innerHTML = marked.parse(content);
          // Apply syntax highlighting if available
          if (typeof hljs !== "undefined") {
            contentDiv.querySelectorAll("pre code").forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          contentDiv.textContent = content;
        }
      } catch (error) {
        console.warn("Markdown parsing error:", error);
        contentDiv.textContent = content;
      }
    }

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function startNewChat() {
    // Clear chat messages
    if (chatMessages) {
      chatMessages.innerHTML = `
        <div class="welcome-message">
          <div class="welcome-content">
            <div class="welcome-avatar">
              <i class="fas fa-microphone-alt"></i>
            </div>
            <h2>Welcome to AI Voice Agent</h2>
            <p>Start a conversation by clicking the microphone button below. I'll listen and respond in real-time!</p>
          </div>
        </div>
      `;
    }

    // Generate new session
    sessionId = generateSessionId();
    updateUrlWithSessionId(sessionId);

    // Reset current assistant text
    currentAssistantText = "";
  }

  function updateConnectionStatus(status, text) {
    if (connectionStatus) {
      connectionStatus.className = `status-dot ${status}`;
    }
    if (statusText) {
      statusText.textContent = text;
    }
  }

  function getSessionIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("session_id");
  }

  function generateSessionId() {
    // Generate a proper UUID v4 format instead of custom session format
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        var r = (Math.random() * 16) | 0,
          v = c == "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      }
    );
  }

  function getPersonaDisplayName(persona) {
    const personaNames = {
      developer: "Developer (Default)",
      aizen: "Sosuke Aizen (Bleach)",
      luffy: "Monkey D. Luffy (One Piece)",
      politician: "Politician",
    };
    return personaNames[persona] || personaNames["developer"];
  }

  function updateUrlWithSessionId(sessionId) {
    const url = new URL(window.location);
    url.searchParams.set("session_id", sessionId);
    window.history.replaceState({}, "", url);
    const sessionIdElement = document.getElementById("sessionId");
    if (sessionIdElement) {
      sessionIdElement.textContent = sessionId;
    }
  }

  async function initializeSession() {
    updateUrlWithSessionId(sessionId);
    await loadChatHistory();

    // Initialize persona display
    updatePersonaDisplay();

    // Initialize persona badge
    const personaBadge = document.getElementById("currentPersona");
    if (personaBadge) {
      personaBadge.textContent =
        getPersonaDisplayName(selectedPersona).split(" ")[0];
      personaBadge.setAttribute("data-persona", selectedPersona);
    }

    // Check API keys on startup
    checkApiKeysOnStartup();
  }

  // Settings Functions
  function checkApiKeysOnStartup() {
    const apiKeys = getStoredApiKeys();
    const requiredKeys = ["murfApiKey", "assemblyaiApiKey", "geminiApiKey"];
    const missingKeys = requiredKeys.filter(
      (key) => !apiKeys[key] || apiKeys[key].trim() === ""
    );

    if (missingKeys.length > 0) {
      showApiKeysAlert();

      // Disable microphone button
      const audioStreamBtn = document.getElementById("audioStreamBtn");
      if (audioStreamBtn) {
        audioStreamBtn.disabled = true;
        audioStreamBtn.style.opacity = "0.5";
        audioStreamBtn.style.cursor = "not-allowed";
        audioStreamBtn.title = "Please configure API keys in settings first";
      }

      // Show disabled message in welcome
      const welcomeMessage = document.querySelector(".welcome-message p");
      if (welcomeMessage) {
        welcomeMessage.textContent =
          "Please configure your API keys in settings before using the voice agent.";
        welcomeMessage.style.color = "#ef4444";
      }
    } else {
      // Enable microphone button
      const audioStreamBtn = document.getElementById("audioStreamBtn");
      if (audioStreamBtn) {
        audioStreamBtn.disabled = false;
        audioStreamBtn.style.opacity = "1";
        audioStreamBtn.style.cursor = "pointer";
        audioStreamBtn.title = "Click to talk";
      }
    }
  }

  function getStoredApiKeys() {
    return {
      murfApiKey: localStorage.getItem("voice_agent_murf_api_key") || "",
      assemblyaiApiKey:
        localStorage.getItem("voice_agent_assemblyai_api_key") || "",
      murfVoiceId:
        localStorage.getItem("voice_agent_murf_voice_id") || "en-IN-aarav",
      geminiApiKey: localStorage.getItem("voice_agent_gemini_api_key") || "",
      tavilyApiKey: localStorage.getItem("voice_agent_tavily_api_key") || "",
    };
  }

  function openSettings() {
    const settingsModal = document.getElementById("settingsModal");
    const apiKeys = getStoredApiKeys();

    // Populate form with stored values
    document.getElementById("murfApiKey").value = apiKeys.murfApiKey;
    document.getElementById("assemblyaiApiKey").value =
      apiKeys.assemblyaiApiKey;
    document.getElementById("murfVoiceId").value = apiKeys.murfVoiceId;
    document.getElementById("geminiApiKey").value = apiKeys.geminiApiKey;
    document.getElementById("tavilyApiKey").value = apiKeys.tavilyApiKey;

    settingsModal.style.display = "flex";
    hideApiKeysAlert();
  }

  function closeSettings() {
    const settingsModal = document.getElementById("settingsModal");
    settingsModal.style.display = "none";
  }

  function saveApiKeysToStorage() {
    const formData = {
      murfApiKey: document.getElementById("murfApiKey").value.trim(),
      assemblyaiApiKey: document
        .getElementById("assemblyaiApiKey")
        .value.trim(),
      murfVoiceId:
        document.getElementById("murfVoiceId").value.trim() || "en-IN-aarav",
      geminiApiKey: document.getElementById("geminiApiKey").value.trim(),
      tavilyApiKey: document.getElementById("tavilyApiKey").value.trim(),
    };

    // Validate required fields
    const requiredFields = ["murfApiKey", "assemblyaiApiKey", "geminiApiKey"];
    const missingFields = requiredFields.filter((field) => !formData[field]);

    if (missingFields.length > 0) {
      alert(
        "Please fill in all required fields: " +
          missingFields
            .map((f) =>
              f
                .replace(/([A-Z])/g, " $1")
                .replace(/^./, (str) => str.toUpperCase())
            )
            .join(", ")
      );
      return;
    }

    // Store in localStorage
    localStorage.setItem("voice_agent_murf_api_key", formData.murfApiKey);
    localStorage.setItem(
      "voice_agent_assemblyai_api_key",
      formData.assemblyaiApiKey
    );
    localStorage.setItem("voice_agent_murf_voice_id", formData.murfVoiceId);
    localStorage.setItem("voice_agent_gemini_api_key", formData.geminiApiKey);
    localStorage.setItem("voice_agent_tavily_api_key", formData.tavilyApiKey);

    closeSettings();

    // Re-enable microphone button and restore welcome message
    const audioStreamBtn = document.getElementById("audioStreamBtn");
    if (audioStreamBtn) {
      audioStreamBtn.disabled = false;
      audioStreamBtn.style.opacity = "1";
      audioStreamBtn.style.cursor = "pointer";
      audioStreamBtn.title = "Click to talk";
    }

    // Restore welcome message
    const welcomeMessage = document.querySelector(".welcome-message p");
    if (welcomeMessage) {
      welcomeMessage.textContent =
        "Start a conversation by clicking the microphone button below. I'll listen and respond in real-time!";
      welcomeMessage.style.color = "";
    }

    // Send API keys to WebSocket if connected
    if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
      audioStreamSocket.send(
        JSON.stringify({
          type: "api_keys_update",
          api_keys: {
            murf_api_key: formData.murfApiKey,
            assemblyai_api_key: formData.assemblyaiApiKey,
            murf_voice_id: formData.murfVoiceId,
            gemini_api_key: formData.geminiApiKey,
            tavily_api_key: formData.tavilyApiKey,
          },
        })
      );
      showNotification("API keys saved and updated successfully!", "success");
    } else {
      showNotification(
        "API keys saved successfully! Please start a new conversation to use the new settings.",
        "success"
      );
    }
  }

  function clearAllApiKeys() {
    if (
      confirm(
        "Are you sure you want to clear all API keys? This cannot be undone."
      )
    ) {
      localStorage.removeItem("voice_agent_murf_api_key");
      localStorage.removeItem("voice_agent_assemblyai_api_key");
      localStorage.removeItem("voice_agent_murf_voice_id");
      localStorage.removeItem("voice_agent_gemini_api_key");
      localStorage.removeItem("voice_agent_tavily_api_key");

      // Clear form
      document.getElementById("murfApiKey").value = "";
      document.getElementById("assemblyaiApiKey").value = "";
      document.getElementById("murfVoiceId").value = "en-IN-aarav";
      document.getElementById("geminiApiKey").value = "";
      document.getElementById("tavilyApiKey").value = "";

      showNotification("All API keys cleared", "info");
    }
  }

  function showApiKeysAlert() {
    const apiKeysAlert = document.getElementById("apiKeysAlert");
    if (apiKeysAlert) {
      apiKeysAlert.style.display = "block";
    }
  }

  function hideApiKeysAlert() {
    const apiKeysAlert = document.getElementById("apiKeysAlert");
    if (apiKeysAlert) {
      apiKeysAlert.style.display = "none";
    }
  }

  function showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-${
          type === "success"
            ? "check-circle"
            : type === "error"
            ? "exclamation-circle"
            : "info-circle"
        }"></i>
        <span>${message}</span>
      </div>
    `;

    // Add styles
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${
        type === "success"
          ? "#10b981"
          : type === "error"
          ? "#ef4444"
          : "#3b82f6"
      };
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10002;
      animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    // Remove after 4 seconds
    setTimeout(() => {
      notification.style.animation = "slideInRight 0.3s ease-out reverse";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 4000);
  }

  function initializeStreamingMode() {
    const audioStreamBtn = document.getElementById("audioStreamBtn");
    if (audioStreamBtn) {
      audioStreamBtn.addEventListener("click", function () {
        const state = this.getAttribute("data-state");

        // Prevent clicks while connecting
        if (isConnecting) {
          return;
        }

        if (state === "ready") {
          startAudioStreaming();
        } else if (state === "recording") {
          stopAudioStreaming();
        }
      });
    }

    resetStreamingState();
  }

  async function loadChatHistory() {
    try {
      const response = await fetch(`/agent/chat/${sessionId}/history`);
      const data = await response.json();
      if (data.success && data.messages.length > 0) {
        displayChatHistory(data.messages);
        showMessage(
          `Previous session loaded with ${data.message_count} messages. Click "Show Chat History" to view them.`,
          "success"
        );
      }
    } catch (error) {}
  }

  function displayChatHistory(messages) {
    const chatHistoryList = document.getElementById("chatHistoryList");
    if (!chatHistoryList) return;

    chatHistoryList.innerHTML = "";

    if (messages.length === 0) {
      chatHistoryList.innerHTML =
        '<p class="no-history">No previous messages in this session.</p>';
      return;
    }

    // Group messages by conversation pairs (user + assistant)
    const conversations = [];
    for (let i = 0; i < messages.length; i += 2) {
      const userMsg = messages[i];
      const assistantMsg = messages[i + 1];
      if (
        userMsg &&
        userMsg.role === "user" &&
        assistantMsg &&
        assistantMsg.role === "assistant"
      ) {
        conversations.push({ user: userMsg, assistant: assistantMsg });
      } else if (userMsg && userMsg.role === "user") {
        // Handle case where user message doesn't have corresponding assistant message
        conversations.push({ user: userMsg, assistant: null });
      }
    }

    conversations.forEach((conv, index) => {
      const conversationDiv = document.createElement("div");
      conversationDiv.className = "conversation-pair";

      // User message
      const userDiv = document.createElement("div");
      userDiv.className = "chat-message user";
      userDiv.innerHTML = `
        <div class="message-header">
          <span class="message-role">👤 You</span>
          <small class="message-time">${new Date(
            conv.user.timestamp
          ).toLocaleString()}</small>
        </div>
        <div class="message-content">${conv.user.content}</div>
      `;

      // Assistant message
      const assistantDiv = document.createElement("div");
      assistantDiv.className = "chat-message assistant";
      if (conv.assistant) {
        // Parse markdown content if available
        let assistantContent = conv.assistant.content;
        try {
          if (typeof marked !== "undefined") {
            assistantContent = marked.parse(conv.assistant.content);
          }
        } catch (error) {
          console.warn("Markdown parsing error:", error);
        }

        assistantDiv.innerHTML = `
          <div class="message-header">
            <span class="message-role">🤖 AI Assistant</span>
            <small class="message-time">${new Date(
              conv.assistant.timestamp
            ).toLocaleString()}</small>
          </div>
          <div class="message-content">${assistantContent}</div>
        `;
      } else {
        assistantDiv.innerHTML = `
          <div class="message-header">
            <span class="message-role">🤖 AI Assistant</span>
            <small class="message-time">Pending...</small>
          </div>
          <div class="message-content"><em>Response pending...</em></div>
        `;
      }

      conversationDiv.appendChild(userDiv);
      conversationDiv.appendChild(assistantDiv);

      // Add click event listener to open modal
      conversationDiv.addEventListener("click", function () {
        const userMessage = conv.user.content;
        const assistantMessage = conv.assistant
          ? conv.assistant.content
          : "No response available";
        openConversationModal(userMessage, assistantMessage);
      });

      chatHistoryList.appendChild(conversationDiv);
    });

    // Apply syntax highlighting to code blocks if available
    if (typeof hljs !== "undefined") {
      chatHistoryList.querySelectorAll("pre code").forEach((block) => {
        hljs.highlightElement(block);
      });
    }
  }

  function toggleChatHistory() {
    if (chatHistoryContainer) {
      const isVisible = chatHistoryContainer.style.display !== "none";
      chatHistoryContainer.style.display = isVisible ? "none" : "block";

      if (toggleChatHistoryBtn) {
        toggleChatHistoryBtn.textContent = isVisible
          ? "Show Chat History"
          : "Hide Chat History";
      }

      if (!isVisible) {
        // Reload chat history when showing
        loadChatHistory();
      }
    }
  }

  // Modal Functions
  function openConversationModal(userMessage, assistantMessage) {
    if (!conversationModal || !modalQuestionContent || !modalResponseContent)
      return;

    // Set the content
    modalQuestionContent.textContent = userMessage;

    // Parse assistant message as markdown
    try {
      if (typeof marked !== "undefined" && assistantMessage) {
        const markdownHtml = marked.parse(assistantMessage);
        modalResponseContent.innerHTML = markdownHtml;

        // Apply syntax highlighting if available
        if (typeof hljs !== "undefined") {
          modalResponseContent.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
          });
        }
      } else {
        modalResponseContent.innerHTML = assistantMessage
          ? assistantMessage.replace(/\n/g, "<br>")
          : "No response available";
      }
    } catch (error) {
      console.warn("Markdown parsing error in modal:", error);
      modalResponseContent.innerHTML = assistantMessage
        ? assistantMessage.replace(/\n/g, "<br>")
        : "No response available";
    }

    // Show the modal
    conversationModal.style.display = "flex";
    document.body.style.overflow = "hidden"; // Prevent background scrolling
  }

  function closeModal() {
    if (conversationModal) {
      conversationModal.style.display = "none";
      document.body.style.overflow = ""; // Restore scrolling
    }
  }

  async function startAudioStreaming() {
    try {
      // Prevent multiple simultaneous connection attempts
      if (isConnecting) {
        return;
      }

      isConnecting = true;

      // Show connecting state in button
      if (audioStreamBtn) {
        audioStreamBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        audioStreamBtn.className = "mic-button connecting";
        audioStreamBtn.setAttribute("data-state", "connecting");

        const micStatus = audioStreamBtn.querySelector(".mic-status");
        if (micStatus) {
          micStatus.textContent = "Connecting...";
        } else {
          audioStreamBtn.innerHTML +=
            '<span class="mic-status">Connecting...</span>';
        }
      }

      // Reset streaming state and UI
      resetStreamingState();

      updateConnectionStatus("connecting", "Connecting...");

      // Clear any previous transcriptions
      clearPreviousTranscriptions();

      // Close any existing WebSocket connection
      if (audioStreamSocket) {
        audioStreamSocket.close();
        audioStreamSocket = null;
      }

      // Connect to WebSocket with session ID and timeout
      // Determine WebSocket protocol based on environment
      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const wsProtocol = isLocalhost ? 'ws' : 'wss';
      const wsHost = isLocalhost ? `${window.location.hostname}:8000` : window.location.host;
      const wsUrl = `${wsProtocol}://${wsHost}/ws/audio-stream?session_id=${sessionId}`;
      audioStreamSocket = new WebSocket(wsUrl);

      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (
          audioStreamSocket &&
          audioStreamSocket.readyState === WebSocket.CONNECTING
        ) {
          audioStreamSocket.close();
          updateConnectionStatus("disconnected", "Connection timeout");
          isConnecting = false;
        }
      }, 3000); // Reduced to 3 seconds for faster response

      audioStreamSocket.onopen = function (event) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        updateConnectionStatus("connected", "Connected");

        // Ensure audio playback system is ready for this session
        ensureAudioSystemReady();

        // Send session ID and persona to establish the session on the backend
        audioStreamSocket.send(
          JSON.stringify({
            type: "session_id",
            session_id: sessionId,
            persona: selectedPersona,
            web_search_enabled: webSearchEnabled,
          })
        );

        // Send API keys if available
        const apiKeys = getStoredApiKeys();
        const hasRequiredKeys =
          apiKeys.murfApiKey &&
          apiKeys.assemblyaiApiKey &&
          apiKeys.geminiApiKey;

        if (hasRequiredKeys) {
          audioStreamSocket.send(
            JSON.stringify({
              type: "api_keys_update",
              api_keys: {
                murf_api_key: apiKeys.murfApiKey,
                assemblyai_api_key: apiKeys.assemblyaiApiKey,
                murf_voice_id: apiKeys.murfVoiceId,
                gemini_api_key: apiKeys.geminiApiKey,
                tavily_api_key: apiKeys.tavilyApiKey,
              },
            })
          );
        }
      };

      audioStreamSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === "audio_stream_ready") {
          updateStreamingStatus(
            `Ready to stream audio with transcription. Session: ${data.session_id}`,
            "info"
          );
          streamingSessionId.textContent = `Session: ${data.session_id}`;

          // Ensure the frontend session ID matches the backend
          if (data.session_id !== sessionId) {
            sessionId = data.session_id;
            updateUrlWithSessionId(sessionId);
          }

          if (data.transcription_enabled) {
            // Remove transcription enabled message as requested
          }
          startRecordingForStreaming();
        } else if (data.type === "chunk_ack") {
          // Removed excessive chunk acknowledgment logging
        } else if (data.type === "command_response") {
          updateStreamingStatus(data.message, "info");
        } else if (data.type === "transcription_ready") {
          updateStreamingStatus("🎯 " + data.message, "success");
        } else if (data.type === "final_transcript") {
          // Display final transcription only if we have text
          if (data.text && data.text.trim()) {
            updateStreamingStatus(`🎙️ FINAL: "${data.text}"`, "recording");
          }
        } else if (data.type === "partial_transcript") {
          // Show partial transcripts for feedback
          if (data.text && data.text.trim()) {
            updateStreamingStatus(`🎙️ ${data.text}`, "info");
          }
        } else if (data.type === "turn_end") {
          updateStreamingStatus(
            "🛑 Turn ended - User stopped talking",
            "success"
          );
          if (data.final_transcript && data.final_transcript.trim()) {
            updateStreamingStatus(
              `✅ TURN COMPLETE: "${data.final_transcript}"`,
              "success"
            );
          } else {
            updateStreamingStatus(
              "⚠️ Turn ended but no speech detected",
              "warning"
            );
            showNoSpeechMessage();
          }
        } else if (data.type === "transcription_complete") {
          if (data.text && data.text.trim()) {
            // Remove complete transcription message as requested
          } else {
            updateStreamingStatus(
              "⚠️ No speech detected in recording",
              "warning"
            );
            showNoSpeechMessage();
          }
        } else if (data.type === "streaming_complete") {
          updateStreamingStatus(`🎯 ${data.message}`, "success");
          if (!data.transcription || !data.transcription.trim()) {
            updateStreamingStatus(
              "⚠️ Recording completed but no speech was detected",
              "warning"
            );
            showNoSpeechMessage();
          }
        } else if (data.type === "transcription_error") {
          updateStreamingStatus(
            "❌ Transcription error: " + data.message,
            "error"
          );
        } else if (data.type === "transcription_stopped") {
          updateStreamingStatus("🛑 " + data.message, "warning");
        } else if (data.type === "llm_streaming_start") {
          updateStreamingStatus(`🤖 ${data.message}`, "info");
          resetAudioPlayback();
          displayLLMStreamingStart(data.user_message);
          // Add user message to chat history immediately
          addUserMessageToChatHistory(data.user_message);
        } else if (data.type === "llm_streaming_chunk") {
          // Display LLM text chunks as they arrive
          displayLLMTextChunk(data.chunk, data.accumulated_length);
          // Update the assistant response in chat history in real-time
          updateAssistantResponseInChatHistory(data.chunk);
        } else if (data.type === "tts_streaming_start") {
          updateStreamingStatus(`🎵 ${data.message}`, "info");
          // Stop any previous audio before starting new TTS
          stopAllAudioPlayback();
          displayTTSStreamingStart();
        } else if (data.type === "tts_audio_chunk") {
          // Handle audio base64 chunks from TTS
          handleAudioChunk(data);
        } else if (data.type === "tts_status") {
          // Removed excessive TTS status logging
        } else if (data.type === "llm_streaming_complete") {
          updateStreamingStatus(`✅ ${data.message}`, "success");
          displayStreamingComplete(data);

          // Reset streaming state to allow next query
          isStreaming = false;

          // Ensure button is ready for next interaction
          if (audioStreamBtn) {
            audioStreamBtn.setAttribute("data-state", "ready");
          }

          // Chat history is now updated in real-time when response is saved
          // No need for delayed reload
        } else if (data.type === "llm_streaming_error") {
          updateStreamingStatus(`❌ ${data.message}`, "error");
        } else if (data.type === "tts_streaming_error") {
          updateStreamingStatus(`❌ ${data.message}`, "error");
        } else if (data.type === "tts_streaming_timeout") {
          updateStreamingStatus(`⏰ ${data.message}`, "warning");
          // Reset audio playback state when TTS times out
          resetAudioPlayback();
        } else if (data.type === "tts_fallback_audio") {
          updateStreamingStatus(`🔄 ${data.message}`, "info");
          // Play fallback audio using HTML5 audio element
          playFallbackAudio(data.audio_url);
        } else if (data.type === "audio_stop") {
          // Stop all current audio playback when new query starts
          updateStreamingStatus(`🛑 ${data.message}`, "info");
          stopAllAudioPlayback();
        } else if (data.type === "response_saved") {
          updateStreamingStatus(`💾 ${data.message}`, "success");
          // Response is already being updated in real-time, just mark as saved
          markResponseAsSaved();

          // Reset streaming state after response is saved
          isStreaming = false;

          // Refresh sessions list to update preview and last activity
          loadAllSessions();
        } else if (data.type === "persona_updated") {
          updateStreamingStatus(`🎭 ${data.message}`, "success");
          // Update the persona badge to reflect the change
          const personaBadge = document.getElementById("currentPersona");
          if (personaBadge) {
            personaBadge.textContent = getPersonaDisplayName(
              data.persona
            ).split(" ")[0];
            personaBadge.setAttribute("data-persona", data.persona);
          }
        } else if (data.type === "api_keys_required") {
          // Stop audio recording if active
          if (
            audioStreamRecorder &&
            audioStreamRecorder.state === "recording"
          ) {
            audioStreamRecorder.stop();
          }

          // Update status
          updateStreamingStatus(`🔒 ${data.message}`, "error");

          // Show API keys alert
          showApiKeysAlert();

          // Reset streaming state
          resetStreamingState();

          console.warn("API keys required:", data.message);
        } else if (data.type === "api_keys_updated") {
          if (data.success) {
            updateStreamingStatus(`✅ ${data.message}`, "success");
            hideApiKeysAlert();

            if (data.streaming_ready) {
              showNotification(
                "API keys updated successfully! Voice agent is ready to use.",
                "success"
              );
              updateStreamingStatus(
                "🎯 Streaming client ready - You can now use voice input",
                "success"
              );
            } else {
              showNotification(
                "API keys updated but streaming not ready. Please try refreshing.",
                "warning"
              );
            }
          } else {
            updateStreamingStatus(`❌ ${data.message}`, "error");
            showNotification(
              "Failed to update API keys. Please check your keys and try again.",
              "error"
            );
          }
        }
      };

      audioStreamSocket.onerror = function (error) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        updateConnectionStatus("error", "Connection Error");

        // Reset button state on error
        if (audioStreamBtn) {
          audioStreamBtn.innerHTML = '<i class="fas fa-microphone"></i>';
          audioStreamBtn.className = "mic-button";
          audioStreamBtn.setAttribute("data-state", "ready");

          const micStatus = audioStreamBtn.querySelector(".mic-status");
          if (micStatus) {
            micStatus.textContent = "Click to talk";
          } else {
            audioStreamBtn.innerHTML +=
              '<span class="mic-status">Click to talk</span>';
          }
        }
      };

      audioStreamSocket.onclose = function (event) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        updateConnectionStatus("disconnected", "Disconnected");

        // Only show close message if it wasn't intentional
        if (event.code !== 1000) {
          // WebSocket closed unexpectedly but we'll handle it silently
        }

        // Reset button state on close
        if (audioStreamBtn) {
          audioStreamBtn.innerHTML = '<i class="fas fa-microphone"></i>';
          audioStreamBtn.className = "mic-button";
          audioStreamBtn.setAttribute("data-state", "ready");

          const micStatus = audioStreamBtn.querySelector(".mic-status");
          if (micStatus) {
            micStatus.textContent = "Click to talk";
          } else {
            audioStreamBtn.innerHTML +=
              '<span class="mic-status">Click to talk</span>';
          }
        }
      };
    } catch (error) {
      isConnecting = false;
      updateConnectionStatus("error", "Error");
      updateStreamingStatus(
        "Error starting streaming: " + error.message,
        "error"
      );
    }
  }

  async function startRecordingForStreaming() {
    try {
      // Prevent starting if already streaming
      if (isStreaming) {
        return;
      }

      audioStreamStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000, // 16kHz for AssemblyAI
          channelCount: 1, // Mono
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const audioContext = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: 16000,
      });

      const source = audioContext.createMediaStreamSource(audioStreamStream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = function (e) {
        if (
          audioStreamSocket &&
          audioStreamSocket.readyState === WebSocket.OPEN
        ) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            pcmData[i] = Math.max(
              -32768,
              Math.min(32767, inputData[i] * 32767)
            );
          }
          audioStreamSocket.send(pcmData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      // Store references for cleanup
      audioStreamRecorder = {
        stop: () => {
          processor.disconnect();
          source.disconnect();
          audioContext.close();
        },
      };

      isStreaming = true;
      if (audioStreamBtn) {
        audioStreamBtn.innerHTML = '<i class="fas fa-stop"></i>';
        audioStreamBtn.className = "mic-button recording";
        audioStreamBtn.setAttribute("data-state", "recording");

        // Update mic status
        const micStatus = audioStreamBtn.querySelector(".mic-status");
        if (micStatus) {
          micStatus.textContent = "Recording...";
        } else {
          audioStreamBtn.innerHTML +=
            '<span class="mic-status">Recording...</span>';
        }
      }

      updateConnectionStatus("recording", "Recording & Streaming");
      updateStreamingStatus("Recording and streaming audio...", "recording");
      if (
        audioStreamSocket &&
        audioStreamSocket.readyState === WebSocket.OPEN
      ) {
        audioStreamSocket.send("start_streaming");
      }
    } catch (error) {
      updateConnectionStatus("error", "Recording Error");
      updateStreamingStatus(
        "Error starting recording: " + error.message,
        "error"
      );
    }
  }

  async function stopAudioStreaming() {
    try {
      isStreaming = false; // Reset streaming state first

      // Stop the audio recording (either MediaRecorder or custom processor)
      if (audioStreamRecorder) {
        if (typeof audioStreamRecorder.stop === "function") {
          audioStreamRecorder.stop();
        }
        audioStreamRecorder = null;
      }

      // Stop media stream
      if (audioStreamStream) {
        audioStreamStream.getTracks().forEach((track) => track.stop());
        audioStreamStream = null;
      }

      // Send stop signal if WebSocket is open
      if (
        audioStreamSocket &&
        audioStreamSocket.readyState === WebSocket.OPEN
      ) {
        audioStreamSocket.send("stop_streaming");

        // Close WebSocket immediately for faster response
        audioStreamSocket.close(1000, "User stopped streaming");
        audioStreamSocket = null;
      }

      // Update UI immediately
      if (audioStreamBtn) {
        audioStreamBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        audioStreamBtn.className = "mic-button";
        audioStreamBtn.setAttribute("data-state", "ready");

        // Update mic status
        const micStatus = audioStreamBtn.querySelector(".mic-status");
        if (micStatus) {
          micStatus.textContent = "Click to talk";
        } else {
          audioStreamBtn.innerHTML +=
            '<span class="mic-status">Click to talk</span>';
        }
      }

      updateConnectionStatus("disconnected", "Disconnected");
      updateStreamingStatus("Audio streaming stopped", "info");

      // Stop any currently playing HTML5 Audio element
      if (currentAudioElement) {
        try {
          currentAudioElement.pause();
          currentAudioElement.currentTime = 0;
          currentAudioElement = null;
          console.log("🛑 Stopped HTML5 audio when stopping streaming");
        } catch (error) {
          console.warn("Error stopping HTML5 audio when stopping streaming:", error);
        }
      }
    } catch (error) {
      updateStreamingStatus(
        "Error stopping streaming: " + error.message,
        "error"
      );
    }
  }

  function updateConnectionStatus(status, text) {
    if (connectionStatus) {
      connectionStatus.className = `status-badge ${status}`;
      connectionStatus.textContent = text;
    }
  }

  function updateStreamingStatus(message, type) {
    if (streamingStatusLog && audioStreamStatus) {
      audioStreamStatus.style.display = "block";

      const statusEntry = document.createElement("div");
      statusEntry.className = `streaming-status ${type}`;
      statusEntry.innerHTML = `
        <strong>${new Date().toLocaleTimeString()}</strong>: ${message}
      `;

      streamingStatusLog.appendChild(statusEntry);
      streamingStatusLog.scrollTop = streamingStatusLog.scrollHeight;
    }
  }

  function resetStreamingState() {
    // Reset connection flags
    isConnecting = false;

    // Hide previous streaming UI elements
    const elementsToHide = [
      "llmStreamingArea",
      "ttsStreamingArea",
      "streamingSummaryArea",
      "noSpeechArea",
    ];

    elementsToHide.forEach((elementId) => {
      const element = document.getElementById(elementId);
      if (element) {
        element.style.display = "none";
        if (elementId === "llmStreamingArea") {
          element.innerHTML = "";
        }
      }
    });

    // Clear status log
    if (streamingStatusLog) {
      streamingStatusLog.innerHTML = "";
    }

    // Hide status container
    if (audioStreamStatus) {
      audioStreamStatus.style.display = "none";
    }

    // Reset chat history state
    currentAssistantText = "";

    resetAudioPlayback();
  }

  function clearPreviousTranscriptions() {
    // Clear live transcription area
    const liveArea = document.getElementById("liveTranscriptionArea");
    if (liveArea) {
      liveArea.style.display = "none";
      const transcriptionText = document.getElementById("transcriptionText");
      if (transcriptionText) {
        transcriptionText.innerHTML = "";
      }
    }

    // Clear complete transcription area
    const completeArea = document.getElementById("completeTranscriptionArea");
    if (completeArea) {
      completeArea.style.display = "none";
    }

    // Clear no speech area
    const noSpeechArea = document.getElementById("noSpeechArea");
    if (noSpeechArea) {
      noSpeechArea.style.display = "none";
    }

    // Clear LLM streaming area
    const llmArea = document.getElementById("llmStreamingArea");
    if (llmArea) {
      llmArea.style.display = "none";
      llmArea.innerHTML = "";
    }
  }

  function showNoSpeechMessage() {
    // Speech detection happens in backend, UI display disabled
  }

  // Function to add user message to chat history immediately
  function addUserMessageToChatHistory(userMessage) {
    // Add to new chat interface
    addMessageToChat(userMessage, true);

    // Create streaming assistant message in new UI
    currentStreamingMessage = addMessageToChat("", false, true);

    // Reset current assistant text for new conversation
    currentAssistantText = "";

    // Also add to legacy chat history for compatibility
    const chatHistoryList = document.getElementById("chatHistoryList");
    if (!chatHistoryList) return;

    // Remove "no history" message if it exists
    const noHistoryMsg = chatHistoryList.querySelector(".no-history");
    if (noHistoryMsg) {
      noHistoryMsg.remove();
    }

    // Create new conversation pair
    const conversationDiv = document.createElement("div");
    conversationDiv.className = "conversation-pair new-conversation";
    conversationDiv.id = `conversation-${Date.now()}`;

    const currentTime = new Date();

    // User message
    const userDiv = document.createElement("div");
    userDiv.className = "chat-message user";
    userDiv.innerHTML = `
      <div class="message-header">
        <span class="message-role">👤 You</span>
        <small class="message-time">${currentTime.toLocaleString()}</small>
      </div>
      <div class="message-content">${userMessage}</div>
    `;

    // Assistant message placeholder
    const assistantDiv = document.createElement("div");
    assistantDiv.className = "chat-message assistant";
    assistantDiv.id = "current-assistant-response";
    assistantDiv.innerHTML = `
      <div class="message-header">
        <span class="message-role">🤖 AI Assistant</span>
        <small class="message-time">${currentTime.toLocaleString()}</small>
      </div>
      <div class="message-content" id="assistant-content">
        <em>Generating response...</em>
      </div>
    `;

    conversationDiv.appendChild(userDiv);
    conversationDiv.appendChild(assistantDiv);
    chatHistoryList.appendChild(conversationDiv);

    // Add click event listener to open modal
    conversationDiv.addEventListener("click", function () {
      const currentUserMessage = userMessage;
      const assistantMessage =
        currentAssistantText || "Response in progress...";
      openConversationModal(currentUserMessage, assistantMessage);
    });

    // Scroll to new conversation
    conversationDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Show notification that new conversation started
    if (chatHistoryContainer && chatHistoryContainer.style.display === "none") {
      if (toggleChatHistoryBtn) {
        toggleChatHistoryBtn.textContent = "Show Chat History (New!)";
        toggleChatHistoryBtn.style.backgroundColor = "#667eea";
      }
    }
  }

  // Function to update assistant response in real-time
  function updateAssistantResponseInChatHistory(chunk) {
    // Accumulate the response text
    currentAssistantText += chunk;

    // Update new chat interface
    if (currentStreamingMessage) {
      updateStreamingMessage(currentStreamingMessage, currentAssistantText);
    }

    // Update legacy chat history
    const assistantContent = document.getElementById("assistant-content");
    if (!assistantContent) return;

    // Parse and display the markdown
    try {
      if (typeof marked !== "undefined") {
        const markdownHtml = marked.parse(currentAssistantText);
        assistantContent.innerHTML = markdownHtml;

        // Apply syntax highlighting if available
        if (typeof hljs !== "undefined") {
          assistantContent.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
          });
        }
      } else {
        assistantContent.innerHTML = currentAssistantText.replace(
          /\n/g,
          "<br>"
        );
      }
    } catch (error) {
      console.warn("Markdown parsing error:", error);
      assistantContent.innerHTML = currentAssistantText.replace(/\n/g, "<br>");
    }

    // Scroll to keep the conversation visible
    const assistantDiv = document.getElementById("current-assistant-response");
    if (assistantDiv) {
      assistantDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  // Function to mark the response as saved
  function markResponseAsSaved() {
    // Mark streaming as complete in new UI
    if (currentStreamingMessage) {
      const contentDiv =
        currentStreamingMessage.querySelector(".message-content");
      if (contentDiv) {
        contentDiv.classList.remove("streaming");
      }
      currentStreamingMessage = null;
    }

    // Update legacy interface
    const assistantDiv = document.getElementById("current-assistant-response");
    if (assistantDiv) {
      // Remove the ID since this conversation is now complete
      assistantDiv.removeAttribute("id");
      const assistantContent = assistantDiv.querySelector(".message-content");
      if (assistantContent) {
        assistantContent.removeAttribute("id");
      }

      // Add a "saved" indicator
      const messageHeader = assistantDiv.querySelector(".message-header");
      if (messageHeader) {
        const savedIndicator = document.createElement("span");
        savedIndicator.className = "saved-indicator";
        savedIndicator.innerHTML = "💾";
        savedIndicator.title = "Response saved to database";
        savedIndicator.style.marginLeft = "8px";
        savedIndicator.style.fontSize = "12px";
        messageHeader.appendChild(savedIndicator);
      }
    }

    // Reset the accumulated text for next conversation
    currentAssistantText = "";

    // Update button text back to normal
    if (
      toggleChatHistoryBtn &&
      toggleChatHistoryBtn.textContent.includes("New!")
    ) {
      toggleChatHistoryBtn.textContent = "Show Chat History";
      toggleChatHistoryBtn.style.backgroundColor = "";
    }
  }

  function handleAudioChunk(audioData) {
    // Stop any currently playing HTML5 Audio element before starting WebSocket streaming
    if (currentAudioElement) {
      try {
        currentAudioElement.pause();
        currentAudioElement.currentTime = 0;
        currentAudioElement = null;
        console.log("🛑 Stopped HTML5 audio before starting WebSocket streaming");
      } catch (error) {
        console.warn("Error stopping HTML5 audio:", error);
      }
    }

    // Play the audio chunk for streaming
    playAudioChunk(audioData.audio_base64);

    // Remove the audio chunk received message as requested

    if (audioData.is_final) {
      updateStreamingStatus("Audio streaming complete!", "success");
      setTimeout(() => {
        if (!isPlaying && audioChunks.length === 0) {
          updatePlaybackStatus("Audio streaming complete!");
          setTimeout(() => {
            hideAudioPlaybackIndicator();
            // Clean up temporary audio files after playback is complete
            cleanupTempAudioFiles();
          }, 2000);
        }
      }, 1000);
    }
  }

  // Function to clean up temporary audio files
  async function cleanupTempAudioFiles() {
    try {
      const response = await fetch('/cleanup/temp-audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          console.log('🧹 Temporary audio files cleaned up successfully');
        }
      }
    } catch (error) {
      console.warn('Failed to cleanup temporary audio files:', error);
    }
  }

  // Function to handle audio recovery when glitches occur
  function recoverAudioPlayback() {
    console.log("🔧 Attempting audio playback recovery...");
    
    // Stop current playback
    isPlaying = false;
    isBuffering = false;
    
    // Reset audio context
    if (audioContext && audioContext.state !== "closed") {
      try {
        audioContext.close();
      } catch (e) {
        console.warn("Error closing audio context:", e);
      }
    }
    
    audioContext = null;
    
    // Wait a moment then reinitialize
    setTimeout(() => {
      if (audioChunks.length > 0 || audioBuffer.length > 0) {
        console.log("🔄 Reinitializing audio playback...");
        initializeAudioContext();
        
        // Combine any remaining chunks
        if (audioBuffer.length > 0) {
          audioChunks = [...audioBuffer, ...audioChunks];
          audioBuffer = [];
        }
        
        if (audioChunks.length > 0) {
          isPlaying = true;
          chunkPlay();
        }
      }
    }, 100);
  }

  // Function to play fallback audio when TTS streaming fails
  function playFallbackAudio(audioUrl) {
    try {
      console.log("🔄 Playing fallback audio from URL:", audioUrl);

      // Stop any currently playing HTML5 Audio element before starting new one
      if (currentAudioElement) {
        try {
          currentAudioElement.pause();
          currentAudioElement.currentTime = 0;
          console.log("🛑 Stopped previous fallback audio before starting new one");
        } catch (error) {
          console.warn("Error stopping previous fallback audio:", error);
        }
      }

      // Also reset WebSocket streaming audio to prevent overlap
      resetAudioPlayback();

      // Show audio playback indicator
      showAudioPlaybackIndicator();
      updatePlaybackStatus("Playing fallback audio...");

      // Create HTML5 audio element
      const audio = new Audio(audioUrl);
      currentAudioElement = audio; // Track this audio element
      audio.preload = 'auto';
      
      audio.addEventListener('loadstart', () => {
        updatePlaybackStatus("Loading fallback audio...");
      });
      
      audio.addEventListener('canplay', () => {
        updatePlaybackStatus("Fallback audio ready, starting playback...");
        audio.play().catch(error => {
          console.error("Failed to play fallback audio:", error);
          updateStreamingStatus("❌ Failed to play fallback audio", "error");
          hideAudioPlaybackIndicator();
        });
      });
      
      audio.addEventListener('play', () => {
        updatePlaybackStatus("Playing fallback audio...");
      });
      
      audio.addEventListener('ended', () => {
        updatePlaybackStatus("Fallback audio playback complete!");
        currentAudioElement = null; // Clear reference when audio ends
        setTimeout(() => {
          hideAudioPlaybackIndicator();
          // Clean up temporary audio files after playback
          cleanupTempAudioFiles();
        }, 2000);
      });
      
      audio.addEventListener('error', (e) => {
        console.error("Fallback audio error:", e);
        updateStreamingStatus("❌ Error playing fallback audio", "error");
        currentAudioElement = null; // Clear reference on error
        hideAudioPlaybackIndicator();
      });
      
      // Set volume and start loading
      audio.volume = 1.0;
      audio.load();
      
    } catch (error) {
      console.error("Error setting up fallback audio:", error);
      updateStreamingStatus("❌ Failed to setup fallback audio", "error");
      hideAudioPlaybackIndicator();
    }
  }

  function displayLLMStreamingStart(userMessage) {
    let llmArea = document.getElementById("llmStreamingArea");

    if (!llmArea) {
      llmArea = document.createElement("div");
      llmArea.id = "llmStreamingArea";
      llmArea.className = "llm-streaming-area";

      // Insert after the complete transcription area or streaming status
      const completeArea = document.getElementById("completeTranscriptionArea");
      const statusContainer = document.getElementById("audioStreamStatus");
      const insertAfter = completeArea || statusContainer;

      if (insertAfter) {
        insertAfter.parentNode.insertBefore(llmArea, insertAfter.nextSibling);
      }
    }

    // Update content with current user message
    llmArea.innerHTML = `
      <h4>🤖 AI Response Generation</h4>
      <div class="user-query">
        <strong>Your question:</strong> "${userMessage}"
      </div>
      <div class="llm-response">
        <strong>AI Response:</strong>
        <div id="llmResponseText" class="llm-response-text"></div>
      </div>
    `;

    llmArea.style.display = "block";

    // Clear previous response and show generating message
    const responseText = document.getElementById("llmResponseText");
    if (responseText) {
      responseText.innerHTML = "<em>Generating response...</em>";
      responseText.setAttribute("data-raw-text", "");
    }
  }

  // Function to display LLM text chunks
  function displayLLMTextChunk(chunk, accumulatedLength) {
    const responseText = document.getElementById("llmResponseText");
    if (responseText) {
      // Append the new chunk
      let currentText = responseText.getAttribute("data-raw-text") || "";
      if (currentText === "Generating response...") {
        currentText = "";
      }

      // Accumulate the raw text
      const newText = currentText + chunk;
      responseText.setAttribute("data-raw-text", newText);

      // Parse as Markdown and display
      try {
        if (typeof marked !== "undefined") {
          const markdownHtml = marked.parse(newText);
          responseText.innerHTML = markdownHtml;

          // Apply syntax highlighting if available
          if (typeof hljs !== "undefined") {
            responseText.querySelectorAll("pre code").forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          // Fallback to simple line break replacement
          responseText.innerHTML = newText.replace(/\n/g, "<br>");
        }
      } catch (error) {
        console.warn("Markdown parsing error:", error);
        responseText.innerHTML = newText.replace(/\n/g, "<br>");
      }

      // Scroll to bottom
      responseText.scrollTop = responseText.scrollHeight;
    }
  }

  function displayTTSStreamingStart() {
    // Basic TTS streaming UI
    let ttsArea = document.getElementById("ttsStreamingArea");

    if (!ttsArea) {
      ttsArea = document.createElement("div");
      ttsArea.id = "ttsStreamingArea";
      ttsArea.className = "tts-streaming-area";
      ttsArea.innerHTML = `<h4>🎵 Audio Generation</h4><div class="audio-status">Generating audio...</div>`;

      const llmArea = document.getElementById("llmStreamingArea");
      const statusContainer = document.getElementById("audioStreamStatus");
      const insertAfter = llmArea || statusContainer;

      if (insertAfter) {
        insertAfter.parentNode.insertBefore(ttsArea, insertAfter.nextSibling);
      }
    }

    ttsArea.style.display = "block";
  }

  // Removed displayAudioChunkReceived function - not needed for basic functionality

  function displayStreamingComplete(data) {
    let summaryArea = document.getElementById("streamingSummaryArea");

    if (!summaryArea) {
      summaryArea = document.createElement("div");
      summaryArea.id = "streamingSummaryArea";
      summaryArea.className = "streaming-summary-area";

      const ttsArea = document.getElementById("ttsStreamingArea");
      const statusContainer = document.getElementById("audioStreamStatus");
      const insertAfter = ttsArea || statusContainer;

      if (insertAfter) {
        insertAfter.parentNode.insertBefore(
          summaryArea,
          insertAfter.nextSibling
        );
      }
    }

    summaryArea.innerHTML = `
      <h4>✅ Conversation Complete</h4>
      <div class="streaming-summary">
        <div class="summary-item">
          <strong>Complete Response:</strong>
          <div class="final-response" id="finalResponseContent"></div>
        </div>
      </div>
    `;

    summaryArea.style.display = "block";

    // Render final response as Markdown
    const finalResponseElement = document.getElementById(
      "finalResponseContent"
    );
    if (finalResponseElement && data.complete_response) {
      try {
        if (typeof marked !== "undefined") {
          const markdownHtml = marked.parse(data.complete_response);
          finalResponseElement.innerHTML = markdownHtml;

          if (typeof hljs !== "undefined") {
            finalResponseElement
              .querySelectorAll("pre code")
              .forEach((block) => {
                hljs.highlightElement(block);
              });
          }
        } else {
          finalResponseElement.innerHTML = data.complete_response.replace(
            /\n/g,
            "<br>"
          );
        }
      } catch (error) {
        console.warn("Markdown parsing error in final response:", error);
        finalResponseElement.innerHTML = data.complete_response.replace(
          /\n/g,
          "<br>"
        );
      }
    }

    summaryArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // Removed displayAudioStreamingComplete function - not needed

  // ==================== AUDIO STREAMING PLAYBACK FUNCTIONS ====================
  // Based on Murf's WebSocket streaming reference implementation

  function initializeAudioContext() {
    try {
      // If audio context doesn't exist or is closed, create a new one
      if (!audioContext || audioContext.state === "closed") {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: SAMPLE_RATE,
          latencyHint: "interactive" // Optimize for low latency
        });
        playheadTime = audioContext.currentTime;
        
        // Handle audio context state changes
        audioContext.addEventListener('statechange', () => {
          if (audioContext.state === 'suspended') {
            // Try to resume if suspended
            audioContext.resume().catch(err => {
              console.warn('Failed to resume audio context:', err);
            });
          }
        });
      }

      // If audio context is suspended, try to resume it
      if (audioContext.state === "suspended") {
        audioContext.resume().catch((err) => {
          // Audio context resume failed
        });
      }

      return true;
    } catch (error) {
      console.error("Failed to initialize audio context:", error);
      return false;
    }
  }

  function base64ToPCMFloat32(base64) {
    try {
      if (!base64 || base64.length === 0) {
        console.warn("Empty base64 audio data received");
        return null;
      }
      
      let binary = atob(base64);
      const offset = wavHeaderSet ? 44 : 0; // Skip WAV header if present

      if (wavHeaderSet) {
        wavHeaderSet = false; // Only process header once per session
      }

      const length = binary.length - offset;
      if (length <= 0) {
        console.warn("Invalid audio data length after offset");
        return null;
      }
      
      const buffer = new ArrayBuffer(length);
      const byteArray = new Uint8Array(buffer);

      for (let i = 0; i < byteArray.length; i++) {
        byteArray[i] = binary.charCodeAt(i + offset);
      }

      const view = new DataView(byteArray.buffer);
      const sampleCount = byteArray.length / 2; // 16-bit samples
      
      if (sampleCount === 0) {
        console.warn("No audio samples found");
        return null;
      }
      
      const float32Array = new Float32Array(sampleCount);

      for (let i = 0; i < sampleCount; i++) {
        const int16 = view.getInt16(i * 2, true); // Little endian
        float32Array[i] = Math.max(-1, Math.min(1, int16 / 32768)); // Clamp and convert to float32 range [-1, 1]
      }

      return float32Array;
    } catch (error) {
      console.error("Error converting base64 to PCM:", error);
      return null;
    }
  }

  function chunkPlay() {
    if (audioChunks.length > 0) {
      const chunk = audioChunks.shift();

      // Ensure audio context is ready before playing
      if (!audioContext || audioContext.state === "closed") {
        if (!initializeAudioContext()) {
          isPlaying = false;
          hideAudioPlaybackIndicator();
          return;
        }
      }

      if (audioContext.state === "suspended") {
        audioContext.resume().catch((err) => {
          console.warn("Audio context resume failed:", err);
        });
      }

      try {
        const buffer = audioContext.createBuffer(1, chunk.length, SAMPLE_RATE);
        buffer.copyToChannel(chunk, 0);

        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        
        // Add a gain node for better audio control
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 1.0;
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);

        const now = audioContext.currentTime;
        // Better timing management to prevent gaps
        if (playheadTime < now + 0.1) {
          playheadTime = now + 0.1; // Small buffer to prevent immediate playback issues
        }

        source.start(playheadTime);
        playheadTime += buffer.duration;

        // Add fade-in for smoother transitions
        if (audioChunks.length === 0) {
          gainNode.gain.setValueAtTime(0.8, playheadTime - buffer.duration);
          gainNode.gain.linearRampToValueAtTime(1.0, playheadTime - buffer.duration + 0.05);
        }

        updatePlaybackStatus(`Playing audio chunk (Session: ${sessionId})`);

        // Schedule next chunk with better timing
        const nextChunkDelay = Math.max(0, (buffer.duration * 1000) - 50); // Play next chunk 50ms before current ends
        setTimeout(() => {
          if (audioChunks.length > 0) {
            chunkPlay();
          } else {
            isPlaying = false;
            updatePlaybackStatus(
              "Audio streaming paused - waiting for more chunks..."
            );
          }
        }, nextChunkDelay);
        
      } catch (error) {
        console.error("Audio playback error:", error);
        isPlaying = false;
        hideAudioPlaybackIndicator();
        
        // Try to recover by restarting playback after a brief delay
        if (audioChunks.length > 0) {
          console.log("🔄 Attempting audio recovery...");
          setTimeout(() => {
            recoverAudioPlayback();
          }, 200);
        }
      }
    }
  }

  function playAudioChunk(base64Audio) {
    try {
      // Initialize audio context if not already done
      if (!initializeAudioContext()) {
        console.error("Failed to initialize audio context");
        return;
      }

      // Show audio playback indicator
      showAudioPlaybackIndicator();

      // Convert base64 to PCM data
      const float32Array = base64ToPCMFloat32(base64Audio);
      if (!float32Array || float32Array.length === 0) {
        console.warn("Invalid audio data received");
        return;
      }

      // Add chunk to buffer for smoother playback
      audioBuffer.push(float32Array);
      
      // Wait for minimum buffer before starting playback to prevent choppy audio
      if (!isPlaying && !isBuffering) {
        if (audioBuffer.length >= minBufferSize) {
          // We have enough chunks buffered, start playing
          isBuffering = false;
          audioChunks = [...audioBuffer]; // Copy buffered chunks to playback queue
          audioBuffer = []; // Clear buffer
          
          isPlaying = true;
          audioContext
            .resume()
            .then(() => {
              console.log("Starting audio playback with", audioChunks.length, "chunks");
              chunkPlay();
            })
            .catch((err) => {
              console.error("Failed to resume audio context:", err);
              isPlaying = false;
            });
        } else {
          // Still buffering
          isBuffering = true;
          console.log(`Buffering audio chunks: ${audioBuffer.length}/${minBufferSize}`);
        }
      } else if (isPlaying) {
        // Already playing, add directly to playback queue
        audioChunks.push(float32Array);
      } else if (isBuffering) {
        // Check if we have enough to start playing now
        if (audioBuffer.length >= minBufferSize) {
          isBuffering = false;
          audioChunks = [...audioBuffer];
          audioBuffer = [];
          
          isPlaying = true;
          audioContext
            .resume()
            .then(() => {
              console.log("Starting buffered audio playback");
              chunkPlay();
            })
            .catch((err) => {
              console.error("Failed to resume audio context:", err);
              isPlaying = false;
            });
        }
      }
    } catch (error) {
      console.error("Error in playAudioChunk:", error);
      isPlaying = false;
      isBuffering = false;
      hideAudioPlaybackIndicator();
    }
  }

  /**
   * Stop all audio playback immediately (both WebSocket streaming and HTML5 audio)
   * This is called when a new query starts to prevent overlapping audio
   */
  function stopAllAudioPlayback() {
    console.log("🛑 Stopping all audio playback for new query");
    
    // Stop WebSocket streaming audio
    resetAudioPlayback();
    
    // Stop any currently playing HTML5 Audio element
    if (currentAudioElement) {
      try {
        currentAudioElement.pause();
        currentAudioElement.currentTime = 0;
        currentAudioElement = null;
        console.log("🛑 Stopped HTML5 audio playback");
      } catch (error) {
        console.warn("Error stopping HTML5 audio:", error);
      }
    }
    
    // Stop and close audio context completely
    if (audioContext && audioContext.state !== "closed") {
      try {
        audioContext.suspend().then(() => {
          if (audioContext && audioContext.state !== "closed") {
            audioContext.close();
          }
        }).catch(err => console.warn("Error closing audio context:", err));
        audioContext = null;
      } catch (error) {
        console.warn("Error stopping audio context:", error);
      }
    }
    
    // Hide any audio indicators
    hideAudioPlaybackIndicator();
    
    console.log("✅ All audio playback stopped successfully");
  }

  function resetAudioPlayback() {
    audioChunks = [];
    audioBuffer = [];
    isPlaying = false;
    isBuffering = false;
    wavHeaderSet = true;

    if (audioContext) {
      playheadTime = audioContext.currentTime;
    }

    // Stop any currently playing HTML5 Audio element
    if (currentAudioElement) {
      try {
        currentAudioElement.pause();
        currentAudioElement.currentTime = 0;
        currentAudioElement = null;
        console.log("🛑 Stopped previous HTML5 audio playback");
      } catch (error) {
        console.warn("Error stopping previous audio:", error);
      }
    }

    hideAudioPlaybackIndicator();
  }

  /**
   * Reset audio playback system specifically for session switching
   * This ensures clean audio state when switching between chat sessions
   */
  function resetAudioPlaybackForNewSession() {
    // Stop any currently playing audio
    if (audioContext && audioContext.state !== "closed") {
      try {
        // Suspend and close the audio context to stop all audio nodes
        audioContext
          .suspend()
          .then(() => {
            if (audioContext && audioContext.state !== "closed") {
              return audioContext.close();
            }
          })
          .catch((err) => {
            // Audio context close error
          });
      } catch (error) {
        // Error stopping audio context
      }
    }

    // Reset all audio playback variables to ensure clean state
    audioContext = null;
    audioChunks = [];
    audioBuffer = [];
    playheadTime = 0;
    isPlaying = false;
    isBuffering = false;
    wavHeaderSet = true; // Reset WAV header flag for new session

    // Stop any currently playing HTML5 Audio element
    if (currentAudioElement) {
      try {
        currentAudioElement.pause();
        currentAudioElement.currentTime = 0;
        currentAudioElement = null;
        console.log("🛑 Stopped HTML5 audio for new session");
      } catch (error) {
        console.warn("Error stopping HTML5 audio for new session:", error);
      }
    }

    // Hide any audio playback indicators
    hideAudioPlaybackIndicator();

    // Clear any TTS status
    const ttsArea = document.getElementById("ttsStreamingArea");
    if (ttsArea) {
      ttsArea.remove();
    }

    // Clear any LLM streaming area
    const llmArea = document.getElementById("llmStreamingArea");
    if (llmArea) {
      llmArea.remove();
    }

    // Clean up temporary audio files when switching sessions
    cleanupTempAudioFiles();
  }

  /**
   * Ensure audio system is ready for the current session
   * This should be called when establishing a new WebSocket connection
   */
  function ensureAudioSystemReady() {
    // Reset audio state to ensure clean initialization for new session
    audioChunks = [];
    isPlaying = false;
    wavHeaderSet = true; // Ensure WAV header processing is reset for new session

    // Don't create audio context here - let it be created when first needed
    // This prevents issues with browser audio policy
    if (audioContext) {
      playheadTime = audioContext.currentTime;
    } else {
      playheadTime = 0;
    }

    // Hide any old audio indicators
    hideAudioPlaybackIndicator();
  }

  /**
   * Show the audio playback indicator with animation
   */
  function showAudioPlaybackIndicator() {
    const playbackContainer = document.getElementById("audioPlaybackStatus");
    if (playbackContainer) {
      playbackContainer.style.display = "block";

      // Update status text
      const statusText = document.getElementById("playbackStatusText");
      if (statusText) {
        statusText.textContent = "Audio is streaming and playing...";
      }
    }
  }

  /**
   * Hide the audio playback indicator
   */
  function hideAudioPlaybackIndicator() {
    const playbackContainer = document.getElementById("audioPlaybackStatus");
    if (playbackContainer) {
      playbackContainer.style.display = "none";
    }
  }

  /**
   * Update playback status text
   */
  function updatePlaybackStatus(text) {
    const statusText = document.getElementById("playbackStatusText");
    if (statusText) {
      statusText.textContent = text;
    }
  }

  // Session Management Functions

  /**
   * Load all sessions from the backend
   */
  async function loadAllSessions() {
    try {
      const response = await fetch("/api/sessions");
      const data = await response.json();

      if (data.success) {
        allSessions = data.sessions;
        displaySessionsInSidebar();
      } else {
      }
    } catch (error) {}
  }

  /**
   * Display sessions in the sidebar grouped by time
   */
  function displaySessionsInSidebar() {
    const today = new Date();
    const todayChats = document.getElementById("todayChats");
    const weekChats = document.getElementById("weekChats");
    const monthChats = document.getElementById("monthChats");

    // Clear existing content
    if (todayChats) todayChats.innerHTML = "";
    if (weekChats) weekChats.innerHTML = "";
    if (monthChats) monthChats.innerHTML = "";

    allSessions.forEach((session) => {
      const sessionDate = new Date(session.last_activity);
      const timeDiff = today - sessionDate;
      const daysDiff = Math.floor(timeDiff / (1000 * 60 * 60 * 24));

      const chatItem = createChatItem(session);

      if (daysDiff === 0) {
        // Today
        if (todayChats) todayChats.appendChild(chatItem);
      } else if (daysDiff <= 7) {
        // Past 7 days
        if (weekChats) weekChats.appendChild(chatItem);
      } else if (daysDiff <= 30) {
        // Past 30 days
        if (monthChats) monthChats.appendChild(chatItem);
      }
    });

    // Mark current session as active
    updateActiveSession();
  }

  /**
   * Create a chat item element for the sidebar
   */
  function createChatItem(session) {
    const chatItem = document.createElement("button");
    chatItem.className = "chat-item";
    chatItem.setAttribute("data-session-id", session.session_id);

    // Create preview text
    let previewText = session.preview || "New conversation";
    if (previewText.length > 40) {
      previewText = previewText.substring(0, 40) + "...";
    }

    chatItem.textContent = previewText;
    chatItem.title = previewText; // Show full text on hover

    // Add click event to switch to this session
    chatItem.addEventListener("click", () => {
      switchToSession(session.session_id);
    });

    return chatItem;
  }

  /**
   * Switch to a different session
   */
  async function switchToSession(newSessionId) {
    if (newSessionId === sessionId) return; // Already on this session
    // Stop any ongoing streaming before switching sessions
    if (isStreaming) {
      await stopAudioStreaming();
    }

    // Reset audio playback system for new session
    resetAudioPlaybackForNewSession();

    // Update session ID
    sessionId = newSessionId;

    // Update URL without page refresh
    const newUrl = `${window.location.pathname}?session_id=${sessionId}`;
    window.history.pushState({ sessionId }, "", newUrl);

    // Update session display
    updateSessionDisplay();
    updateActiveSession();

    // Load chat history for this session
    await loadChatHistory();

    // Disconnect current WebSocket if connected and reconnect with new session
    if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
      audioStreamSocket.close();
      // Small delay before updating status
      setTimeout(() => {
        // Don't auto-reconnect, let user click to start streaming
        updateConnectionStatus("disconnected");
      }, 100);
    }
  }

  /**
   * Start a new chat session
   */
  function startNewChat() {
    const newSessionId = generateSessionId();
    switchToSession(newSessionId);
  }

  /**
   * Update active session highlighting in sidebar
   */
  function updateActiveSession() {
    // Remove active class from all chat items
    document.querySelectorAll(".chat-item").forEach((item) => {
      item.classList.remove("active");
    });

    // Add active class to current session
    const currentSessionItem = document.querySelector(
      `[data-session-id="${sessionId}"]`
    );
    if (currentSessionItem) {
      currentSessionItem.classList.add("active");
    }
  }

  /**
   * Update session display in footer
   */
  function updateSessionDisplay() {
    const sessionIdElement = document.getElementById("sessionId");
    if (sessionIdElement) {
      // Show only last 8 characters of session ID
      sessionIdElement.textContent = sessionId.slice(-8);
      sessionIdElement.title = sessionId; // Show full ID on hover
    }

    const streamingSessionElement =
      document.getElementById("streamingSessionId");
    if (streamingSessionElement) {
      streamingSessionElement.textContent = sessionId;
    }
  }

  /**
   * Load chat history for current session
   */
  async function loadChatHistory() {
    try {
      const response = await fetch(`/agent/chat/${sessionId}/history`);
      const data = await response.json();

      if (data.success && data.messages) {
        // Clear current messages
        if (chatMessages) {
          chatMessages.innerHTML = "";
        }

        // Add messages to chat
        data.messages.forEach((message) => {
          if (message.role === "user") {
            addMessageToChat(message.content, true);
          } else if (message.role === "assistant") {
            addMessageToChat(message.content, false);
          }
        });

        // If no messages, show welcome message
        if (data.messages.length === 0) {
          showWelcomeMessage();
        }
      } else {
        // Show welcome message for new sessions
        showWelcomeMessage();
      }
    } catch (error) {
      showWelcomeMessage();
    }
  }

  /**
   * Show welcome message
   */
  function showWelcomeMessage() {
    if (!chatMessages) return;

    chatMessages.innerHTML = `
      <div class="welcome-message">
        <div class="welcome-content">
          <div class="welcome-avatar">
            <i class="fas fa-microphone-alt"></i>
          </div>
          <h2>Welcome to AI Voice Agent</h2>
          <p>Start a conversation by clicking the microphone button below. I'll listen and respond in real-time!</p>
        </div>
      </div>
    `;
  }

  // Override the existing initializeSession function to include session display update
  const originalInitializeSession = initializeSession;
  initializeSession = function () {
    if (originalInitializeSession) {
      originalInitializeSession();
    }
    updateSessionDisplay();
  };

  /**
   * Update web search toggle button state
   */
  function updateWebSearchToggle() {
    if (!webSearchToggle) {
      return;
    }

    webSearchToggle.setAttribute("data-enabled", webSearchEnabled);
    const span = webSearchToggle.querySelector("span");
    if (span) {
      const newText = webSearchEnabled ? "Web Search: ON" : "Web Search";
      span.textContent = newText;
    } else {
    }

    // Visual feedback
    if (webSearchEnabled) {
    } else {
    }
  }

  /**
   * Show web search notification
   */
  function showWebSearchNotification(enabled) {
    const notification = document.createElement("div");
    notification.className = "web-search-notification";
    notification.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-${enabled ? "check-circle" : "times-circle"}"></i>
        <span>Web Search ${enabled ? "Enabled" : "Disabled"}</span>
      </div>
    `;

    // Style the notification
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${
        enabled
          ? "linear-gradient(135deg, #10b981, #059669)"
          : "linear-gradient(135deg, #ef4444, #dc2626)"
      };
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 1000;
      opacity: 0;
      transform: translateX(100%);
      transition: all 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.style.opacity = "1";
      notification.style.transform = "translateX(0)";
    }, 10);

    // Animate out and remove
    setTimeout(() => {
      notification.style.opacity = "0";
      notification.style.transform = "translateX(100%)";
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }

  /**
   * Search the web using Tavily API
   */
  async function searchWeb(query) {
    try {
      const response = await fetch("/api/web-search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return {
        success: false,
        query,
        results: [],
        error_message: "Failed to perform web search",
      };
    }
  }

  /**
   * Display web search results in chat
   */
  function displayWebSearchResults(searchData) {
    if (
      !searchData.success ||
      !searchData.results ||
      searchData.results.length === 0
    ) {
      return "";
    }

    let resultsHtml = `
      <div class="web-search-results">
        <div class="web-search-header">
          <i class="fas fa-globe"></i>
          <span>Web Search Results for "${searchData.query}"</span>
        </div>
        <ul class="web-search-list">
    `;

    searchData.results.forEach((result, index) => {
      resultsHtml += `
        <li class="web-search-item">
          <div class="web-result-title">${escapeHtml(result.title)}</div>
          <div class="web-result-snippet">${escapeHtml(result.snippet)}</div>
          <a href="${escapeHtml(
            result.url
          )}" target="_blank" class="web-result-link" rel="noopener noreferrer">
            ${escapeHtml(result.url)}
          </a>
        </li>
      `;
    });

    resultsHtml += `
        </ul>
      </div>
    `;

    return resultsHtml;
  }

  /**
   * Show web search status indicator
   */
  function showWebSearchStatus(query) {
    if (!chatMessages) return;

    const statusElement = document.createElement("div");
    statusElement.className = "web-search-status searching";
    statusElement.innerHTML = `
      <i class="fas fa-spinner"></i>
      <span>Searching the web for "${escapeHtml(query)}"...</span>
    `;

    chatMessages.appendChild(statusElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return statusElement;
  }

  /**
   * Escape HTML to prevent XSS
   */
  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Expose webSearchEnabled globally for WebSocket
  window.getWebSearchEnabled = function () {
    return webSearchEnabled;
  };
});
