class VoiceSearch {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.voiceButton = document.getElementById('voiceSearchButton');
        this.feedbackElement = document.getElementById('voiceFeedback');
        this.loadingElement = document.getElementById('searchLoading');
        this.searchForm = document.getElementById('searchForm');
        this.isRecording = false;
        
        this.setupVoiceRecognition();
        this.setupEventListeners();
    }

    setupVoiceRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.setupRecognitionEvents();
        } else {
            this.voiceButton.style.display = 'none';
            console.log('Speech recognition not supported');
        }
    }

    cleanSearchText(text) {
        return text
            .toLowerCase()                    // Convert to lowercase
            .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "") // Remove punctuation
            .replace(/\s{2,}/g, " ")         // Remove extra spaces
            .trim();                         // Remove leading/trailing spaces
    }

    setupRecognitionEvents() {
        this.recognition.onstart = () => {
            this.isRecording = true;
            this.updateUI('Listening...', 'info');
            this.updateButtonState();
        };

        this.recognition.onend = () => {
            this.isRecording = false;
            this.updateButtonState();
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            // Clean the recognized text
            const cleanedText = this.cleanSearchText(transcript);
            
            // Update search input with cleaned text
            this.searchInput.value = cleanedText;
            this.updateUI(`Searching: ${cleanedText}`, 'success');
            
            // Stop recording
            this.stopRecording();
            
            // Trigger live search
            this.triggerLiveSearch();
            
            // Submit the form automatically after a brief delay
            setTimeout(() => {
                this.searchForm.submit();
            }, 1000);
        };

        this.recognition.onerror = (event) => {
            this.isRecording = false;
            this.updateUI(`Error: ${event.error}`, 'error');
            this.updateButtonState();
        };
    }

    setupEventListeners() {
        this.voiceButton.addEventListener('click', () => {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        });
    }

    startRecording() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.updateUI('Error starting voice recognition', 'error');
        }
    }

    stopRecording() {
        if (this.isRecording) {
            this.recognition.stop();
        }
    }

    triggerLiveSearch() {
        // Trigger the input event for live search
        const inputEvent = new Event('input', { bubbles: true });
        this.searchInput.dispatchEvent(inputEvent);
    }

    updateButtonState() {
        if (this.isRecording) {
            this.voiceButton.classList.add('recording');
            this.voiceButton.querySelector('i').classList.remove('fa-microphone');
            this.voiceButton.querySelector('i').classList.add('fa-stop');
        } else {
            this.voiceButton.classList.remove('recording');
            this.voiceButton.querySelector('i').classList.remove('fa-stop');
            this.voiceButton.querySelector('i').classList.add('fa-microphone');
        }
    }

    updateUI(message, type = 'info') {
        this.feedbackElement.textContent = message;
        this.feedbackElement.className = `voice-feedback ${type}`;
        
        // Hide feedback after 3 seconds
        setTimeout(() => {
            this.feedbackElement.className = 'voice-feedback hidden';
        }, 3000);
    }
}

// Initialize voice search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceSearch();
});