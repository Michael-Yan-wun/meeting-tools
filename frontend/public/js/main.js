// API Base URL (指向 FastAPI)
const API_BASE = 'http://localhost:8000/api';

document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
        });
    }

    // 載入歷史記錄
    loadHistory();

    // 處理上傳
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', handleUpload);
});

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/meetings`);
        const meetings = await response.json();
        const list = document.getElementById('history-list');
        list.innerHTML = '';

        if (meetings.length === 0) {
            list.innerHTML = '<div class="text-center py-3 text-muted small">無記錄</div>';
            return;
        }

        meetings.forEach(m => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action list-group-item-light p-3';
            item.href = '#';
            item.onclick = (e) => {
                e.preventDefault();
                loadMeetingDetails(m.id);
                // Highlight active
                document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
            };
            
            const date = new Date(m.created_at).toLocaleDateString('zh-TW');
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0 text-truncate" style="max-width: 120px;">${m.filename}</h6>
                    <small class="text-muted">${date}</small>
                </div>
                <small class="text-muted text-truncate d-block mt-1">${m.summary ? m.summary.substring(0, 20) + '...' : '無摘要'}</small>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load history:", err);
    }
}

async function loadMeetingDetails(id) {
    try {
        const response = await fetch(`${API_BASE}/meetings/${id}`);
        const data = await response.json();
        
        document.getElementById('welcome-screen').style.display = 'none';
        document.getElementById('result-view').style.display = 'block';

        document.getElementById('meeting-title').innerText = data.filename;
        document.getElementById('meeting-date').innerText = new Date(data.created_at).toLocaleString('zh-TW');
        document.getElementById('meeting-summary').innerText = data.summary || '(無總結)';

        // Topics
        const topicsList = document.getElementById('meeting-topics-list');
        topicsList.innerHTML = '';
        if (data.meeting_topics && data.meeting_topics.length > 0) {
            data.meeting_topics.forEach(topic => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `<i class="fas fa-angle-right me-2 text-muted"></i>${topic}`;
                topicsList.appendChild(li);
            });
        } else {
            topicsList.innerHTML = '<li class="list-group-item text-muted">無主題</li>';
        }

        // Participants
        const pTableBody = document.querySelector('#participants-table tbody');
        pTableBody.innerHTML = '';
        if (data.participants && data.participants.length > 0) {
            data.participants.forEach(p => {
                const row = pTableBody.insertRow();
                if (typeof p === 'string') {
                    row.innerHTML = `<td>${p}</td><td></td>`;
                } else {
                    row.innerHTML = `<td><strong>${p.name || ''}</strong></td><td>${p.role || ''}</td>`;
                }
            });
        } else {
            pTableBody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">無資料</td></tr>';
        }

        // Key Points
        const kList = document.getElementById('key-points-list');
        kList.innerHTML = '';
        if (data.key_points && data.key_points.length > 0) {
            data.key_points.forEach((kp, idx) => {
                const div = document.createElement('div');
                div.className = 'mb-3';
                if (typeof kp === 'string') {
                    div.innerHTML = `<p>${kp}</p>`;
                } else {
                    div.innerHTML = `
                        <h6 class="fw-bold text-dark">${idx + 1}. ${kp.title}</h6>
                        <p class="text-muted ms-3 border-start ps-2 border-3">${kp.content}</p>
                    `;
                }
                kList.appendChild(div);
            });
        } else {
            kList.innerHTML = '<p class="text-muted">無重點</p>';
        }

        // Next Steps
        const nsTableBody = document.querySelector('#next-steps-table tbody');
        nsTableBody.innerHTML = '';
        if (data.next_steps && data.next_steps.length > 0) {
            data.next_steps.forEach(step => {
                const row = nsTableBody.insertRow();
                if (typeof step === 'string') {
                    row.innerHTML = `<td>${step}</td><td></td>`;
                } else {
                    row.innerHTML = `<td>${step.action}</td><td><span class="badge bg-secondary">${step.owner || '未指定'}</span></td>`;
                }
            });
        } else {
            nsTableBody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">無待辦事項</td></tr>';
        }

        // Download Link
        if (data.doc_url) {
            // 如果 API 直接回傳了下載網址 (例如上傳成功時)
             document.getElementById('download-btn').href = `http://localhost:8000${data.doc_url}`;
        } else {
            // 否則組裝下載網址
            const filenameNoExt = data.filename.replace(/\.[^/.]+$/, "");
            document.getElementById('download-btn').href = `http://localhost:8000/api/download/Meeting_${filenameNoExt}.docx`;
        }

    } catch (err) {
        console.error(err);
    }
}

async function handleUpload(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const progressBar = document.querySelector('#upload-progress .progress-bar');
    const progressContainer = document.getElementById('upload-progress');
    const statusText = document.getElementById('status-text');
    const submitBtn = document.getElementById('submit-btn');

    progressContainer.classList.remove('d-none');
    submitBtn.disabled = true;
    statusText.innerText = '正在上傳檔案...';
    progressBar.style.width = '10%';

    let interval;

    try {
        // 模擬進度條
        let progress = 10;
        interval = setInterval(() => {
            if (progress < 90) {
                progress += 5;
                progressBar.style.width = `${progress}%`;
                if (progress > 30) statusText.innerText = '正在進行語音轉錄 (Whisper)...';
                if (progress > 60) statusText.innerText = '正在進行 AI 結構化分析 (Gemini)...';
            }
        }, 2000);

        // 注意：改成呼叫 FastAPI
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Upload failed');
        }

        const result = await response.json();
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-animated');
        progressBar.classList.add('bg-success');
        statusText.innerText = '處理完成！';

        setTimeout(() => {
            const modalEl = document.getElementById('uploadModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            
            e.target.reset();
            progressBar.style.width = '0%';
            progressContainer.classList.add('d-none');
            submitBtn.disabled = false;
            
            loadHistory();
            loadMeetingDetails(result.id);
        }, 1000);

    } catch (err) {
        clearInterval(interval); // 確保清除 timer
        statusText.innerText = `錯誤: ${err.message}`;
        statusText.classList.add('text-danger');
        progressBar.classList.add('bg-danger');
        submitBtn.disabled = false;
    }
}
