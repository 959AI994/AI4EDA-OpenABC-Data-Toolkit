// AI4EDA Toolkit - Web Interface JavaScript (Enhanced Version)

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tab switching
    initTabSwitching();

    // Initialize conversion form
    initConversionForm();

    // Initialize metrics form
    initMetricsForm();

    // Initialize analysis form
    initAnalysisForm();

    // Initialize help modal
    initHelpModal();

    // Initialize reset buttons
    initResetButtons();
});

// Tab Switching
function initTabSwitching() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;

            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update active tab content
            tabContents.forEach(content => {
                if (content.id === `tab-${tabName}`) {
                    content.classList.add('active');
                    content.style.display = 'block';
                } else {
                    content.classList.remove('active');
                    content.style.display = 'none';
                }
            });
        });
    });
}

// Format Conversion Form
function initConversionForm() {
    const form = document.getElementById('conversionForm');
    const batchMode = document.getElementById('batchMode');
    const singleFileGroup = document.getElementById('singleFileGroup');
    const batchFileGroup = document.getElementById('batchFileGroup');
    const fileInput = document.getElementById('fileInput');
    const batchFileInput = document.getElementById('batchFileInput');
    const submitBtnText = document.getElementById('submitBtnText');
    const conversionType = document.getElementById('conversionType');
    const topModuleGroup = document.getElementById('topModuleGroup');

    // Batch mode toggle
    batchMode.addEventListener('change', function() {
        if (this.checked) {
            singleFileGroup.style.display = 'none';
            batchFileGroup.style.display = 'block';
            submitBtnText.textContent = 'Convert Files';
        } else {
            singleFileGroup.style.display = 'block';
            batchFileGroup.style.display = 'none';
            submitBtnText.textContent = 'Convert File';
        }
    });

    // File input handlers
    setupFileInput(fileInput, document.getElementById('fileLabel'), document.getElementById('fileInfo'));
    setupBatchFileInput(batchFileInput, document.getElementById('batchFileList'));

    // Conversion type change
    conversionType.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const inputType = selectedOption.dataset.input;

        if (inputType === 'verilog') {
            topModuleGroup.style.display = 'block';
        } else {
            topModuleGroup.style.display = 'none';
        }

        // Reset files
        fileInput.value = '';
        batchFileInput.value = '';
        document.getElementById('fileLabel').textContent = 'Choose a file or drag & drop here';
        document.getElementById('fileInfo').style.display = 'none';
        document.getElementById('batchFileList').innerHTML = '';
        document.getElementById('resultSection').style.display = 'none';
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!conversionType.value) {
            showError('conversion', 'Please select a conversion type');
            return;
        }

        const isBatchMode = batchMode.checked;

        if (isBatchMode) {
            await handleBatchConversion();
        } else {
            await handleSingleConversion();
        }
    });
}

async function handleSingleConversion() {
    const form = document.getElementById('conversionForm');
    const formData = new FormData(form);

    if (!formData.get('file') || formData.get('file').size === 0) {
        showError('conversion', 'Please select a file to convert');
        return;
    }

    showProgress('conversion', 'Converting your file...');

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showSuccessResult('conversion', result);
        } else {
            showError('conversion', result.error || 'Conversion failed');
        }
    } catch (error) {
        showError('conversion', 'Network error: ' + error.message);
    }
}

async function handleBatchConversion() {
    const formData = new FormData();
    const conversionType = document.getElementById('conversionType').value;
    const batchFileInput = document.getElementById('batchFileInput');
    const topModule = document.getElementById('topModule').value;

    if (!batchFileInput.files || batchFileInput.files.length === 0) {
        showError('conversion', 'Please select files to convert');
        return;
    }

    formData.append('conversion_type', conversionType);
    if (topModule) {
        formData.append('top_module', topModule);
    }

    for (let file of batchFileInput.files) {
        formData.append('files', file);
    }

    showProgress('conversion', `Converting ${batchFileInput.files.length} files...`);

    try {
        const response = await fetch('/api/convert/batch', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showBatchResults('conversion', result);
        } else {
            showError('conversion', result.error || 'Batch conversion failed');
        }
    } catch (error) {
        showError('conversion', 'Network error: ' + error.message);
    }
}

// Metrics Form
function initMetricsForm() {
    const form = document.getElementById('metricsForm');
    const batchMode = document.getElementById('metricsBatchMode');
    const singleFileGroup = document.getElementById('metricsSingleFileGroup');
    const batchFileGroup = document.getElementById('metricsBatchFileGroup');
    const fileInput = document.getElementById('metricsFileInput');
    const batchFileInput = document.getElementById('metricsBatchFileInput');
    const submitBtnText = document.getElementById('metricsSubmitBtnText');
    const libFile = document.getElementById('libFile');
    const customLibGroup = document.getElementById('customLibGroup');

    // Batch mode toggle
    batchMode.addEventListener('change', function() {
        if (this.checked) {
            singleFileGroup.style.display = 'none';
            batchFileGroup.style.display = 'block';
            submitBtnText.textContent = 'Calculate Metrics (Batch)';
        } else {
            singleFileGroup.style.display = 'block';
            batchFileGroup.style.display = 'none';
            submitBtnText.textContent = 'Calculate Metrics';
        }
    });

    // Liberty library selection
    libFile.addEventListener('change', function() {
        if (this.value === 'custom') {
            customLibGroup.style.display = 'block';
        } else {
            customLibGroup.style.display = 'none';
        }
    });

    // File input handlers
    setupFileInput(fileInput, document.getElementById('metricsFileLabel'), document.getElementById('metricsFileInfo'));
    setupBatchFileInputMetrics(batchFileInput, document.getElementById('metricsBatchFileList'));

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const isBatchMode = batchMode.checked;

        if (isBatchMode) {
            await handleBatchMetrics();
        } else {
            await handleSingleMetrics();
        }
    });
}

