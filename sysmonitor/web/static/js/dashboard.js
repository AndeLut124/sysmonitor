let ws = null;
const statusEl = document.getElementById("status");

const history = {
    cpu: new Array(60).fill(0),
    gpu: new Array(60).fill(0),
    netUp: new Array(60).fill(0),
    netDown: new Array(60).fill(0),
};

const canvases = {
    cpu: document.getElementById("cpu-chart"),
    gpu: document.getElementById("gpu-chart"),
    net: document.getElementById("net-chart"),
};

function connect() {
    ws = new WebSocket(`ws://${location.host}/ws`);

    ws.onopen = () => {
        statusEl.textContent = "● Онлайн";
        statusEl.className = "status online";
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };

    ws.onclose = () => {
        statusEl.textContent = "● Отключено";
        statusEl.className = "status offline";
        setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
}

function updateDashboard(data) {
    // CPU
    updateGauge("cpu-gauge", data.cpu.percent, 326.73);
    document.getElementById("cpu-value").textContent = `${Math.round(data.cpu.percent)}%`;
    document.getElementById("cpu-cores").textContent = `Ядер: ${data.cpu.cores}`;

    // GPU
    if (data.gpu) {
        document.getElementById("gpu-load").textContent = `${data.gpu.load_percent}%`;
        document.getElementById("gpu-vram").textContent = `${data.gpu.memory_used_mb}/${data.gpu.memory_total_mb} MB`;
        document.getElementById("gpu-temp").textContent = `${data.gpu.temperature}°C`;
        document.getElementById("gpu-name").textContent = data.gpu.name;
    } else {
        document.getElementById("gpu-load").textContent = "--%";
        document.getElementById("gpu-vram").textContent = "--/-- MB";
        document.getElementById("gpu-temp").textContent = "--°C";
        document.getElementById("gpu-name").textContent = "GPU не обнаружен (установите pip install gputil)";
    }

    // RAM
    updateGauge("ram-gauge", data.memory.percent, 263.89);
    document.getElementById("ram-value").textContent = `${Math.round(data.memory.percent)}%`;
    document.getElementById("ram-used").textContent = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;

    // Диски
    updateDisks(data.disks);

    // Сеть
    document.getElementById("net-up").textContent = `${data.network.speed_sent_mbps} Mbps`;
    document.getElementById("net-down").textContent = `${data.network.speed_recv_mbps} Mbps`;

    // Процессы
    updateProcesses(data.processes);

    // Графики
    updateCharts(data);
}

function updateGauge(id, percent, circumference) {
    const circle = document.getElementById(id);
    if (!circle) return;
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = offset;

    if (percent > 90) circle.style.stroke = "#f85149";
    else if (percent > 70) circle.style.stroke = "#d2991d";
    else circle.style.stroke = "#3fb950";
}

function updateDisks(disks) {
    const container = document.getElementById("disk-list");
    container.innerHTML = disks.map(d => `
        <div class="disk-item">
            <span>${d.mount_point}</span>
            <div class="disk-bar">
                <div class="disk-bar-fill" style="width:${d.percent}%"></div>
            </div>
            <span>${d.used_gb}/${d.total_gb} GB</span>
        </div>
    `).join("");
}

function updateProcesses(procs) {
    const tbody = document.getElementById("process-table");
    tbody.innerHTML = procs.map(p => `
        <tr>
            <td>${p.pid}</td>
            <td>${p.name}</td>
            <td>${p.cpu_percent.toFixed(1)}</td>
            <td>${p.memory_percent.toFixed(1)}</td>
        </tr>
    `).join("");
}

function updateCharts(data) {
    history.cpu.push(data.cpu.percent);
    history.netUp.push(data.network.speed_sent_mbps);
    history.netDown.push(data.network.speed_recv_mbps);

    if (data.gpu) {
        history.gpu.push(data.gpu.load_percent);
    } else {
        history.gpu.push(0);
    }

    ["cpu", "gpu", "netUp", "netDown"].forEach(k => {
        if (history[k].length > 60) history[k].shift();
    });

    drawLineChart(canvases.cpu, history.cpu, "#3fb950");
    drawLineChart(canvases.gpu, history.gpu, "#a371f7");
    drawNetChart();
}

function drawLineChart(canvas, data, color) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const max = Math.max(...data, 100);

    ctx.clearRect(0, 0, w, h);

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;

    data.forEach((val, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - (val / max) * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();

    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, color + "40");
    gradient.addColorStop(1, color + "00");

    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
}

function drawNetChart() {
    const ctx = canvases.net.getContext("2d");
    const w = canvases.net.width;
    const h = canvases.net.height;
    const all = [...history.netUp, ...history.netDown];
    const max = Math.max(...all, 0.1);

    ctx.clearRect(0, 0, w, h);

    drawNetLine(ctx, history.netDown, "#58a6ff", w, h, max);
    drawNetLine(ctx, history.netUp, "#3fb950", w, h, max);
}

function drawNetLine(ctx, data, color, w, h, max) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;

    data.forEach((val, i) => {
        const x = (i / (data.length - 1)) * w;
        const y = h - (val / max) * h;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();
}

connect();