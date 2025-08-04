document.addEventListener("DOMContentLoaded", function () {
  console.log("Voice Agents App Loaded!");

  const textInput = document.getElementById("textInput");
  const generateBtn = document.getElementById("generateBtn");
  const testBackendBtn = document.getElementById("testBackendBtn");
  const messageDisplay = document.getElementById("messageDisplay");
  const audioContainer = document.getElementById("audioContainer");
  const audioPlayer = document.getElementById("audioPlayer");
  const charCount = document.getElementById("charCount");
  const btnText = document.querySelector(".btn-text");
  const btnLoader = document.querySelector(".btn-loader");

  // Character counter
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
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
          speed: 1.0,
          pitch: 1.0,
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === "success") {
        showMessage("Audio generated successfully!", "success");
        showAudio(data.response, data.text);
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
});
