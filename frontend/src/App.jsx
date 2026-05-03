import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";
const API_KEY = "dev-secret-key";

const headers = {
  "X-API-Key": API_KEY,
};

const attackSimulations = [
  {
    name: "SQL Injection",
    description: "Injects SQL logic into a query parameter to test authentication bypass or database extraction detection.",
    log_line: `10.0.0.5 - - [03/May/2026:10:01:00 +0100] "GET /login?user=admin' OR 1=1-- HTTP/1.1" 200 900`
  },
  {
    name: "XSS",
    description: "Sends script-like content to test detection of client-side code injection attempts.",
    log_line: `10.0.0.6 - - [03/May/2026:10:02:00 +0100] "GET /search?q=<script>alert(1)</script> HTTP/1.1" 200 1200`
  },
  {
    name: "Path Traversal",
    description: "Uses ../ style paths to test detection of attempts to access files outside the web directory.",
    log_line: `10.0.0.7 - - [03/May/2026:10:03:00 +0100] "GET /download?file=../../../etc/passwd HTTP/1.1" 403 700`
  },
  {
    name: "Command Injection",
    description: "Sends command-like parameters to test detection of suspicious operating-system command patterns.",
    log_line: `10.0.0.8 - - [03/May/2026:10:04:00 +0100] "GET /api?cmd=whoami HTTP/1.1" 200 800`
  },
  {
    name: "SSRF",
    description: "Attempts to make the server request an internal or sensitive address through a URL parameter.",
    log_line: `10.0.0.9 - - [03/May/2026:10:05:00 +0100] "GET /fetch?url=http://169.254.169.254/latest/meta-data/ HTTP/1.1" 403 600`
  },
  {
    name: "Log4Shell",
    description: "Uses a Log4Shell-like lookup string to test detection of dangerous logging payload patterns.",
    log_line: `10.0.0.10 - - [03/May/2026:10:06:00 +0100] "GET /?q=\${jndi:ldap://example.local/a} HTTP/1.1" 400 500`
  },
  {
    name: "Spoofing",
    description: "Simulates identity spoofing through suspicious admin/root parameters.",
    log_line: `10.0.0.11 - - [03/May/2026:10:07:00 +0100] "GET /admin?user=root&spoofed_ip=127.0.0.1 HTTP/1.1" 403 650`
  },
  {
    name: "Noise / Bruit",
    description: "Adds random-looking characters and unusual request patterns to test model robustness against noisy input.",
    log_line: `10.0.0.12 - - [03/May/2026:10:08:00 +0100] "GET /search?q=%%%%%252525@@@@@!!!!admin HTTP/1.1" 400 450`
  },
  {
    name: "Compression / Encoded Payload",
    description: "Uses encoded payloads to test whether obfuscated attacks are still detected.",
    log_line: `10.0.0.13 - - [03/May/2026:10:09:00 +0100] "GET /login?user=admin%27%20OR%201%3D1-- HTTP/1.1" 200 900`
  }
];

function Navigation() {
  return (
    <nav className="nav">
      <a href="/">Dashboard</a>
      <a href="/attacks">Attack Simulations</a>
    </nav>
  );
}

