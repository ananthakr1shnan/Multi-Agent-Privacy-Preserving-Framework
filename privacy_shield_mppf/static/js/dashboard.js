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
        // Display final response
        const formattedResponse = formatMarkdown(result.final_response);
        $('#finalResponse').html(formattedResponse);

        // Display DP metrics if available
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
                $list.append(`<div style="margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px dotted #444;">• ${ctx}</div>`);
            });
            $('#retrieverSection').show();
        } else {
            $('#retrieverSection').hide();
        }

        // Display agent contributions chart
        displayContributionChart(result.agent_contributions);

        // Show processing time
        addTraceLog(
            'success',
            'COMPLETE',
            `Workflow completed in ${Math.round(result.total_processing_time_ms)}ms`
        );
    }

    function displayContributionChart(contributions) {
        $('#chartContainer').show();

        const ctx = document.getElementById('contributionChart');

        // Destroy existing chart
        if (contributionChart) {
            contributionChart.destroy();
        }

        const labels = Object.keys(contributions).map(k =>
            k.replace('_', ' ').split(' ').map(w =>
                w.charAt(0).toUpperCase() + w.slice(1)
            ).join(' ')
        );

        const data = Object.values(contributions).map(v => (v * 100).toFixed(1));

        contributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(66, 135, 245, 0.8)',
                        'rgba(138, 43, 226, 0.8)',
                        'rgba(0, 200, 150, 0.8)'
                    ],
                    borderColor: [
                        'rgba(66, 135, 245, 1)',
                        'rgba(138, 43, 226, 1)',
                        'rgba(0, 200, 150, 1)'
                    ],
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
                            font: {
                                size: 12,
                                family: 'Inter'
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
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
