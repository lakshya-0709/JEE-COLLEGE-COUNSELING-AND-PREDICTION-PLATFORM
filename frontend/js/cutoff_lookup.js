// cutoff_lookup.js — Cutoff Lookup page: search by college, branch, category, quota


document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const cutoffForm = document.getElementById('cutoffForm');
    const cutoffInstitute = document.getElementById('cutoffInstitute');
    const cutoffInstituteDropdown = document.getElementById('cutoffInstituteDropdown');
    const cutoffProgram = document.getElementById('cutoffProgram');
    const cutoffCategory = document.getElementById('cutoffCategory');
    const cutoffGender = document.getElementById('cutoffGender');
    const cutoffQuota = document.getElementById('cutoffQuota');
    const cutoffSubmitBtn = document.getElementById('cutoffSubmitBtn');
    const cutoffResults = document.getElementById('cutoffResults');

    initCutoffLookupTab();

    function initCutoffLookupTab() {
        if (!cutoffForm) return;

        // Sync Category and Gender from predict page if set
        const mainCatSelect = document.getElementById('selectCategory');
        if (mainCatSelect && mainCatSelect.value) {
            cutoffCategory.value = mainCatSelect.value;
        }
        const mainGenderSelect = document.getElementById('selectGender');
        if (mainGenderSelect && mainGenderSelect.value) {
            cutoffGender.value = mainGenderSelect.value;
        }

        // Autocomplete search with debounce
        cutoffInstitute.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                cutoffInstituteDropdown.style.display = 'none';
                return;
            }
            try {
                const colleges = await api.searchColleges(query);
                renderAutocompleteDropdown(colleges);
            } catch (err) {
                console.error(err);
            }
        }, 250));

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== cutoffInstitute && e.target !== cutoffInstituteDropdown) {
                cutoffInstituteDropdown.style.display = 'none';
            }
        });

        // Form Submit
        cutoffForm.addEventListener('submit', handleLookupSubmit);
    }

    function renderAutocompleteDropdown(colleges) {
        cutoffInstituteDropdown.innerHTML = '';
        if (colleges.length === 0) {
            cutoffInstituteDropdown.style.display = 'none';
            return;
        }

        colleges.forEach(col => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `
                <div class="item-title">${col.institute_short}</div>
                <div class="item-subtitle">${col.institute} (${col.institute_type})</div>
            `;
            item.addEventListener('click', () => {
                cutoffInstitute.value = col.institute;
                cutoffInstituteDropdown.style.display = 'none';
                loadProgramsForInstitute(col.institute);
            });
            cutoffInstituteDropdown.appendChild(item);
        });

        cutoffInstituteDropdown.style.display = 'block';
    }

    async function loadProgramsForInstitute(instituteName) {
        cutoffProgram.innerHTML = '<option value="">Loading programs...</option>';
        try {
            const programs = await api.getPrograms(instituteName);
            cutoffProgram.innerHTML = '<option value="" disabled selected>Select program...</option>';
            programs.forEach(prog => {
                const opt = document.createElement('option');
                opt.value = prog.program;
                opt.textContent = `${prog.branch_short} — ${prog.degree_type}`;
                cutoffProgram.appendChild(opt);
            });
        } catch (err) {
            console.error(err);
            cutoffProgram.innerHTML = '<option value="">Failed to load programs</option>';
        }
    }

    async function handleLookupSubmit(e) {
        e.preventDefault();

        const institute = cutoffInstitute.value.trim();
        const program = cutoffProgram.value;
        if (!institute || !program) {
            showToast('Please select an institute and a program!', 'error');
            return;
        }

        const btnText = cutoffSubmitBtn.querySelector('.btn-text');
        const btnLoader = cutoffSubmitBtn.querySelector('.btn-loader');
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        cutoffSubmitBtn.disabled = true;

        showSkeletons(cutoffResults, 1);
        const cutoffLayout = document.getElementById('cutoffLayout');
        if (cutoffLayout) cutoffLayout.classList.remove('initial-state');
        cutoffResults.style.display = 'block';
        cutoffResults.scrollIntoView({ behavior: 'smooth' });

        try {
            const data = await api.getTrends({
                institute,
                program,
                seat_type: cutoffCategory.value,
                gender: cutoffGender.value,
                quota: cutoffQuota.value
            });
            renderLookupResults(data);
        } catch (err) {
            console.error(err);
            showToast('Failed to fetch cutoff details. Try another category/quota.', 'error');
            cutoffResults.style.display = 'none';
            if (cutoffLayout) cutoffLayout.classList.add('initial-state');
        } finally {
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            cutoffSubmitBtn.disabled = false;
        }
    }

    function renderLookupResults(data) {
        cutoffResults.innerHTML = '';

        if (!data.trends || data.trends.length === 0) {
            cutoffResults.innerHTML = `
                <div class="glass-card no-results">
                    <p class="no-results-emoji">🏜️</p>
                    <h3>No Cutoff Ranks Found</h3>
                    <p>No historical cutoff data found matching your Category, Gender, or Quota combination.</p>
                </div>
            `;
            return;
        }

        // Predicted closing rank card
        const predictYear = data.predict_year || 'Next';
        const predictedRankStr = data.predicted_closing_rank
            ? data.predicted_closing_rank.toLocaleString('en-IN')
            : 'N/A';
        const minStr = data.predicted_range_min ? data.predicted_range_min.toLocaleString('en-IN') : null;
        const rangeDisplay = (minStr && predictedRankStr !== 'N/A') ? `${minStr} – ${predictedRankStr}` : predictedRankStr;

        const trendLower = data.trend_direction.toLowerCase();
        const trendColor = trendLower === 'getting_harder' ? 'var(--red)' : trendLower === 'getting_easier' ? 'var(--safe-color)' : 'var(--text-secondary)';
        const trendText = trendLower === 'getting_harder' ? '🔴 Getting Harder (increasingly competitive)' : trendLower === 'getting_easier' ? '🟢 Getting Easier (higher ranks accepted)' : '⚪ Stable Cutoffs';

        // Render table rows
        let tableRowsHtml = '';
        data.trends.forEach(t => {
            const openRank = t.opening_rank ? t.opening_rank.toLocaleString('en-IN') : 'N/A';
            const closeRank = t.closing_rank ? t.closing_rank.toLocaleString('en-IN') : 'N/A';
            tableRowsHtml += `
                <tr>
                    <td><strong>${t.year}</strong></td>
                    <td>${openRank}</td>
                    <td>${closeRank}</td>
                </tr>
            `;
        });

        cutoffResults.innerHTML = `
            <div class="glass-card cutoff-header-card fade-in" style="flex-direction: column; align-items: stretch; gap: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                    <div>
                        <span class="badge ${data.institute_type ? data.institute_type.toLowerCase() : 'nit'}-badge" style="margin-bottom: 0.25rem; display: inline-block;">${data.institute_type || 'JoSAA'}</span>
                        <h3 style="margin: 0; font-size: 1.25rem;">${data.institute}</h3>
                        <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: var(--text-secondary);">${data.program}</p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                    <div>
                        <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">Seat Type / Quota</p>
                        <p style="margin: 0.25rem 0 0 0; font-weight: 600;">${data.seat_type} / ${data.quota}</p>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">Gender Filter</p>
                        <p style="margin: 0.25rem 0 0 0; font-weight: 600;">${data.gender === 'Gender-Neutral' ? 'Male / Gender-Neutral' : 'Female-Only'}</p>
                    </div>
                </div>
            </div>

            <!-- Predicted Closing Rank Card -->
            <div class="glass-card cutoff-item-card fade-in" style="border: 1px solid rgba(0, 212, 255, 0.45); cursor: default; justify-content: space-between; padding: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 2rem;">🔮</div>
                    <div>
                        <h4 style="margin: 0; font-size: 1.1rem; color: var(--cyan);">${predictYear} Predicted Expected Range</h4>
                        <p style="margin: 0.2rem 0 0 0; font-size: 0.82rem; color: var(--text-secondary);">Expected closing cutoff range (Model prediction: ${predictedRankStr})</p>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="font-family: var(--font-heading); font-size: 2.2rem; font-weight: 900; color: var(--cyan); line-height: 1;">${rangeDisplay}</span>
                </div>
            </div>

            <!-- Historical Cutoff Table -->
            <div class="glass-card fade-in" style="padding: 1.5rem; margin-top: 1rem;">
                <h4 style="margin: 0 0 1rem 0; font-size: 1rem; font-family: var(--font-heading); display: flex; justify-content: space-between; align-items: center;">
                    <span>📜 Historical Closing Cutoffs</span>
                    <span style="font-size: 0.85rem; font-weight: 500; color: ${trendColor}">${trendText}</span>
                </h4>
                <div style="overflow-x: auto;">
                    <table class="trend-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">
                                <th style="padding: 0.5rem 0.25rem;">Year</th>
                                <th style="padding: 0.5rem 0.25rem;">Opening Rank</th>
                                <th style="padding: 0.5rem 0.25rem;">Closing Rank</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableRowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
});