async function handleSingleMetrics() {
    const form = document.getElementById('metricsForm');
    const formData = new FormData(form);

    if (!formData.get('file') || formData.get('file').size === 0) {
        showError('metrics', 'Please select a file');
        return;
    }

    showProgress('metrics', 'Calculating metrics...');

    try {
        const response = await fetch('/api/metrics', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showMetricsResult(result);
        } else {
            showError('metrics', result.error || 'Metrics calculation failed');
        }
    } catch (error) {
        showError('metrics', 'Network error: ' + error.message);
    }
}

async function handleBatchMetrics() {
    const formData = new FormData();
    const batchFileInput = document.getElementById('metricsBatchFileInput');
    const libFile = document.getElementById('libFile').value;
    const optScript = document.getElementById('optScript').value;
    const customLibInput = document.getElementById('customLibInput');

    if (!batchFileInput.files || batchFileInput.files.length === 0) {
        showError('metrics', 'Please select files');
        return;
    }

    formData.append('lib_file', libFile);
    if (optScript) {
        formData.append('opt_script', optScript);
    }
    if (libFile === 'custom' && customLibInput.files.length > 0) {
        formData.append('custom_lib', customLibInput.files[0]);
    }

    for (let file of batchFileInput.files) {
        formData.append('files', file);
    }

    showProgress('metrics', `Calculating metrics for ${batchFileInput.files.length} files...`);

    try {
        const response = await fetch('/api/metrics/batch', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showBatchMetricsResults(result);
        } else {
            showError('metrics', result.error || 'Batch metrics calculation failed');
        }
    } catch (error) {
        showError('metrics', 'Network error: ' + error.message);
    }
}

// File Input Helpers
function setupFileInput(input, label, info) {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            label.textContent = file.name;
            info.innerHTML = `
                <i class="fas fa-file"></i>
                <strong>${file.name}</strong> (${formatFileSize(file.size)})
            `;
            info.style.display = 'block';
        }
    });

    // Drag and drop
    const uploadDisplay = input.parentElement.querySelector('.file-upload-display');
    if (uploadDisplay) {
        uploadDisplay.addEventListener('click', () => input.click());
        setupDragDrop(uploadDisplay, input);
    }
}

function setupBatchFileInput(input, listElement) {
    let filesArray = [];

    input.addEventListener('change', function(e) {
        // Filter out non-file items (directories, etc.)
        const validFiles = Array.from(e.target.files).filter(file => {
            // Check if it's actually a file (has size or type)
            return file.size > 0 || file.type !== '';
        });

        if (validFiles.length === 0) {
            showError('conversion', 'No valid files selected. Folders are not supported.');
            return;
        }

        filesArray = validFiles;
        updateBatchFileList(filesArray, listElement, input);
    });

    const uploadDisplay = input.parentElement.querySelector('.file-upload-display');
    if (uploadDisplay) {
        uploadDisplay.addEventListener('click', () => input.click());
        setupDragDropBatch(uploadDisplay, input, listElement);
    }
}

function updateBatchFileList(filesArray, listElement, inputElement) {
    listElement.innerHTML = '';

    if (!filesArray || filesArray.length === 0) {
        return;
    }

    filesArray.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'batch-file-item';
        item.innerHTML = `
            <span class="file-name"><i class="fas fa-file"></i> ${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
            <button type="button" class="remove-btn" data-index="${index}">
                <i class="fas fa-times"></i> Remove
            </button>
        `;

        // Add click handler for remove button
        const removeBtn = item.querySelector('.remove-btn');
        removeBtn.addEventListener('click', function() {
            // Remove file from array
            filesArray.splice(index, 1);

            // Update the file input with the new file list
            const dt = new DataTransfer();
            filesArray.forEach(f => dt.items.add(f));
            inputElement.files = dt.files;

            // Refresh the display
            updateBatchFileList(filesArray, listElement, inputElement);
        });

        listElement.appendChild(item);
    });
}

function setupDragDrop(element, input) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary-color)';
        element.style.background = '#eff6ff';
    });

    element.addEventListener('dragleave', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// Specialized drag and drop for batch file inputs
function setupDragDropBatch(element, input, listElement) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary-color)';
        element.style.background = '#eff6ff';
    });

    element.addEventListener('dragleave', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Filter out folders and invalid files
            const validFiles = Array.from(files).filter(file => {
                return file.size > 0 || file.type !== '';
            });

            if (validFiles.length === 0) {
                showError('conversion', 'No valid files selected. Folders are not supported.');
                return;
            }

            // Create a new DataTransfer object with only valid files
            const dt = new DataTransfer();
            validFiles.forEach(f => dt.items.add(f));
            input.files = dt.files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// Batch file input handler for metrics
function setupBatchFileInputMetrics(input, listElement) {
    let filesArray = [];

    input.addEventListener('change', function(e) {
        // Filter out non-file items (directories, etc.)
        const validFiles = Array.from(e.target.files).filter(file => {
            // Check if it's actually a file (has size or type)
            return file.size > 0 || file.type !== '';
        });

        if (validFiles.length === 0) {
            showError('metrics', 'No valid files selected. Folders are not supported.');
            return;
        }

        filesArray = validFiles;
        updateBatchFileList(filesArray, listElement, input);
    });

    const uploadDisplay = input.parentElement.querySelector('.file-upload-display');
    if (uploadDisplay) {
        uploadDisplay.addEventListener('click', () => input.click());
        setupDragDropBatchMetrics(uploadDisplay, input, listElement);
    }
}

// Specialized drag and drop for batch metrics file inputs
function setupDragDropBatchMetrics(element, input, listElement) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary-color)';
        element.style.background = '#eff6ff';
    });

    element.addEventListener('dragleave', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--border-color)';
        element.style.background = 'var(--bg-secondary)';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Filter out folders and invalid files
            const validFiles = Array.from(files).filter(file => {
                return file.size > 0 || file.type !== '';
            });

            if (validFiles.length === 0) {
                showError('metrics', 'No valid files selected. Folders are not supported.');
                return;
            }

            // Create a new DataTransfer object with only valid files
            const dt = new DataTransfer();
            validFiles.forEach(f => dt.items.add(f));
            input.files = dt.files;
            input.dispatchEvent(new Event('change'));
        }
    });
}


