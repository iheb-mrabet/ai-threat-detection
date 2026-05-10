import { useEffect, useState } from "react";
import axios from "axios";
import { startAuthentication } from "@simplewebauthn/browser";

function getApiUrl() {
  return `${window.location.origin}/api`;
}

export default function MobileLogin() {
  const [sessionId, setSessionId] = useState("");
  const [status, setStatus] = useState("Checking QR session...");
  const [canAuthenticate, setCanAuthenticate] = useState(false);

  useEffect(() => {
    const parts = window.location.pathname.split("/");
    const id = parts[parts.length - 1];

    setSessionId(id);

    async function checkSession() {
      try {
        const apiUrl = getApiUrl();
        const response = await axios.get(`${apiUrl}/auth/qr/status/${id}`);

        if (response.data.status === "pending") {
          setStatus("QR session detected. Ready for Face ID / passkey verification.");
          setCanAuthenticate(true);
        } else {
          setStatus(`Session status: ${response.data.status}`);
          setCanAuthenticate(false);
        }
      } catch (error) {
        console.error(error);
        setStatus("QR session expired or invalid.");
        setCanAuthenticate(false);
      }
    }

    checkSession();
  }, []);

  async function authenticateWithPasskey() {
    try {
      setStatus("Requesting Face ID / passkey challenge...");

      const apiUrl = getApiUrl();

      const optionsResponse = await axios.post(
        `${apiUrl}/auth/webauthn/login/options/${sessionId}`
      );

      setStatus("Use Face ID / fingerprint / screen lock to approve login...");

      const authResponse = await startAuthentication({ optionsJSON: optionsResponse.data });

      setStatus("Verifying authentication with backend...");

      await axios.post(
        `${apiUrl}/auth/webauthn/login/verify/${sessionId}`,
        authResponse
      );

      setStatus("Approved. Return to your desktop.");
      setCanAuthenticate(false);
    } catch (error) {
      console.error(error);
      setStatus(error?.response?.data?.detail || "Authentication failed or was cancelled.");
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Mobile Biometric Login</h1>

        <p style={styles.text}>{status}</p>

        <p style={styles.small}>
          Session ID: {sessionId}
        </p>

        <button
          style={{
            ...styles.button,
            opacity: canAuthenticate ? 1 : 0.5,
            cursor: canAuthenticate ? "pointer" : "not-allowed"
          }}
          disabled={!canAuthenticate}
          onClick={authenticateWithPasskey}
        >
          Verify with Face ID / Passkey
        </button>

        <a href="/register-passkey" style={styles.link}>
          Register this phone first
        </a>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#020617",
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
    width: "400px",
    textAlign: "center",
    boxShadow: "0 20px 40px rgba(0,0,0,0.4)"
  },
  title: {
    marginBottom: "12px"
  },
  text: {
    color: "#d1d5db"
  },
  small: {
    fontSize: "12px",
    color: "#9ca3af",
    wordBreak: "break-all"
  },
  button: {
    marginTop: "20px",
    padding: "12px 18px",
    borderRadius: "10px",
    border: "none",
    background: "#2563eb",
    color: "white",
    fontWeight: "bold"
  },
  link: {
    display: "block",
    marginTop: "20px",
    color: "#38bdf8",
    textDecoration: "none"
  }
};
