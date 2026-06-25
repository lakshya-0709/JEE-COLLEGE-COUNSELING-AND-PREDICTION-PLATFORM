// compare.js — College Comparison page: dual autocomplete, chart, metrics table


document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const compareInstA = document.getElementById('compareInstA');
    const compareInstADropdown = document.getElementById('compareInstADropdown');
    const compareProgA = document.getElementById('compareProgA');

    const compareInstB = document.getElementById('compareInstB');
    const compareInstBDropdown = document.getElementById('compareInstBDropdown');
    const compareProgB = document.getElementById('compareProgB');

    const compareBtn = document.getElementById('compareBtn');
    const compareResults = document.getElementById('compareResults');

    // Chart tracker
    let compareChartInstance = null;

    initCompareTab();

    function initCompareTab() {
        if (!compareInstA || !compareInstB) return;

        // Autocomplete College A
        compareInstA.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                compareInstADropdown.style.display = 'none';
                return;
            }
            try {
                const colleges = await api.searchColleges(query);
                renderAutocomplete(colleges, compareInstA, compareInstADropdown, compareProgA);
            } catch (err) {
                console.error(err);
            }
        }, 250));

        // Autocomplete College B
        compareInstB.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                compareInstBDropdown.style.display = 'none';
                return;
            }
            try {
                const colleges = await api.searchColleges(query);
                renderAutocomplete(colleges, compareInstB, compareInstBDropdown, compareProgB);
            } catch (err) {
                console.error(err);
            }
        }, 250));

        // Close dropdowns on outside clicks
        document.addEventListener('click', (e) => {
            if (e.target !== compareInstA && e.target !== compareInstADropdown) {
                compareInstADropdown.style.display = 'none';
            }
            if (e.target !== compareInstB && e.target !== compareInstBDropdown) {
                compareInstBDropdown.style.display = 'none';
            }
        });

        // Compare Action
        compareBtn.addEventListener('click', handleCompare);
    }

    function renderAutocomplete(colleges, inputEl, dropdownEl, progSelectEl) {
        dropdownEl.innerHTML = '';
        if (colleges.length === 0) {
            dropdownEl.style.display = 'none';
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
                inputEl.value = col.institute;
                dropdownEl.style.display = 'none';
                loadPrograms(col.institute, progSelectEl);
            });
            dropdownEl.appendChild(item);
        });

        dropdownEl.style.display = 'block';
    }

    async function loadPrograms(instituteName, progSelectEl) {
        progSelectEl.innerHTML = '<option value="">Loading programs...</option>';
        try {
            const programs = await api.getPrograms(instituteName);
            progSelectEl.innerHTML = '<option value="" disabled selected>Select program...</option>';
            programs.forEach(prog => {
                const opt = document.createElement('option');
                opt.value = prog.program;
                opt.textContent = `${prog.branch_short} — ${prog.degree_type}`;
                progSelectEl.appendChild(opt);
            });
        } catch (err) {
            console.error(err);
            progSelectEl.innerHTML = '<option value="">Failed to load programs</option>';
        }
    }

    async function handleCompare() {
        const collegeAInst = compareInstA.value.trim();
        const collegeAProg = compareProgA.value;
        const collegeBInst = compareInstB.value.trim();
        const collegeBProg = compareProgB.value;

        if (!collegeAInst || !collegeAProg || !collegeBInst || !collegeBProg) {
            showToast('Please select both College A and College B (Institutes & Programs)!', 'error');
            return;
        }

        compareBtn.disabled = true;
        compareBtn.textContent = 'Comparing...';

        // Read prediction filters if set, otherwise use defaults
        const selectCategory = document.getElementById('selectCategory');
        const selectGender = document.getElementById('selectGender');

        const seatType = selectCategory ? selectCategory.value : 'OPEN';
        const gender = selectGender ? selectGender.value : 'Gender-Neutral';

        // Determine default Quota: IITs only use AI, others use OS/AI
        // Let's check backend/routes/compare.py for defaults if we don't pass
        const payload = {
            college_a_institute: collegeAInst,
            college_a_program: collegeAProg,
            college_b_institute: collegeBInst,
            college_b_program: collegeBProg,
            seat_type: seatType,
            gender: gender,
            quota: 'AI' // Default to All India for general comparison
        };

        try {
            const data = await api.compareColleges(payload);
            renderComparison(data);
        } catch (err) {
            console.error(err);
            showToast('Failed to compare. Ensure both programs have historical cutoff data.', 'error');
        } finally {
            compareBtn.disabled = false;
            compareBtn.textContent = 'Compare Colleges';
        }
    }

    function renderComparison(data) {
        compareResults.innerHTML = '';
        compareResults.style.display = 'block';

        const itemA = data.college_a;
        const itemB = data.college_b;

        // Build side-by-side details layout
        let html = `
            <div class="compare-details-grid">
                <!-- College A Summary Card -->
                <div class="glass-card compare-col-card border-cyan">
                    <span class="badge cyan-badge">${itemA.institute_type}</span>
                    <span class="badge state-badge">${itemA.state}</span>
                    <h3 class="compare-col-name">${itemA.institute}</h3>
                    <p class="compare-col-prog">${itemA.program}</p>
                    <div class="compare-rank-display">
                        <div class="rank-title">Latest Closing Rank</div>
                        <div class="rank-value cyan-text text-glow">${formatRank(itemA.latest_closing)}</div>
                        <div class="trend-direction-mini">${formatTrendIcon(itemA.trend_direction)}</div>
                    </div>
                </div>

                <!-- College B Summary Card -->
                <div class="glass-card compare-col-card border-orange">
                    <span class="badge orange-badge">${itemB.institute_type}</span>
                    <span class="badge state-badge">${itemB.state}</span>
                    <h3 class="compare-col-name">${itemB.institute}</h3>
                    <p class="compare-col-prog">${itemB.program}</p>
                    <div class="compare-rank-display">
                        <div class="rank-title">Latest Closing Rank</div>
                        <div class="rank-value orange-text text-glow">${formatRank(itemB.latest_closing)}</div>
                        <div class="trend-direction-mini">${formatTrendIcon(itemB.trend_direction)}</div>
                    </div>
                </div>
            </div>

            <!-- Recommendation Card -->
            <div class="glass-card recommendation-card fade-in" style="margin-top: 1.5rem;">
                <div class="recommendation-badge">🤖 Counselor Verdict</div>
                <p class="recommendation-text">${data.recommendation}</p>
            </div>

            <!-- Overlaid Chart Card -->
            <div class="glass-card compare-chart-card fade-in" style="margin-top: 1.5rem;">
                <h4 class="card-title">Cutoff Overlap Comparison</h4>
                <div class="compare-canvas-container">
                    <canvas id="compareChartCanvas"></canvas>
                </div>
            </div>

            <!-- Comparison Table Card -->
            <div class="glass-card compare-table-card fade-in" style="margin-top: 1.5rem;">
                <h4 class="card-title">Detailed Metrics</h4>
                <table class="compare-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th class="cyan-text">${itemA.institute_short}</th>
                            <th class="orange-text">${itemB.institute_short}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Institute Type</strong></td>
                            <td>${itemA.institute_type}</td>
                            <td>${itemB.institute_type}</td>
                        </tr>
                        <tr>
                            <td><strong>State</strong></td>
                            <td>${itemA.state}</td>
                            <td>${itemB.state}</td>
                        </tr>
                        <tr>
                            <td><strong>Branch Code</strong></td>
                            <td>${itemA.branch_short}</td>
                            <td>${itemB.branch_short}</td>
                        </tr>
                        <tr>
                            <td><strong>Latest Cutoff ('24)</strong></td>
                            <td class="${itemA.latest_closing <= itemB.latest_closing ? 'text-safe font-bold' : ''}">${formatRank(itemA.latest_closing)}</td>
                            <td class="${itemB.latest_closing <= itemA.latest_closing ? 'text-safe font-bold' : ''}">${formatRank(itemB.latest_closing)}</td>
                        </tr>
                        <tr>
                            <td><strong>Demand Trend</strong></td>
                            <td>${formatTrendText(itemA.trend_direction)}</td>
                            <td>${formatTrendText(itemB.trend_direction)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;

        compareResults.innerHTML = html;
        compareResults.scrollIntoView({ behavior: 'smooth' });

        // Render overlaid Chart
        renderCompareChart(itemA, itemB);
    }

    function formatTrendIcon(direction) {
        if (direction === 'getting_harder') return '📈 Cutoffs decreasing (Higher Demand)';
        if (direction === 'getting_easier') return '📉 Cutoffs increasing (Lower Demand)';
        return '🔄 Cutoffs stable';
    }

    function formatTrendText(direction) {
        if (direction === 'getting_harder') return 'Increasing Demand (Harder)';
        if (direction === 'getting_easier') return 'Decreasing Demand (Easier)';
        return 'Stable';
    }

    function renderCompareChart(itemA, itemB) {
        const ctx = document.getElementById('compareChartCanvas').getContext('2d');

        if (compareChartInstance) {
            compareChartInstance.destroy();
        }

        // Align years from both sets
        const yearsA = itemA.trends.reduce((acc, t) => { acc[t.year] = t.closing_rank; return acc; }, {});
        const yearsB = itemB.trends.reduce((acc, t) => { acc[t.year] = t.closing_rank; return acc; }, {});

        const allYears = sortedUniqueKeys(yearsA, yearsB);
        const dataPointsA = allYears.map(y => yearsA[y] || null);
        const dataPointsB = allYears.map(y => yearsB[y] || null);

        compareChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: allYears.map(String),
                datasets: [
                    {
                        label: itemA.institute_short,
                        data: dataPointsA,
                        borderColor: '#00d4ff',
                        backgroundColor: 'transparent',
                        tension: 0.3,
                        pointBackgroundColor: '#00d4ff',
                        pointRadius: 5,
                        pointHoverRadius: 7
                    },
                    {
                        label: itemB.institute_short,
                        data: dataPointsB,
                        borderColor: '#ff6b35',
                        backgroundColor: 'transparent',
                        tension: 0.3,
                        pointBackgroundColor: '#ff6b35',
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e2e8f0', font: { family: 'Inter' } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        reverse: true, // Lower ranks = better/higher in chart
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            callback: function (val) { return formatRank(val); }
                        }
                    }
                }
            }
        });
    }

});
