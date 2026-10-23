import { useState } from "react"
import { Stars, Skyline } from "./Scenery"

const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "")

// palette pulled from the cover art
const C = {
  cream: "#ffecc8",
  creamGlow: "#f7c568",
  blue: "#bcdcfa",
  blueGlow: "#4a90e2",
  butter: "#efe7a5",
  panel: "#101c29",
  field: "#0b1520",
  line: "#22354b",
  text: "#e6edf5",
  muted: "#8a9db3",
}

const s = {
  page: { position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", padding: "64px 16px 0" },
  header: { textAlign: "center", marginBottom: "40px" },
  titleTop: { display: "block", fontFamily: "'Cherry Bomb One', sans-serif", fontWeight: 400, fontSize: "clamp(44px, 9vw, 64px)", lineHeight: 1, color: C.cream, textShadow: `0 0 6px ${C.creamGlow}aa, 0 0 22px ${C.creamGlow}55`, transform: "rotate(-3deg)" },
  titleBottom: { display: "block", fontFamily: "'Cherry Bomb One', sans-serif", fontWeight: 400, fontSize: "clamp(64px, 14vw, 104px)", lineHeight: 1.05, color: C.blue, textShadow: `0 0 8px ${C.blueGlow}aa, 0 0 28px ${C.blueGlow}66`, marginTop: "-4px" },
  subtitle: { fontSize: "16px", color: C.muted, marginTop: "18px", fontWeight: "600" },

  card: { background: C.panel, border: `1px solid ${C.line}`, borderRadius: "18px", boxShadow: "0 16px 40px rgba(0,0,0,0.35)", padding: "clamp(18px, 5vw, 28px)", width: "100%", maxWidth: "600px", marginBottom: "20px" },

  label: { display: "block", fontSize: "13px", fontWeight: "700", color: C.muted, marginBottom: "8px" },
  input: { width: "100%", padding: "12px 14px", border: `1px solid ${C.line}`, background: C.field, borderRadius: "10px", fontSize: "15px", color: C.text, outline: "none", transition: "border-color 0.15s, box-shadow 0.15s", fontFamily: "inherit" },

  row: { display: "flex", gap: "12px", marginTop: "18px" },
  budgetWrap: { flex: "0 0 160px" },

  btn: { width: "100%", padding: "13px", borderRadius: "10px", border: "none", cursor: "pointer", fontSize: "15px", fontWeight: "800", fontFamily: "inherit" },
  btnPrimary: { background: C.cream, color: "#1a1408", boxShadow: "inset 0 -3px 0 #e2c48a" },
  btnSuccess: { background: C.blue, color: "#0b1724", boxShadow: "inset 0 -3px 0 #8db8e3" },
  btnSm: { padding: "8px 18px", fontSize: "13px", borderRadius: "8px", border: "none", cursor: "pointer", fontWeight: "700", fontFamily: "inherit" },

  error: { background: "#2a1418", border: "1px solid #5c2a33", color: "#ffb3bf", borderRadius: "10px", padding: "11px 14px", fontSize: "14px", marginTop: "14px" },
  success: { background: "#11261f", border: "1px solid #24503f", color: "#a8f0d6", borderRadius: "10px", padding: "11px 14px", fontSize: "14px", marginTop: "14px" },

  resultsHeader: { display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "8px", marginBottom: "14px" },
  resultsTitle: { fontSize: "18px", fontWeight: "800", color: C.text },
  count: { fontSize: "13px", fontWeight: "600", color: C.muted },

  listingCard: { padding: "14px 2px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", borderTop: `1px solid ${C.line}` },
  listingLeft: { flex: 1, minWidth: 0 },
  listingName: { fontWeight: "700", fontSize: "15px", color: C.text, lineHeight: 1.35 },
  listingArea: { fontSize: "13px", color: C.muted, marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  listingRight: { display: "flex", alignItems: "center", gap: "14px", flexShrink: 0 },
  price: { fontWeight: "800", fontSize: "15px", color: C.butter, fontVariantNumeric: "tabular-nums" },
  viewBtn: { color: C.blue, fontSize: "13px", fontWeight: "700", textDecoration: "none", whiteSpace: "nowrap" },

  emailSection: { marginTop: "6px", paddingTop: "20px", borderTop: `1px solid ${C.line}` },
  segment: { display: "inline-flex", padding: "3px", background: C.field, border: `1px solid ${C.line}`, borderRadius: "10px", marginBottom: "12px" },
  emailRow: { display: "flex", flexWrap: "wrap", gap: "10px" },

  spinner: { display: "inline-block", width: "16px", height: "16px", border: "2px solid rgba(0,0,0,0.2)", borderTopColor: "currentColor", borderRadius: "50%", animation: "spin 0.7s linear infinite", marginRight: "8px", verticalAlign: "-3px" },
  empty: { textAlign: "center", color: C.muted, padding: "28px 0 12px", fontSize: "15px", lineHeight: 1.6, borderTop: `1px solid ${C.line}` },
}

export default function App() {
  const [url, setUrl]               = useState("")
  const [budget, setBudget]         = useState("")
  const [loading, setLoading]       = useState(false)
  const [listings, setListings]     = useState(null)
  const [error, setError]           = useState("")
  const [email, setEmail]             = useState("")
  const [frequency, setFrequency]     = useState("once")
  const [sending, setSending]         = useState(false)
  const [emailSent, setEmailSent]     = useState(false)
  const [subscribed, setSubscribed]   = useState(false)
  const [emailError, setEmailError]   = useState("")

  const handleSearch = async () => {
    if (!url || !budget) return
    setLoading(true)
    setError("")
    setListings(null)
    setEmailSent(false)
    setEmailError("")
    try {
      const res = await fetch(`${API}/scrape`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, budget: parseFloat(budget) }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Something went wrong")
      setListings(data.listings)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEmail = async () => {
    if (!email) return
    setSending(true)
    setEmailError("")
    try {
      if (frequency === "once") {
        const res = await fetch(`${API}/email`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ listings, budget: parseFloat(budget), site_url: url, email }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || "Failed to send email")
        setEmailSent(true)
      } else {
        const res = await fetch(`${API}/subscribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, site_url: url, budget: parseFloat(budget), frequency }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || "Failed to subscribe")
        setSubscribed(true)
      }
    } catch (e) {
      setEmailError(e.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <Stars />

      <div style={s.page}>
        {/* Header */}
        <div style={s.header}>
          <h1 aria-label="Live With Ease">
            <span style={s.titleTop}>live with</span>
            <span style={s.titleBottom}>ease</span>
          </h1>
          <p style={s.subtitle}>Toronto rentals that actually fit your budget.</p>
        </div>

        {/* Search card */}
        <div style={s.card}>
          <div>
            <label style={s.label}>Rental site URL</label>
            <input
              style={s.input}
              type="url"
              placeholder="https://www.zumper.com/apartments-for-rent/toronto-on"
              value={url}
              onChange={e => setUrl(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSearch()}
            />
          </div>

          <div style={s.row}>
            <div style={{ flex: 1 }}>
              <label style={s.label}>Monthly budget (CAD)</label>
              <input
                style={s.input}
                type="number"
                placeholder="2000"
                value={budget}
                onChange={e => setBudget(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSearch()}
              />
            </div>
          </div>

          <div style={{ marginTop: "20px" }}>
            <button
              style={{ ...s.btn, ...s.btnPrimary, opacity: loading || !url || !budget ? 0.7 : 1 }}
              onClick={handleSearch}
              disabled={loading || !url || !budget}
            >
              {loading && <span style={s.spinner} />}
              {loading ? "Searching…" : "Search listings"}
            </button>
          </div>

          {error && <div style={s.error}>{error}</div>}
        </div>

        {/* Results card */}
        {listings !== null && (
          <div style={s.card}>
            <div style={s.resultsHeader}>
              <span style={s.resultsTitle}>Under ${parseFloat(budget).toLocaleString()}/mo</span>
              <span style={s.count}>{listings.length} listing{listings.length !== 1 ? "s" : ""}</span>
            </div>

            {listings.length === 0 ? (
              <div style={s.empty}>Nothing under ${parseFloat(budget).toLocaleString()}/mo.<br />Try a different site or raise your budget.</div>
            ) : (
              listings.map((apt, i) => (
                <div key={i} className="listing-card" style={s.listingCard}>
                  <div style={s.listingLeft}>
                    <div style={s.listingName}>{apt.building}</div>
                    {apt.area && <div style={s.listingArea}>{apt.area}</div>}
                  </div>
                  <div style={s.listingRight}>
                    <span style={s.price}>${apt.price.toLocaleString()}/mo</span>
                    <a href={apt.url} target="_blank" rel="noreferrer" className="view-btn" style={s.viewBtn}>View ↗</a>
                  </div>
                </div>
              ))
            )}

            {/* Email section */}
            {listings.length > 0 && (
              <div style={s.emailSection}>
                <label style={s.label}>Email me these results</label>

                {/* Frequency tabs */}
                <div style={s.segment}>
                  {[["once", "Send once"], ["weekly", "Weekly"], ["monthly", "Monthly"]].map(([val, label]) => (
                    <button key={val} onClick={() => { setFrequency(val); setEmailSent(false); setSubscribed(false); setEmailError("") }}
                      style={{ padding: "6px 14px", borderRadius: "7px", border: "none",
                        background: frequency === val ? C.line : "transparent",
                        color: frequency === val ? C.text : C.muted,
                        fontWeight: "700", fontSize: "13px", cursor: "pointer", fontFamily: "inherit" }}>
                      {label}
                    </button>
                  ))}
                </div>

                <div style={s.emailRow}>
                  <input
                    style={{ ...s.input, flex: "1 1 200px" }}
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleEmail()}
                  />
                  <button
                    style={{ ...s.btn, ...s.btnSuccess, width: "auto", flex: "0 0 auto", padding: "12px 22px", opacity: sending || !email ? 0.7 : 1 }}
                    onClick={handleEmail}
                    disabled={sending || !email}
                  >
                    {sending && <span style={s.spinner} />}
                    {sending ? (frequency === "once" ? "Sending…" : "Subscribing…") : (frequency === "once" ? "Send" : "Subscribe")}
                  </button>
                </div>

                {emailSent   && <div style={s.success}>Sent. Check your inbox.</div>}
                {subscribed  && <div style={s.success}>You're subscribed to {frequency} updates. Every email has an unsubscribe link.</div>}
                {emailError  && <div style={s.error}>{emailError}</div>}
              </div>
            )}
          </div>
        )}

        <div style={{ flex: 1, minHeight: "40px" }} />
        <Skyline />
      </div>
    </>
  )
}
