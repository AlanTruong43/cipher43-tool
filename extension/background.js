// background.js — Chỉ làm 1 việc: tìm debug port theo URL của tab

const BATCH   = 300;
const TIMEOUT = 100;  // ECONNREFUSED trả về gần như ngay, chỉ cần timeout cho port mở nhưng không phải Chrome

const RANGES = [
    [9200,  9500 ],
    [10000, 12000],
    [20000, 30000],
    [40000, 50000],
    [50000, 65535],
    [9000,  9199 ],
];

async function checkPort(port, targetUrl, signal) {
    try {
        const r = await fetch(`http://127.0.0.1:${port}/json`, {
            signal: AbortSignal.any([AbortSignal.timeout(TIMEOUT), signal])
        });
        const tabs = await r.json();
        return tabs.find(t => t.url === targetUrl) ? port : null;
    } catch {
        return null;
    }
}

async function findDebugPort(targetUrl) {
    const abort = new AbortController();
    let found   = null;

    async function scanRange(start, end) {
        for (let s = start; s <= end; s += BATCH) {
            if (found) return;                           // range khác đã tìm thấy → dừng
            const len  = Math.min(BATCH, end - s + 1);
            const ports = Array.from({ length: len }, (_, i) => s + i);
            const hits  = await Promise.all(ports.map(p => checkPort(p, targetUrl, abort.signal)));
            const hit   = hits.find(p => p !== null);
            if (hit) {
                found = hit;
                abort.abort();                          // huỷ tất cả range còn lại
                return;
            }
        }
    }

    // Tất cả range chạy song song — trả về ngay khi range nào tìm thấy trước
    await Promise.all(RANGES.map(([s, e]) => scanRange(s, e)));
    return found;
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.action === "find_port_for_url") {
        findDebugPort(msg.url).then(port =>
            sendResponse(port ? { success: true, port } : { success: false })
        );
        return true;
    }
});