// UI Helper Functions
function showProgress(section, message) {
    const submitBtn = section === 'conversion' ?
        document.getElementById('submitBtn') :
        document.getElementById('metricsSubmitBtn');
    const progressSection = section === 'conversion' ?
        document.getElementById('progressSection') :
        document.getElementById('metricsProgressSection');
    const progressText = section === 'conversion' ?
        document.getElementById('progressText') :
        document.getElementById('metricsProgressText');
    const resultSection = section === 'conversion' ?
        document.getElementById('resultSection') :
        document.getElementById('metricsResultSection');

    submitBtn.disabled = true;
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    progressText.textContent = message;
}

function showSuccessResult(section, result) {
    const submitBtn = document.getElementById('submitBtn');
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    resultSection.innerHTML = `
        <div class="result-success">
            <i class="fas fa-check-circle"></i>
            <h3>Conversion Successful!</h3>
            <p>Successfully converted to <strong>${result.filename}</strong></p>
            <a href="${result.download_url}" class="btn btn-success" download>
                <i class="fas fa-download"></i> Download File
            </a>
        </div>
    `;
}

function showBatchResults(section, result) {
    const submitBtn = document.getElementById('submitBtn');
    const progressSection = document.getElementById('progressSection');
    const resultSection = document.getElementById('resultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    let html = `
        <div class="result-success">
            <i class="fas fa-check-circle"></i>
            <h3>Batch Conversion Complete</h3>
            <p><strong>${result.successful}/${result.total}</strong> files converted successfully</p>
        </div>
        <div style="margin-top: 1.5rem;">
    `;

    result.results.forEach(r => {
        const statusClass = r.success ? 'success' : 'error';
        const icon = r.success ? 'fa-check-circle' : 'fa-exclamation-circle';

        html += `
            <div class="result-card ${statusClass}">
                <div class="result-card-header">
                    <span class="result-card-file">${r.filename}</span>
                    <span class="result-card-status ${statusClass}">
                        <i class="fas ${icon}"></i>
                        ${r.success ? 'Success' : 'Failed'}
                    </span>
                </div>
                ${r.success ? `
                    <div class="result-card-download">
                        <a href="${r.download_url}" class="btn btn-success btn-sm" download>
                            <i class="fas fa-download"></i> Download ${r.output_filename}
                        </a>
                    </div>
                ` : `
                    <div class="result-card-message">${r.error}</div>
                `}
            </div>
        `;
    });

    html += '</div>';
    resultSection.innerHTML = html;
}

function showMetricsResult(result) {
    const submitBtn = document.getElementById('metricsSubmitBtn');
    const progressSection = document.getElementById('metricsProgressSection');
    const resultSection = document.getElementById('metricsResultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    resultSection.innerHTML = `
        <div class="result-success">
            <i class="fas fa-check-circle"></i>
            <h3>Metrics Calculated Successfully</h3>
            <p><strong>${result.filename}</strong></p>
            <table class="metrics-table">
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Area</td>
                    <td class="metric-value">${result.area.toFixed(2)}</td>
                </tr>
                <tr>
                    <td>Delay</td>
                    <td class="metric-value">${result.delay.toFixed(2)}</td>
                </tr>
            </table>
        </div>
    `;
}

function showBatchMetricsResults(result) {
    const submitBtn = document.getElementById('metricsSubmitBtn');
    const progressSection = document.getElementById('metricsProgressSection');
    const resultSection = document.getElementById('metricsResultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    let html = `
        <div class="result-success">
            <i class="fas fa-check-circle"></i>
            <h3>Batch Metrics Calculation Complete</h3>
            <p><strong>${result.successful}/${result.total}</strong> files processed successfully</p>
        </div>
        <table class="metrics-table" style="margin-top: 1.5rem;">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Area</th>
                    <th>Delay</th>
                </tr>
            </thead>
            <tbody>
    `;

    result.results.forEach(r => {
        if (r.success) {
            html += `
                <tr>
                    <td>${r.filename}</td>
                    <td style="color: var(--success-color);">
                        <i class="fas fa-check-circle"></i> Success
                    </td>
                    <td class="metric-value">${r.area.toFixed(2)}</td>
                    <td class="metric-value">${r.delay.toFixed(2)}</td>
                </tr>
            `;
        } else {
            html += `
                <tr>
                    <td>${r.filename}</td>
                    <td style="color: var(--error-color);">
                        <i class="fas fa-exclamation-circle"></i> Failed
                    </td>
                    <td colspan="2">${r.error}</td>
                </tr>
            `;
        }
    });

    html += `
            </tbody>
        </table>
    `;

    resultSection.innerHTML = html;
}

function showError(section, message) {
    const submitBtn = section === 'conversion' ?
        document.getElementById('submitBtn') :
        document.getElementById('metricsSubmitBtn');
    const progressSection = section === 'conversion' ?
        document.getElementById('progressSection') :
        document.getElementById('metricsProgressSection');
    const resultSection = section === 'conversion' ?
        document.getElementById('resultSection') :
        document.getElementById('metricsResultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    resultSection.innerHTML = `
        <div class="result-error">
            <i class="fas fa-exclamation-circle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Analysis Form
function initAnalysisForm() {
    const form = document.getElementById('analysisForm');
    const fileInput = document.getElementById('analysisFileInput');
    const fileLabel = document.getElementById('analysisFileLabel');
    const fileInfo = document.getElementById('analysisFileInfo');

    // File input handler
    setupFileInput(fileInput, fileLabel, fileInfo);

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleAnalysis();
    });
}

