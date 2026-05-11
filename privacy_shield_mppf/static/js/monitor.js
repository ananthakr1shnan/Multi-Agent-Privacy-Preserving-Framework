/**
 * Real-time Monitor
 * Handles SSE connection and live trace updates for the new sequential pipeline.
 */

$(document).ready(function () {
    let eventSource = null;

    // ── SSE Connection ──────────────────────────────────────────────────────
    function initializeSSE() {
        eventSource = new EventSource('/api/stream');

        eventSource.addEventListener('connected', function (e) {
            console.log('SSE Connected:', JSON.parse(e.data).message);
        });

        eventSource.addEventListener('trace', function (e) {
            handleTraceEvent(JSON.parse(e.data));
        });

        eventSource.addEventListener('ping', function () { /* keepalive */ });

        eventSource.onerror = function () {
            setTimeout(initializeSSE, 5000);
        };
    }

    // ── Main event router ───────────────────────────────────────────────────
    function handleTraceEvent(event) {
        const { node_type, status, message, data } = event;

        addTraceToTerminal(node_type, status, message, data);

        switch (node_type) {
            case 'privacy_shield':
                handlePrivacyShieldEvent(status, data);
                break;

            case 'domain_expert':
                handleDomainExpertEvent(status, data);
                break;

            case 'web_search':
                handleWebSearchEvent(status, message, data);
                break;

            case 'creativity_agent':
                handleAgentEvent('creativity', status, data);
                break;

            case 'productivity_agent':
                handleAgentEvent('productivity', status, data);
                break;

            case 'ethics_agent':
                handleEthicsEvent(status, data);
                break;

            case 'aggregator':
                handleAggregatorEvent(status, data);
                break;
        }
    }

    // ── Privacy Shield ──────────────────────────────────────────────────────
    function handlePrivacyShieldEvent(status, data) {
        if (status === 'started') {
            $('#privacyContent').html(spinner('Analyzing for PII...', 'text-warning'));
        } else if (status === 'completed' && data && data.anonymized_query !== undefined) {
            displayPrivacyAnalysis(data);
        }
    }

    function displayPrivacyAnalysis(data) {
        const { anonymized_query, redaction_count } = data;
        $('#privacyContent').html(
            '<div class="privacy-comparison">' +
            '<div class="comparison-section">' +
            '<h6>Anonymized Query (sent to cloud)</h6>' +
            '<div class="comparison-text anonymized-text">' +
            highlightPII(anonymized_query) +
            '</div></div></div>'
        );
        $('#redactionCount').text(redaction_count);
        $('#privacyStats').show();
    }

    function highlightPII(text) {
        return text
            ? text.replace(/(<[A-Z_]+>)/g, '<span class="entity-highlight">$1</span>')
            : '';
    }

    // ── Domain Expert ───────────────────────────────────────────────────────
    function handleDomainExpertEvent(status, data) {
        if (status === 'started') {
            $('#domainContent').html(spinner('Classifying domain...', 'text-info'));
        } else if (status === 'completed' && data && data.predicted_domain) {
            if (window.dashboardUI && window.dashboardUI.displayDomainAnalysis) {
                window.dashboardUI.displayDomainAnalysis(data);
            }
        }
    }

    // ── Web Search ──────────────────────────────────────────────────────────
    function handleWebSearchEvent(status, message, data) {
        const $webStatus = $('#webSearchStatus');
        if (status === 'started') {
            $webStatus.html(
                '<span class="badge bg-info me-1">🔍 WEB SEARCH</span>' +
                '<span class="text-info">Searching the web...</span>'
            ).show();
        } else if (status === 'processing') {
            // Skipped domain
            $webStatus.html(
                '<span class="badge bg-secondary me-1">🔍 WEB SEARCH</span>' +
                '<span class="text-muted">' + message + '</span>'
            ).show();
        } else if (status === 'completed' && data) {
            $webStatus.html(
                '<span class="badge bg-success me-1">🔍 WEB SEARCH</span>' +
                `<span class="text-success">${data.results_count} result(s) for: "${data.search_query}"</span>`
            ).show();
        }
    }

    // ── Agent events ────────────────────────────────────────────────────────
    function handleAgentEvent(agentKey, status, data) {
        const $el = $(`.agent-status[data-agent="${agentKey}"]`);
        if (status === 'started') {
            $el.addClass('active').removeClass('completed');
            $el.find('.agent-state').text('Processing...');
            $el.find('.agent-badge').remove();
        } else if (status === 'completed') {
            $el.removeClass('active').addClass('completed');
            const retryLabel = (data && data.retry_count > 0) ? ` (retry ${data.retry_count})` : '';
            $el.find('.agent-state').text(`Done${retryLabel} (${Math.round(data?.processing_time_ms || 0)}ms)`);
        }
    }

    // ── Ethics Agent ────────────────────────────────────────────────────────
    function handleEthicsEvent(status, data) {
        const $el = $('.agent-status[data-agent="ethics"]');
        if (status === 'started') {
            $el.addClass('active').removeClass('completed');
            $el.find('.agent-state').text('Reviewing...');
            $el.find('.ethics-badge').remove();
        } else if (status === 'completed' && data) {
            $el.removeClass('active').addClass('completed');
            const isPass = data.verdict === 'PASS';
            const badge = isPass
                ? '<span class="badge bg-success ethics-badge ms-1">✅ PASS</span>'
                : '<span class="badge bg-danger ethics-badge ms-1">❌ FAIL</span>';
            $el.find('.agent-state').text(`${data.verdict} (${Math.round(data.processing_time_ms || 0)}ms)`);
            $el.find('.agent-name').append(badge);

            // Show suggestions if fail
            if (!isPass && data.suggestions && data.suggestions.length > 0) {
                const suggHtml = data.suggestions.map(s => `<li>${s}</li>`).join('');
                $el.find('.agent-state').after(
                    `<ul class="ethics-suggestions text-warning" style="font-size:0.75rem;margin-top:4px;padding-left:16px;">${suggHtml}</ul>`
                );
            }
        }
    }

    // ── Aggregator ──────────────────────────────────────────────────────────
    function handleAggregatorEvent(status, data) {
        if (status === 'started') {
            const retryLabel = (data && data.retry_count > 0) ? ` (retry ${data.retry_count})...` : '...';
            $('#finalResponse').html(
                spinner(`Aggregator judging response${retryLabel}`, 'text-primary')
            );
            // Update retry counter
            if (data && data.retry_count > 0) {
                $('#retryCounter').text(`Retry ${data.retry_count}`).show();
            }
        } else if (status === 'completed' && data) {
            if (data.dp_metrics && window.dashboardUI && window.dashboardUI.displayDPMetrics) {
                window.dashboardUI.displayDPMetrics(data.dp_metrics);
            }
            // Show decision badge in pipeline panel
            if (data.action) {
                const actionClass = data.action === 'ACCEPT' ? 'bg-success'
                    : data.action === 'FORCE_ACCEPT' ? 'bg-warning text-dark' : 'bg-info';
                $('#aggregatorDecision')
                    .html(`<span class="badge ${actionClass}">${data.action}</span>`)
                    .show();
            }
        }
    }

    // ── Terminal logger ─────────────────────────────────────────────────────
    function addTraceToTerminal(nodeType, status, message, data) {
        const timestamp = new Date().toLocaleTimeString();
        const label = nodeType.toUpperCase().replace(/_/g, ' ');
        const statusClass = status === 'completed' ? 'success'
            : status === 'error' ? 'error' : 'agent';

        // Add retry info if present
        let extra = '';
        if (data && data.retry_count > 0) {
            extra = ` <span class="text-warning">[Retry ${data.retry_count}]</span>`;
        }

        const $log = $('<div>')
            .addClass('terminal-line ' + statusClass)
            .html(
                `<span class="timestamp">[${timestamp}]</span>` +
                `<span class="message">` +
                `<span class="node-badge ${getNodeBadgeClass(nodeType)}">${label}</span> ` +
                `${message}${extra}` +
                `</span>`
            );

        $('#traceTerminal').append($log);
        const terminal = document.getElementById('traceTerminal');
        if (terminal) terminal.scrollTop = terminal.scrollHeight;
    }

    function getNodeBadgeClass(nodeType) {
        if (nodeType === 'privacy_shield') return 'privacy';
        if (nodeType === 'domain_expert') return 'domain';
        if (nodeType === 'aggregator') return 'aggregator';
        if (nodeType === 'web_search') return 'web-search';
        if (nodeType === 'ethics_agent') return 'ethics';
        return 'agent';
    }

    function spinner(text, colorClass) {
        return `<div class="placeholder-state">` +
            `<div class="spinner-border ${colorClass}" role="status"></div>` +
            `<p class="placeholder-text mt-3">${text}</p>` +
            `</div>`;
    }

    // ── Init ────────────────────────────────────────────────────────────────
    initializeSSE();

    document.addEventListener('visibilitychange', function () {
        if (!document.hidden && (!eventSource || eventSource.readyState === EventSource.CLOSED)) {
            initializeSSE();
        }
    });
});
