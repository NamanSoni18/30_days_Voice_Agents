document.addEventListener("DOMContentLoaded", function () {
  // Global variables
  let sessionId = getSessionIdFromUrl() || window.SESSION_ID || generateSessionId();
  let currentAssistantText = ""; // For real-time chat history updates
  let selectedPersona = "developer"; // Default persona
  let currentStreamingMessage = null; // Track current streaming message in new UI
  let isConnecting = false; // Track connection state
  let isStreaming = false; // Track streaming state
  let allSessions = []; // Store all sessions
  
  // DOM elements
  const toggleChatHistoryBtn = document.getElementById("toggleChatHistory");
  const chatHistoryContainer = document.getElementById("chatHistoryContainer");
  const personaSelect = document.getElementById("personaSelect");
  
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

  // Event listeners for new UI
  if (newChatBtn) {
    newChatBtn.addEventListener("click", startNewChat);
  }

  // Event listeners
  if (toggleChatHistoryBtn) {
    toggleChatHistoryBtn.addEventListener("click", toggleChatHistory);
  }

  // Persona selection event listener
  if (personaSelect) {
    personaSelect.addEventListener("change", function() {
      selectedPersona = personaSelect.value;
      updatePersonaDisplay();
      
      // Send persona update to WebSocket if connected
      if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
        audioStreamSocket.send(JSON.stringify({
          type: "persona_update",
          persona: selectedPersona
        }));
      }
      
      // Update persona badge
      const personaBadge = document.getElementById("currentPersona");
      if (personaBadge) {
        personaBadge.textContent = getPersonaDisplayName(selectedPersona).split(' ')[0];
        personaBadge.setAttribute('data-persona', selectedPersona);
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
    conversationModal.addEventListener("click", function(e) {
      if (e.target === conversationModal) {
        closeModal();
      }
    });
  }
  
  // Close modal with Escape key
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && conversationModal && conversationModal.style.display !== "none") {
      closeModal();
    }
  });

  // Initialize streaming mode
  initializeStreamingMode();

  // New UI Functions
  function updatePersonaDisplay() {
    const displayName = getPersonaDisplayName(selectedPersona);
    if (personaName) {
      personaName.textContent = displayName.split(' ')[0]; // Show just the first part
    }
    
    // Update avatar icon based on persona
    if (personaAvatar) {
      const icons = {
        developer: "fas fa-code",
        aizen: "fas fa-crown",
        luffy: "fas fa-anchor",
        politician: "fas fa-user-tie"
      };
      personaAvatar.innerHTML = `<i class="${icons[selectedPersona] || 'fas fa-robot'}"></i>`;
    }
    
    document.title = `Voice Agent - ${displayName}`;
  }

  function addMessageToChat(content, isUser = false, isStreaming = false) {
    if (!chatMessages) return;
    
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
      welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    if (isUser) {
      avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
    } else {
      const icons = {
        developer: "fas fa-code",
        aizen: "fas fa-crown", 
        luffy: "fas fa-anchor",
        politician: "fas fa-user-tie"
      };
      avatarDiv.innerHTML = `<i class="${icons[selectedPersona] || 'fas fa-robot'}"></i>`;
    }
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isUser) {
      contentDiv.textContent = content;
    } else {
      // For assistant messages, parse markdown
      try {
        if (typeof marked !== "undefined" && content) {
          contentDiv.innerHTML = marked.parse(content);
          // Apply syntax highlighting if available
          if (typeof hljs !== "undefined") {
            contentDiv.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          contentDiv.textContent = content;
        }
      } catch (error) {
        console.warn('Markdown parsing error:', error);
        contentDiv.textContent = content;
      }
    }
    
    if (isStreaming) {
      contentDiv.classList.add('streaming');
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
    
    const contentDiv = messageElement.querySelector('.message-content');
    if (contentDiv) {
      try {
        if (typeof marked !== "undefined" && content) {
          contentDiv.innerHTML = marked.parse(content);
          // Apply syntax highlighting if available
          if (typeof hljs !== "undefined") {
            contentDiv.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          contentDiv.textContent = content;
        }
      } catch (error) {
        console.warn('Markdown parsing error:', error);
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
    return (
      "session_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now()
    );
  }

  function getPersonaDisplayName(persona) {
    const personaNames = {
      "developer": "Developer (Default)",
      "aizen": "Sosuke Aizen (Bleach)",
      "luffy": "Monkey D. Luffy (One Piece)",
      "politician": "Politician"
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
      personaBadge.textContent = getPersonaDisplayName(selectedPersona).split(' ')[0];
      personaBadge.setAttribute('data-persona', selectedPersona);
    }
    
    console.log("Session initialized:", sessionId);
  }

  function initializeStreamingMode() {
    const audioStreamBtn = document.getElementById("audioStreamBtn");
    if (audioStreamBtn) {
      audioStreamBtn.addEventListener("click", function () {
        const state = this.getAttribute("data-state");
        
        // Prevent clicks while connecting
        if (isConnecting) {
          console.log("Connection in progress, please wait...");
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
    } catch (error) {
      console.error("Failed to load chat history:", error);
    }
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
      conversationDiv.addEventListener('click', function() {
        const userMessage = conv.user.content;
        const assistantMessage = conv.assistant ? conv.assistant.content : 'No response available';
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
    if (!conversationModal || !modalQuestionContent || !modalResponseContent) return;
    
    // Set the content
    modalQuestionContent.textContent = userMessage;
    
    // Parse assistant message as markdown
    try {
      if (typeof marked !== "undefined" && assistantMessage) {
        const markdownHtml = marked.parse(assistantMessage);
        modalResponseContent.innerHTML = markdownHtml;
        
        // Apply syntax highlighting if available
        if (typeof hljs !== "undefined") {
          modalResponseContent.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
          });
        }
      } else {
        modalResponseContent.innerHTML = assistantMessage ? assistantMessage.replace(/\n/g, '<br>') : 'No response available';
      }
    } catch (error) {
      console.warn('Markdown parsing error in modal:', error);
      modalResponseContent.innerHTML = assistantMessage ? assistantMessage.replace(/\n/g, '<br>') : 'No response available';
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

  function showMessage(message, type) {
    // Simple console log for now - can be enhanced with UI notifications
  }

  // ==================== AUDIO STREAMING FUNCTIONALITY ====================

  async function startAudioStreaming() {
    try {
      // Prevent multiple simultaneous connection attempts
      if (isConnecting) {
        console.log("Already connecting, please wait...");
        return;
      }
      
      isConnecting = true;
      
      // Show connecting state in button
      if (audioStreamBtn) {
        audioStreamBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        audioStreamBtn.className = "mic-button connecting";
        audioStreamBtn.setAttribute("data-state", "connecting");
        
        const micStatus = audioStreamBtn.querySelector('.mic-status');
        if (micStatus) {
          micStatus.textContent = 'Connecting...';
        } else {
          audioStreamBtn.innerHTML += '<span class="mic-status">Connecting...</span>';
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
      const wsUrl = `ws://localhost:8000/ws/audio-stream?session_id=${sessionId}`;
      audioStreamSocket = new WebSocket(wsUrl);
      
      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.CONNECTING) {
          audioStreamSocket.close();
          updateConnectionStatus("disconnected", "Connection timeout");
          isConnecting = false;
          console.error("WebSocket connection timeout");
        }
      }, 3000); // Reduced to 3 seconds for faster response

      audioStreamSocket.onopen = function (event) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        updateConnectionStatus("connected", "Connected");
        console.log("WebSocket connected successfully");
        
        // Send session ID and persona to establish the session on the backend
        audioStreamSocket.send(JSON.stringify({
          type: "session_id",
          session_id: sessionId,
          persona: selectedPersona
        }));
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
          updateStreamingStatus("🛑 Turn ended - User stopped talking", "success");
          if (data.final_transcript && data.final_transcript.trim()) {
            updateStreamingStatus(`✅ TURN COMPLETE: "${data.final_transcript}"`, "success");
          } else {
            updateStreamingStatus("⚠️ Turn ended but no speech detected", "warning");
            showNoSpeechMessage();
          }
        } else if (data.type === "transcription_complete") {
          if (data.text && data.text.trim()) {
            // Remove complete transcription message as requested
          } else {
            updateStreamingStatus("⚠️ No speech detected in recording", "warning");
            showNoSpeechMessage();
          }
        } else if (data.type === "streaming_complete") {
          updateStreamingStatus(`🎯 ${data.message}`, "success");
          if (!data.transcription || !data.transcription.trim()) {
            updateStreamingStatus("⚠️ Recording completed but no speech was detected", "warning");
            showNoSpeechMessage();
          }
        } else if (data.type === "transcription_error") {
          updateStreamingStatus("❌ Transcription error: " + data.message, "error");
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
            personaBadge.textContent = getPersonaDisplayName(data.persona).split(' ')[0];
            personaBadge.setAttribute('data-persona', data.persona);
          }
        }
      };

      audioStreamSocket.onerror = function (error) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        console.error("WebSocket error:", error);
        updateConnectionStatus("error", "Connection Error");
        
        // Reset button state on error
        if (audioStreamBtn) {
          audioStreamBtn.innerHTML = '<i class="fas fa-microphone"></i>';
          audioStreamBtn.className = "mic-button";
          audioStreamBtn.setAttribute("data-state", "ready");
          
          const micStatus = audioStreamBtn.querySelector('.mic-status');
          if (micStatus) {
            micStatus.textContent = 'Click to talk';
          } else {
            audioStreamBtn.innerHTML += '<span class="mic-status">Click to talk</span>';
          }
        }
      };

      audioStreamSocket.onclose = function (event) {
        clearTimeout(connectionTimeout);
        isConnecting = false;
        updateConnectionStatus("disconnected", "Disconnected");
        
        // Only show close message if it wasn't intentional
        if (event.code !== 1000) {
          console.log("WebSocket closed unexpectedly:", event.code, event.reason);
        }
        
        // Reset button state on close
        if (audioStreamBtn) {
          audioStreamBtn.innerHTML = '<i class="fas fa-microphone"></i>';
          audioStreamBtn.className = "mic-button";
          audioStreamBtn.setAttribute("data-state", "ready");
          
          const micStatus = audioStreamBtn.querySelector('.mic-status');
          if (micStatus) {
            micStatus.textContent = 'Click to talk';
          } else {
            audioStreamBtn.innerHTML += '<span class="mic-status">Click to talk</span>';
          }
        }
      };
    } catch (error) {
      isConnecting = false;
      console.error("Error starting audio streaming:", error);
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
        console.log("Already streaming, ignoring start request");
        return;
      }
      
      audioStreamStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,  // 16kHz for AssemblyAI
          channelCount: 1,    // Mono
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
      });

      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
      
      const source = audioContext.createMediaStreamSource(audioStreamStream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      
      processor.onaudioprocess = function(e) {
        if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32767));
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
        }
      };
      
      isStreaming = true;
      if (audioStreamBtn) {
        audioStreamBtn.innerHTML = '<i class="fas fa-stop"></i>';
        audioStreamBtn.className = "mic-button recording";
        audioStreamBtn.setAttribute("data-state", "recording");
        
        // Update mic status
        const micStatus = audioStreamBtn.querySelector('.mic-status');
        if (micStatus) {
          micStatus.textContent = 'Recording...';
        } else {
          audioStreamBtn.innerHTML += '<span class="mic-status">Recording...</span>';
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
      console.error("Error starting recording for streaming:", error);
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
        if (typeof audioStreamRecorder.stop === 'function') {
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
      if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
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
        const micStatus = audioStreamBtn.querySelector('.mic-status');
        if (micStatus) {
          micStatus.textContent = 'Click to talk';
        } else {
          audioStreamBtn.innerHTML += '<span class="mic-status">Click to talk</span>';
        }
      }

      updateConnectionStatus("disconnected", "Disconnected");
      updateStreamingStatus("Audio streaming stopped", "info");
    } catch (error) {
      console.error("Error stopping audio streaming:", error);
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
      'llmStreamingArea',
      'ttsStreamingArea', 
      'streamingSummaryArea',
      'noSpeechArea'
    ];
    
    elementsToHide.forEach(elementId => {
      const element = document.getElementById(elementId);
      if (element) {
        element.style.display = 'none';
        if (elementId === 'llmStreamingArea') {
          element.innerHTML = '';
        }
      }
    });
    
    // Clear status log
    if (streamingStatusLog) {
      streamingStatusLog.innerHTML = '';
    }
    
    // Hide status container
    if (audioStreamStatus) {
      audioStreamStatus.style.display = 'none';
    }
    
    // Reset chat history state
    currentAssistantText = "";
    
    resetAudioPlayback();
  }

  function clearPreviousTranscriptions() {
    // Clear live transcription area
    const liveArea = document.getElementById('liveTranscriptionArea');
    if (liveArea) {
      liveArea.style.display = 'none';
      const transcriptionText = document.getElementById('transcriptionText');
      if (transcriptionText) {
        transcriptionText.innerHTML = '';
      }
    }
    
    // Clear complete transcription area
    const completeArea = document.getElementById('completeTranscriptionArea');
    if (completeArea) {
      completeArea.style.display = 'none';
    }
    
    // Clear no speech area
    const noSpeechArea = document.getElementById('noSpeechArea');
    if (noSpeechArea) {
      noSpeechArea.style.display = 'none';
    }
    
    // Clear LLM streaming area
    const llmArea = document.getElementById('llmStreamingArea');
    if (llmArea) {
      llmArea.style.display = 'none';
      llmArea.innerHTML = '';
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
    const noHistoryMsg = chatHistoryList.querySelector('.no-history');
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
    conversationDiv.addEventListener('click', function() {
      const currentUserMessage = userMessage;
      const assistantMessage = currentAssistantText || 'Response in progress...';
      openConversationModal(currentUserMessage, assistantMessage);
    });

    // Scroll to new conversation
    conversationDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

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
          assistantContent.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
          });
        }
      } else {
        assistantContent.innerHTML = currentAssistantText.replace(/\n/g, '<br>');
      }
    } catch (error) {
      console.warn('Markdown parsing error:', error);
      assistantContent.innerHTML = currentAssistantText.replace(/\n/g, '<br>');
    }

    // Scroll to keep the conversation visible
    const assistantDiv = document.getElementById("current-assistant-response");
    if (assistantDiv) {
      assistantDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // Function to mark the response as saved
  function markResponseAsSaved() {
    // Mark streaming as complete in new UI
    if (currentStreamingMessage) {
      const contentDiv = currentStreamingMessage.querySelector('.message-content');
      if (contentDiv) {
        contentDiv.classList.remove('streaming');
      }
      currentStreamingMessage = null;
    }
    
    // Update legacy interface
    const assistantDiv = document.getElementById("current-assistant-response");
    if (assistantDiv) {
      // Remove the ID since this conversation is now complete
      assistantDiv.removeAttribute('id');
      const assistantContent = assistantDiv.querySelector('.message-content');
      if (assistantContent) {
        assistantContent.removeAttribute('id');
      }
      
      // Add a "saved" indicator
      const messageHeader = assistantDiv.querySelector('.message-header');
      if (messageHeader) {
        const savedIndicator = document.createElement('span');
        savedIndicator.className = 'saved-indicator';
        savedIndicator.innerHTML = '💾';
        savedIndicator.title = 'Response saved to database';
        savedIndicator.style.marginLeft = '8px';
        savedIndicator.style.fontSize = '12px';
        messageHeader.appendChild(savedIndicator);
      }
    }

    // Reset the accumulated text for next conversation
    currentAssistantText = "";

    // Update button text back to normal
    if (toggleChatHistoryBtn && toggleChatHistoryBtn.textContent.includes("New!")) {
      toggleChatHistoryBtn.textContent = "Show Chat History";
      toggleChatHistoryBtn.style.backgroundColor = "";
    }
  }

  function handleAudioChunk(audioData) {
    // Play the audio chunk for streaming
    playAudioChunk(audioData.audio_base64);
    
    // Remove the audio chunk received message as requested
    
    if (audioData.is_final) {
      updateStreamingStatus("Audio streaming complete!", "success");
      setTimeout(() => {
        if (!isPlaying && audioChunks.length === 0) {
          updatePlaybackStatus('Audio streaming complete!');
          setTimeout(() => {
            hideAudioPlaybackIndicator();
          }, 2000);
        }
      }, 1000);
    }
  }

  function displayLLMStreamingStart(userMessage) {
    let llmArea = document.getElementById('llmStreamingArea');
    
    if (!llmArea) {
      llmArea = document.createElement('div');
      llmArea.id = 'llmStreamingArea';
      llmArea.className = 'llm-streaming-area';
      
      // Insert after the complete transcription area or streaming status
      const completeArea = document.getElementById('completeTranscriptionArea');
      const statusContainer = document.getElementById('audioStreamStatus');
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
    
    llmArea.style.display = 'block';
    
    // Clear previous response and show generating message
    const responseText = document.getElementById('llmResponseText');
    if (responseText) {
      responseText.innerHTML = '<em>Generating response...</em>';
      responseText.setAttribute('data-raw-text', '');
    }
  }

  // Function to display LLM text chunks
  function displayLLMTextChunk(chunk, accumulatedLength) {
    const responseText = document.getElementById('llmResponseText');
    if (responseText) {
      // Append the new chunk
      let currentText = responseText.getAttribute('data-raw-text') || '';
      if (currentText === 'Generating response...') {
        currentText = '';
      }
      
      // Accumulate the raw text
      const newText = currentText + chunk;
      responseText.setAttribute('data-raw-text', newText);
      
      // Parse as Markdown and display
      try {
        if (typeof marked !== 'undefined') {
          const markdownHtml = marked.parse(newText);
          responseText.innerHTML = markdownHtml;
          
          // Apply syntax highlighting if available
          if (typeof hljs !== 'undefined') {
            responseText.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          // Fallback to simple line break replacement
          responseText.innerHTML = newText.replace(/\n/g, '<br>');
        }
      } catch (error) {
        console.warn('Markdown parsing error:', error);
        responseText.innerHTML = newText.replace(/\n/g, '<br>');
      }
      
      // Scroll to bottom
      responseText.scrollTop = responseText.scrollHeight;
    }
  }

  function displayTTSStreamingStart() {
    // Basic TTS streaming UI
    let ttsArea = document.getElementById('ttsStreamingArea');
    
    if (!ttsArea) {
      ttsArea = document.createElement('div');
      ttsArea.id = 'ttsStreamingArea';
      ttsArea.className = 'tts-streaming-area';
      ttsArea.innerHTML = `<h4>🎵 Audio Generation</h4><div class="audio-status">Generating audio...</div>`;
      
      const llmArea = document.getElementById('llmStreamingArea');
      const statusContainer = document.getElementById('audioStreamStatus');
      const insertAfter = llmArea || statusContainer;
      
      if (insertAfter) {
        insertAfter.parentNode.insertBefore(ttsArea, insertAfter.nextSibling);
      }
    }
    
    ttsArea.style.display = 'block';
  }

  // Removed displayAudioChunkReceived function - not needed for basic functionality

  function displayStreamingComplete(data) {
    let summaryArea = document.getElementById('streamingSummaryArea');
    
    if (!summaryArea) {
      summaryArea = document.createElement('div');
      summaryArea.id = 'streamingSummaryArea';
      summaryArea.className = 'streaming-summary-area';
      
      const ttsArea = document.getElementById('ttsStreamingArea');
      const statusContainer = document.getElementById('audioStreamStatus');
      const insertAfter = ttsArea || statusContainer;
      
      if (insertAfter) {
        insertAfter.parentNode.insertBefore(summaryArea, insertAfter.nextSibling);
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
    
    summaryArea.style.display = 'block';
    
    // Render final response as Markdown
    const finalResponseElement = document.getElementById('finalResponseContent');
    if (finalResponseElement && data.complete_response) {
      try {
        if (typeof marked !== 'undefined') {
          const markdownHtml = marked.parse(data.complete_response);
          finalResponseElement.innerHTML = markdownHtml;
          
          if (typeof hljs !== 'undefined') {
            finalResponseElement.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          finalResponseElement.innerHTML = data.complete_response.replace(/\n/g, '<br>');
        }
      } catch (error) {
        console.warn('Markdown parsing error in final response:', error);
        finalResponseElement.innerHTML = data.complete_response.replace(/\n/g, '<br>');
      }
    }
    
    summaryArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Removed displayAudioStreamingComplete function - not needed

  // ==================== AUDIO STREAMING PLAYBACK FUNCTIONS ====================
  // Based on Murf's WebSocket streaming reference implementation
  
  function initializeAudioContext() {
    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        playheadTime = audioContext.currentTime;
      }
      return true;
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
      return false;
    }
  }

  function base64ToPCMFloat32(base64) {
    try {
      let binary = atob(base64);
      const offset = wavHeaderSet ? 44 : 0; // Skip WAV header if present
      
      if (wavHeaderSet) {
        wavHeaderSet = false; // Only process header once
      }
      
      const length = binary.length - offset;
      const buffer = new ArrayBuffer(length);
      const byteArray = new Uint8Array(buffer);
      
      for (let i = 0; i < byteArray.length; i++) {
        byteArray[i] = binary.charCodeAt(i + offset);
      }

      const view = new DataView(byteArray.buffer);
      const sampleCount = byteArray.length / 2; // 16-bit samples
      const float32Array = new Float32Array(sampleCount);

      for (let i = 0; i < sampleCount; i++) {
        const int16 = view.getInt16(i * 2, true); // Little endian
        float32Array[i] = int16 / 32768; // Convert to float32 range [-1, 1]
      }

      return float32Array;
    } catch (error) {
      console.error('Error converting base64 to PCM:', error);
      return null;
    }
  }

  function chunkPlay() {
    if (audioChunks.length > 0) {
      const chunk = audioChunks.shift();
      
      if (audioContext.state === "suspended") {
        audioContext.resume();
      }
      
      try {
        const buffer = audioContext.createBuffer(1, chunk.length, SAMPLE_RATE);
        buffer.copyToChannel(chunk, 0);
        
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        
        const now = audioContext.currentTime;
        if (playheadTime < now) {
          playheadTime = now + 0.05; // Add small delay to prevent audio gaps
        }
        
        source.start(playheadTime);
        playheadTime += buffer.duration;
        
        updatePlaybackStatus(`Playing audio chunk`);
        
        // Continue playing remaining chunks
        if (audioChunks.length > 0) {
          chunkPlay();
        } else {
          isPlaying = false;
          updatePlaybackStatus('Audio streaming paused - waiting for more chunks...');
        }
      } catch (error) {
        console.error('Error playing audio chunk:', error);
        isPlaying = false;
        hideAudioPlaybackIndicator();
      }
    }
  }

  function playAudioChunk(base64Audio) {
    try {
      // Initialize audio context if not already done
      if (!initializeAudioContext()) {
        return;
      }

      // Show audio playback indicator
      showAudioPlaybackIndicator();

      // Convert base64 to PCM data
      const float32Array = base64ToPCMFloat32(base64Audio);
      if (!float32Array || float32Array.length === 0) {
        return;
      }
      
      // Add chunk to playback queue
      audioChunks.push(float32Array);

      // Start playback if not already playing
      if (!isPlaying && (playheadTime <= audioContext.currentTime + 0.1 || audioChunks.length >= 2)) {
        isPlaying = true;
        audioContext.resume().then(() => {
          chunkPlay();
        });
      }
    } catch (error) {
      console.error('Error in playAudioChunk:', error);
    }
  }

  function resetAudioPlayback() {
    audioChunks = [];
    isPlaying = false;
    wavHeaderSet = true;
    
    if (audioContext) {
      playheadTime = audioContext.currentTime;
    }
    
    hideAudioPlaybackIndicator();
  }

  /**
   * Show the audio playback indicator with animation
   */
  function showAudioPlaybackIndicator() {
    const playbackContainer = document.getElementById('audioPlaybackStatus');
    if (playbackContainer) {
      playbackContainer.style.display = 'block';
      
      // Update status text
      const statusText = document.getElementById('playbackStatusText');
      if (statusText) {
        statusText.textContent = 'Audio is streaming and playing...';
      }
    }
  }

  /**
   * Hide the audio playback indicator
   */
  function hideAudioPlaybackIndicator() {
    const playbackContainer = document.getElementById('audioPlaybackStatus');
    if (playbackContainer) {
      playbackContainer.style.display = 'none';
    }
  }

  /**
   * Update playback status text
   */
  function updatePlaybackStatus(text) {
    const statusText = document.getElementById('playbackStatusText');
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
      const response = await fetch('/api/sessions');
      const data = await response.json();
      
      if (data.success) {
        allSessions = data.sessions;
        displaySessionsInSidebar();
      } else {
        console.error('Failed to load sessions:', data.error);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  }

  /**
   * Display sessions in the sidebar grouped by time
   */
  function displaySessionsInSidebar() {
    const today = new Date();
    const todayChats = document.getElementById('todayChats');
    const weekChats = document.getElementById('weekChats');
    const monthChats = document.getElementById('monthChats');

    // Clear existing content
    if (todayChats) todayChats.innerHTML = '';
    if (weekChats) weekChats.innerHTML = '';
    if (monthChats) monthChats.innerHTML = '';

    allSessions.forEach(session => {
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
    const chatItem = document.createElement('button');
    chatItem.className = 'chat-item';
    chatItem.setAttribute('data-session-id', session.session_id);
    
    // Create preview text
    let previewText = session.preview || 'New conversation';
    if (previewText.length > 40) {
      previewText = previewText.substring(0, 40) + '...';
    }
    
    chatItem.textContent = previewText;
    chatItem.title = previewText; // Show full text on hover

    // Add click event to switch to this session
    chatItem.addEventListener('click', () => {
      switchToSession(session.session_id);
    });

    return chatItem;
  }

  /**
   * Switch to a different session
   */
  async function switchToSession(newSessionId) {
    if (newSessionId === sessionId) return; // Already on this session

    // Update session ID
    sessionId = newSessionId;
    
    // Update URL without page refresh
    const newUrl = `${window.location.pathname}?session_id=${sessionId}`;
    window.history.pushState({ sessionId }, '', newUrl);

    // Update session display
    updateSessionDisplay();
    updateActiveSession();

    // Load chat history for this session
    await loadChatHistory();

    // Disconnect current WebSocket if connected and reconnect with new session
    if (audioStreamSocket && audioStreamSocket.readyState === WebSocket.OPEN) {
      audioStreamSocket.close();
      // Small delay before reconnecting
      setTimeout(() => {
        // Don't auto-reconnect, let user click to start streaming
        updateConnectionStatus('disconnected');
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
    document.querySelectorAll('.chat-item').forEach(item => {
      item.classList.remove('active');
    });

    // Add active class to current session
    const currentSessionItem = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (currentSessionItem) {
      currentSessionItem.classList.add('active');
    }
  }

  /**
   * Update session display in footer
   */
  function updateSessionDisplay() {
    const sessionIdElement = document.getElementById('sessionId');
    if (sessionIdElement) {
      // Show only last 8 characters of session ID
      sessionIdElement.textContent = sessionId.slice(-8);
      sessionIdElement.title = sessionId; // Show full ID on hover
    }

    const streamingSessionElement = document.getElementById('streamingSessionId');
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
          chatMessages.innerHTML = '';
        }

        // Add messages to chat
        data.messages.forEach(message => {
          if (message.role === 'user') {
            addMessageToChat(message.content, true);
          } else if (message.role === 'assistant') {
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
      console.error('Error loading chat history:', error);
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
  initializeSession = function() {
    if (originalInitializeSession) {
      originalInitializeSession();
    }
    updateSessionDisplay();
  };
});
