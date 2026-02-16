// Generate page JavaScript with real-time progress tracking

const uploadForm = document.getElementById('uploadForm');
const videoInput = document.getElementById('video');
const fileInputDisplay = document.querySelector('.file-input-display');
const fileText = document.querySelector('.file-text');
const submitBtn = document.getElementById('submitBtn');

const progressModal = document.getElementById('progressModal');
const progressBar = document.getElementById('progressBar');
const progressPercent = document.getElementById('progressPercent');

const errorSection = document.getElementById('errorSection');
const resultsSection = document.getElementById('resultsSection');

const transcriptionContent = document.getElementById('transcriptionContent');
const styleContent = document.getElementById('styleContent');
const scriptContent = document.getElementById('scriptContent');

const copyBtn = document.getElementById('copyBtn');
const resetBtn = document.getElementById('resetBtn');

const websiteUrlInput = document.getElementById('website_url');
const scrapeBtn = document.getElementById('scrapeBtn');
const scrapeBtnText = document.getElementById('scrapeBtnText');
const brandInput = document.getElementById('brand_input');

// Progress tracking
let currentStep = 0;
const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];

function updateProgress(step, status, message) {
    const stepElement = document.getElementById(steps[step - 1]);
    const statusElement = stepElement.querySelector('.step-status');
    const loader = stepElement.querySelector('.step-loader');
    
    // Remove previous states
    stepElement.classList.remove('active', 'completed');
    
    if (status === 'active') {
        stepElement.classList.add('active');
        loader.style.display = 'block';
        statusElement.textContent = message || 'Processing...';
    } else if (status === 'completed') {
        stepElement.classList.add('completed');
        loader.style.display = 'none';
        statusElement.textContent = 'Completed';
    }
    
    // Update progress bar
    const percentage = (step / steps.length) * 100;
    progressBar.style.width = percentage + '%';
    progressPercent.textContent = Math.round(percentage) + '%';
}

function showProgressModal() {
    progressModal.classList.add('active');
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    
    // Reset all steps
    steps.forEach(stepId => {
        const stepElement = document.getElementById(stepId);
        stepElement.classList.remove('active', 'completed');
        stepElement.querySelector('.step-loader').style.display = 'none';
        stepElement.querySelector('.step-status').textContent = 'Waiting...';
    });
}

function hideProgressModal() {
    progressModal.classList.remove('active');
}

// Scrape website content
scrapeBtn.addEventListener('click', async () => {
    const url = websiteUrlInput.value.trim();
    
    if (!url) {
        showToast('Please enter a website URL first', 'error');
        return;
    }
    
    // Basic validation - just check if it looks like a domain
    if (!url.match(/^(https?:\/\/)?([\w.-]+\.[a-z]{2,})/i)) {
        showToast('Please enter a valid domain (e.g., example.com or https://example.com)', 'error');
        return;
    }
    
    scrapeBtn.disabled = true;
    scrapeBtn.classList.add('loading');
    const originalText = scrapeBtnText.textContent;
    scrapeBtnText.textContent = 'Scraping...';
    
    try {
        const response = await fetch('/scrape-website', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            brandInput.value = data.content;
            scrapeBtnText.textContent = '✓ Content Loaded!';
            scrapeBtn.style.background = '#10b981';
            showToast('Website content loaded!', 'success');
            
            setTimeout(() => {
                scrapeBtnText.textContent = originalText;
                scrapeBtn.style.background = '';
            }, 2000);
        } else {
            scrapeBtnText.textContent = originalText;
            showToast(data.error || 'Failed to scrape website', 'error');
        }
    } catch (error) {
        scrapeBtnText.textContent = originalText;
        showToast('Network error: Unable to scrape website', 'error');
        console.error('Scraping error:', error);
    } finally {
        scrapeBtn.disabled = false;
        scrapeBtn.classList.remove('loading');
    }
});

// Update file input display
videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const fileName = e.target.files[0].name;
        const fileSize = formatFileSize(e.target.files[0].size);
        fileText.textContent = `${fileName} (${fileSize})`;
        fileInputDisplay.style.borderColor = '#10b981';
        fileInputDisplay.style.background = '#d1fae5';
    } else {
        fileText.textContent = 'Choose a video file...';
        fileInputDisplay.style.borderColor = '';
        fileInputDisplay.style.background = '';
    }
});

// Form submission with real-time progress
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const instagramUrl = document.getElementById('instagram_url').value.trim();
    const hasFile = videoInput.files.length > 0;
    
    if (!instagramUrl && !hasFile) {
        showToast('Please provide either an Instagram URL or upload a video file', 'error');
        return;
    }
    
    hideAllSections();
    showProgressModal();
    submitBtn.disabled = true;
    
    const formData = new FormData();
    if (instagramUrl) {
        formData.append('instagram_url', instagramUrl);
    } else if (hasFile) {
        formData.append('video', videoInput.files[0]);
    }
    formData.append('brand_input', brandInput.value);
    
    // Simulate progress (since we don't have real WebSocket yet)
    simulateProgress();
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateProgress(5, 'completed', 'Done!');
            setTimeout(() => {
                hideProgressModal();
                displayResults(data);
            }, 1000);
        } else {
            hideProgressModal();
            showError(data.error || 'An error occurred while processing your video.');
        }
    } catch (error) {
        hideProgressModal();
        showError('Network error: Unable to connect to the server. Please try again.');
    } finally {
        submitBtn.disabled = false;
    }
});

function simulateProgress() {
    updateProgress(1, 'active', 'Downloading...');
    
    setTimeout(() => {
        updateProgress(1, 'completed');
        updateProgress(2, 'active', 'Extracting audio...');
    }, 2000);
    
    setTimeout(() => {
        updateProgress(2, 'completed');
        updateProgress(3, 'active', 'Transcribing with Whisper...');
    }, 5000);
    
    setTimeout(() => {
        updateProgress(3, 'completed');
        updateProgress(4, 'active', 'Analyzing video style...');
    }, 30000);
    
    setTimeout(() => {
        updateProgress(4, 'completed');
        updateProgress(5, 'active', 'Generating your script...');
    }, 45000);
}

function displayResults(data) {
    transcriptionContent.textContent = data.transcription;
    styleContent.textContent = data.style_analysis;
    scriptContent.textContent = data.rewritten_script;
    
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    showToast('Script generated successfully!', 'success');
}

function showError(message) {
    const errorText = document.querySelector('.error-text');
    errorText.textContent = message;
    errorSection.classList.remove('hidden');
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    showToast(message, 'error');
}

function hideAllSections() {
    errorSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

copyBtn.addEventListener('click', async () => {
    const scriptText = scriptContent.textContent;
    const success = await copyToClipboard(scriptText);
    
    if (success) {
        copyBtn.innerHTML = '<span>✓ Copied!</span>';
        copyBtn.style.background = '#10b981';
        copyBtn.style.color = 'white';
        
        setTimeout(() => {
            copyBtn.innerHTML = '<span>📋 Copy Script</span>';
            copyBtn.style.background = '';
            copyBtn.style.color = '';
        }, 2000);
    }
});

resetBtn.addEventListener('click', () => {
    uploadForm.reset();
    fileText.textContent = 'Choose a video file...';
    fileInputDisplay.style.borderColor = '';
    fileInputDisplay.style.background = '';
    hideAllSections();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
