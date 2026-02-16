// Library page JavaScript

const searchInput = document.getElementById('searchInput');
const filterSelect = document.getElementById('filterSelect');
const sortSelect = document.getElementById('sortSelect');
const libraryGrid = document.getElementById('libraryGrid');

// Search functionality
if (searchInput) {
    searchInput.addEventListener('input', debounce(filterLibrary, 300));
}

// Filter and sort
if (filterSelect) {
    filterSelect.addEventListener('change', filterLibrary);
}

if (sortSelect) {
    sortSelect.addEventListener('change', sortLibrary);
}

function filterLibrary() {
    const searchTerm = searchInput.value.toLowerCase();
    const filterType = filterSelect.value;
    const items = document.querySelectorAll('.library-item');
    
    items.forEach(item => {
        const source = item.dataset.source;
        const text = item.textContent.toLowerCase();
        
        const matchesSearch = text.includes(searchTerm);
        const matchesFilter = filterType === 'all' || source === filterType;
        
        item.style.display = (matchesSearch && matchesFilter) ? 'block' : 'none';
    });
}

function sortLibrary() {
    const sortType = sortSelect.value;
    const items = Array.from(document.querySelectorAll('.library-item'));
    
    items.sort((a, b) => {
        if (sortType === 'newest') {
            return b.dataset.timestamp.localeCompare(a.dataset.timestamp);
        } else if (sortType === 'oldest') {
            return a.dataset.timestamp.localeCompare(b.dataset.timestamp);
        } else if (sortType === 'longest') {
            return parseInt(b.dataset.length) - parseInt(a.dataset.length);
        }
    });
    
    items.forEach(item => libraryGrid.appendChild(item));
}

function toggleMenu(button) {
    const menu = button.nextElementSibling;
    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.library-item-menu')) {
        document.querySelectorAll('.menu-dropdown').forEach(menu => {
            menu.style.display = 'none';
        });
    }
});

async function copyScript(scriptId) {
    try {
        const response = await fetch(`/api/script/${scriptId}`);
        const data = await response.json();
        await copyToClipboard(data.rewritten_script);
    } catch (error) {
        showToast('Failed to copy script', 'error');
    }
}

async function exportScript(scriptId) {
    window.location.href = `/api/script/${scriptId}/export`;
}

async function deleteScript(scriptId) {
    if (!confirm('Are you sure you want to delete this script?')) return;
    
    try {
        const response = await fetch(`/api/script/${scriptId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Script deleted', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('Failed to delete script', 'error');
        }
    } catch (error) {
        showToast('Error deleting script', 'error');
    }
}
