/**
 * Real-time Monitor
 * Handles SSE connection and live trace updates
 */

$(document).ready(function () {
    let eventSource = null;

    // Initialize SSE connection
    function initializeSSE() {
        eventSource = new EventSource('/api/stream');

        eventSource.addEventListener('connected', function (e) {
            const data = JSON.parse(e.data);
            console.log('SSE Connected:', data.message);
        });

        eventSource.addEventListener('trace', function (e) {
            const event = JSON.parse(e.data);
            handleTraceEvent(event);
        });

        eventSource.addEventListener('ping', function (e) {
            // Keepalive ping, do nothing
        });

        eventSource.onerror = function (e) {
            console.error('SSE Error:', e);
            setTimeout(initializeSSE, 5000); // Reconnect after 5s
        };
    }

    function handleTraceEvent(event) {
        const { node_type, status, message, data } = event;

        // Update trace terminal
        addTraceToTerminal(node_type, status, message);

        // Update specific UI elements based on node type
        switch (node_type) {
            case 'privacy_shield':
                handlePrivacyShieldEvent(status, message, data);
                break;

            case 'productivity_agent':
            case 'ethics_agent':
            case 'creativity_agent':
                handleAgentEvent(node_type, status, message, data);
                break;

            case 'aggregator':
                handleAggregatorEvent(status, message, data);
                break;
        }
    }

    function handlePrivacyShieldEvent(status, message, data) {
        if (status === 'started') {
            $('#privacyContent').html(
                '<div class="placeholder-state">' +
                '<div class="spinner-border text-warning" role="status"></div>' +
                '<p class="placeholder-text mt-3">Analyzing for PII...</p>' +
                '</div>'
            );
        } else if (status === 'completed' && data) {
            displayPrivacyAnalysis(data);
        }
    }

    function displayPrivacyAnalysis(data) {
        const { anonymized_query, redaction_count, processing_time_ms } = data;

        // Show anonymized text
        $('#privacyContent').html(
            '<div class="privacy-comparison">' +
            '<div class="comparison-section">' +
            '<h6>Anonymized Query (sent to cloud)</h6>' +
            '<div class="comparison-text anonymized-text">' +
            highlightPII(anonymized_query) +
            '</div>' +
            '</div>' +
            '</div>'
        );

        // Show stats
        $('#redactionCount').text(redaction_count);
        $('#privacyTime').text(Math.round(processing_time_ms) + 'ms');
        $('#privacyStats').show();
    }

    function highlightPII(text) {
        // Highlight PII placeholders
        return text.replace(/(<[A-Z_]+>)/g, '<span class="entity-highlight">$1</span>');
    }

    function handleAgentEvent(nodeType, status, message, data) {
        const agentName = nodeType.replace('_agent', '');
        const $agentStatus = $(`.agent-status[data-agent="${agentName}"]`);

        if (status === 'started') {
            $agentStatus.addClass('active');
            $agentStatus.find('.agent-state').text('Processing...');
        } else if (status === 'completed') {
            $agentStatus.removeClass('active').addClass('completed');
            $agentStatus.find('.agent-state').text(
                `Completed (${Math.round(data?.processing_time_ms || 0)}ms)`
            );
        }
    }

    function handleAggregatorEvent(status, message, data) {
        if (status === 'started') {
            $('#finalResponse').html(
                '<div class="placeholder-state">' +
                '<div class="spinner-border text-primary" role="status"></div>' +
                '<p class="placeholder-text mt-3">Synthesizing responses...</p>' +
                '</div>'
            );
        }
    }

    function addTraceToTerminal(nodeType, status, message) {
        const timestamp = new Date().toLocaleTimeString();
        const nodeLabel = nodeType.toUpperCase().replace('_', ' ');
        const statusClass = status === 'completed' ? 'success' :
            status === 'error' ? 'error' : 'agent';

        const $log = $('<div>')
            .addClass('terminal-line')
            .addClass(statusClass)
            .html(
                `<span class="timestamp">[${timestamp}]</span>` +
                `<span class="message">` +
                `<span class="node-badge ${getNodeBadgeClass(nodeType)}">${nodeLabel}</span> ` +
                `${message}` +
                `</span>`
            );

        $('#traceTerminal').append($log);

        // Auto-scroll to bottom
        const terminal = document.getElementById('traceTerminal');
        if (terminal) {
            terminal.scrollTop = terminal.scrollHeight;
        }
    }

    function getNodeBadgeClass(nodeType) {
        if (nodeType === 'privacy_shield') return 'privacy';
        if (nodeType === 'aggregator') return 'aggregator';
        return 'agent';
    }

    // Initialize on page load
    initializeSSE();

    // Reconnect on page visibility change
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden && (!eventSource || eventSource.readyState === EventSource.CLOSED)) {
            initializeSSE();
        }
    });
});
