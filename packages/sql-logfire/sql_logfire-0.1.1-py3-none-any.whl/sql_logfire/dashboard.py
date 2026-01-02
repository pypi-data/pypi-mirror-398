html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LogFire Dashboard</title>
    <style>
        :root { --primary: #2563eb; --bg: #f8fafc; --surface: #ffffff; --text: #1e293b; --border: #e2e8f0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .card { background: var(--surface); border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
        .controls { padding: 15px; border-bottom: 1px solid var(--border); display: flex; gap: 10px; flex-wrap: wrap; }
        input, select, button { padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; }
        button { background: var(--primary); color: white; border: none; cursor: pointer; }
        button:hover { opacity: 0.9; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); }
        th { background: #f1f5f9; font-weight: 600; }
        .tag { padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .tag-INFO { background: #dbeafe; color: #1e40af; }
        .tag-ERROR { background: #fee2e2; color: #991b1b; }
        .tag-WARNING { background: #fef3c7; color: #92400e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔥 LogFire Monitor</h2>
            <div id="status" style="font-size: 0.9em; color: #64748b;"></div>
        </div>
        
        <div class="card">
            <div class="controls">
                <input type="text" id="searchInput" placeholder="Search logs (e.g. 'failed')..." style="flex-grow: 1;">
                <select id="timeFilter">
                    <option value="0">All Time</option>
                    <option value="60">Last 1 Hour</option>
                    <option value="15">Last 15 Minutes</option>
                    <option value="5" selected>Last 5 Minutes</option>
                </select>
                <button onclick="fetchLogs()">Refresh Logs</button>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 180px;">Timestamp</th>
                            <th style="width: 100px;">Level</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody id="logTableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function fetchLogs() {
            const search = document.getElementById('searchInput').value;
            const minutes = document.getElementById('timeFilter').value;
            const btn = document.querySelector('button');
            
            btn.disabled = true;
            btn.innerText = 'Loading...';
            
            try {
                // Determine base URL dynamically
                const basePath = window.location.pathname.replace(/\/$/, "");
                const res = await fetch(`${basePath}/api/logs?minutes=${minutes}&q=${encodeURIComponent(search)}`);
                const data = await res.json();
                
                const tbody = document.getElementById('logTableBody');
                tbody.innerHTML = '';
                
                if(data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;">No logs found</td></tr>';
                }

                data.forEach(log => {
                    const row = document.createElement('tr');
                    const date = new Date(log.created_at).toLocaleString();
                    row.innerHTML = `
                        <td style="white-space: nowrap; color: #64748b;">${date}</td>
                        <td><span class="tag tag-${log.level}">${log.level}</span></td>
                        <td style="font-family: monospace;">${log.message}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                document.getElementById('status').innerText = `Showing ${data.length} logs`;
            } catch (err) {
                console.error(err);
                alert('Failed to load logs');
            } finally {
                btn.disabled = false;
                btn.innerText = 'Refresh Logs';
            }
        }

        // Auto-load on start
        fetchLogs();
    </script>
</body>
</html>
"""