async function handleAnalysis() {
    const form = document.getElementById('analysisForm');
    const formData = new FormData(form);
    const fileInput = document.getElementById('analysisFileInput');
    const promptInput = document.getElementById('analysisPrompt');

    if (!fileInput.files || fileInput.files.length === 0) {
        showAnalysisError('请选择一个Verilog文件');
        return;
    }

    // Check file size (100KB limit)
    const file = fileInput.files[0];
    if (file.size > 100 * 1024) {
        showAnalysisError('文件太大。最大文件大小为100KB');
        return;
    }

    if (!promptInput.value.trim()) {
        showAnalysisError('请输入问题或请求');
        return;
    }

    showAnalysisProgress('AI正在分析您的代码，请稍候...');

    try {
        // Create a timeout promise
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('请求超时，请稍后重试')), 180000); // 3 minutes
        });

        // Create the fetch promise
        const fetchPromise = fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        // Race between fetch and timeout
        const response = await Promise.race([fetchPromise, timeoutPromise]);

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = '分析失败';
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.error || errorMessage;
            } catch (e) {
                errorMessage = `服务器错误: ${response.status} ${response.statusText}`;
            }
            showAnalysisError(errorMessage);
            return;
        }

        let result;
        try {
            result = await response.json();
        } catch (parseError) {
            showAnalysisError('解析服务器响应时出错: ' + parseError.message);
            return;
        }

        if (result.success) {
            showAnalysisResult(result);
        } else {
            showAnalysisError(result.error || '分析失败');
        }
    } catch (error) {
        if (error.name === 'AbortError' || error.message.includes('超时')) {
            showAnalysisError('请求超时。AI分析可能需要较长时间，请稍后重试。');
        } else if (error.message.includes('Failed to fetch')) {
            showAnalysisError('网络错误：无法连接到服务器。请检查网络连接。');
        } else {
            showAnalysisError('发生错误: ' + error.message);
        }
        console.error('Analysis error:', error);
    }
}

function showAnalysisProgress(message) {
    const submitBtn = document.getElementById('analysisSubmitBtn');
    const progressSection = document.getElementById('analysisProgressSection');
    const progressText = document.getElementById('analysisProgressText');
    const resultSection = document.getElementById('analysisResultSection');

    submitBtn.disabled = true;
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    progressText.textContent = message;
}

