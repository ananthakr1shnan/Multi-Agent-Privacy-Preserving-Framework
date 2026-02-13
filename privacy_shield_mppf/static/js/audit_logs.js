/**
 * Audit Log Viewer - Paginated Log Table
 */

$(document).ready(function () {
    const $logTable = $('#logTable');
    const $pagination = $('#pagination');

    let currentPage = 1;
    const limit = 20;

    loadLogs(currentPage);

    function loadLogs(page) {
        $.get(`/api/audit-logs?page=${page}&limit=${limit}`, function (data) {
            if (data.logs.length === 0) {
                $logTable.html('<div class="text-center text-muted py-5">No audit logs found.</div>');
                return;
            }

            let html = '<div class="table-responsive"><table class="table table-dark table-hover table-sm">';
            html += '<thead><tr>';
            html += '<th>ID</th>';
            html += '<th>Timestamp</th>';
            html += '<th>Query</th>';
            html += '<th>Domain</th>';
            html += '<th>Redactions</th>';
            html += '<th>Time (ms)</th>';
            html += '</tr></thead><tbody>';

            data.logs.forEach(log => {
                const timestamp = new Date(log.timestamp).toLocaleString();

                html += '<tr>';
                html += `<td>${log.id}</td>`;
                html += `<td>${timestamp}</td>`;
                html += `<td title="${log.query}">${log.query.substring(0, 50)}...</td>`;
                html += `<td><span class="badge bg-primary">${log.domain}</span></td>`;
                html += `<td>${log.redaction_count}</td>`;
                html += `<td>${log.processing_time_ms?.toFixed(0) || 'N/A'}</td>`;
                html += '</tr>';
            });

            html += '</tbody></table></div>';
            $logTable.html(html);

            // Render pagination
            renderPagination(data.page, data.total_pages);
        });
    }

    function renderPagination(page, totalPages) {
        if (totalPages <= 1) {
            $pagination.html('');
            return;
        }

        let html = '<nav><ul class="pagination justify-content-center">';

        // Previous
        html += `<li class="page-item ${page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${page - 1}">Previous</a>
        </li>`;

        // Pages
        for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
            html += `<li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }

        // Next
        html += `<li class="page-item ${page === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${page + 1}">Next</a>
        </li>`;

        html += '</ul></nav>';
        $pagination.html(html);

        // Attach handlers
        $('.page-link').on('click', function (e) {
            e.preventDefault();
            const newPage = parseInt($(this).data('page'));
            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                loadLogs(currentPage);
            }
        });
    }
});
