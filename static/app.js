document.addEventListener("DOMContentLoaded", function () {
  console.log("Voice Agents App Loaded!");
  let voiceQueryRecorder;
  let voiceQueryChunks = [];
  let voiceQueryStream;
  let voiceQueryStartTime;
  let voiceQueryTimerInterval;

  // Voice query elements
  const startVoiceQueryBtn = document.getElementById("startVoiceQueryBtn");
  const stopVoiceQueryBtn = document.getElementById("stopVoiceQueryBtn");
  const voiceQueryStatus = document.getElementById("voiceQueryStatus");
  const voiceQueryTimer = document.getElementById("voiceQueryTimer");
  const voiceQueryMessageDisplay = document.getElementById("voiceQueryMessageDisplay");
  const voiceQueryContainer = document.getElementById("voiceQueryContainer");
  const voiceQueryTranscription = document.getElementById("voiceQueryTranscription");
  const voiceQueryLLMResponse = document.getElementById("voiceQueryLLMResponse");
  const voiceQueryAudioPlayer = document.getElementById("voiceQueryAudioPlayer");
  const askAgainBtn = document.getElementById("askAgainBtn");



  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (startVoiceQueryBtn) {
      showVoiceQueryMessage("Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Safari.", "error");
      startVoiceQueryBtn.disabled = true;
    }
  } else {
    if (startVoiceQueryBtn && stopVoiceQueryBtn) {
      startVoiceQueryBtn.addEventListener("click", startVoiceQuery);
      stopVoiceQueryBtn.addEventListener("click", stopVoiceQuery);
      
      if (askAgainBtn) {
        askAgainBtn.addEventListener("click", function() {
          hideVoiceQuery();
          resetVoiceQueryState();
        });
      }
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
        startVoiceQueryBtn.disabled = true;
        stopVoiceQueryBtn.disabled = false;
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
    if (startVoiceQueryBtn) startVoiceQueryBtn.disabled = false;
    if (stopVoiceQueryBtn) stopVoiceQueryBtn.disabled = true;
    if (voiceQueryStatus) voiceQueryStatus.style.display = "none";
    
    stopVoiceQueryTimer();
    
    if (voiceQueryStream) {
      voiceQueryStream.getTracks().forEach(track => track.stop());
      voiceQueryStream = null;
    }
  }

  async function processVoiceQuery(audioBlob) {
    try {
      // Show initial processing state
      showVoiceQueryProcessing();
      
      const formData = new FormData();
      const filename = `voice_query_${Date.now()}.wav`;
      formData.append('audio', audioBlob, filename);
      
      // Start with transcribing step
      updateProcessingStep('transcribing');
      
      // Simulate realistic processing times
      setTimeout(() => updateProcessingStep('analyzing'), 1000);
      setTimeout(() => updateProcessingStep('generating'), 2000);
      setTimeout(() => updateProcessingStep('speech'), 3000);
      
      const response = await fetch('/llm/query', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        // Update to final step
        updateProcessingStep('completed');
        
        // Small delay to show completion
        setTimeout(() => {
          hideVoiceQueryProcessing();
          showVoiceQuery(data.transcription, data.llm_response, data.audio_url);
          showVoiceQueryMessage('AI response generated successfully!', 'success');
        }, 1000);
      } else {
        hideVoiceQueryProcessing();
        throw new Error(data.message || 'Failed to process voice query');
      }
      
    } catch (error) {
      console.error('Voice query processing error:', error);
      hideVoiceQueryProcessing();
      showVoiceQueryMessage(`Voice query failed: ${error.message}`, 'error');
    }
  }

  function showVoiceQuery(transcription, llmResponse, audioUrl) {
    if (voiceQueryContainer && voiceQueryTranscription && voiceQueryLLMResponse && voiceQueryAudioPlayer) {
      voiceQueryTranscription.innerHTML = transcription;
      try {
        // Configure marked for better rendering
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
      voiceQueryAudioPlayer.src = audioUrl;
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

      if (type === "success") {
        setTimeout(() => {
          voiceQueryMessageDisplay.innerHTML = "";
          voiceQueryMessageDisplay.style.display = "none";
        }, 5000);
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
