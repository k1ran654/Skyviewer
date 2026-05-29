// Initialize Lucide icons
lucide.createIcons();

// Toggle sidebar folder groups
function toggleGroup(id) {
    const list = document.getElementById(id);
    if (list) {
        list.classList.toggle('active');
    }
}

// Switch between data sections (Inventory, Skills, etc.)
function showSection(id) {
    // Forcefully hide every data section block
    document.querySelectorAll('.data-section').forEach(s => s.style.display = 'none');
    
    // Unhide the targeted container
    const section = document.getElementById(id);
    if (section) {
        section.style.display = 'block';
    } else {
        console.error("Section not found:", id);
    }

    // Manage the middle player model visibility contextually
    const pmCol = document.getElementById('player-model-col');
    if (pmCol) {
        const showPM = ['inventory', 'storage', 'wardrobe', 'accessories', 'sacks'].includes(id);
        pmCol.style.display = showPM ? 'flex' : 'none';
    }
}

// Toggle HotM dropdown menu
function toggleHotm() {
    const hotmMenu = document.getElementById('hotm-dropdown');
    if (hotmMenu) {
        if (hotmMenu.style.display === 'none') {
            hotmMenu.style.display = 'block';
        } else {
            hotmMenu.style.display = 'none';
        }
    }
}

// Run immediately when layout loads
window.onload = () => {
    if(document.getElementById('inventory')) {
        showSection('inventory');
    }
};