import { useState } from "react";
import axios from "axios";
import { startRegistration } from "@simplewebauthn/browser";

function getApiUrl() {
  return `${window.location.origin}/api`;
}

export default function RegisterPasskey() {
  const [status, setStatus] = useState("Ready to register this phone as a passkey.");

  async function registerPasskey() {
    try {
      setStatus("Requesting registration challenge...");

      const apiUrl = getApiUrl();
      const optionsResponse = await axios.post(`${apiUrl}/auth/webauthn/register/options`);

      setStatus("Use Face ID / Touch ID / screen lock to create your passkey...");

      const attestationResponse = await startRegistration({ optionsJSON: optionsResponse.data });

      setStatus("Verifying passkey with backend...");

      await axios.post(`${apiUrl}/auth/webauthn/register/verify`, attestationResponse);

      setStatus("Passkey registered successfully. You can now use QR biometric login.");
    } catch (error) {
      console.error(error);
      setStatus(error?.response?.data?.detail || "Passkey registration failed or was cancelled.");
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1>Register Phone Passkey</h1>

        <p style={styles.text}>
          This registers your phone browser for Face ID / fingerprint login.
        </p>

        <button style={styles.button} onClick={registerPasskey}>
          Register this phone
        </button>

        <p style={styles.status}>{status}</p>

        <a href="/login-qr" style={styles.link}>
          Go to QR login
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
    width: "420px",
    textAlign: "center",
    boxShadow: "0 20px 40px rgba(0,0,0,0.4)"
  },
  text: {
    color: "#d1d5db"
  },
  button: {
    marginTop: "20px",
    padding: "12px 18px",
    borderRadius: "10px",
    border: "none",
    background: "#16a34a",
    color: "white",
    fontWeight: "bold"
  },
  status: {
    marginTop: "20px",
    color: "#cbd5e1"
  },
  link: {
    display: "inline-block",
    marginTop: "20px",
    color: "#38bdf8",
    textDecoration: "none"
  }
};
