/**
 * Main Dashboard Logic
 * Handles form submission and UI updates
 */

$(document).ready(function () {
    let contributionChart = null;

    // Form submission
    $('#queryForm').on('submit', async function (e) {
        e.preventDefault();

        const query = $('#userQuery').val().trim();
        if (!query) return;

        // Reset UI
        resetDashboard();

        // Update button state
        toggleSubmitButton(true);

        // Clear trace terminal
        $('#traceTerminal').html('');

        // Submit query
        try {
            const response = await $.ajax({
                url: '/api/query',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ query })
            });

            if (response.success) {
                displayFinalResult(response.result);
            } else {
                showError(response.error || 'Unknown error occurred');
            }

        } catch (error) {
            showError(error.responseJSON?.error || 'Network error occurred');
        } finally {
            toggleSubmitButton(false);
        }
    });

    // Clear button
    $('#clearBtn').on('click', function () {
        $('#userQuery').val('');
        resetDashboard();
    });

    // Clear trace button
    $('#clearTraceBtn').on('click', function () {
        $('#traceTerminal').html(
            '<div class="terminal-line system">' +
            '<span class="timestamp">[SYSTEM]</span>' +
            '<span class="message">Trace cleared.</span>' +
            '</div>'
        );
    });

    function toggleSubmitButton(loading) {
        const $btn = $('#submitBtn');
        $btn.prop('disabled', loading);

        if (loading) {
            $btn.find('.btn-text').hide();
            $btn.find('.btn-loader').show();
        } else {
            $btn.find('.btn-text').show();
            $btn.find('.btn-loader').hide();
        }
    }

    function resetDashboard() {
        // Reset privacy panel
        $('#privacyContent').html(
            '<div class="placeholder-state">' +
            '<div class="placeholder-icon">🔒</div>' +
            '<p class="placeholder-text">Processing...</p>' +
            '</div>'
        );
        $('#privacyStats').hide();

        // Reset domain expert panel
        $('#domainContent').html(
            '<div class="placeholder-state">' +
            '<div class="placeholder-icon">🎯</div>' +
            '<p class="placeholder-text">Analyzing...</p>' +
            '</div>'
        );
        $('#domainStats').hide();

        // Reset agent statuses
        $('.agent-status').removeClass('active completed').each(function () {
            $(this).find('.agent-state').text('Idle');
        });

        // Reset final response
        $('#finalResponse').html(
            '<div class="placeholder-state">' +
            '<div class="placeholder-icon">⏳</div>' +
            '<p class="placeholder-text">Processing your query...</p>' +
            '</div>'
        );

        // Hide chart
        $('#chartContainer').hide();
    }

    function displayFinalResult(result) {
        // Display final response (markdown rendered)
        const formattedResponse = formatMarkdown(result.final_response);
        $('#finalResponse').html(formattedResponse);

        // Display DP metrics
        if (result.dp_metrics) {
            displayDPMetrics(result.dp_metrics);
        }

        // Display Audit Log ID
        if (result.audit_id) {
            $('#auditIdDisplay').text('#' + result.audit_id);
            $('#auditLogInfo').show();
        }

        // Display Retrieved Context
        if (result.retrieved_context && result.retrieved_context.length > 0) {
            const $list = $('#retrievedContextList');
            $list.empty();
            result.retrieved_context.forEach(ctx => {
                $list.append(`<div style="margin-bottom:4px;padding-bottom:4px;border-bottom:1px dotted #444;">• ${ctx}</div>`);
            });
            $('#retrieverSection').show();
        } else {
            $('#retrieverSection').hide();
        }

        // Display Ethics Verdict
        if (result.ethics_verdict) {
            const v = result.ethics_verdict;
            const isPass = v.verdict === 'PASS';
            const badgeClass = isPass ? 'bg-success' : 'bg-danger';
            let ethicsHtml = `<div class="mt-3 p-2" style="border:1px solid #444;border-radius:6px;background:#111;">
                <strong style="color:#e0e0e0;">Ethics Review</strong>
                <span class="badge ${badgeClass} ms-2">${v.verdict}</span>
                <p style="font-size:0.85rem;color:#aaaaaa;margin-top:6px;margin-bottom:4px;">${v.reason}</p>`;
            if (v.suggestions && v.suggestions.length > 0) {
                ethicsHtml += `<ul style="font-size:0.8rem;color:#ffc107;margin-bottom:0;padding-left:18px;">` +
                    v.suggestions.map(s => `<li>${s}</li>`).join('') + `</ul>`;
            }
            ethicsHtml += `</div>`;
            $('#finalResponse').append(ethicsHtml);
        }

        // Display Aggregator Decision + retry count
        if (result.aggregator_decision) {
            const d = result.aggregator_decision;
            const actionClass = d.action === 'ACCEPT' ? 'bg-success'
                : d.action === 'FORCE_ACCEPT' ? 'bg-warning text-dark' : 'bg-info';
            const retryTxt = result.retry_count > 0
                ? ` after ${result.retry_count} retry attempt(s)` : '';
            $('#finalResponse').append(
                `<div class="mt-2 text-end">
                    <span class="badge ${actionClass}">Aggregator: ${d.action}${retryTxt}</span>
                </div>`
            );
        }

        // Display pipeline chart (productivity vs ethics contribution proxy)
        displayContributionChart(result.agent_contributions);

        addTraceLog(
            'success',
            'COMPLETE',
            `Pipeline complete in ${Math.round(result.total_processing_time_ms)}ms` +
            (result.retry_count > 0 ? ` (${result.retry_count} retry/retries)` : '')
        );
    }

    function displayContributionChart(contributions) {
        if (!contributions || Object.keys(contributions).length === 0) return;
        $('#chartContainer').show();

        const ctx = document.getElementById('contributionChart');
        if (contributionChart) contributionChart.destroy();

        // Fixed per-agent labels and colors (order-independent)
        const agentMeta = {
            creativity_agent:   { label: '🎨 Creativity',   bg: 'rgba(0, 180, 240, 0.85)',  border: 'rgba(0, 180, 240, 1)'  },
            productivity_agent: { label: '💼 Productivity', bg: 'rgba(138, 43, 226, 0.85)', border: 'rgba(138, 43, 226, 1)' },
            ethics_agent:       { label: '⚖️ Ethics',       bg: 'rgba(0, 200, 150, 0.85)',  border: 'rgba(0, 200, 150, 1)'  },
        };

        const keys         = Object.keys(contributions);
        const labels       = keys.map(k => agentMeta[k] ? agentMeta[k].label : k.replaceAll('_', ' '));
        const data         = keys.map(k => (contributions[k] * 100).toFixed(1));
        const bgColors     = keys.map(k => agentMeta[k] ? agentMeta[k].bg     : 'rgba(180,180,180,0.8)');
        const borderColors = keys.map(k => agentMeta[k] ? agentMeta[k].border : 'rgba(180,180,180,1)');

        contributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e0e0e0',
                            padding: 15,
                            font: { size: 12, family: 'Inter' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${ctx.parsed}%`
                        }
                    }
                }
            }
        });
    }

    function formatMarkdown(text) {
        // Basic markdown formatting
        return text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    function showError(message) {
        $('#finalResponse').html(
            '<div class="alert alert-danger">' +
            '<strong>Error:</strong> ' + message +
            '</div>'
        );

        addTraceLog('error', 'ERROR', message);
    }

    function addTraceLog(type, label, message) {
        const timestamp = new Date().toLocaleTimeString();
        const $log = $('<div>')
            .addClass('terminal-line')
            .addClass(type)
            .html(
                `<span class="timestamp">[${label}]</span>` +
                `<span class="message">${message}</span>`
            );

        $('#traceTerminal').append($log);

        // Auto-scroll to bottom
        const terminal = document.getElementById('traceTerminal');
        terminal.scrollTop = terminal.scrollHeight;
    }

    function displayDomainAnalysis(domainAnalysis) {
        if (!domainAnalysis) return;

        console.log("Domain Analysis Data:", domainAnalysis);
        console.log("Confidence:", domainAnalysis.confidence, "ProcessingTime:", domainAnalysis.processing_time_ms);

        // Show domain stats
        $('#domainStats').show();
        $('#domainContent').hide();

        // Update domain name
        $('#domainName').text(domainAnalysis.predicted_domain || 'Unknown');

        // Update confidence meter - handle undefined/null/string
        let confidence = domainAnalysis.confidence;
        if (typeof confidence === 'string') confidence = parseFloat(confidence);
        const confidencePct = (confidence != null && !isNaN(confidence))
            ? Math.round(confidence * 100)
            : 0;
        $('#confidenceBar').css('width', confidencePct + '%');
        $('#confidenceText').text(confidencePct + '%');

        // Show/hide sensitivity indicator
        if (domainAnalysis.is_high_sensitivity) {
            $('#sensitivityIndicator').show();
        } else {
            $('#sensitivityIndicator').hide();
        }
    }

    // Display Differential Privacy Metrics
    function displayDPMetrics(dpMetrics) {
        if (!dpMetrics) return;

        // Show DP metrics panel
        $('#dpMetrics').show();
        $('#dpContent').hide();

        // Update privacy guarantee
        $('#dpGuarantee').text(dpMetrics.privacy_guarantee);

        // Update budget meter
        const budgetPct = (dpMetrics.budget_used / dpMetrics.epsilon_budget) * 100;
        $('#budgetBar').css('width', budgetPct + '%');
        $('#budgetText').text(dpMetrics.budget_used.toFixed(2) + ' / ' + dpMetrics.epsilon_budget.toFixed(1));

        // Update stats
        $('#queriesProcessed').text(dpMetrics.queries_processed);
        $('#noiseScale').text(dpMetrics.noise_scale.toFixed(2));
    }

    // Export for use by monitor.js
    window.dashboardUI = {
        addTraceLog,
        toggleSubmitButton,
        displayDomainAnalysis,
        displayDPMetrics
    };
});

// Display Differential Privacy Metrics
function displayDPMetrics(dpMetrics) {
    if (!dpMetrics) return;

    // Show DP metrics panel
    $('#dpMetrics').show();
    $('#dpContent').hide();

    // Update privacy guarantee
    $('#dpGuarantee').text(dpMetrics.privacy_guarantee);

    // Update budget meter
    const budgetPct = (dpMetrics.budget_used / dpMetrics.epsilon_budget) * 100;
    $('#budgetBar').css('width', budgetPct + '%');
    $('#budgetText').text(dpMetrics.budget_used.toFixed(2) + ' / ' + dpMetrics.epsilon_budget.toFixed(1));

    // Update stats
    $('#queriesProcessed').text(dpMetrics.queries_processed);
    $('#noiseScale').text(dpMetrics.noise_scale.toFixed(2));
}

// Initialize dashboardUI namespace if it doesn't exist
window.dashboardUI = window.dashboardUI || {};

// Export DP function
window.dashboardUI.displayDPMetrics = displayDPMetrics;
