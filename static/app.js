document.addEventListener("DOMContentLoaded", function () {
  console.log("Voice Agents App Loaded!");

  // Removed TTS text generation functionality
  
  let mediaRecorder;
  let audioChunks = [];
  let currentStream;
  let recordingStartTime;
  let recordingTimer;

  const startRecordingBtn = document.getElementById("startRecordingBtn");
  const stopRecordingBtn = document.getElementById("stopRecordingBtn");
  const recordingStatus = document.getElementById("recordingStatus");
  const recordingTimerDisplay = document.getElementById("recordingTimer");
  const echoMessageDisplay = document.getElementById("echoMessageDisplay");
  const echoAudioContainer = document.getElementById("echoAudioContainer");
  const echoAudioPlayer = document.getElementById("echoAudioPlayer");
  const recordAgainBtn = document.getElementById("recordAgainBtn");
  const echoMurfBtn = document.getElementById("echoMurfBtn");
  const murfEchoContainer = document.getElementById("murfEchoContainer");
  const murfEchoPlayer = document.getElementById("murfEchoPlayer");
  const murfTranscriptionText = document.getElementById("murfTranscriptionText");

  let currentAudioBlob = null;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (startRecordingBtn) {
      showEchoMessage("Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Safari.", "error");
      startRecordingBtn.disabled = true;
    }
  } else {
    if (startRecordingBtn && stopRecordingBtn) {
      startRecordingBtn.addEventListener("click", startRecording);
      stopRecordingBtn.addEventListener("click", stopRecording);
      
      
      if (recordAgainBtn) {
        recordAgainBtn.addEventListener("click", function() {
          hideEchoAudio();
          hideMurfEcho();
          resetRecordingState();
        });
      }
      
      if (echoMurfBtn) {
        echoMurfBtn.addEventListener("click", function() {
          if (currentAudioBlob) {
            echoWithMurfVoice(currentAudioBlob);
          } else {
            showEchoMessage("No audio available. Please record something first.", "error");
          }
        });
      }
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showEchoMessage("Your browser doesn't support audio recording.", "error");
      return;
    }

    try {
      audioChunks = [];
      recordingStartTime = Date.now();
      currentStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });

      mediaRecorder = new MediaRecorder(currentStream, {
        mimeType: getSupportedMimeType()
      });

      mediaRecorder.onstart = function() {
        console.log("Recording started");
        recordingStatus.style.display = "block";
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = false;
        hideEchoAudio();
        showEchoMessage("Recording started! Speak into your microphone.", "success");
        
        startRecordingTimer();
      };

      mediaRecorder.ondataavailable = function(event) {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = function() {
        console.log("Recording stopped");
        const recordingDuration = Math.round((Date.now() - recordingStartTime) / 1000);
        
        const audioBlob = new Blob(audioChunks, { type: getSupportedMimeType() });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        showEchoAudio(audioUrl, recordingDuration, audioBlob);
        
        if (currentStream) {
          currentStream.getTracks().forEach(track => track.stop());
        }
        
        resetRecordingState();
      };

      mediaRecorder.onerror = function(event) {
        console.error("MediaRecorder error:", event.error);
        showEchoMessage("Recording failed. Please try again.", "error");
        resetRecordingState();
      };

      mediaRecorder.start();

    } catch (error) {
      console.error("Error starting recording:", error);
      
      if (error.name === 'NotAllowedError') {
        showEchoMessage("Microphone access denied. Please allow microphone access and try again.", "error");
      } else if (error.name === 'NotFoundError') {
        showEchoMessage("No microphone found. Please connect a microphone and try again.", "error");
      } else if (error.name === 'NotSupportedError') {
        showEchoMessage("Audio recording not supported in your browser.", "error");
      } else {
        showEchoMessage("Failed to start recording: " + error.message, "error");
      }
      
      resetRecordingState();
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      stopRecordingTimer();
      showEchoMessage("Recording stopped! Processing audio...", "success");
    } else {
      console.log("No active recording to stop");
      resetRecordingState();
    }
  }

  function startRecordingTimer() {
    if (recordingTimerDisplay) {
      let seconds = 0;
      recordingTimerDisplay.textContent = "0s";
      
      recordingTimer = setInterval(() => {
        seconds++;
        recordingTimerDisplay.textContent = `${seconds}s`;
      }, 1000);
    }
  }

  function stopRecordingTimer() {
    if (recordingTimer) {
      clearInterval(recordingTimer);
      recordingTimer = null;
    }
  }

  function resetRecordingState() {
    if (startRecordingBtn) startRecordingBtn.disabled = false;
    if (stopRecordingBtn) stopRecordingBtn.disabled = true;
    if (recordingStatus) recordingStatus.style.display = "none";
    
    stopRecordingTimer();
    
    if (currentStream) {
      currentStream.getTracks().forEach(track => track.stop());
      currentStream = null;
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

  function showEchoMessage(message, type) {
    if (echoMessageDisplay) {
      echoMessageDisplay.style.display = "flex";
      echoMessageDisplay.innerHTML = `
        <div class="${type}-message">
          ${message}
        </div>
      `;

      if (type === "success") {
        setTimeout(() => {
          echoMessageDisplay.innerHTML = "";
          echoMessageDisplay.style.display = "none";
        }, 5000);
      }
    }
  }

  function showEchoAudio(audioUrl, duration, audioBlob) {
    if (echoAudioPlayer && echoAudioContainer) {
      // Store the audio blob for Murf echo functionality
      currentAudioBlob = audioBlob;
      
      echoAudioPlayer.src = audioUrl;
      echoAudioContainer.style.display = "block";
      
      const durationText = duration ? ` (${duration}s)` : "";
      showEchoMessage(`Recording complete${durationText}! Your echo is ready to play.`, "success");
      
      // Enable the echo with Murf button
      if (echoMurfBtn) {
        echoMurfBtn.disabled = false;
      }
      
      echoAudioContainer.scrollIntoView({ behavior: "smooth" });
      
      setTimeout(() => {
        echoAudioPlayer.play().catch(e => {
          console.log("Auto-play failed (browser policy):", e);
        });
      }, 500);
    }
  }

  function hideEchoAudio() {
    if (echoAudioContainer) {
      echoAudioContainer.style.display = "none";
      
      const transcribeBtn = document.getElementById("transcribeAudioBtn");
      if (transcribeBtn) {
        transcribeBtn.remove();
      }
    }
    if (echoAudioPlayer && echoAudioPlayer.src) {
      URL.revokeObjectURL(echoAudioPlayer.src);
      echoAudioPlayer.src = "";
    }
    
    // Reset audio blob and disable Murf button
    currentAudioBlob = null;
    if (echoMurfBtn) {
      echoMurfBtn.disabled = true;
    }
    hideMurfEcho();
  }

  async function echoWithMurfVoice(audioBlob) {
    try {
      if (echoMurfBtn) {
        echoMurfBtn.disabled = true;
        echoMurfBtn.innerHTML = '<span class="btn-loader">Processing with Murf...</span>';
      }
      
      showEchoMessage("Processing audio with Murf voice...", "success");
      const formData = new FormData();
      const filename = `echo_recording_${Date.now()}.wav`;
      formData.append('audio', audioBlob, filename);
      const response = await fetch('/tts/echo', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok && data.success && data.audio_url) {
        // Show the Murf echo result
        showMurfEcho(data.audio_url, data.transcription);
        showEchoMessage('Echo with Murf voice generated successfully!', 'success');
      } else {
        throw new Error(data.detail || data.message || 'Failed to generate Murf echo');
      }
      
    } catch (error) {
      console.error('Murf echo error:', error);
      showEchoMessage(`Murf echo failed: ${error.message}`, 'error');
    } finally {
      // Reset button state
      if (echoMurfBtn) {
        echoMurfBtn.disabled = false;
        echoMurfBtn.innerHTML = '<span class="btn-text">Echo with Murf Voice</span>';
      }
    }
  }

  function showMurfEcho(audioUrl, transcription) {
    if (murfEchoContainer && murfEchoPlayer && murfTranscriptionText) {
      // Display transcription
      murfTranscriptionText.innerHTML = `<strong>Transcription:</strong> "${transcription}"`;
      
      // Set up audio player
      murfEchoPlayer.src = audioUrl;
      murfEchoContainer.style.display = "block";
      
      // Scroll to Murf echo container
      murfEchoContainer.scrollIntoView({ behavior: "smooth" });
      
      // Auto-play the Murf audio
      setTimeout(() => {
        murfEchoPlayer.play().catch(e => {
          console.log("Auto-play failed (browser policy):", e);
        });
      }, 500);
    }
  }

  function hideMurfEcho() {
    if (murfEchoContainer) {
      murfEchoContainer.style.display = "none";
    }
    if (murfEchoPlayer && murfEchoPlayer.src) {
      murfEchoPlayer.src = "";
    }
    if (murfTranscriptionText) {
      murfTranscriptionText.innerHTML = "";
    }
  }

});
