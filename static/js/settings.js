// Settings page JavaScript

function saveSettings() {
    // Get all settings values
    const settings = {
        model: document.getElementById('modelSelect').value,
        temperature: document.getElementById('temperature').value,
        maxFileSize: document.getElementById('maxFileSize').value,
        historyLimit: document.getElementById('historyLimit').value
    };
    
    // Save to localStorage
    localStorage.setItem('appSettings', JSON.stringify(settings));
    
    showToast('Settings saved successfully!', 'success');
}

function resetSettings() {
    if (!confirm('Reset all settings to defaults?')) return;
    
    localStorage.removeItem('appSettings');
    location.reload();
}

function clearHistory() {
    if (!confirm('This will delete all your script history. This action cannot be undone!')) return;
    
    fetch('/api/clear-history', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                showToast('History cleared', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('Failed to clear history', 'error');
            }
        })
        .catch(() => showToast('Error clearing history', 'error'));
}

function exportData() {
    fetch('/api/export-all')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `script-history-${Date.now()}.json`;
            a.click();
            showToast('Data exported successfully!', 'success');
        })
        .catch(() => showToast('Failed to export data', 'error'));
}

// Load storage info
function loadStorageInfo() {
    const container = document.getElementById('storageInfo');
    if (!container) return;
    
    fetch('/api/storage-info')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const storage = data.storage;
                container.innerHTML = `
                    <div class="storage-stats">
                        <div class="storage-stat">
                            <span class="stat-label">📁 Total Files:</span>
                            <span class="stat-value">${storage.total_files}</span>
                        </div>
                        <div class="storage-stat">
                            <span class="stat-label">💽 Total Size:</span>
                            <span class="stat-value">${storage.total_size_formatted}</span>
                        </div>
                        <div class="storage-stat">
                            <span class="stat-label">🎬 Videos:</span>
                            <span class="stat-value">${storage.videos.count} (${storage.videos.size_formatted})</span>
                        </div>
                        <div class="storage-stat">
                            <span class="stat-label">🎵 Audio:</span>
                            <span class="stat-value">${storage.audio.count} (${storage.audio.size_formatted})</span>
                        </div>
                    </div>
                `;
            } else {
                container.innerHTML = '<div class="storage-error">Failed to load storage info</div>';
            }
        })
        .catch(() => {
            container.innerHTML = '<div class="storage-error">Error loading storage info</div>';
        });
}

// Cleanup uploaded videos
function cleanupUploads() {
    if (!confirm('This will delete all uploaded video and audio files. Your script history will be preserved. Continue?')) {
        return;
    }
    
    fetch('/api/cleanup', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(`Cleanup complete! Deleted ${data.deleted_files} files, freed ${data.freed_space_formatted}`, 'success');
                loadStorageInfo(); // Refresh storage info
            } else {
                showToast(data.error || 'Cleanup failed', 'error');
            }
        })
        .catch(() => {
            showToast('Error during cleanup', 'error');
        });
}

// Load saved settings on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load storage info
    loadStorageInfo();
    
    // Load saved settings
    const saved = localStorage.getItem('appSettings');
    if (saved) {
        const settings = JSON.parse(saved);
        
        if (settings.model) document.getElementById('modelSelect').value = settings.model;
        if (settings.temperature) document.getElementById('temperature').value = settings.temperature;
        if (settings.maxFileSize) document.getElementById('maxFileSize').value = settings.maxFileSize;
        if (settings.historyLimit) document.getElementById('historyLimit').value = settings.historyLimit;
    }
});

// Import file handler
document.getElementById('importFile').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
        try {
            const data = JSON.parse(event.target.result);
            
            fetch('/api/import-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (response.ok) {
                    showToast('Data imported successfully!', 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showToast('Failed to import data', 'error');
                }
            });
        } catch (error) {
            showToast('Invalid JSON file', 'error');
        }
    };
    reader.readAsText(file);
});
