import { useEffect, useState } from "react";
import "./Backendstatus.css";

// Keep in sync with the url in Nav.jsx and Container.jsx
const url = "https://pdfai-backend-h0cb.onrender.com";
//const url = "http://127.0.0.1:8000";

const SHOW_AFTER_MS = 1000; // don't flash the banner if the backend answers quickly
const RETRY_MS = 3000; // wait between attempts while Render is waking up
const ATTEMPT_TIMEOUT_MS = 10000; // give up on a single hanging request
const READY_VISIBLE_MS = 1500; // how long "ready" stays on screen

// Pings the backend until it responds. Render's free tier sleeps when idle,
// so the first request after a while can take a minute.
function Backendstatus() {
  const [status, setStatus] = useState("idle"); // idle | waiting | ready

  useEffect(() => {
    let cancelled = false;
    let bannerShown = false;
    let showTimer;
    let retryTimer;
    let hideTimer;

    showTimer = setTimeout(() => {
      if (cancelled) return;
      bannerShown = true;
      setStatus("waiting");
    }, SHOW_AFTER_MS);

    const ping = async () => {
      const controller = new AbortController();
      const abortTimer = setTimeout(() => controller.abort(), ATTEMPT_TIMEOUT_MS);
      try {
        const res = await fetch(url + "/", { signal: controller.signal });
        if (!res.ok) throw new Error("Backend not ready");
        if (cancelled) return;
        clearTimeout(showTimer);
        if (bannerShown) {
          setStatus("ready");
          hideTimer = setTimeout(() => setStatus("idle"), READY_VISIBLE_MS);
        } else {
          setStatus("idle");
        }
      } catch {
        if (!cancelled) retryTimer = setTimeout(ping, RETRY_MS);
      } finally {
        clearTimeout(abortTimer);
      }
    };

    ping();

    return () => {
      cancelled = true;
      clearTimeout(showTimer);
      clearTimeout(retryTimer);
      clearTimeout(hideTimer);
    };
  }, []);

  if (status === "idle") return null;

  return (
    <div className={`backend-status ${status}`} role="status" aria-live="polite">
      {status === "waiting" ? (
        <>
          <span className="backend-spinner" aria-hidden="true"></span>
          Render backend is starting, please wait...
        </>
      ) : (
        "Backend is ready"
      )}
    </div>
  );
}

export default Backendstatus;