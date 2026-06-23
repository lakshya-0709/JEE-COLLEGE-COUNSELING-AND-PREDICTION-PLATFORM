/* ═══════════════════════════════════════════════════
   JEE Counselor — Preference List Generator Module
   ═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const preferenceForm = document.getElementById('preferenceForm');
    const prefRank = document.getElementById('prefRank');
    const prefCategory = document.getElementById('prefCategory');
    const prefSubmitBtn = document.getElementById('prefSubmitBtn');
    const preferenceResults = document.getElementById('preferenceResults');

    // Priority Button Toggles
    const prefBranchFirst = document.getElementById('prefBranchFirst');
    const prefBalanced = document.getElementById('prefBalanced');
    const prefCollegeFirst = document.getElementById('prefCollegeFirst');

    // Risk Button Toggles
    const prefSafe = document.getElementById('prefSafe');
    const prefRiskBalanced = document.getElementById('prefRiskBalanced');
    const prefAggressive = document.getElementById('prefAggressive');

    // State Variables
    let selectedPriority = 'balanced';
    let selectedRisk = 'balanced';
    let currentPrefList = [];

    initPreferenceTab();

    function initPreferenceTab() {
        if (!preferenceForm) return;

        // Sync inputs: if user already entered their details in prediction form, copy them
        const mainRankInput = document.getElementById('inputRank');
        const mainCatSelect = document.getElementById('selectCategory');
        if (mainRankInput && mainRankInput.value) {
            prefRank.value = mainRankInput.value;
        }
        if (mainCatSelect && mainCatSelect.value) {
            prefCategory.value = mainCatSelect.value;
        }

        // Sync Category and update labels
        if (prefCategory) {
            prefCategory.addEventListener('change', () => {
                const val = prefCategory.value;
                const selectCategory = document.getElementById('selectCategory');
                if (selectCategory && selectCategory.value !== val) {
                    selectCategory.value = val;
                    selectCategory.dispatchEvent(new Event('change'));
                }
                updatePrefRankLabelAndHint(val);
            });
            // Initial call to sync
            updatePrefRankLabelAndHint(prefCategory.value);
        }

        // Sync Rank
        if (prefRank) {
            prefRank.addEventListener('input', () => {
                const val = prefRank.value;
                const inputRank = document.getElementById('inputRank');
                if (inputRank && inputRank.value !== val) {
                    inputRank.value = val;
                }
            });
        }

        // Toggle Priority Buttons
        const priorityBtns = [prefBranchFirst, prefBalanced, prefCollegeFirst];
        priorityBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    priorityBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    selectedPriority = btn.getAttribute('data-val');
                });
            }
        });

        // Toggle Risk Buttons
        const riskBtns = [prefSafe, prefRiskBalanced, prefAggressive];
        riskBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    riskBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    selectedRisk = btn.getAttribute('data-val');
                });
            }
        });

        // Form Submit
        preferenceForm.addEventListener('submit', handlePreferenceSubmit);
    }

    async function handlePreferenceSubmit(e) {
        e.preventDefault();

        const rankVal = prefRank.value ? parseInt(prefRank.value, 10) : null;
        if (!rankVal) {
            showToast('Please enter your JEE Main Rank to generate the choice list!', 'error');
            return;
        }

        const btnText = prefSubmitBtn.querySelector('.btn-text');
        const btnLoader = prefSubmitBtn.querySelector('.btn-loader');
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        prefSubmitBtn.disabled = true;

        showSkeletons(preferenceResults, 5);
        const preferenceLayout = document.getElementById('preferenceLayout');
        if (preferenceLayout) {
            preferenceLayout.classList.remove('initial-state');
        }
        preferenceResults.style.display = 'block';
        preferenceResults.scrollIntoView({ behavior: 'smooth' });

        // Retrieve extra filters from prediction form if set
        const selectGender = document.getElementById('selectGender');
        const selectState = document.getElementById('selectState');
        const chkIIT = document.getElementById('chkIIT');
        const chkNIT = document.getElementById('chkNIT');
        const chkIIIT = document.getElementById('chkIIIT');
        const chkGFTI = document.getElementById('chkGFTI');

        const gender = selectGender ? selectGender.value : 'Gender-Neutral';
        const homeState = selectState ? selectState.value : null;

        const preferredBranches = [];
        const selectedChips = document.querySelectorAll('#selectedBranches .branch-chip');
        selectedChips.forEach(chip => preferredBranches.push(chip.dataset.val));

        const instituteTypes = [];
        if (chkIIT && chkIIT.checked) instituteTypes.push('IIT');
        if (chkNIT && chkNIT.checked) instituteTypes.push('NIT');
        if (chkIIIT && chkIIIT.checked) instituteTypes.push('IIIT');
        if (chkGFTI && chkGFTI.checked) instituteTypes.push('GFTI');

        const payload = {
            jee_main_rank: rankVal,
            category: prefCategory.value,
            gender: gender,
            home_state: homeState || null,
            preferred_branches: preferredBranches,
            institute_types: instituteTypes,
            branch_priority: selectedPriority,
            risk_tolerance: selectedRisk
        };

        try {
            const data = await api.getPreferenceList(payload);
            currentPrefList = data.preference_list;
            renderPreferenceList(data);
        } catch (err) {
            console.error(err);
            showToast('Failed to generate choice list. Try tweaking filters.', 'error');
            preferenceResults.style.display = 'none';
            if (preferenceLayout) {
                preferenceLayout.classList.add('initial-state');
            }
        } finally {
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            prefSubmitBtn.disabled = false;
        }
    }

    function renderPreferenceList(data) {
        preferenceResults.innerHTML = '';

        if (data.preference_list.length === 0) {
            preferenceResults.innerHTML = `
                <div class="glass-card no-results">
                    <p class="no-results-emoji">🏜️</p>
                    <h3>No choices generated</h3>
                    <p>Try expanding your branch preferences or rank limit parameters.</p>
                </div>
            `;
            return;
        }

        // Header Actions Card
        let html = `
            <div class="glass-card pref-header-card fade-in">
                <div class="pref-meta">
                    <h3 class="card-title">Generated Preference Order</h3>
                    <p>Optimized choice list for Rank <strong>${formatRank(data.your_rank)}</strong> using a <strong>${data.strategy}</strong> strategy.</p>
                </div>
                <div class="pref-actions">
                    <button class="card-btn secondary-btn" id="btnExportTxt">💾 Export txt</button>
                    <button class="card-btn primary-btn" id="btnExportCsv">📊 Export CSV</button>
                </div>
            </div>
            
            <p class="drag-hint">💡 Pro-Tip: You can <strong>drag & drop</strong> rows to fine-tune your JoSAA choice order!</p>
            
            <div class="preference-list-container" id="draggableList">
        `;

        data.preference_list.forEach((item) => {
            const chanceLower = item.chance_category.toLowerCase();
            const badgeIcon = chanceLower === 'safe' ? '✅' : chanceLower === 'moderate' ? '⚡' : '🌟';

            html += `
                <div class="pref-item-card glass-card fade-in" draggable="true" data-order="${item.rank_order}">
                    <div class="pref-drag-handle">☰</div>
                    <div class="pref-index">${item.rank_order}</div>
                    <div class="pref-details">
                        <div class="pref-title-row">
                            <span class="badge ${item.institute_type.toLowerCase()}-badge">${item.institute_type}</span>
                            <span class="badge state-badge">${item.state}</span>
                        </div>
                        <h4 class="pref-college">${item.institute}</h4>
                        <p class="pref-program">${item.program}</p>
                        <div class="pref-reason">${item.reason}</div>
                    </div>
                    <div class="pref-chance-badge ${chanceLower}-badge">
                        <span>${badgeIcon}</span>
                        <span>${item.chance_category}</span>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        preferenceResults.innerHTML = html;

        // Initialize Drag and Drop
        initDragAndDrop();

        // Bind Export Actions
        document.getElementById('btnExportTxt').addEventListener('click', exportToTxt);
        document.getElementById('btnExportCsv').addEventListener('click', exportToCsv);
    }

    function initDragAndDrop() {
        const container = document.getElementById('draggableList');
        if (!container) return;

        let dragEl = null;

        container.addEventListener('dragstart', (e) => {
            const card = e.target.closest('.pref-item-card');
            if (card) {
                dragEl = card;
                card.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }
        });

        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(container, e.clientY);
            const draggingCard = document.querySelector('.dragging');
            if (afterElement == null) {
                container.appendChild(draggingCard);
            } else {
                container.insertBefore(draggingCard, afterElement);
            }
        });

        container.addEventListener('dragend', () => {
            if (dragEl) {
                dragEl.classList.remove('dragging');
                dragEl = null;
                recalculateIndices();
            }
        });
    }

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.pref-item-card:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    function recalculateIndices() {
        const cards = document.querySelectorAll('#draggableList .pref-item-card');
        cards.forEach((card, idx) => {
            const indexDisplay = card.querySelector('.pref-index');
            if (indexDisplay) {
                indexDisplay.textContent = idx + 1;
            }
            card.setAttribute('data-order', idx + 1);
        });
        showToast('Choice orders updated!', 'info');
    }

    // Export Helpers
    function exportToTxt() {
        const cards = document.querySelectorAll('#draggableList .pref-item-card');
        if (cards.length === 0) return;

        let content = `JEE COUNSELOR — OPTIMIZED CHOICE FILLING ORDER\n`;
        content += `Generated on: ${new Date().toLocaleDateString()}\n`;
        content += `Rank: ${prefRank.value} | Category: ${prefCategory.value}\n`;
        content += `========================================================================\n\n`;

        cards.forEach(card => {
            const order = card.getAttribute('data-order');
            const college = card.querySelector('.pref-college').textContent;
            const program = card.querySelector('.pref-program').textContent;
            const chance = card.querySelector('.pref-chance-badge').textContent.trim();
            content += `${order}. [${chance}] ${college}\n   Branch: ${program}\n\n`;
        });

        triggerDownload(content, 'jee_choices.txt', 'text/plain');
    }

    function exportToCsv() {
        const cards = document.querySelectorAll('#draggableList .pref-item-card');
        if (cards.length === 0) return;

        let csv = 'Choice Code,Institute,Program,Chance Category\n';
        cards.forEach(card => {
            const order = card.getAttribute('data-order');
            const college = escapeCsv(card.querySelector('.pref-college').textContent);
            const program = escapeCsv(card.querySelector('.pref-program').textContent);
            const chance = escapeCsv(card.querySelector('.pref-chance-badge').textContent.trim());
            csv += `${order},${college},${program},${chance}\n`;
        });

        triggerDownload(csv, 'jee_choices.csv', 'text/csv');
    }

    function escapeCsv(str) {
        return `"${str.replace(/"/g, '""')}"`;
    }

    function triggerDownload(content, fileName, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Downloaded ${fileName}!`, 'success');
    }

    function updatePrefRankLabelAndHint(category) {
        const rankLabel = document.getElementById('prefRankLabel');
        const rankHint = document.getElementById('prefRankHint');
        const prefRankInput = document.getElementById('prefRank');
        
        if (!rankLabel) return;
        
        if (category === 'OPEN') {
            rankLabel.textContent = 'JEE Main Rank (AIR)';
            if (prefRankInput) prefRankInput.placeholder = 'e.g. 15000';
            if (rankHint) {
                rankHint.textContent = 'Enter Common Rank List (CRL) for General.';
                rankHint.style.color = 'var(--text-muted)';
            }
        } else {
            rankLabel.textContent = `JEE Main Rank (${category} Category)`;
            if (prefRankInput) prefRankInput.placeholder = 'e.g. 1500';
            if (rankHint) {
                rankHint.innerHTML = `⚠️ Enter your <strong>${category} Category Rank</strong>, NOT your CRL (AIR). JoSAA uses category ranks.`;
                rankHint.style.color = 'var(--orange)';
            }
        }
    }
});
