import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";
const API_KEY = "dev-secret-key";

function App() {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [status, setStatus] = useState("connecting");

  const headers = {
    "X-API-Key": API_KEY,
  };

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

      if (data.type === "connection") {
        return;
      }

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

export default App;
