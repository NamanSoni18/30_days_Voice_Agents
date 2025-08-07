document.addEventListener("DOMContentLoaded", function () {
  console.log("Voice Agents App Loaded!");

  const textInput = document.getElementById("textInput");
  const generateBtn = document.getElementById("generateBtn");
  const messageDisplay = document.getElementById("messageDisplay");
  const audioContainer = document.getElementById("audioContainer");
  const audioPlayer = document.getElementById("audioPlayer");
  const charCount = document.getElementById("charCount");
  const btnText = document.querySelector(".btn-text");
  const btnLoader = document.querySelector(".btn-loader");
  
  textInput.addEventListener("input", function () {
    const count = textInput.value.length;
    charCount.textContent = count;

    if (count > 450) {
      charCount.style.color = "#e74c3c";
    } else if (count > 350) {
      charCount.style.color = "#f39c12";
    } else {
      charCount.style.color = "#27ae60";
    }
  });

  generateBtn.addEventListener("click", async function () {
    const text = textInput.value.trim();

    if (!text) {
      showMessage("Please enter some text to convert to speech.", "error");
      return;
    }

    if (text.length > 500) {
      showMessage(
        "Text is too long. Please keep it under 500 characters.",
        "error"
      );
      return;
    }

    setLoadingState(true);
    hideAudio();

    try {
      const response = await fetch("/tts/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
        }),
      });

      const data = await response.json();

      if (response.ok && data.audio_url) {
        showMessage("Audio generated successfully!", "success");
        showAudio(data.audio_url, data.text);
      } else {
        showMessage(
          `Error: ${data.detail || "Failed to generate audio"}`,
          "error"
        );
      }
    } catch (error) {
      console.error("Error:", error);
      showMessage("Could not connect to backend. Please try again.", "error");
    } finally {
      setLoadingState(false);
    }
  });

  function setLoadingState(loading) {
    if (loading) {
      generateBtn.disabled = true;
      btnText.style.display = "none";
      btnLoader.style.display = "inline";
    } else {
      generateBtn.disabled = false;
      btnText.style.display = "inline";
      btnLoader.style.display = "none";
    }
  }

  function showMessage(message, type) {
    messageDisplay.style.display = "flex";

    messageDisplay.innerHTML = `
        <div class="${type}-message">
            ${message}
        </div>
    `;

    if (type === "success") {
      setTimeout(() => {
        messageDisplay.innerHTML = "";
        messageDisplay.style.display = "none";
      }, 5000);
    }
  }

  function showAudio(audioUrl, text) {
    audioPlayer.src = audioUrl;
    audioContainer.style.display = "block";

    // Scroll to audio container
    audioContainer.scrollIntoView({ behavior: "smooth" });
  }

  function hideAudio() {
    audioContainer.style.display = "none";
    audioPlayer.src = "";
  }

  // Enable Enter key to generate audio
  textInput.addEventListener("keydown", function (event) {
    if (event.ctrlKey && event.key === "Enter") {
      generateBtn.click();
    }
  });
  
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
  const playAgainBtn = document.getElementById("playAgainBtn");
  const recordAgainBtn = document.getElementById("recordAgainBtn");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    if (startRecordingBtn) {
      showEchoMessage("Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Safari.", "error");
      startRecordingBtn.disabled = true;
    }
  } else {
    if (startRecordingBtn && stopRecordingBtn) {
      startRecordingBtn.addEventListener("click", startRecording);
      stopRecordingBtn.addEventListener("click", stopRecording);
      
      if (playAgainBtn) {
        playAgainBtn.addEventListener("click", function() {
          echoAudioPlayer.currentTime = 0;
          echoAudioPlayer.play().catch(e => console.log("Play failed:", e));
        });
      }
      
      if (recordAgainBtn) {
        recordAgainBtn.addEventListener("click", function() {
          hideEchoAudio();
          resetRecordingState();
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
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
      'audio/wav'
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
      echoAudioPlayer.src = audioUrl;
      echoAudioContainer.style.display = "block";
      
      const durationText = duration ? ` (${duration}s)` : "";
      showEchoMessage(`Recording complete${durationText}! Your echo is ready to play.`, "success");
      
      // Add transcribe button if it doesn't exist
      let transcribeBtn = document.getElementById("transcribeAudioBtn");
      if (!transcribeBtn && audioBlob) {
        transcribeBtn = document.createElement("button");
        transcribeBtn.id = "transcribeAudioBtn";
        transcribeBtn.className = "btn primary";
        transcribeBtn.innerHTML = '<span class="btn-text">Transcribe Audio</span><span class="btn-loader" style="display: none">Transcribing...</span>';
        
        const audioActions = echoAudioContainer.querySelector('.audio-actions');
        if (audioActions) {
          audioActions.appendChild(transcribeBtn);
        }
        
        transcribeBtn.addEventListener("click", function() {
          transcribeAudioFile(audioBlob, transcribeBtn);
        });
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
    
    // Hide transcription container
    const transcriptionContainer = document.getElementById("transcriptionContainer");
    if (transcriptionContainer) {
      transcriptionContainer.style.display = "none";
    }
  }

  async function transcribeAudioFile(audioBlob, transcribeBtn) {
    try {
      const btnText = transcribeBtn.querySelector('.btn-text');
      const btnLoader = transcribeBtn.querySelector('.btn-loader');
      transcribeBtn.disabled = true;
      btnText.style.display = 'none';
      btnLoader.style.display = 'inline';
      
      const formData = new FormData();
      const filename = `recording_${Date.now()}.wav`;
      formData.append('audio', audioBlob, filename);
      
      const response = await fetch('/transcribe/file', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        showTranscription(data);
        showEchoMessage('Transcription completed successfully!', 'success');
        
        btnText.textContent = 'Transcribed Successfully';
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        transcribeBtn.style.backgroundColor = '#27ae60';
        transcribeBtn.disabled = true;
      } else {
        throw new Error(data.detail || 'Transcription failed');
      }
      
    } catch (error) {
      console.error('Transcription error:', error);
      showEchoMessage(`Transcription failed: ${error.message}`, 'error');
      
      const btnText = transcribeBtn.querySelector('.btn-text');
      const btnLoader = transcribeBtn.querySelector('.btn-loader');
      transcribeBtn.disabled = false;
      btnText.style.display = 'inline';
      btnLoader.style.display = 'none';
    }
  }

  function showTranscription(data) {
    const transcriptionContainer = document.getElementById("transcriptionContainer");
    const transcriptionText = document.getElementById("transcriptionText");
    const transcriptionDetails = document.getElementById("transcriptionDetails");
    
    if (transcriptionContainer && transcriptionText) {
      // Display the transcription text
      transcriptionText.textContent = data.transcription || "No transcription available";
      
      // Simple status message
      if (transcriptionDetails) {
        transcriptionDetails.innerHTML = '<span>Status: Completed</span>';
      }
      
      // Show the container
      transcriptionContainer.style.display = "block";
      
      // Scroll to transcription
      transcriptionContainer.scrollIntoView({ behavior: "smooth" });
    }
  }

});
