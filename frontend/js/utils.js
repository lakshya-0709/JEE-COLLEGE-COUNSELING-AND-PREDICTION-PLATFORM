/* ═══════════════════════════════════════════════════
   Utility Functions
   ═══════════════════════════════════════════════════ */

const TOTAL_CANDIDATES_MAIN = 1550000;
const TOTAL_CANDIDATES_ADV = 250000;

/**
 * Convert percentile to approximate rank
 */
function percentileToRank(percentile, exam = 'main') {
    const total = exam === 'main' ? TOTAL_CANDIDATES_MAIN : TOTAL_CANDIDATES_ADV;
    return Math.max(1, Math.round((100 - percentile) / 100 * total) + 1);
}

/**
 * Format rank with commas
 */
function formatRank(rank) {
    if (rank == null) return 'N/A';
    return rank.toLocaleString('en-IN');
}

/**
 * Get color for chance category
 */
function getChanceColor(category) {
    const colors = {
        safe: '#00c853',
        moderate: '#ff9800',
        dream: '#00d4ff',
        Safe: '#00c853',
        Moderate: '#ff9800',
        Dream: '#00d4ff',
    };
    return colors[category] || '#94a3b8';
}

/**
 * Debounce function
 */
function debounce(fn, ms = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
    };
}

/**
 * Animate a number counter
 */
function animateCounter(element, target, duration = 1500) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        element.textContent = current.toLocaleString('en-IN');

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Show loading skeletons
 */
function showSkeletons(container, count = 5) {
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
        container.innerHTML += `<div class="skeleton skeleton-card"></div>`;
    }
}

/**
 * Indian states list
 */
const INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh",
    "Chhattisgarh", "Daman & Diu", "Delhi", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry",
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
];
