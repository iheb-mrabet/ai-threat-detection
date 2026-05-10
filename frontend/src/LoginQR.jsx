import { useEffect, useState } from "react";
import QRCode from "react-qr-code";
import axios from "axios";

function getApiUrl() {
  return `${window.location.origin}/api`;
}

function getWsUrl(sessionId) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/auth/qr/ws/${sessionId}`;
}

export default function LoginQR() {
  const [qrUrl, setQrUrl] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [expiresIn, setExpiresIn] = useState(0);
  const [status, setStatus] = useState("Creating secure QR session...");
  const [syncStatus, setSyncStatus] = useState("Not connected yet");

  function approveDesktopLogin(token) {
    if (!token) {
      setSyncStatus("Approved but token missing.");
      return;
    }

    localStorage.setItem("jwt_token", token);

    setSyncStatus("Login approved from phone.");
    setStatus("Authentication approved. Redirecting to dashboard...");

    setTimeout(() => {
      window.location.href = "/";
    }, 800);
  }

  useEffect(() => {
    async function createQrSession() {
      try {
        const apiUrl = getApiUrl();
        const response = await axios.post(`${apiUrl}/auth/qr/start`);

        const newSessionId = response.data.session_id;
        const publicMobileUrl = `${window.location.origin}/mobile-login/${newSessionId}`;

        setSessionId(newSessionId);
        setQrUrl(publicMobileUrl);
        setExpiresIn(response.data.expires_in);
        setStatus("Scan this QR code with your phone.");
      } catch (error) {
        console.error(error);
        setStatus("Failed to create QR login session.");
      }
    }

    createQrSession();
  }, []);

  // WebSocket live sync
  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(getWsUrl(sessionId));

    ws.onopen = () => {
      setSyncStatus("WebSocket connected. Waiting for mobile authentication...");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("QR WebSocket message:", data);

        if (data.status === "approved") {
          approveDesktopLogin(data.token);
        } else if (data.status === "expired") {
          setSyncStatus("QR session expired. Refresh the page.");
          setStatus("QR session expired.");
        } else if (data.message) {
          setSyncStatus(data.message);
        }
      } catch (error) {
        console.error("Invalid WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("QR WebSocket error:", error);
      setSyncStatus("WebSocket error. Polling fallback is active.");
    };

    ws.onclose = () => {
      setSyncStatus("WebSocket closed. Polling fallback is active.");
    };

    return () => ws.close();
  }, [sessionId]);

  // Fallback polling: this is the important fix
  useEffect(() => {
    if (!sessionId) return;

    const apiUrl = getApiUrl();

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${apiUrl}/auth/qr/status/${sessionId}`);
        const data = response.data;

        console.log("QR polling status:", data);

        if (data.status === "approved") {
          clearInterval(interval);
          approveDesktopLogin(data.approved_token);
        }

        if (data.status === "pending") {
          setSyncStatus("Waiting for mobile authentication...");
        }
      } catch (error) {
        console.error("QR polling failed:", error);
        clearInterval(interval);
        setSyncStatus("QR session expired or invalid.");
        setStatus("QR session expired.");
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>AI Threat Detection Login</h1>

        <p style={styles.text}>
          Scan this QR code with your smartphone to continue authentication.
        </p>

        {qrUrl ? (
          <div style={styles.qrBox}>
            <QRCode value={qrUrl} size={220} />
          </div>
        ) : (
          <p>Generating QR code...</p>
        )}

        <p>
          <strong>Status:</strong> {status}
        </p>

        <p>
          <strong>Live sync:</strong> {syncStatus}
        </p>

        {qrUrl && (
          <p style={styles.small}>
            QR URL: {qrUrl}
          </p>
        )}

        {sessionId && (
          <p style={styles.small}>
            Session ID: {sessionId}
          </p>
        )}

        {expiresIn > 0 && (
          <p style={styles.small}>
            Expires in: {expiresIn} seconds
          </p>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0f172a",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "Arial, sans-serif",
    padding: "20px"
  },
  card: {
    background: "#111827",
    padding: "32px",
    borderRadius: "16px",
    width: "460px",
    textAlign: "center",
    boxShadow: "0 20px 40px rgba(0,0,0,0.4)"
  },
  title: {
    marginBottom: "12px"
  },
  text: {
    color: "#d1d5db"
  },
  qrBox: {
    background: "white",
    padding: "16px",
    borderRadius: "12px",
    display: "inline-block",
    margin: "20px 0"
  },
  small: {
    fontSize: "12px",
    color: "#9ca3af",
    wordBreak: "break-all"
  }
};
