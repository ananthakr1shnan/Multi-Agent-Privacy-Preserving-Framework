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

    // Export for use by monitor.js
    window.dashboardUI = {
        addTraceLog,
        toggleSubmitButton
    };
});
