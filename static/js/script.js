// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const videoInput = document.getElementById('video');
const fileInputDisplay = document.querySelector('.file-input-display');
const fileText = document.querySelector('.file-text');
const submitBtn = document.getElementById('submitBtn');

const loadingSection = document.getElementById('loadingSection');
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

// Scrape website content
scrapeBtn.addEventListener('click', async () => {
    const url = websiteUrlInput.value.trim();
    
    if (!url) {
        alert('Please enter a website URL first');
        return;
    }
    
    // Basic validation - just check if it looks like a domain
    if (!url.match(/^(https?:\/\/)?([\w.-]+\.[a-z]{2,})/i)) {
        alert('Please enter a valid domain (e.g., example.com or https://example.com)');
        return;
    }
    
    // Show loading state
    scrapeBtn.disabled = true;
    scrapeBtn.classList.add('loading');
    const originalText = scrapeBtnText.textContent;
    scrapeBtnText.textContent = 'Scraping...';
    
    try {
        const response = await fetch('/scrape-website', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Fill the textarea with scraped content
            brandInput.value = data.content;
            
            // Visual feedback
            scrapeBtnText.textContent = '✓ Content Loaded!';
            scrapeBtn.style.background = '#10b981';
            
            setTimeout(() => {
                scrapeBtnText.textContent = originalText;
                scrapeBtn.style.background = '';
            }, 2000);
        } else {
            scrapeBtnText.textContent = originalText;
            alert(data.error || 'Failed to scrape website');
        }
    } catch (error) {
        scrapeBtnText.textContent = originalText;
        alert('Network error: Unable to scrape website. Please try again.');
        console.error('Scraping error:', error);
    } finally {
        scrapeBtn.disabled = false;
        scrapeBtn.classList.remove('loading');
    }
});

// Update file input display when file is selected
videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const fileName = e.target.files[0].name;
        const fileSize = (e.target.files[0].size / (1024 * 1024)).toFixed(2);
        fileText.textContent = `${fileName} (${fileSize} MB)`;
        fileInputDisplay.style.borderColor = '#10b981';
        fileInputDisplay.style.background = '#d1fae5';
    } else {
        fileText.textContent = 'Choose a video file...';
        fileInputDisplay.style.borderColor = '';
        fileInputDisplay.style.background = '';
    }
});

// Form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate that either URL or file is provided
    const instagramUrl = document.getElementById('instagram_url').value.trim();
    const hasFile = videoInput.files.length > 0;
    
    if (!instagramUrl && !hasFile) {
        showError('Please provide either an Instagram URL or upload a video file.');
        return;
    }
    
    // Hide previous results/errors
    hideAllSections();
    
    // Show loading
    loadingSection.classList.remove('hidden');
    submitBtn.disabled = true;
    
    // Prepare form data
    const formData = new FormData();
    
    if (instagramUrl) {
        formData.append('instagram_url', instagramUrl);
    } else if (hasFile) {
        formData.append('video', videoInput.files[0]);
    }
    
    formData.append('brand_input', document.getElementById('brand_input').value);
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Display results
            displayResults(data);
        } else {
            // Display error
            showError(data.error || 'An error occurred while processing your video.');
        }
    } catch (error) {
        showError('Network error: Unable to connect to the server. Please try again.');
    } finally {
        loadingSection.classList.add('hidden');
        submitBtn.disabled = false;
    }
});

// Display results
function displayResults(data) {
    transcriptionContent.textContent = data.transcription;
    styleContent.textContent = data.style_analysis;
    scriptContent.textContent = data.rewritten_script;
    
    resultsSection.classList.remove('hidden');
    
    // Smooth scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Show error message
function showError(message) {
    const errorText = document.querySelector('.error-text');
    errorText.textContent = message;
    errorSection.classList.remove('hidden');
    
    // Smooth scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide all sections
function hideAllSections() {
    loadingSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

// Copy script to clipboard
copyBtn.addEventListener('click', async () => {
    const scriptText = scriptContent.textContent;
    
    try {
        await navigator.clipboard.writeText(scriptText);
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span>✓ Copied!</span>';
        copyBtn.style.background = '#10b981';
        copyBtn.style.color = 'white';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
            copyBtn.style.color = '';
        }, 2000);
    } catch (error) {
        alert('Failed to copy to clipboard. Please select and copy manually.');
    }
});

// Reset form
resetBtn.addEventListener('click', () => {
    // Reset form
    uploadForm.reset();
    fileText.textContent = 'Choose a video file...';
    fileInputDisplay.style.borderColor = '';
    fileInputDisplay.style.background = '';
    
    // Hide results
    hideAllSections();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Drag and drop support
const uploadSection = document.querySelector('.upload-section');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadSection.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadSection.addEventListener(eventName, () => {
        fileInputDisplay.style.borderColor = '#6366f1';
        fileInputDisplay.style.background = '#f0f0ff';
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadSection.addEventListener(eventName, () => {
        fileInputDisplay.style.borderColor = '';
        fileInputDisplay.style.background = '';
    }, false);
});

uploadSection.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        videoInput.files = files;
        const event = new Event('change');
        videoInput.dispatchEvent(event);
    }
}, false);
