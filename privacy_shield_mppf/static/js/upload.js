/**
 * Upload Manager - File Upload UI
 */

$(document).ready(function () {
    const $uploadZone = $('#uploadZone');
    const $fileInput = $('#fileInput');
    const $uploadProgress = $('#uploadProgress');
    const $uploadStatus = $('#uploadStatus');
    const $kbStats = $('#kbStats');

    // Load KB stats on page load
    loadKBStats();

    // Drag and drop handlers
    $uploadZone.on('dragover', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('drag-over');
    });

    $uploadZone.on('dragleave', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');
    });

    $uploadZone.on('drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');

        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // Click to upload
    $uploadZone.on('click', function () {
        $fileInput.click();
    });

    $fileInput.on('change', function () {
        if (this.files.length > 0) {
            handleFileUpload(this.files[0]);
        }
    });

    function handleFileUpload(file) {
        // Validate file type
        const validTypes = ['application/pdf', 'text/plain'];
        if (!validTypes.includes(file.type)) {
            showStatus('error', 'Invalid file type. Only PDF and TXT files are allowed.');
            return;
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showStatus('error', 'File too large. Maximum size is 10MB.');
            return;
        }

        // Show progress
        $uploadProgress.show();
        $uploadProgress.find('.progress-bar').css('width', '0%');

        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Upload
        $.ajax({
            url: '/api/upload',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function () {
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        $uploadProgress.find('.progress-bar').css('width', percentComplete + '%');
                    }
                });
                return xhr;
            },
            success: function (response) {
                showStatus('success',
                    `✅ ${response.filename} uploaded successfully! ` +
                    `${response.total_chunks} chunks indexed.`
                );
                loadKBStats();
                setTimeout(() => {
                    $uploadProgress.hide();
                }, 1000);
            },
            error: function (xhr) {
                const error = xhr.responseJSON?.detail || 'Upload failed';
                showStatus('error', '❌ ' + error);
                $uploadProgress.hide();
            }
        });
    }

    function showStatus(type, message) {
        $uploadStatus.removeClass('alert-success alert-danger');
        $uploadStatus.addClass(type === 'success' ? 'alert-success' : 'alert-danger');
        $uploadStatus.text(message);
        $uploadStatus.show();

        setTimeout(() => {
            $uploadStatus.fadeOut();
        }, 5000);
    }

    function loadKBStats() {
        $.get('/api/knowledge-base/stats', function (data) {
            $kbStats.html(`
                <div class="stat-item">
                    <span class="stat-label">Total Chunks:</span>
                    <span class="stat-value">${data.total_chunks}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value ${data.status === 'healthy' ? 'text-success' : 'text-danger'}">
                        ${data.status}
                    </span>
                </div>
            `);
        });
    }
});
