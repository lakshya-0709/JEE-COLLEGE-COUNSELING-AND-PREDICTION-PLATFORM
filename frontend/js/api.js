/* ═══════════════════════════════════════════════════
   API Client Module
   ═══════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000/api';

const api = {
    /**
     * Predict colleges based on student details
     */
    async predictColleges(formData) {
        const res = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Prediction failed');
        }
        return res.json();
    },

    /**
     * Get cutoff trends
     */
    async getTrends(params) {
        const qs = new URLSearchParams(params).toString();
        const res = await fetch(`${API_BASE}/trends?${qs}`);
        if (!res.ok) throw new Error('Failed to fetch trends');
        return res.json();
    },

    /**
     * Compare two colleges
     */
    async compareColleges(data) {
        const res = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Comparison failed');
        return res.json();
    },

    /**
     * Search colleges (autocomplete)
     */
    async searchColleges(query) {
        const res = await fetch(`${API_BASE}/colleges?search=${encodeURIComponent(query)}`);
        if (!res.ok) return [];
        return res.json();
    },

    /**
     * Get programs for a college
     */
    async getPrograms(institute) {
        const res = await fetch(`${API_BASE}/colleges/programs?institute=${encodeURIComponent(institute)}`);
        if (!res.ok) return [];
        return res.json();
    },

    /**
     * Get all branch names, optionally filtered by institute types
     */
    async getBranches(types = []) {
        let url = `${API_BASE}/colleges/branches`;
        if (types && types.length > 0) {
            url += `?types=${encodeURIComponent(types.join(','))}`;
        }
        const res = await fetch(url);
        if (!res.ok) return [];
        return res.json();
    },

    /**
     * Get metadata
     */
    async getMetadata() {
        const res = await fetch(`${API_BASE}/colleges/metadata`);
        if (!res.ok) return {};
        return res.json();
    },

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            return res.ok;
        } catch {
            return false;
        }
    }
};
