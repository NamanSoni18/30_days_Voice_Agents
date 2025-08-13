document.addEventListener("DOMContentLoaded", function () {
  console.log("Voice Agents App Loaded!");
  let voiceQueryRecorder;
  let voiceQueryChunks = [];
  let voiceQueryStream;
  let voiceQueryStartTime;
  let voiceQueryTimerInterval;

  // Session management
  let sessionId = getSessionIdFromUrl() || window.SESSION_ID || generateSessionId();
  initializeSession();

  // Voice query elements
  const voiceQueryBtn = document.getElementById("voiceQueryBtn");
  const voiceQueryStatus = document.getElementById("voiceQueryStatus");
  const voiceQueryTimer = document.getElementById("voiceQueryTimer");
  const voiceQueryMessageDisplay = document.getElementById("voiceQueryMessageDisplay");
  const voiceQueryContainer = document.getElementById("voiceQueryContainer");
  const voiceQueryTranscription = document.getElementById("voiceQueryTranscription");
  const voiceQueryLLMResponse = document.getElementById("voiceQueryLLMResponse");
  const voiceQueryAudioPlayer = document.getElementById("voiceQueryAudioPlayer");
  const askAgainBtn = document.getElementById("askAgainBtn");
  const toggleChatHistoryBtn = document.getElementById("toggleChatHistory");
  const chatHistoryContainer = document.getElementById("chatHistoryContainer");

  // Chat history management
  if (toggleChatHistoryBtn) {
    toggleChatHistoryBtn.addEventListener("click", toggleChatHistory);
  }

  // Session management functions
  function getSessionIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('session_id');
  }

  function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  function updateUrlWithSessionId(sessionId) {
    const url = new URL(window.location);
    url.searchParams.set('session_id', sessionId);
    window.history.replaceState({}, '', url);
    
    // Update session ID display
    const sessionIdElement = document.getElementById('sessionId');
    if (sessionIdElement) {
      sessionIdElement.textContent = sessionId;
    }
  }

  async function initializeSession() {
    updateUrlWithSessionId(sessionId);
    console.log(`Initializing session: ${sessionId}`);
    
    // Load existing chat history for this session
    await loadChatHistory();
  }

  async function loadChatHistory() {
    try {
      const response = await fetch(`/agent/chat/${sessionId}/history`);
      const data = await response.json();
      
      if (data.success && data.messages.length > 0) {
        console.log(`Loaded ${data.message_count} messages for session ${sessionId}`);
        displayChatHistory(data.messages);
        
        // Show notification that previous session was loaded
        showVoiceQueryMessage(`Previous session loaded with ${data.message_count} messages. Click "Show Chat History" to view them.`, 'success');
      } else {
        console.log(`No previous messages found for session ${sessionId}`);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }

  function displayChatHistory(messages) {
    const chatHistoryList = document.getElementById('chatHistoryList');
    if (!chatHistoryList) return;

    chatHistoryList.innerHTML = '';
    
    if (messages.length === 0) {
      chatHistoryList.innerHTML = '<p class="no-history">No previous messages in this session.</p>';
      return;
    }

    // Group messages by conversation pairs (user + assistant)
    const conversations = [];
    for (let i = 0; i < messages.length; i += 2) {
      const userMsg = messages[i];
      const assistantMsg = messages[i + 1];
      if (userMsg && assistantMsg && userMsg.role === 'user' && assistantMsg.role === 'assistant') {
        conversations.push({
          user: userMsg,
          assistant: assistantMsg,
          timestamp: userMsg.timestamp
        });
      }
    }

    if (conversations.length === 0) {
      chatHistoryList.innerHTML = '<p class="no-history">No complete conversations found.</p>';
      return;
    }

    conversations.forEach((conv, index) => {
      const conversationDiv = document.createElement('div');
      conversationDiv.className = 'conversation-card';
      conversationDiv.style.cursor = 'pointer';
      
      // Simple timestamp formatting - display as received from backend
      let timestamp;
      try {
        const dateObj = new Date(conv.timestamp);
        // Simple format: Month Day, Year at Hour:Minute AM/PM
        timestamp = dateObj.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
      } catch (error) {
        console.error('Error parsing timestamp:', error);
        timestamp = 'Just now';
      }
      
      const userPreview = conv.user.content.length > 80 ? 
        conv.user.content.substring(0, 80) + '...' : 
        conv.user.content;
      const assistantPreview = conv.assistant.content.length > 100 ? 
        conv.assistant.content.substring(0, 100) + '...' : 
        conv.assistant.content;

      conversationDiv.innerHTML = `
        <div class="conversation-header">
          <span class="conversation-number">Conversation ${conversations.length - index}</span>
          <span class="conversation-time">${timestamp}</span>
        </div>
        <div class="conversation-content">
          <div class="user-preview">
            <span class="role-label">👤 You:</span>
            <span class="preview-text">${userPreview}</span>
          </div>
          <div class="assistant-preview">
            <span class="role-label">🤖 AI:</span>
            <span class="preview-text">${assistantPreview}</span>
          </div>
        </div>
      `;
      
      // Add click event to display the conversation in the main area
      conversationDiv.addEventListener('click', function() {
        displayConversationInMainArea(conv.user.content, conv.assistant.content);
        
        // Close the chat history
        toggleChatHistory();
      });
      
      chatHistoryList.appendChild(conversationDiv);
    });
  }

  function displayConversationInMainArea(userQuestion, assistantResponse) {
    // Show the voice query container
    if (voiceQueryContainer) {
      voiceQueryContainer.style.display = "block";
    }
    
    // Display the user question
    if (voiceQueryTranscription) {
      voiceQueryTranscription.innerHTML = userQuestion;
    }
    
    // Display the AI response with markdown rendering
    if (voiceQueryLLMResponse) {
      try {
        if (typeof marked !== 'undefined') {
          marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false,
            highlight: function(code, lang) {
              if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                try {
                  return hljs.highlight(code, { language: lang }).value;
                } catch (err) {}
              }
              return code;
            }
          });
          const markdownHtml = marked.parse(assistantResponse);
          voiceQueryLLMResponse.innerHTML = markdownHtml;
          
          // Apply syntax highlighting
          if (typeof hljs !== 'undefined') {
            voiceQueryLLMResponse.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          voiceQueryLLMResponse.innerHTML = assistantResponse.replace(/\n/g, '<br>');
        }
      } catch (error) {
        console.error('Markdown parsing error:', error);
        voiceQueryLLMResponse.innerHTML = assistantResponse.replace(/\n/g, '<br>');
      }
    }
    
    // Clear audio player since this is from history (no audio available)
    if (voiceQueryAudioPlayer) {
      voiceQueryAudioPlayer.src = "";
    }
    
    // Keep the audio section hidden for history items
    const responseAudioSection = document.querySelector('.response-audio-section');
    if (responseAudioSection) {
      responseAudioSection.style.display = "none";
    }
    
    // Scroll to the conversation area
    voiceQueryContainer.scrollIntoView({ behavior: "smooth" });
    
    // Show success message
    showVoiceQueryMessage('Previous conversation loaded successfully!', 'success');
  }

  function toggleChatHistory() {
    const container = document.getElementById('chatHistoryContainer');
    const button = document.getElementById('toggleChatHistory');
    
    if (container.style.display === 'none' || !container.style.display) {
      container.style.display = 'block';
      button.textContent = 'Hide Chat History';
      loadChatHistory(); // Refresh the history
    } else {
      container.style.display = 'none';
      button.textContent = 'Show Chat History';
    }
  }

  // Audio player event listeners for auto-recording
  if (voiceQueryAudioPlayer) {
    voiceQueryAudioPlayer.addEventListener('ended', function() {
      console.log("Audio playback ended, starting auto-recording...");
      setTimeout(() => {
        if (!voiceQueryRecorder || voiceQueryRecorder.state !== "recording") {
          updateVoiceQueryButton('ready');
          startVoiceQuery();
        }
      }, 1000); // Wait 1 second before starting auto-recording
    });
  }



  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (voiceQueryBtn) {
      showVoiceQueryMessage("Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Safari.", "error");
      voiceQueryBtn.disabled = true;
    }
  } else {
    if (voiceQueryBtn) {
      voiceQueryBtn.addEventListener("click", toggleVoiceQuery);
      
      if (askAgainBtn) {
        askAgainBtn.addEventListener("click", function() {
          hideVoiceQuery();
          resetVoiceQueryState();
          // Don't auto-start recording when manually clicking "Ask Again"
        });
      }
    }
  }

  // Toggle function for the combined button
  function toggleVoiceQuery() {
    const currentState = voiceQueryBtn.getAttribute('data-state');
    
    if (currentState === 'ready' || currentState === 'completed') {
      startVoiceQuery();
    } else if (currentState === 'recording') {
      stopVoiceQuery();
    }
  }

  // Update button state and appearance
  function updateVoiceQueryButton(state) {
    if (!voiceQueryBtn) return;
    
    const btnIcon = voiceQueryBtn.querySelector('.btn-icon');
    const btnText = voiceQueryBtn.querySelector('.btn-text');
    
    voiceQueryBtn.setAttribute('data-state', state);
    
    switch (state) {
      case 'ready':
        voiceQueryBtn.disabled = false;
        voiceQueryBtn.className = 'btn primary';
        btnIcon.textContent = '🎤';
        btnText.textContent = 'Start Recording';
        break;
      case 'recording':
        voiceQueryBtn.disabled = false;
        voiceQueryBtn.className = 'btn secondary recording';
        btnIcon.textContent = '⏹️';
        btnText.textContent = 'Stop Recording';
        break;
      case 'processing':
        voiceQueryBtn.disabled = true;
        voiceQueryBtn.className = 'btn processing';
        btnIcon.textContent = '⏳';
        btnText.textContent = 'Processing...';
        break;
      case 'completed':
        voiceQueryBtn.disabled = false;
        voiceQueryBtn.className = 'btn primary';
        btnIcon.textContent = '🎤';
        btnText.textContent = 'Ask Another Question';
        break;
    }
  }

  function getSupportedMimeType() {
    const mimeTypes = [
      'audio/webm',
    ];
    
    for (let mimeType of mimeTypes) {
      if (MediaRecorder.isTypeSupported(mimeType)) {
        return mimeType;
      }
    }
    
    return 'audio/webm';
  }
  async function startVoiceQuery() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showVoiceQueryMessage("Your browser doesn't support audio recording.", "error");
      return;
    }

    try {
      voiceQueryChunks = [];
      voiceQueryStartTime = Date.now();
      voiceQueryStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });

      voiceQueryRecorder = new MediaRecorder(voiceQueryStream, {
        mimeType: getSupportedMimeType()
      });

      voiceQueryRecorder.onstart = function() {
        console.log("Voice query recording started");
        voiceQueryStatus.style.display = "block";
        updateVoiceQueryButton('recording');
        hideVoiceQuery();
        showVoiceQueryMessage("Recording your question! Speak clearly into your microphone.", "success");
        
        startVoiceQueryTimer();
      };

      voiceQueryRecorder.ondataavailable = function(event) {
        if (event.data.size > 0) {
          voiceQueryChunks.push(event.data);
        }
      };

      voiceQueryRecorder.onstop = function() {
        console.log("Voice query recording stopped");
        const recordingDuration = Math.round((Date.now() - voiceQueryStartTime) / 1000);
        
        const audioBlob = new Blob(voiceQueryChunks, { type: getSupportedMimeType() });
        processVoiceQuery(audioBlob);
        
        if (voiceQueryStream) {
          voiceQueryStream.getTracks().forEach(track => track.stop());
        }
        
        resetVoiceQueryState();
      };

      voiceQueryRecorder.onerror = function(event) {
        console.error("Voice query recorder error:", event.error);
        showVoiceQueryMessage("Recording failed. Please try again.", "error");
        resetVoiceQueryState();
      };

      voiceQueryRecorder.start();

    } catch (error) {
      console.error("Error starting voice query:", error);
      
      if (error.name === 'NotAllowedError') {
        showVoiceQueryMessage("Microphone access denied. Please allow microphone access and try again.", "error");
      } else if (error.name === 'NotFoundError') {
        showVoiceQueryMessage("No microphone found. Please connect a microphone and try again.", "error");
      } else if (error.name === 'NotSupportedError') {
        showVoiceQueryMessage("Audio recording not supported in your browser.", "error");
      } else {
        showVoiceQueryMessage("Failed to start recording: " + error.message, "error");
      }
      
      resetVoiceQueryState();
    }
  }

  function stopVoiceQuery() {
    if (voiceQueryRecorder && voiceQueryRecorder.state === "recording") {
      voiceQueryRecorder.stop();
      stopVoiceQueryTimer();
      showVoiceQueryMessage("Recording stopped! Preparing to process...", "loading");
    } else {
      console.log("No active voice query recording to stop");
      resetVoiceQueryState();
    }
  }

  function startVoiceQueryTimer() {
    if (voiceQueryTimer) {
      let seconds = 0;
      voiceQueryTimer.textContent = "0s";
      
      voiceQueryTimerInterval = setInterval(() => {
        seconds++;
        voiceQueryTimer.textContent = `${seconds}s`;
      }, 1000);
    }
  }

  function stopVoiceQueryTimer() {
    if (voiceQueryTimerInterval) {
      clearInterval(voiceQueryTimerInterval);
      voiceQueryTimerInterval = null;
    }
  }

  function resetVoiceQueryState() {
    updateVoiceQueryButton('ready');
    if (voiceQueryStatus) voiceQueryStatus.style.display = "none";
    
    stopVoiceQueryTimer();
    
    if (voiceQueryStream) {
      voiceQueryStream.getTracks().forEach(track => track.stop());
      voiceQueryStream = null;
    }
  }

  async function processVoiceQuery(audioBlob) {
    try {
      updateVoiceQueryButton('processing');
      showVoiceQueryProcessing();
      
      const formData = new FormData();
      const filename = `voice_query_${Date.now()}.wav`;
      formData.append('audio', audioBlob, filename);
      updateProcessingStep('transcribing');
    
      setTimeout(() => updateProcessingStep('analyzing'), 1000);
      setTimeout(() => updateProcessingStep('generating'), 2000);
      setTimeout(() => updateProcessingStep('speech'), 3000);
      
      // Use the new chat endpoint with session ID with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
      
      const response = await fetch(`/agent/chat/${sessionId}`, {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        // Update to final step
        updateProcessingStep('completed');
        
        // Small delay to show completion
        setTimeout(() => {
          hideVoiceQueryProcessing();
          updateVoiceQueryButton('completed');
          showVoiceQuery(data.transcription, data.llm_response, data.audio_url);
          showVoiceQueryMessage('AI response generated successfully! Audio will auto-play and then start recording for your next question.', 'success');
          
          // Refresh chat history if it's currently visible
          if (chatHistoryContainer && chatHistoryContainer.style.display === 'block') {
            loadChatHistory();
          }
        }, 1000);
      } else {
        // Handle error responses with fallback audio
        hideVoiceQueryProcessing();
        updateVoiceQueryButton('ready');
        
        // Determine error type and show appropriate message
        const errorType = data.error_type || 'general_error';
        const errorMessage = data.message || 'An unexpected error occurred';
        
        console.error(`Voice query error (${errorType}):`, errorMessage);
        
        // Show error-specific messages to user
        let userMessage = '';
        switch (errorType) {
          case 'api_keys_missing':
            userMessage = '🔧 Configuration issue detected. Please contact support.';
            break;
          case 'file_error':
            userMessage = '🎤 Audio file issue. Please try recording again.';
            break;
          case 'stt_error':
            userMessage = '🎯 Having trouble understanding your audio. Please speak clearly and try again.';
            break;
          case 'no_speech':
            userMessage = '🔇 No speech detected. Please speak clearly into your microphone.';
            break;
          case 'llm_error':
            userMessage = '🤖 AI thinking process interrupted. Please try again in a moment.';
            break;
          case 'tts_error':
            userMessage = '🔊 Voice generation issue. The text response is still available.';
            break;
          default:
            userMessage = '⚠️ Connection issue. Please check your internet and try again.';
        }
        
        showVoiceQueryMessage(userMessage, 'error');
        
        // If there's fallback audio or any response content, show it
        if (data.audio_url || data.llm_response || data.transcription) {
          setTimeout(() => {
            showVoiceQuery(
              data.transcription || '', 
              data.llm_response || errorMessage, 
              data.audio_url
            );
            
            // Auto-play fallback audio if available
            if (data.audio_url && voiceQueryAudioPlayer) {
              setTimeout(() => {
                voiceQueryAudioPlayer.play().catch(e => {
                  console.log("Auto-play failed for fallback audio:", e);
                });
              }, 500);
            }
          }, 2000);
        }
        
        // Auto-restart recording for certain error types after delay
        if (['no_speech', 'stt_error', 'file_error'].includes(errorType)) {
          setTimeout(() => {
            if (!voiceQueryRecorder || voiceQueryRecorder.state !== "recording") {
              console.log("Auto-restarting recording after error...");
              updateVoiceQueryButton('ready');
              startVoiceQuery();
            }
          }, 3000);
        }
      }
      
    } catch (error) {
      console.error('Voice query processing error:', error);
      hideVoiceQueryProcessing();
      updateVoiceQueryButton('ready');
      
      // Handle network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        showVoiceQueryMessage('🌐 Network connection error. Please check your internet connection and try again.', 'error');
      } else if (error.name === 'AbortError') {
        showVoiceQueryMessage('⏱️ Request timed out. Please try again.', 'error');
      } else {
        showVoiceQueryMessage(`❌ Unexpected error: ${error.message}`, 'error');
      }
      
      // Auto-restart recording after network errors
      setTimeout(() => {
        if (!voiceQueryRecorder || voiceQueryRecorder.state !== "recording") {
          console.log("Auto-restarting recording after network error...");
          updateVoiceQueryButton('ready');
          startVoiceQuery();
        }
      }, 4000);
    }
  }

  function showVoiceQuery(transcription, llmResponse, audioUrl) {
    if (voiceQueryContainer && voiceQueryTranscription && voiceQueryLLMResponse && voiceQueryAudioPlayer) {
      voiceQueryTranscription.innerHTML = transcription;
      try {

        if (typeof marked !== 'undefined') {
          marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false,
            highlight: function(code, lang) {
              if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                try {
                  return hljs.highlight(code, { language: lang }).value;
                } catch (err) {}
              }
              return code;
            }
          });
          const markdownHtml = marked.parse(llmResponse);
          voiceQueryLLMResponse.innerHTML = markdownHtml;
          if (typeof hljs !== 'undefined') {
            voiceQueryLLMResponse.querySelectorAll('pre code').forEach((block) => {
              hljs.highlightElement(block);
            });
          }
        } else {
          voiceQueryLLMResponse.innerHTML = llmResponse.replace(/\n/g, '<br>');
        }
      } catch (error) {
        console.error('Markdown parsing error:', error);
        voiceQueryLLMResponse.innerHTML = llmResponse.replace(/\n/g, '<br>');
      }
      
      // Keep audio section hidden for new responses (audio will auto-play)
      const responseAudioSection = document.querySelector('.response-audio-section');
      if (responseAudioSection) {
        responseAudioSection.style.display = "none";
      }
      
      voiceQueryAudioPlayer.src = audioUrl;
      voiceQueryAudioPlayer.style.display = "none"; // Keep player hidden
      voiceQueryContainer.style.display = "block";
      voiceQueryContainer.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => {
        voiceQueryAudioPlayer.play().catch(e => {
          console.log("Auto-play failed (browser policy):", e);
        });
      }, 500);
    }
  }

  function hideVoiceQuery() {
    if (voiceQueryContainer) {
      voiceQueryContainer.style.display = "none";
    }
    if (voiceQueryAudioPlayer && voiceQueryAudioPlayer.src) {
      voiceQueryAudioPlayer.src = "";
    }
    if (voiceQueryTranscription) {
      voiceQueryTranscription.innerHTML = "";
    }
    if (voiceQueryLLMResponse) {
      voiceQueryLLMResponse.innerHTML = "";
    }
  }

  function showVoiceQueryMessage(message, type) {
    if (voiceQueryMessageDisplay) {
      voiceQueryMessageDisplay.style.display = "flex";
      
      if (type === "loading") {
        voiceQueryMessageDisplay.innerHTML = `
          <div class="${type}-message">
            <div class="loading-spinner"></div>
            ${message}
          </div>
        `;
      } else {
        voiceQueryMessageDisplay.innerHTML = `
          <div class="${type}-message">
            ${message}
          </div>
        `;
      }

      // Auto-hide success and error messages after different durations
      if (type === "success") {
        setTimeout(() => {
          voiceQueryMessageDisplay.innerHTML = "";
          voiceQueryMessageDisplay.style.display = "none";
        }, 5000);
      } else if (type === "error") {
        setTimeout(() => {
          voiceQueryMessageDisplay.innerHTML = "";
          voiceQueryMessageDisplay.style.display = "none";
        }, 8000); // Show errors a bit longer
      }
    }
  }

  function showVoiceQueryProcessing() {
    if (voiceQueryMessageDisplay) {
      voiceQueryMessageDisplay.style.display = "flex";
      voiceQueryMessageDisplay.innerHTML = `
        <div class="processing-container">
          <div class="processing-title">🤖 AI is processing your question...</div>
          <div class="processing-steps">
            <div class="processing-step active" id="step-transcribing">
              <div class="step-icon loading"></div>
              <span>Transcribing audio</span>
            </div>
            <div class="processing-step" id="step-analyzing">
              <div class="step-icon"></div>
              <span>Analyzing question</span>
            </div>
            <div class="processing-step" id="step-generating">
              <div class="step-icon"></div>
              <span>Generating response</span>
            </div>
            <div class="processing-step" id="step-speech">
              <div class="step-icon"></div>
              <span>Creating speech</span>
            </div>
          </div>
        </div>
      `;
    }
  }

  function updateProcessingStep(currentStep) {
    const steps = {
      'transcribing': ['step-transcribing'],
      'analyzing': ['step-transcribing', 'step-analyzing'],
      'generating': ['step-transcribing', 'step-analyzing', 'step-generating'],
      'speech': ['step-transcribing', 'step-analyzing', 'step-generating', 'step-speech'],
      'completed': ['step-transcribing', 'step-analyzing', 'step-generating', 'step-speech']
    };

    // Reset all steps
    document.querySelectorAll('.processing-step').forEach(step => {
      step.classList.remove('active', 'completed');
      const icon = step.querySelector('.step-icon');
      icon.classList.remove('loading', 'completed');
    });

    const activeSteps = steps[currentStep] || [];
    
    activeSteps.forEach((stepId, index) => {
      const stepElement = document.getElementById(stepId);
      const icon = stepElement?.querySelector('.step-icon');
      
      if (index < activeSteps.length - 1 || currentStep === 'completed') {
        // Completed steps
        stepElement?.classList.add('completed');
        icon?.classList.add('completed');
      } else {
        // Current active step
        stepElement?.classList.add('active');
        icon?.classList.add('loading');
      }
    });
  }

  function hideVoiceQueryProcessing() {
    if (voiceQueryMessageDisplay) {
      voiceQueryMessageDisplay.innerHTML = "";
      voiceQueryMessageDisplay.style.display = "none";
    }
  }

});
