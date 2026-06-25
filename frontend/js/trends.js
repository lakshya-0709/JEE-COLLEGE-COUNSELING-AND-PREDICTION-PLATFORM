// trends.js — Cutoff Trends page: autocomplete, chart, table


document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const trendInstitute = document.getElementById('trendInstitute');
    const trendInstituteDropdown = document.getElementById('trendInstituteDropdown');
    const trendProgram = document.getElementById('trendProgram');
    const trendSeatType = document.getElementById('trendSeatType');
    const trendQuota = document.getElementById('trendQuota');
    const trendBtn = document.getElementById('trendBtn');
    const trendChartContainer = document.getElementById('trendChartContainer');
    const trendDirection = document.getElementById('trendDirection');
    const trendChartCanvas = document.getElementById('trendChart');
    const trendTable = document.getElementById('trendTable');

    // Chart instance tracker
    let trendChartInstance = null;

    // Initialize Autocomplete listeners
    initTrendsTab();

    function initTrendsTab() {
        if (!trendInstitute) return;

        // Autocomplete search with debounce
        trendInstitute.addEventListener('input', debounce(async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                trendInstituteDropdown.style.display = 'none';
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
            if (e.target !== trendInstitute && e.target !== trendInstituteDropdown) {
                trendInstituteDropdown.style.display = 'none';
            }
        });

        // Trigger trend query
        trendBtn.addEventListener('click', loadTrendsData);
    }

    function renderAutocompleteDropdown(colleges) {
        trendInstituteDropdown.innerHTML = '';
        if (colleges.length === 0) {
            trendInstituteDropdown.style.display = 'none';
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
                trendInstitute.value = col.institute;
                trendInstituteDropdown.style.display = 'none';
                loadProgramsForInstitute(col.institute);
            });
            trendInstituteDropdown.appendChild(item);
        });

        trendInstituteDropdown.style.display = 'block';
    }

    async function loadProgramsForInstitute(instituteName) {
        trendProgram.innerHTML = '<option value="">Loading programs...</option>';
        try {
            const programs = await api.getPrograms(instituteName);
            trendProgram.innerHTML = '<option value="" disabled selected>Select program...</option>';
            programs.forEach(prog => {
                const opt = document.createElement('option');
                opt.value = prog.program;
                opt.textContent = `${prog.branch_short} — ${prog.degree_type}`;
                trendProgram.appendChild(opt);
            });
        } catch (err) {
            console.error(err);
            trendProgram.innerHTML = '<option value="">Failed to load programs</option>';
        }
    }

    async function loadTrendsData() {
        const institute = trendInstitute.value.trim();
        const program = trendProgram.value;
        const seatType = trendSeatType.value;
        const quota = trendQuota.value;

        if (!institute || !program) {
            showToast('Please select both Institute and Program!', 'error');
            return;
        }

        trendBtn.disabled = true;
        trendBtn.textContent = 'Fetching...';

        const params = {
            institute: institute,
            program: program,
            seat_type: seatType,
            gender: 'Gender-Neutral', // default filter for trends
            quota: quota
        };

        try {
            const data = await api.getTrends(params);
            trendChartContainer.style.display = 'block';

            // Format Trend Direction Label
            renderTrendDirection(data.trend_direction);

            // Render Chart
            renderChart(data);

            // Render Table
            renderTableDetails(data.trends);

            trendChartContainer.scrollIntoView({ behavior: 'smooth' });
        } catch (err) {
            console.error(err);
            showToast('Failed to load cutoff trends. Check selection or filters.', 'error');
        } finally {
            trendBtn.disabled = false;
            trendBtn.textContent = 'Show Trend';
        }
    }

    function renderTrendDirection(direction) {
        let directionHtml = '';
        if (direction === 'getting_harder') {
            directionHtml = `
                <div class="trend-direction-badge harder">
                    🔴 Cutoffs getting harder (Admission closing ranks are decreasing)
                </div>
            `;
        } else if (direction === 'getting_easier') {
            directionHtml = `
                <div class="trend-direction-badge easier">
                    🟢 Cutoffs getting easier (Admission closing ranks are increasing)
                </div>
            `;
        } else {
            directionHtml = `
                <div class="trend-direction-badge stable">
                    ⚪ Cutoffs are relatively stable
                </div>
            `;
        }
        trendDirection.innerHTML = directionHtml;
    }

    function renderChart(data) {
        const ctx = trendChartCanvas.getContext('2d');

        if (trendChartInstance) {
            trendChartInstance.destroy();
        }

        const labels = data.trends.map(t => t.year.toString());
        const closingRanks = data.trends.map(t => t.closing_rank);
        const openingRanks = data.trends.map(t => t.opening_rank);

        // Chart gradient coloring
        const chartGradient = ctx.createLinearGradient(0, 0, 0, 400);
        chartGradient.addColorStop(0, 'rgba(0, 212, 255, 0.2)');
        chartGradient.addColorStop(1, 'rgba(0, 212, 255, 0)');

        trendChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Closing Rank',
                        data: closingRanks,
                        borderColor: '#00d4ff',
                        backgroundColor: chartGradient,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#00d4ff',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Opening Rank',
                        data: openingRanks,
                        borderColor: '#ff6b35',
                        backgroundColor: 'transparent',
                        fill: false,
                        tension: 0.35,
                        pointBackgroundColor: '#ff6b35',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 1.5,
                        pointRadius: 5,
                        borderDash: [6, 4]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#e2e8f0',
                            font: { family: 'Inter', size: 13 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += formatRank(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8', font: { family: 'Inter' } }
                    },
                    y: {
                        reverse: true, // Reversed ranks are more intuitive
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Inter' },
                            callback: function (value) {
                                return formatRank(value);
                            }
                        }
                    }
                }
            }
        });
    }

    function renderTableDetails(trends) {
        if (trends.length === 0) {
            trendTable.innerHTML = '<p class="no-data">No history available for this combination.</p>';
            return;
        }

        let html = `
            <table class="compare-table">
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

        trends.forEach(t => {
            html += `
                <tr>
                    <td><strong>${t.year}</strong></td>
                    <td>${formatRank(t.opening_rank)}</td>
                    <td class="text-glow cyan-text">${formatRank(t.closing_rank)}</td>
                    <td>Round ${t.round}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        trendTable.innerHTML = html;
    }
});