function AttackPage() {
  const [simulationStatus, setSimulationStatus] = useState("");

  async function simulateAttack(simulation) {
    try {
      setSimulationStatus(`Running ${simulation.name} simulation...`);

      const response = await axios.post(
        `${API_BASE}/analyze`,
        { log_line: simulation.log_line },
        { headers }
      );

      setSimulationStatus(
        `${simulation.name} simulated. Result: ${response.data.threat_type} | Score: ${response.data.score}`
      );
    } catch (error) {
      console.error(error);
      setSimulationStatus(`Simulation failed: ${simulation.name}`);
    }
  }

  return (
    <div className="app">
      <Navigation />

      <header className="header">
        <div>
          <h1>Attack Simulations</h1>
          <p>Run safe simulated nginx attack logs and watch the dashboard update in real time.</p>
        </div>
      </header>

      {simulationStatus && (
        <div className="simulation-status">{simulationStatus}</div>
      )}

      <section className="panel">
        <div className="simulation-grid">
          {attackSimulations.map((simulation) => (
            <div className="simulation-card" key={simulation.name}>
              <button onClick={() => simulateAttack(simulation)}>
                Run {simulation.name}
              </button>
              <p>{simulation.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [status, setStatus] = useState("connecting");

  async function loadData() {
    try {
      const statsRes = await axios.get(`${API_BASE}/stats`, { headers });
      const eventsRes = await axios.get(`${API_BASE}/events?limit=20`, { headers });
      const alertsRes = await axios.get(`${API_BASE}/threats?limit=20`, { headers });
      const modelRes = await axios.get(`${API_BASE}/models/status`, { headers });

      setStats(statsRes.data);
      setEvents(eventsRes.data.events || []);
      setAlerts(alertsRes.data.alerts || []);
      setModelStatus(modelRes.data);
    } catch (error) {
      console.error(error);
      setStatus("api_error");
    }
  }

  useEffect(() => {
    loadData();

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/alerts");

    ws.onopen = () => setStatus("connected");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "connection") return;

      setLiveAlerts((prev) => [data, ...prev].slice(0, 10));
      loadData();
    };

    ws.onerror = () => setStatus("websocket_error");
    ws.onclose = () => setStatus("disconnected");

    return () => ws.close();
  }, []);

  const severityClass = (severity) => {
    if (severity === "critical") return "severity critical";
    if (severity === "high") return "severity high";
    if (severity === "medium") return "severity medium";
    return "severity low";
  };

  return (
    <div className="app">
      <Navigation />

      <header className="header">
        <div>
          <h1>AI Threat Detection Dashboard</h1>
          <p>Real-time nginx threat detection with rules, ML ensemble, ONNX, Redis, and PostgreSQL.</p>
        </div>

        <div className={`connection ${status}`}>
          WebSocket: {status}
        </div>
      </header>

      <section className="cards">
        <div className="card">
          <h3>Total Events</h3>
          <p>{stats?.total_events ?? 0}</p>
        </div>

        <div className="card">
          <h3>Total Alerts</h3>
          <p>{stats?.total_alerts ?? 0}</p>
        </div>

        <div className="card">
          <h3>Benign Events</h3>
          <p>{stats?.benign_events ?? 0}</p>
        </div>

        <div className="card">
          <h3>Model Status</h3>
          <p>{modelStatus?.ready ? "Ready" : "Not Ready"}</p>
        </div>
      </section>

      <section className="panel">
        <h2>Model Information</h2>
        <div className="model-grid">
          <div>
            <strong>Detection backend:</strong>
            <pre>{JSON.stringify(modelStatus?.inference_backend || {}, null, 2)}</pre>
          </div>
          <div>
            <strong>Metrics:</strong>
            <pre>{JSON.stringify(modelStatus?.metadata?.metrics || {}, null, 2)}</pre>
          </div>
          <div>
            <strong>Dataset:</strong>
            <pre>{JSON.stringify(modelStatus?.metadata?.dataset || {}, null, 2)}</pre>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Live Alerts</h2>
        {liveAlerts.length === 0 ? (
          <p className="muted">No live alerts received yet.</p>
        ) : (
          <div className="alert-list">
            {liveAlerts.map((alert, index) => (
              <div className="alert-item" key={index}>
                <span className={severityClass(alert.severity)}>{alert.severity}</span>
                <strong>{alert.threat_type}</strong>
                <p>{alert.log_line}</p>
                <small>Score: {alert.score} | Mode: {alert.detection_mode}</small>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Recent Threats</h2>
        <table>
          <thead>
            <tr>
              <th>Severity</th>
              <th>Type</th>
              <th>Score</th>
              <th>Event ID</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr key={alert.id}>
                <td><span className={severityClass(alert.severity)}>{alert.severity}</span></td>
                <td>{alert.threat_type}</td>
                <td>{alert.score}</td>
                <td>{alert.event_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Recent Events</h2>
        <table>
          <thead>
            <tr>
              <th>Threat</th>
              <th>Type</th>
              <th>Score</th>
              <th>Mode</th>
              <th>Log</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td>{event.is_threat ? "Yes" : "No"}</td>
                <td>{event.threat_type}</td>
                <td>{event.score}</td>
                <td>{event.detection_mode}</td>
                <td className="log-cell">{event.log_line}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function App() {
  const path = window.location.pathname;

  if (path === "/attacks") {
    return <AttackPage />;
  }

  return <DashboardPage />;
}

export default App;
