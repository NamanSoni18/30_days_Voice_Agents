// Simple FastAPI Voice Agents App

document.addEventListener('DOMContentLoaded', function() {
    console.log('FastAPI Voice Agents App Loaded!');
    
    const btn = document.getElementById('getMessageBtn');
    const messageDisplay = document.getElementById('messageDisplay');
    
    btn.addEventListener('click', async function() {
        btn.textContent = 'Loading...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/backend');
            const data = await response.json();
            
            messageDisplay.innerHTML = `
                <div class="success-message">
                    ${data.message}
                </div>
            `;
        } catch (error) {
            messageDisplay.innerHTML = `
                <div class="error-message">
                    Could not connect to backend
                </div>
            `;
        } finally {
            btn.textContent = 'Get Message from Backend';
            btn.disabled = false;
        }
    });
});