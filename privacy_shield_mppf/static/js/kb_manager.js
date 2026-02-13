/**
 * Knowledge Base Manager - Document List UI
 */

$(document).ready(function () {
    const $docList = $('#documentList');

    loadDocuments();

    function loadDocuments() {
        $.get('/api/knowledge-base', function (data) {
            if (data.documents.length === 0) {
                $docList.html(`
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-folder-open" style="font-size: 3rem; opacity: 0.3;"></i>
                        <p class="mt-3">No documents uploaded yet.</p>
                        <a href="/" class="btn btn-primary">Upload Documents</a>
                    </div>
                `);
                return;
            }

            let html = '<div class="table-responsive"><table class="table table-dark table-hover">';
            html += '<thead><tr>';
            html += '<th>Filename</th>';
            html += '<th>Type</th>';
            html += '<th>Size</th>';
            html += '<th>Last Modified</th>';
            html += '<th>Actions</th>';
            html += '</tr></thead><tbody>';

            data.documents.forEach(doc => {
                const sizeKB = (doc.size_bytes / 1024).toFixed(2);
                const date = new Date(doc.modified_date * 1000).toLocaleString();

                html += '<tr>';
                html += `<td>${doc.filename}</td>`;
                html += `<td><span class="badge bg-info">${doc.extension}</span></td>`;
                html += `<td>${sizeKB} KB</td>`;
                html += `<td>${date}</td>`;
                html += `<td>
                    <button class="btn btn-sm btn-danger delete-btn" data-filename="${doc.filename}">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>`;
                html += '</tr>';
            });

            html += '</tbody></table></div>';
            $docList.html(html);

            // Attach delete handlers
            $('.delete-btn').on('click', function () {
                const filename = $(this).data('filename');
                deleteDocument(filename);
            });
        });
    }

    function deleteDocument(filename) {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }

        $.ajax({
            url: `/api/knowledge-base/${filename}`,
            method: 'DELETE',
            success: function (response) {
                alert(response.message);
                loadDocuments();
            },
            error: function (xhr) {
                alert('Delete failed: ' + (xhr.responseJSON?.detail || 'Unknown error'));
            }
        });
    }
});
