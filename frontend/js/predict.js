// predict.js — Prediction page: form, results tabs, trend modal

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const predictionForm = document.getElementById('predictionForm');
    const examMainBtn = document.getElementById('examMainBtn');
    const examAdvBtn = document.getElementById('examAdvBtn');
    const inputRank = document.getElementById('inputRank');
    const selectCategory = document.getElementById('selectCategory');
    const selectGender = document.getElementById('selectGender');
    const selectState = document.getElementById('selectState');
    const branchSelect = document.getElementById('branchSelect');
    const selectedBranchesContainer = document.getElementById('selectedBranches');
    const predictBtn = document.getElementById('predictBtn');

    // Checkbox elements for institute types
    const chkIIT = document.getElementById('chkIIT');
    const chkNIT = document.getElementById('chkNIT');
    const chkIIIT = document.getElementById('chkIIIT');
    const chkGFTI = document.getElementById('chkGFTI');

    // Results panel elements
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsSummary = document.getElementById('resultsSummary');
    const tabSafe = document.getElementById('tabSafe');
    const tabModerate = document.getElementById('tabModerate');
    const tabDream = document.getElementById('tabDream');
    const safeCount = document.getElementById('safeCount');
    const moderateCount = document.getElementById('moderateCount');
    const dreamCount = document.getElementById('dreamCount');
    const resultsCards = document.getElementById('resultsCards');

    // Modal elements
    const trendModal = document.getElementById('trendModal');
    const trendModalClose = document.getElementById('trendModalClose');
    const trendModalTitle = document.getElementById('trendModalTitle');
    const trendModalTable = document.getElementById('trendModalTable');

    // State Variables
    let currentExamType = 'main'; // 'main' or 'advanced'
    let selectedBranchesSet = new Set();
    let currentPredictions = { safe: [], moderate: [], dream: [] };
    let activeTab = 'safe';
    let modalChartInstance = null;
    let showAllTabsMap = { safe: false, moderate: false, dream: false };

    // Initialize Page
    initPredictForm();

    function initPredictForm() {
        if (!predictionForm) return;

        // Populate Home State Dropdown
        if (selectState) {
            INDIAN_STATES.forEach(state => {
                const opt = document.createElement('option');
                opt.value = state;
                opt.textContent = state;
                selectState.appendChild(opt);
            });
        }

        // Toggle Exam Type
        examMainBtn.addEventListener('click', () => setExamType('main'));
        examAdvBtn.addEventListener('click', () => setExamType('advanced'));

        // Initialize the form state based on the default exam type
        setExamType('main');

        // Reload branches when institute type checkboxes change
        [chkIIT, chkNIT, chkIIIT, chkGFTI].forEach(chk => {
            if (chk) {
                chk.addEventListener('change', loadBranches);
            }
        });

        // Sync Category and update labels
        if (selectCategory) {
            selectCategory.addEventListener('change', () => {
                const val = selectCategory.value;
                const prefCategory = document.getElementById('prefCategory');
                if (prefCategory && prefCategory.value !== val) {
                    prefCategory.value = val;
                    prefCategory.dispatchEvent(new Event('change'));
                }
                updateRankLabelAndHint(val);
            });
            // Run initially to set the labels/hints on page load
            updateRankLabelAndHint(selectCategory.value);
        }

        // Sync Rank
        if (inputRank) {
            inputRank.addEventListener('input', () => {
                const val = inputRank.value;
                const prefRank = document.getElementById('prefRank');
                if (prefRank && prefRank.value !== val) {
                    prefRank.value = val;
                }
            });
        }

        // Handle Branch Multiselect Chips
        branchSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            const text = e.target.options[e.target.selectedIndex].text;
            if (val && !selectedBranchesSet.has(val)) {
                addBranchChip(val, text);
            }
            branchSelect.selectedIndex = -1; // Reset selection
        });

        // Form Submit
        predictionForm.addEventListener('submit', handlePredictionSubmit);

        // Tab click handlers
        const tabs = [tabSafe, tabModerate, tabDream];
        tabs.forEach(tab => {
            if (tab) {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    activeTab = tab.getAttribute('data-tab');
                    renderActiveCards();
                });
            }
        });

        // Close Modal events
        if (trendModalClose) {
            trendModalClose.addEventListener('click', closeTrendModal);
        }
        if (trendModal) {
            trendModal.addEventListener('click', (e) => {
                if (e.target === trendModal) closeTrendModal();
            });
        }
    }

    function updateCheckbox(chk, checked, disabled) {
        if (!chk) return;
        chk.checked = checked;
        chk.disabled = disabled;
        chk.parentElement.style.opacity = disabled ? '0.5' : '1';
        chk.parentElement.style.cursor = disabled ? 'not-allowed' : 'pointer';
    }

    function setExamType(type) {
        currentExamType = type;
        const isMain = type === 'main';
        
        examMainBtn.classList.toggle('active', isMain);
        examAdvBtn.classList.toggle('active', !isMain);

        updateCheckbox(chkIIT, !isMain, isMain);
        updateCheckbox(chkNIT, isMain, !isMain);
        updateCheckbox(chkIIIT, isMain, !isMain);
        updateCheckbox(chkGFTI, isMain, !isMain);

        loadBranches();
    }

    async function loadBranches() {
        try {
            const selectedTypes = [];
            if (chkIIT && chkIIT.checked) selectedTypes.push('IIT');
            if (chkNIT && chkNIT.checked) selectedTypes.push('NIT');
            if (chkIIIT && chkIIIT.checked) selectedTypes.push('IIIT');
            if (chkGFTI && chkGFTI.checked) selectedTypes.push('GFTI');

            const branches = await api.getBranches(selectedTypes);
            branchSelect.innerHTML = '<option value="" disabled selected>Select preferred branches...</option>';
            branches.forEach(branch => {
                const opt = document.createElement('option');
                opt.value = branch;
                opt.textContent = branch;
                opt.title = branch; // Add hover tooltip with full branch name
                branchSelect.appendChild(opt);
            });
        } catch (err) {
            console.error('Failed to load branches:', err);
        }
    }

    function addBranchChip(val, text) {
        selectedBranchesSet.add(val);
        const chip = document.createElement('span');
        chip.className = 'branch-chip fade-in';
        chip.dataset.val = val;
        chip.innerHTML = `${text} <span class="chip-remove">&times;</span>`;

        chip.querySelector('.chip-remove').addEventListener('click', () => {
            selectedBranchesSet.delete(val);
            chip.remove();
        });

        selectedBranchesContainer.appendChild(chip);
    }

    async function handlePredictionSubmit(e) {
        e.preventDefault();

        const rankVal = inputRank.value ? parseInt(inputRank.value, 10) : null;

        if (!rankVal) {
            showToast('Please enter your Rank!', 'error');
            return;
        }

        // Setup loading state
        const btnText = predictBtn.querySelector('.btn-text');
        const btnLoader = predictBtn.querySelector('.btn-loader');
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        predictBtn.disabled = true;

        showSkeletons(resultsCards, 6);
        const predictionLayout = document.getElementById('predictionLayout');
        if (predictionLayout) {
            predictionLayout.classList.remove('initial-state');
        }
        resultsPanel.style.display = 'block';
        resultsPanel.scrollIntoView({ behavior: 'smooth' });

        // Build Payload
        const preferredBranches = Array.from(selectedBranchesSet);
        const instituteTypes = [];
        if (chkIIT.checked) instituteTypes.push('IIT');
        if (chkNIT.checked) instituteTypes.push('NIT');
        if (chkIIIT.checked) instituteTypes.push('IIIT');
        if (chkGFTI.checked) instituteTypes.push('GFTI');

        const payload = {
            jee_main_rank: currentExamType === 'main' ? rankVal : null,
            jee_main_percentile: null,
            jee_advanced_rank: currentExamType === 'advanced' ? rankVal : null,
            jee_advanced_percentile: null,
            category: selectCategory.value,
            gender: selectGender.value,
            home_state: selectState.value || null,
            preferred_branches: preferredBranches,
            institute_types: instituteTypes
        };

        try {
            const data = await api.predictColleges(payload);
            currentPredictions = data;
            showAllTabsMap = { safe: false, moderate: false, dream: false };

            // Format results panel
            safeCount.textContent = data.safe.length;
            moderateCount.textContent = data.moderate.length;
            dreamCount.textContent = data.dream.length;

            animateCounter(safeCount, data.safe.length);
            animateCounter(moderateCount, data.moderate.length);
            animateCounter(dreamCount, data.dream.length);

            // Render details summary
            const total = data.safe.length + data.moderate.length + data.dream.length;
            resultsSummary.innerHTML = `
                <div class="summary-text">
                    Analyzed results for <strong>${currentExamType === 'main' ? 'JEE Main' : 'JEE Advanced'}</strong> rank <strong>${formatRank(data.your_rank)}</strong>. 
                    Found <strong>${total}</strong> total matches matching your preferences.
                </div>
            `;

            // Default to first active tab or tab with results
            if (data.safe.length > 0) {
                tabSafe.click();
            } else if (data.moderate.length > 0) {
                tabModerate.click();
            } else {
                tabDream.click();
            }

        } catch (err) {
            console.error(err);
            showToast(err.message || 'Error occurred during prediction', 'error');
            resultsPanel.style.display = 'none';
            if (predictionLayout) {
                predictionLayout.classList.add('initial-state');
            }
        } finally {
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            predictBtn.disabled = false;
        }
    }

    function renderActiveCards() {
        const cards = currentPredictions[activeTab] || [];
        resultsCards.innerHTML = '';

        if (cards.length === 0) {
            const currentCat = selectCategory.value;
            let categoryWarning = '';
            if (currentCat !== 'OPEN') {
                categoryWarning = `
                    <div class="category-warning-box" style="margin-top: 1.5rem; padding: 1.25rem; background: rgba(255, 107, 53, 0.08); border: 1px solid rgba(255, 107, 53, 0.25); border-radius: 8px; text-align: left; font-size: 0.88rem; max-width: 500px; margin-left: auto; margin-right: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                        <p style="color: var(--orange); font-weight: 600; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem; font-size: 0.95rem;">
                            ⚠️ Important: Category Rank Check
                        </p>
                        <p style="color: var(--text-secondary); line-height: 1.6; margin: 0;">
                            You selected <strong>${currentCat}</strong> but might have entered your CRL (Common Rank List / All India Rank). 
                            JoSAA allocates category seats based on your <strong>Category Rank</strong>, which is usually much lower (better) than your CRL rank.
                            <br><br>
                            If so, please try entering your <strong>${currentCat} Category Rank</strong> (e.g., if your CRL is 10,000, your EWS rank is typically ~1,200). Alternatively, switch the category back to <strong>General (OPEN)</strong> if you want to use your CRL rank.
                        </p>
                    </div>
                `;
            }
            resultsCards.innerHTML = `
                <div class="no-results glass-card">
                    <p class="no-results-emoji">🏜️</p>
                    <h3>No colleges found in this category</h3>
                    <p>Try widening your preferred branch options or lowering the rank filter.</p>
                    ${categoryWarning}
                </div>
            `;
            return;
        }

        const showAll = showAllTabsMap[activeTab];
        const limit = showAll ? cards.length : 15;
        const visibleCards = cards.slice(0, limit);

        visibleCards.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'college-card glass-card fade-in';
            card.style.animationDelay = `${index * 30}ms`;

            const rankDiffClass = item.rank_difference >= 0 ? 'text-safe' : 'text-danger';
            const rankDiffText = item.rank_difference >= 0
                ? `+${formatRank(item.rank_difference)} ranks safe`
                : `${formatRank(Math.abs(item.rank_difference))} ranks risky`;

            const latestClosing = item.closing_rank_2024 || item.closing_rank_2023 || 'N/A';
            const closingPredicted = item.predicted_closing_rank ? formatRank(item.predicted_closing_rank) : 'ML Pending';

            card.innerHTML = `
                <div class="card-header">
                    <div>
                        <span class="badge ${item.institute_type.toLowerCase()}-badge">${item.institute_type}</span>
                        <span class="badge state-badge">${item.state}</span>
                    </div>
                    <div class="quota-pill">${item.quota} Quota</div>
                </div>
                
                <h4 class="college-name">${item.institute}</h4>
                <p class="program-name">${item.program}</p>
                
                <div class="card-details">
                    <div class="detail-row">
                        <span class="detail-label">Your AIR:</span>
                        <span class="detail-value text-glow">${formatRank(item.your_rank)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Predicted Closing:</span>
                        <span class="detail-value text-glow cyan-text">${closingPredicted}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Margin:</span>
                        <span class="detail-value ${rankDiffClass}">${rankDiffText}</span>
                    </div>
                </div>

                <!-- Confidence Gauge -->
                <div class="confidence-gauge">
                    <div class="gauge-label">
                        <span>Prediction Confidence</span>
                        <span>${Math.round(item.confidence_score * 100)}%</span>
                    </div>
                    <div class="gauge-bar">
                        <div class="gauge-fill" style="width: ${item.confidence_score * 100}%; background: var(--${activeTab === 'dream' ? 'cyan' : activeTab === 'moderate' ? 'orange' : 'green'})"></div>
                    </div>
                </div>

                <!-- Past cutoffs sparkline summary -->
                <div class="sparkline-summary">
                    <div class="spark-item">
                        <span class="spark-yr">'21</span>
                        <span class="spark-val">${formatRank(item.closing_rank_2021)}</span>
                    </div>
                    <div class="spark-item">
                        <span class="spark-yr">'22</span>
                        <span class="spark-val">${formatRank(item.closing_rank_2022)}</span>
                    </div>
                    <div class="spark-item">
                        <span class="spark-yr">'23</span>
                        <span class="spark-val">${formatRank(item.closing_rank_2023)}</span>
                    </div>
                    <div class="spark-item">
                        <span class="spark-yr">'24</span>
                        <span class="spark-val">${formatRank(item.closing_rank_2024)}</span>
                    </div>
                </div>

                <div class="card-actions">
                    <button class="card-btn secondary-btn" data-action="view-trend">
                        📈 View Trend
                    </button>
                    <button class="card-btn primary-btn" data-action="add-compare">
                        ⚡ Compare
                    </button>
                </div>
            `;

            // Bind Actions
            card.querySelector('[data-action="view-trend"]').addEventListener('click', () => {
                openTrendModal(item);
            });

            card.querySelector('[data-action="add-compare"]').addEventListener('click', () => {
                // Populate comparison inputs
                const compareInstA = document.getElementById('compareInstA');
                const compareInstB = document.getElementById('compareInstB');

                if (!compareInstA.value) {
                    compareInstA.value = item.institute;
                    // Trigger input event to populate programs
                    const event = new Event('input', { bubbles: true });
                    compareInstA.dispatchEvent(event);
                    showToast(`Added ${item.institute_short} as College A! Scroll down to compare.`, 'success');
                } else if (!compareInstB.value) {
                    compareInstB.value = item.institute;
                    const event = new Event('input', { bubbles: true });
                    compareInstB.dispatchEvent(event);
                    showToast(`Added ${item.institute_short} as College B! Scroll down to compare.`, 'success');
                } else {
                    // Overwrite College B
                    compareInstB.value = item.institute;
                    const event = new Event('input', { bubbles: true });
                    compareInstB.dispatchEvent(event);
                    showToast(`Updated College B to ${item.institute_short}!`, 'success');
                }

                // Scroll to Compare Section
                document.getElementById('compare').scrollIntoView({ behavior: 'smooth' });
            });

            resultsCards.appendChild(card);
        });

        // Add Show More button if there are more cards
        if (cards.length > limit) {
            const showMoreContainer = document.createElement('div');
            showMoreContainer.className = 'show-more-container';
            showMoreContainer.style.textAlign = 'center';
            showMoreContainer.style.marginTop = '1.5rem';
            showMoreContainer.style.marginBottom = '1.5rem';

            const showMoreBtn = document.createElement('button');
            showMoreBtn.className = 'submit-btn show-more-btn';
            showMoreBtn.style.width = 'auto';
            showMoreBtn.style.padding = '0.75rem 2rem';
            showMoreBtn.style.display = 'inline-block';
            showMoreBtn.innerHTML = `Show More (${cards.length - limit} remaining)`;

            showMoreBtn.addEventListener('click', () => {
                showAllTabsMap[activeTab] = true;
                renderActiveCards();
            });

            showMoreContainer.appendChild(showMoreBtn);
            resultsCards.appendChild(showMoreContainer);
        }
    }

    // Modal Trend Logic
    async function openTrendModal(item) {
        trendModal.style.display = 'flex';
        trendModalTitle.textContent = `${item.institute_short} — ${item.branch_short}`;

        // Show loading skeletons inside modal table
        showSkeletons(trendModalTable, 3);

        const params = {
            institute: item.institute,
            program: item.program,
            seat_type: selectCategory.value,
            gender: selectGender.value,
            quota: item.quota
        };

        try {
            const data = await api.getTrends(params);
            renderModalChart(data);
            renderModalTable(data);
        } catch (err) {
            console.error(err);
            trendModalTable.innerHTML = `<p class="text-danger">Failed to load trend data.</p>`;
        }
    }

    function renderModalChart(data) {
        const ctx = document.getElementById('trendModalChart').getContext('2d');

        if (modalChartInstance) {
            modalChartInstance.destroy();
        }

        const labels = data.trends.map(t => t.year.toString());
        const closingRanks = data.trends.map(t => t.closing_rank);
        const openingRanks = data.trends.map(t => t.opening_rank);

        // Add predicted closing rank if we have it
        const nextPredictions = currentPredictions.safe.concat(currentPredictions.moderate, currentPredictions.dream);
        const match = nextPredictions.find(p => p.institute === data.institute && p.program === data.program && p.quota === data.quota);
        if (match && match.predicted_closing_rank) {
            labels.push(`${match.predict_year || 'Next'} (Pred)`);
            closingRanks.push(match.predicted_closing_rank);
            openingRanks.push(null); // No opening prediction
        }

        modalChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Closing Rank',
                        data: closingRanks,
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#00d4ff',
                        pointRadius: 5
                    },
                    {
                        label: 'Opening Rank',
                        data: openingRanks,
                        borderColor: '#ff6b35',
                        backgroundColor: 'transparent',
                        fill: false,
                        tension: 0.3,
                        pointBackgroundColor: '#ff6b35',
                        pointRadius: 4,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#f8fafc' }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        reverse: true, // Rank charts are better reversed (lower rank = higher position)
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    function renderModalTable(data) {
        let html = `
            <table class="compare-table" style="margin-top: 1rem;">
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Opening Rank</th>
                        <th>Closing Rank</th>
                        <th>Round</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.trends.forEach(t => {
            html += `
                <tr>
                    <td>${t.year}</td>
                    <td>${formatRank(t.opening_rank)}</td>
                    <td>${formatRank(t.closing_rank)}</td>
                    <td>Round ${t.round}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;
        trendModalTable.innerHTML = html;
    }

    function closeTrendModal() {
        trendModal.style.display = 'none';
        if (modalChartInstance) {
            modalChartInstance.destroy();
            modalChartInstance = null;
        }
    }

    function updateRankLabelAndHint(category) {
        const rankLabel = document.getElementById('rankLabel');
        const rankHint = document.getElementById('rankHint');
        const inputRank = document.getElementById('inputRank');

        if (!rankLabel) return;

        if (category === 'OPEN') {
            rankLabel.textContent = 'Rank (AIR)';
            if (inputRank) inputRank.placeholder = 'e.g. 15000';
            if (rankHint) {
                rankHint.textContent = 'Enter Common Rank List (CRL) for General.';
                rankHint.style.color = 'var(--text-muted)';
            }
        } else {
            rankLabel.textContent = `Rank (${category} Category)`;
            if (inputRank) inputRank.placeholder = 'e.g. 1500';
            if (rankHint) {
                rankHint.innerHTML = `⚠️ Enter your <strong>${category} Category Rank</strong>, NOT your CRL (AIR). JoSAA uses category ranks.`;
                rankHint.style.color = 'var(--orange)';
            }
        }
    }
});
