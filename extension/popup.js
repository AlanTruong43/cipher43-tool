const TOOL_API = 'http://127.0.0.1:8000';
const STORAGE_KEY = 'c43_tool_token';
const EXCEL_KEY   = 'c43_excel_path';

const $token   = document.getElementById('input-token');
const $load    = document.getElementById('btn-load');
const $info    = document.getElementById('tool-info');
const $select  = document.getElementById('select-profile');
const $excel   = document.getElementById('input-excel');
const $run     = document.getElementById('btn-run');
const $result  = document.getElementById('result');
const $dot     = document.getElementById('status-dot');

let currentScriptName = '';

// ── Restore saved values ──────────────────────────────────────────────────────
chrome.storage.local.get([STORAGE_KEY, EXCEL_KEY], (data) => {
    if (data[STORAGE_KEY]) {
        $token.value = data[STORAGE_KEY];
    }
    if (data[EXCEL_KEY]) {
        $excel.value = data[EXCEL_KEY];
    }
});

// ── Check tool server is running ──────────────────────────────────────────────
fetch(`${TOOL_API}/`)
    .then(() => $dot.classList.add('online'))
    .catch(() => setResult('Tool server chưa chạy. Hãy khởi động api_server.py', 'error'));

// ── Load token ────────────────────────────────────────────────────────────────
$load.addEventListener('click', loadToken);
$token.addEventListener('keydown', (e) => { if (e.key === 'Enter') loadToken(); });

async function loadToken() {
    const token = $token.value.trim();
    if (!token) return;

    $load.disabled = true;
    $load.textContent = '...';
    setInfo('', '', 'loading');
    setResult('');

    try {
        const res = await fetch(`${TOOL_API}/tool-info?token=${encodeURIComponent(token)}`);
        const data = await res.json();

        if (!res.ok) {
            setInfo(data.detail || 'Token không hợp lệ', '', 'error');
            return;
        }

        currentScriptName = data.scriptName || '';
        setInfo(data.toolName, data.scriptName, 'ok');
        populateProfiles(data.profiles || []);

        chrome.storage.local.set({ [STORAGE_KEY]: token });
        $run.disabled = false;
    } catch (e) {
        setInfo('Không kết nối được tool server', '', 'error');
    } finally {
        $load.disabled = false;
        $load.textContent = 'Load';
    }
}

// ── Run ───────────────────────────────────────────────────────────────────────
$run.addEventListener('click', async () => {
    const token     = $token.value.trim();
    const excelPath = $excel.value.trim();

    if (!token)     return setResult('Chưa có token', 'error');
    if (!excelPath) return setResult('Chưa nhập đường dẫn Excel', 'error');

    chrome.storage.local.set({ [EXCEL_KEY]: excelPath });

    $run.disabled = true;
    $run.textContent = '⏳ Đang chạy...';
    setResult('Đang gửi lệnh...');

    try {
        const res = await fetch(`${TOOL_API}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_token: token, excel_path: excelPath })
        });
        const data = await res.json();

        if (!res.ok) {
            setResult(data.detail || 'Lỗi không xác định', 'error');
            return;
        }

        const queued  = data.queued_profiles?.length || 0;
        const errors  = data.errors?.length || 0;
        let msg = `✓ Đã queue ${queued} profile`;
        if (errors) msg += `\n⚠ ${errors} profile lỗi`;
        if (data.errors?.length) {
            msg += '\n' + data.errors.map(e => `  • ${e.profile_name || 'unknown'}: ${e.error}`).join('\n');
        }
        setResult(msg, 'success');
    } catch (e) {
        setResult('Không kết nối được tool server', 'error');
    } finally {
        $run.disabled = false;
        $run.textContent = '▶ Chạy';
    }
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function populateProfiles(profiles) {
    $select.innerHTML = '<option value="">-- Tất cả profiles trong Excel --</option>';
    profiles.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = `${p.name} (${p.status})`;
        $select.appendChild(opt);
    });
    $select.disabled = profiles.length === 0;
}

function setInfo(name, script, state) {
    $info.className = 'tool-info';
    if (state === 'loading') {
        $info.innerHTML = '<span style="color:#666">Đang load...</span>';
    } else if (state === 'error') {
        $info.classList.add('error');
        $info.textContent = name;
    } else if (name) {
        $info.innerHTML = `<span class="name">${name}</span><span class="script">${script}</span>`;
    } else {
        $info.classList.add('placeholder');
        $info.innerHTML = '<span>Chưa load token</span>';
    }
}

function setResult(msg, type = '') {
    $result.textContent = msg;
    $result.className = 'result' + (type ? ` ${type}` : '');
}