function showAnalysisResult(result) {
    const submitBtn = document.getElementById('analysisSubmitBtn');
    const progressSection = document.getElementById('analysisProgressSection');
    const resultSection = document.getElementById('analysisResultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    // Show loading state while formatting
    resultSection.innerHTML = `
        <div class="result-success">
            <i class="fas fa-check-circle"></i>
            <h3>Analysis Complete</h3>
            <p>正在格式化结果...</p>
        </div>
    `;

    // Use setTimeout to allow UI to update before heavy processing
    setTimeout(() => {
        try {
            // Format the analysis content with markdown-like rendering
            const formattedAnalysis = formatAnalysisContent(result.analysis || '');
            const filename = result.filename || 'Unknown';
            const prompt = result.prompt || '';
            const promptPreview = prompt.length > 100 ? prompt.substring(0, 100) + '...' : prompt;

            resultSection.innerHTML = `
                <div class="result-success">
                    <i class="fas fa-check-circle"></i>
                    <h3>Analysis Complete</h3>
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: center;">
                        <button class="btn btn-success btn-sm" onclick="exportAnalysisResult('pdf')">
                            <i class="fas fa-file-pdf"></i> Export as PDF
                        </button>
                        <button class="btn btn-success btn-sm" onclick="exportAnalysisResult('word')">
                            <i class="fas fa-file-word"></i> Export as Word
                        </button>
                    </div>
                </div>
                <div class="analysis-result">
                    <h4><i class="fas fa-brain"></i> AI Analysis</h4>
                    <div class="analysis-content">${formattedAnalysis}</div>
                    <div class="analysis-metadata">
                        <div>
                            <i class="fas fa-file-code"></i>
                            <span>${escapeHtml(filename)}</span>
                        </div>
                        <div>
                            <i class="fas fa-question-circle"></i>
                            <span>Prompt: ${escapeHtml(promptPreview)}</span>
                        </div>
                    </div>
                </div>
            `;

            // Scroll to result section smoothly
            resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } catch (error) {
            console.error('Error displaying analysis result:', error);
            resultSection.innerHTML = `
                <div class="result-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>Error Displaying Result</h3>
                    <p>显示结果时出错: ${error.message}</p>
                    <details style="margin-top: 1rem;">
                        <summary>查看原始结果</summary>
                        <pre style="max-height: 400px; overflow: auto; margin-top: 0.5rem;">${escapeHtml((result.analysis || '').substring(0, 2000))}</pre>
                    </details>
                </div>
            `;
        }
    }, 50); // Small delay to allow UI update
}

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatAnalysisContent(content) {
    try {
        // Limit content size to prevent performance issues
        if (!content || typeof content !== 'string') {
            return '<p>No content to display</p>';
        }

        // Truncate very long content to prevent browser freeze
        const MAX_CONTENT_LENGTH = 50000; // 50KB limit
        if (content.length > MAX_CONTENT_LENGTH) {
            content = content.substring(0, MAX_CONTENT_LENGTH) + '\n\n... (内容过长，已截断)';
        }

        let formatted = content;

        // Step 1: Protect code blocks first (before HTML escaping)
        const codeBlockPlaceholders = [];
        let codeBlockIndex = 0;

        // Extract code blocks with improved regex
        formatted = formatted.replace(/```(\w*)?\n?([\s\S]*?)```/g, function(match, lang, code) {
            const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
            codeBlockPlaceholders[codeBlockIndex] = {
                lang: lang || '',
                code: code.trim()
            };
            codeBlockIndex++;
            return placeholder;
        });

        // Step 2: Protect inline code
        const inlineCodePlaceholders = [];
        let inlineCodeIndex = 0;
        formatted = formatted.replace(/`([^`\n]+)`/g, function(match, code) {
            const placeholder = `__INLINE_CODE_${inlineCodeIndex}__`;
            inlineCodePlaceholders[inlineCodeIndex] = code;
            inlineCodeIndex++;
            return placeholder;
        });

        // Step 2.5: Protect bold markers BEFORE HTML escaping
        const boldPlaceholders = [];
        let boldIndex = 0;
        formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, function(match, text) {
            const placeholder = `__BOLD_${boldIndex}__`;
            // Store the text as-is (don't trim, preserve original spacing)
            boldPlaceholders[boldIndex] = text;
            boldIndex++;
            return placeholder;
        });

        // Step 3: Escape HTML (but not in protected code blocks or bold markers)
        formatted = formatted.replace(/&/g, '&amp;')
                             .replace(/</g, '&lt;')
                             .replace(/>/g, '&gt;');

        // Step 4: Restore inline code (but escape its content)
        inlineCodePlaceholders.forEach((code, index) => {
            const escapedCode = code
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            formatted = formatted.replace(
                `__INLINE_CODE_${index}__`,
                `<code>${escapedCode}</code>`
            );
        });

        // Step 4.5: Restore bold markers and convert to <strong>
        boldPlaceholders.forEach((text, index) => {
            // Text was protected, so it hasn't been escaped yet - escape it now
            const escapedText = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            formatted = formatted.replace(
                `__BOLD_${index}__`,
                `<strong>${escapedText}</strong>`
            );
        });

        // Step 5: Convert headers AFTER HTML escaping (#### contains no < or > so not affected)
        // Process all header levels (####, ###, ##, #) - longest first, allow optional spaces after #
        formatted = formatted.replace(/^####\s+(.+)$/gm, '<h5>$1</h5>');
        formatted = formatted.replace(/^###\s+(.+)$/gm, '<h4>$1</h4>');
        formatted = formatted.replace(/^##\s+(.+)$/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^#\s+(.+)$/gm, '<h2>$1</h2>');

        // Step 6: Restore header tags (they were escaped, need to restore them properly)
        formatted = formatted.replace(/&lt;h([2-6])&gt;(.+?)&lt;\/h\1&gt;/g, '<h$1>$2</h$1>');

        // Step 7: Convert bold again (safety net - bold should already be converted in Step 4.5)
        // But do a final pass to catch any that might have been missed during list processing
        formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');

        // Step 8: Process lists (simplified approach)
        const lines = formatted.split('\n');
        const processedLines = [];
        let inOrderedList = false;
        let inUnorderedList = false;
        let listItems = [];

        function closeList() {
            if (inOrderedList && listItems.length > 0) {
                processedLines.push('<ol>');
                processedLines.push(...listItems);
                processedLines.push('</ol>');
                inOrderedList = false;
            } else if (inUnorderedList && listItems.length > 0) {
                processedLines.push('<ul>');
                processedLines.push(...listItems);
                processedLines.push('</ul>');
                inUnorderedList = false;
            }
            listItems = [];
        }

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            // Check for ordered list
            const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/);
            if (orderedMatch) {
                if (inUnorderedList) {
                    closeList();
                }
                inOrderedList = true;
                listItems.push(`<li>${orderedMatch[2]}</li>`);
                continue;
            }

            // Check for unordered list
            const unorderedMatch = line.match(/^[\-\*]\s+(.+)$/);
            if (unorderedMatch) {
                if (inOrderedList) {
                    closeList();
                }
                inUnorderedList = true;
                listItems.push(`<li>${unorderedMatch[1]}</li>`);
                continue;
            }

            // Not a list item - close any open list
            if (inOrderedList || inUnorderedList) {
                closeList();
            }

            // Regular line
            processedLines.push(line);
        }

        // Close any remaining list
        closeList();

        formatted = processedLines.join('\n');

        // Step 8: Handle markdown tables, horizontal rules
        // First, handle horizontal rules (---) - must be before other processing
        formatted = formatted.replace(/^---+$/gm, '<hr>');

        // Convert markdown tables to plain text format (don't use HTML tables)
        // Tables will be converted to simple text with colons or converted to lists
        const tableLines = formatted.split('\n');
        const tableProcessedLines = [];
        let inTable = false;
        let tableRows = [];
        let tableHeaders = [];
        let nextIsSeparator = false;

        for (let i = 0; i < tableLines.length; i++) {
            const line = tableLines[i];
            const trimmedLine = line.trim();

            // Check if this is a table row (contains |)
            if (trimmedLine.includes('|') && trimmedLine.split('|').length >= 3) {
                // Check if this is a separator row (contains --- or ===)
                if (trimmedLine.match(/^\|[\s:\-|]+\|$/)) {
                    // This is a separator - mark that next row is data
                    nextIsSeparator = true;
                    continue;
                }

                inTable = true;
                const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
                if (cells.length > 0) {
                    if (tableHeaders.length === 0 && !nextIsSeparator) {
                        // First row is header
                        tableHeaders = cells;
                    } else {
                        // Regular row - convert to text format: "Header: Value" or as list items
                        if (tableHeaders.length > 0 && cells.length === tableHeaders.length) {
                            // Match headers with cells - format as "Header: Value"
                            const rowText = cells.map((cell, idx) => {
                                if (idx < tableHeaders.length && tableHeaders[idx] && cell) {
                                    return `<strong>${tableHeaders[idx]}:</strong> ${cell}`;
                                }
                                return cell;
                            }).filter(text => text).join(' • ');
                            tableRows.push(`<p style="margin: 0.2rem 0;">${rowText}</p>`);
                        } else if (cells.length > 0) {
                            // Just list the cells with bullets
                            const rowText = cells.filter(c => c).map(cell => `• ${cell}`).join(' ');
                            tableRows.push(`<p style="margin: 0.2rem 0;">${rowText}</p>`);
                        }
                    }
                }
                nextIsSeparator = false;
                continue;
            } else {
                // Not a table row - close table if we were in one
                if (inTable) {
                    // Output table content as plain text paragraphs
                    if (tableRows.length > 0) {
                        tableProcessedLines.push(...tableRows);
                    }
                    tableRows = [];
                    tableHeaders = [];
                    inTable = false;
                    nextIsSeparator = false;
                }
            }

            // Regular line
            tableProcessedLines.push(line);
        }

        // Close any remaining table
        if (inTable && tableRows.length > 0) {
            tableProcessedLines.push(...tableRows);
        }

        formatted = tableProcessedLines.join('\n');

        // Step 9: Restore code blocks (moved after table processing)
        codeBlockPlaceholders.forEach((block, index) => {
            const codeHtml = block.code
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            formatted = formatted.replace(
                `__CODE_BLOCK_${index}__`,
                `<pre><code>${codeHtml}</code></pre>`
            );
        });

        // Step 10: Convert remaining text to paragraphs with better spacing control
        const finalBlocks = [];
        let currentParagraph = [];
        const htmlTagRegex = /^<(h[1-6]|ul|ol|\/ul|\/ol|pre|\/pre|li|p|\/p|hr)/i;
        let previousWasEmpty = false;

        formatted.split('\n').forEach((line) => {
            const trimmedLine = line.trim();
            const isHtmlTag = htmlTagRegex.test(trimmedLine);
            const isEmpty = trimmedLine === '';

            if (isHtmlTag) {
                // Close current paragraph before HTML tag
                if (currentParagraph.length > 0) {
                    const paraText = currentParagraph.join(' ').trim();
                    if (paraText) {
                        finalBlocks.push(`<p>${paraText}</p>`);
                    }
                    currentParagraph = [];
                }
                // Add HTML tag
                finalBlocks.push(line);
                previousWasEmpty = false;
            } else if (!isEmpty) {
                // Non-empty text line - add to current paragraph
                // Always join lines with space (markdown paragraphs are separated by empty lines)
                currentParagraph.push(trimmedLine);
                previousWasEmpty = false;
            } else {
                // Empty line - close paragraph if there is one
                if (currentParagraph.length > 0) {
                    const paraText = currentParagraph.join(' ').trim();
                    if (paraText) {
                        finalBlocks.push(`<p>${paraText}</p>`);
                    }
                    currentParagraph = [];
                }
                // Don't add multiple consecutive empty lines
                if (!previousWasEmpty) {
                    previousWasEmpty = true;
                }
            }
        });

        // Close any remaining paragraph
        if (currentParagraph.length > 0) {
            const paraText = currentParagraph.join(' ').trim();
            if (paraText) {
                finalBlocks.push(`<p>${paraText}</p>`);
            }
        }

        formatted = finalBlocks.join('\n');

        // Step 11: Convert bold again after paragraph processing (in case some were missed)
        // This ensures all **text** inside paragraphs are converted
        formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');

        // Remove all remaining ** markers (simple and direct approach)
        formatted = formatted.replace(/\*\*/g, '');

        // Step 12: Clean up spacing issues more aggressively
        formatted = formatted.replace(/<p>\s*<\/p>/g, '');  // Remove empty paragraphs
        formatted = formatted.replace(/(<\/ol>|<\/ul>)\s*<br>/g, '$1');  // Remove <br> after lists
        formatted = formatted.replace(/<br>\s*(<ol>|<ul>)/g, '$1');  // Remove <br> before lists
        formatted = formatted.replace(/(<\/h[2-6]>)\s*\n\s*(<p>)/g, '$1\n$2');  // Minimal spacing between headers and paragraphs
        formatted = formatted.replace(/(<\/p>)\s*\n\s*<p>\s*<\/p>\s*\n\s*(<p>)/g, '$1\n$2');  // Remove empty paragraphs between real paragraphs
        formatted = formatted.replace(/(<\/h[2-6]>)\s*\n\s*<p>\s*<\/p>\s*\n\s*(<h[2-6]>)/g, '$1\n$2');  // Remove empty paragraphs between headers
        formatted = formatted.replace(/(<\/h[2-6]>)\s*\n\s*(<h[2-6]>)/g, '$1\n$2');  // Minimal spacing between headers
        formatted = formatted.replace(/(<\/h[2-6]>)\s*\n\s*<p>\s*<\/p>/g, '$1');  // Remove empty paragraphs after headers
        formatted = formatted.replace(/<p>\s*<\/p>\s*\n\s*(<h[2-6]>)/g, '$1');  // Remove empty paragraphs before headers
        formatted = formatted.replace(/(<\/table>)\s*\n\s*<p>\s*<\/p>\s*\n\s*(<p>)/g, '$1\n$2');  // Remove empty paragraphs after tables
        formatted = formatted.replace(/(<hr>)\s*\n\s*<p>\s*<\/p>/g, '<hr>');  // Remove empty paragraphs after hr
        formatted = formatted.replace(/\n{3,}/g, '\n');  // Remove excessive newlines (max 1)

        // Step 13: Final pass - convert any remaining **text** patterns and clean up orphaned **
        // Try to convert any remaining **text** patterns (shouldn't happen, but safety net)
        formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');

        // Remove ALL remaining ** markers (simple approach - just remove them all)
        // This ensures no ** characters are displayed in the final output
        formatted = formatted.replace(/\*\*/g, '');

        return formatted;
    } catch (error) {
        console.error('Error formatting analysis content:', error);
        // Return a safe fallback
        return `<div class="error-message">
            <p>格式化内容时出错。显示原始内容：</p>
            <pre>${content.substring(0, 1000)}${content.length > 1000 ? '...' : ''}</pre>
        </div>`;
    }
}

function showAnalysisError(message) {
    const submitBtn = document.getElementById('analysisSubmitBtn');
    const progressSection = document.getElementById('analysisProgressSection');
    const resultSection = document.getElementById('analysisResultSection');

    submitBtn.disabled = false;
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';

    resultSection.innerHTML = `
        <div class="result-error">
            <i class="fas fa-exclamation-circle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

// Help Modal
function initHelpModal() {
    const helpBtn = document.getElementById('helpBtn');
    const modal = document.getElementById('helpModal');
    const closeBtn = document.getElementById('closeHelpModal');

    // Open modal
    helpBtn.addEventListener('click', function() {
        modal.classList.add('active');
    });

    // Close modal when clicking close button
    closeBtn.addEventListener('click', function() {
        modal.classList.remove('active');
    });

    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}

// Reset Button Functions
function initResetButtons() {
    // Conversion Reset
    const resetConversionBtn = document.getElementById('resetConversionBtn');
    if (resetConversionBtn) {
        resetConversionBtn.addEventListener('click', function() {
            resetConversionForm();
        });
    }

    // Metrics Reset
    const resetMetricsBtn = document.getElementById('resetMetricsBtn');
    if (resetMetricsBtn) {
        resetMetricsBtn.addEventListener('click', function() {
            resetMetricsForm();
        });
    }

    // Analysis Reset
    const resetAnalysisBtn = document.getElementById('resetAnalysisBtn');
    if (resetAnalysisBtn) {
        resetAnalysisBtn.addEventListener('click', function() {
            resetAnalysisForm();
        });
    }
}

function resetConversionForm() {
    // Reset form
    const form = document.getElementById('conversionForm');
    form.reset();

    // Reset batch mode
    const batchMode = document.getElementById('batchMode');
    batchMode.checked = false;

    // Show/hide appropriate sections
    document.getElementById('singleFileGroup').style.display = 'block';
    document.getElementById('batchFileGroup').style.display = 'none';
    document.getElementById('topModuleGroup').style.display = 'none';

    // Clear file labels
    document.getElementById('fileLabel').textContent = 'Choose a file or drag & drop here';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('batchFileList').innerHTML = '';

    // Clear results
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';

    // Reset submit button
    document.getElementById('submitBtn').disabled = false;
    document.getElementById('submitBtnText').textContent = 'Convert File';

    // Reset conversion type
    document.getElementById('conversionType').selectedIndex = 0;
}

function resetMetricsForm() {
    // Reset form
    const form = document.getElementById('metricsForm');
    form.reset();

    // Reset batch mode
    const batchMode = document.getElementById('metricsBatchMode');
    batchMode.checked = false;

    // Show/hide appropriate sections
    document.getElementById('metricsSingleFileGroup').style.display = 'block';
    document.getElementById('metricsBatchFileGroup').style.display = 'none';
    document.getElementById('customLibGroup').style.display = 'none';

    // Clear file labels
    document.getElementById('metricsFileLabel').textContent = 'Choose an AIG or BENCH file';
    document.getElementById('metricsFileInfo').style.display = 'none';
    document.getElementById('metricsBatchFileList').innerHTML = '';

    // Clear results
    document.getElementById('metricsProgressSection').style.display = 'none';
    document.getElementById('metricsResultSection').style.display = 'none';

    // Reset submit button
    document.getElementById('metricsSubmitBtn').disabled = false;
    document.getElementById('metricsSubmitBtnText').textContent = 'Calculate Metrics';

    // Reset library selection
    document.getElementById('libFile').selectedIndex = 0;
}

function resetAnalysisForm() {
    // Reset form
    const form = document.getElementById('analysisForm');
    form.reset();

    // Clear file label
    const fileLabel = document.getElementById('analysisFileLabel');
    if (fileLabel) {
        fileLabel.innerHTML = '<i class="fas fa-cloud-upload-alt"></i><span>Choose a Verilog file (.v, .sv) or drag & drop here</span>';
    }

    document.getElementById('analysisFileInfo').style.display = 'none';

    // Clear results
    document.getElementById('analysisProgressSection').style.display = 'none';
    document.getElementById('analysisResultSection').style.display = 'none';

    // Reset submit button
    document.getElementById('analysisSubmitBtn').disabled = false;
    document.getElementById('analysisSubmitBtnText').textContent = 'Analyze with AI';

    // Clear textarea
    document.getElementById('analysisPrompt').value = '';
}

// Language toggle for prompts
let currentLanguage = 'zh'; // Default to Chinese
let lastPromptType = null; // Track which prompt button was last clicked

function toggleLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'zh' : 'en';
    const langBtn = document.getElementById('languageToggle');
    if (langBtn) {
        langBtn.innerHTML = currentLanguage === 'en'
            ? '<i class="fas fa-language"></i> 中文'
            : '<i class="fas fa-language"></i> English';
    }

    // Auto-update the prompt if one was previously set
    const promptTextarea = document.getElementById('analysisPrompt');
    if (promptTextarea && promptTextarea.value && lastPromptType) {
        // Re-apply the same prompt type with new language
        if (lastPromptType === 'debug') {
            setDebugPrompt();
        } else if (lastPromptType === 'explain') {
            setExplainPrompt();
        } else if (lastPromptType === 'optimize') {
            setOptimizePrompt();
        }
    }
}

// Quick action prompt setters with bilingual support
function setDebugPrompt() {
    lastPromptType = 'debug'; // Track this prompt type
    const promptText = currentLanguage === 'zh' ?
    `请分析这段Verilog代码的错误和问题：

1. 首先，检查语法错误和基本结构问题
2. 识别潜在的逻辑错误（竞争条件、不完整的敏感列表等）
3. 检查可能阻止硬件实现的综合问题
4. 查找与时序相关的问题
5. 识别任何非标准的编码实践

对于发现的每个问题，请：
- 清楚地描述问题
- 解释为什么这是有问题的
- 建议修复或改进方案
- 评估严重程度（严重/高/中/低）

如果代码看起来是正确的，请确认并解释代码的功能。

请用中文回答。`
    :
    `Please analyze this Verilog code for bugs and issues:

1. First, check for syntax errors and basic structural problems
2. Identify potential logical bugs (race conditions, incomplete sensitivity lists, etc.)
3. Check for synthesis issues that would prevent hardware implementation
4. Look for timing-related problems
5. Identify any non-standard coding practices

For each issue found, please:
- Describe the problem clearly
- Explain why it's problematic
- Suggest a fix or improvement
- Rate the severity (Critical/High/Medium/Low)

If the code appears to be correct, please confirm that and explain what the code does.

Please answer in English.`;

    document.getElementById('analysisPrompt').value = promptText;
}

function setExplainPrompt() {
    lastPromptType = 'explain'; // Track this prompt type
    const promptText = currentLanguage === 'zh' ?
    `请对这段Verilog代码进行全面的解释：

1. 这个模块的目的和功能是什么？
2. 描述每个输入和输出信号
3. 解释内部逻辑和数据流
4. 识别任何状态机或时序逻辑
5. 描述时序关系和时钟域
6. 解释任何特殊功能或优化

请使用清晰、简洁的语言，适合初学者和有经验的设计师。

请用中文回答。`
    :
    `Please provide a comprehensive explanation of this Verilog code:

1. What is the purpose and functionality of this module?
2. Describe each input and output signal
3. Explain the internal logic and data flow
4. Identify any state machines or sequential logic
5. Describe timing relationships and clock domains
6. Explain any special features or optimizations

Please use clear, concise language suitable for both beginners and experienced designers.

Please answer in English.`;

    document.getElementById('analysisPrompt').value = promptText;
}

function setOptimizePrompt() {
    lastPromptType = 'optimize'; // Track this prompt type
    const promptText = currentLanguage === 'zh' ?
    `请分析这段Verilog代码的优化机会：

1. 识别可以减少资源使用的区域
2. 建议时序改进以获得更好的时钟频率
3. 寻找降低功耗的机会
4. 检查冗余逻辑或低效结构
5. 推荐更好的综合编码实践
6. 如适用，建议替代架构

对于每个优化：
- 解释当前的实现
- 描述建议的改进
- 估计预期的收益
- 注意任何权衡或考虑因素

请用中文回答。`
    :
    `Please analyze this Verilog code for optimization opportunities:

1. Identify areas where resource usage could be reduced
2. Suggest timing improvements for better clock frequency
3. Look for opportunities to reduce power consumption
4. Check for redundant logic or inefficient structures
5. Recommend better coding practices for synthesis
6. Suggest alternative architectures if applicable

For each optimization:
- Explain the current implementation
- Describe the suggested improvement
- Estimate the expected benefits
- Note any trade-offs or considerations

Please answer in English.`;

    document.getElementById('analysisPrompt').value = promptText;
}

// Export analysis result to PDF or Word
function exportAnalysisResult(format) {
    const resultSection = document.getElementById('analysisResultSection');

    if (!resultSection || resultSection.style.display === 'none') {
        alert('No analysis result to export. Please run an analysis first.');
        return;
    }

    const analysisContent = resultSection.querySelector('.analysis-content');
    const filename = resultSection.querySelector('.analysis-metadata span');

    if (!analysisContent) {
        alert('No content found to export.');
        return;
    }

    const filenameText = filename ? filename.textContent : 'verilog_analysis';
    const content = analysisContent.innerHTML;

    if (format === 'pdf') {
        exportToPDF(filenameText, content);
    } else if (format === 'word') {
        exportToWord(filenameText, content);
    }
}

function exportToPDF(filename, htmlContent) {
    // Create a printable version
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>${filename} - Analysis Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }
                h3, h4, h5 { color: #2563eb; margin-top: 1em; }
                code {
                    background: #f0f0f0;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }
                pre {
                    background: #2d2d2d;
                    color: #f8f8f2;
                    padding: 15px;
                    border-radius: 6px;
                    overflow-x: auto;
                }
                pre code {
                    background: none;
                    color: inherit;
                    padding: 0;
                }
                ul, ol { margin: 10px 0; padding-left: 30px; }
                li { margin: 5px 0; }
                p { margin: 8px 0; }
                strong { color: #1d4ed8; }
            </style>
        </head>
        <body>
            <h1>Verilog Analysis Report</h1>
            <h2>${filename}</h2>
            <hr>
            ${htmlContent}
        </body>
        </html>
    `);
    printWindow.document.close();

    // Wait for content to load then print
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

function exportToWord(filename, htmlContent) {
    // Clean up HTML content for Word - remove excessive spacing
    let cleanedContent = htmlContent
        .replace(/(<p>)\s*(<\/p>)/g, '')  // Remove empty paragraphs
        .replace(/(<\/h[2-6]>)\s*(<p>)/g, '$1\n$2')  // Add line break between headers and paragraphs
        .replace(/(<\/p>)\s*(<p>)/g, '$1\n$2')  // Add line break between paragraphs
        .replace(/(<\/h[2-6]>)\s*(<h[2-6]>)/g, '$1\n$2');  // Add line break between headers

    // Create a complete HTML document for Word
    const wordContent = `
        <!DOCTYPE html>
        <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word'>
        <head>
            <meta charset='utf-8'>
            <title>${filename} - Analysis Report</title>
            <!--[if gte mso 9]>
            <xml>
                <w:WordDocument>
                    <w:View>Print</w:View>
                    <w:Zoom>100</w:Zoom>
                    <w:DoNotOptimizeForBrowser/>
                </w:WordDocument>
            </xml>
            <![endif]-->
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.5;
                    margin: 0;
                    padding: 20px;
                }
                h2 {
                    color: #2563eb;
                    margin-top: 12pt;
                    margin-bottom: 6pt;
                    page-break-after: avoid;
                }
                h3 {
                    color: #2563eb;
                    margin-top: 12pt;
                    margin-bottom: 6pt;
                    page-break-after: avoid;
                }
                h4 {
                    color: #2563eb;
                    margin-top: 10pt;
                    margin-bottom: 4pt;
                    page-break-after: avoid;
                }
                h5 {
                    color: #2563eb;
                    margin-top: 8pt;
                    margin-bottom: 4pt;
                    page-break-after: avoid;
                }
                p {
                    margin-top: 0pt;
                    margin-bottom: 6pt;
                    text-align: justify;
                }
                code {
                    background: #f0f0f0;
                    padding: 2px 4px;
                    border-radius: 2px;
                    font-family: 'Courier New', monospace;
                    font-size: 90%;
                }
                pre {
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    padding: 10pt;
                    margin: 8pt 0;
                    overflow-x: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 9pt;
                    page-break-inside: avoid;
                }
                pre code {
                    background: none;
                    padding: 0;
                }
                ul, ol {
                    margin-top: 6pt;
                    margin-bottom: 6pt;
                    padding-left: 30pt;
                }
                li {
                    margin-top: 3pt;
                    margin-bottom: 3pt;
                }
                strong {
                    color: #1d4ed8;
                    font-weight: bold;
                }
                hr {
                    margin: 12pt 0;
                    border: none;
                    border-top: 1px solid #ddd;
                }
            </style>
        </head>
        <body>
            <h1>Verilog Analysis Report</h1>
            <h2>${escapeHtml(filename)}</h2>
            <hr>
            ${cleanedContent}
        </body>
        </html>
    `;

    // Create blob and download
    const blob = new Blob(['\ufeff', wordContent], {
        type: 'application/msword'
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_analysis.doc`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
