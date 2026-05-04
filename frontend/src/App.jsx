import { useState } from "react"

const API = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "")

const s = {
  page: { minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", padding: "48px 16px" },
  header: { textAlign: "center", marginBottom: "40px" },
  logo: { fontSize: "36px", marginBottom: "8px" },
  title: { fontSize: "28px", fontWeight: "700", color: "#1e40af", letterSpacing: "-0.5px" },
  subtitle: { fontSize: "15px", color: "#64748b", marginTop: "6px" },

  card: { background: "#fff", borderRadius: "16px", boxShadow: "0 2px 20px rgba(0,0,0,0.08)", padding: "32px", width: "100%", maxWidth: "640px", marginBottom: "24px" },

  label: { display: "block", fontSize: "13px", fontWeight: "600", color: "#374151", marginBottom: "6px" },
  input: { width: "100%", padding: "10px 14px", border: "1.5px solid #e2e8f0", borderRadius: "8px", fontSize: "14px", outline: "none", transition: "border 0.15s", fontFamily: "inherit" },

  row: { display: "flex", gap: "12px", marginTop: "16px" },
  budgetWrap: { flex: "0 0 160px" },

  btn: { width: "100%", padding: "12px", borderRadius: "8px", border: "none", cursor: "pointer", fontSize: "15px", fontWeight: "600", transition: "opacity 0.15s, transform 0.1s", fontFamily: "inherit" },
  btnPrimary: { background: "#2563eb", color: "#fff" },
  btnSuccess: { background: "#16a34a", color: "#fff" },
  btnSm: { padding: "8px 18px", fontSize: "13px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: "600", fontFamily: "inherit" },

  error: { background: "#fef2f2", border: "1px solid #fecaca", color: "#dc2626", borderRadius: "8px", padding: "12px 16px", fontSize: "14px", marginTop: "12px" },
  success: { background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#16a34a", borderRadius: "8px", padding: "12px 16px", fontSize: "14px", marginTop: "12px" },

  resultsHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" },
  resultsTitle: { fontSize: "17px", fontWeight: "700" },
  count: { fontSize: "13px", color: "#64748b", background: "#f1f5f9", padding: "4px 10px", borderRadius: "99px" },

  listingCard: { border: "1.5px solid #e2e8f0", borderRadius: "10px", padding: "16px", marginBottom: "10px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", transition: "border-color 0.15s" },
  listingLeft: { flex: 1, minWidth: 0 },
  listingName: { fontWeight: "600", fontSize: "15px", color: "#1e293b", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  listingArea: { fontSize: "13px", color: "#64748b", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  listingRight: { display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px", flexShrink: 0 },
  price: { fontWeight: "700", fontSize: "16px", color: "#16a34a" },
  viewBtn: { background: "#eff6ff", color: "#2563eb", padding: "5px 12px", borderRadius: "6px", fontSize: "13px", fontWeight: "600", textDecoration: "none", whiteSpace: "nowrap" },

  emailSection: { marginTop: "8px", paddingTop: "20px", borderTop: "1px solid #e2e8f0" },
  emailRow: { display: "flex", gap: "10px", marginTop: "10px" },

  spinner: { display: "inline-block", width: "18px", height: "18px", border: "3px solid rgba(255,255,255,0.4)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.7s linear infinite", marginRight: "8px", verticalAlign: "middle" },
  empty: { textAlign: "center", color: "#94a3b8", padding: "32px 0", fontSize: "15px" },
}

export default function App() {
  const [url, setUrl]               = useState("")
  const [budget, setBudget]         = useState("")
  const [loading, setLoading]       = useState(false)
  const [listings, setListings]     = useState(null)
  const [error, setError]           = useState("")
  const [email, setEmail]           = useState("")
  const [sending, setSending]       = useState(false)
  const [emailSent, setEmailSent]   = useState(false)
  const [emailError, setEmailError] = useState("")

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
      const res = await fetch(`${API}/email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listings, budget: parseFloat(budget), site_url: url, email }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Failed to send email")
      setEmailSent(true)
    } catch (e) {
      setEmailError(e.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        input:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
        .listing-card:hover { border-color: #93c5fd !important; }
        button:active { transform: scale(0.98); }
      `}</style>

      <div style={s.page}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.logo}>🏠</div>
          <h1 style={s.title}>live-with-ease</h1>
          <p style={s.subtitle}>Find Toronto rentals within your budget, powered by AI</p>
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

          {error && <div style={s.error}>⚠️ {error}</div>}
        </div>

        {/* Results card */}
        {listings !== null && (
          <div style={s.card}>
            <div style={s.resultsHeader}>
              <span style={s.resultsTitle}>Results</span>
              <span style={s.count}>{listings.length} listing{listings.length !== 1 ? "s" : ""} found</span>
            </div>

            {listings.length === 0 ? (
              <div style={s.empty}>No listings found under ${parseFloat(budget).toLocaleString()}/mo.<br />Try a different site or raise your budget.</div>
            ) : (
              listings.map((apt, i) => (
                <div key={i} className="listing-card" style={s.listingCard}>
                  <div style={s.listingLeft}>
                    <div style={s.listingName}>{apt.building}</div>
                    {apt.area && <div style={s.listingArea}>📍 {apt.area}</div>}
                  </div>
                  <div style={s.listingRight}>
                    <span style={s.price}>${apt.price.toLocaleString()}/mo</span>
                    <a href={apt.url} target="_blank" rel="noreferrer" style={s.viewBtn}>View →</a>
                  </div>
                </div>
              ))
            )}

            {/* Email section */}
            {listings.length > 0 && (
              <div style={s.emailSection}>
                <label style={s.label}>Email these results to yourself</label>
                <div style={s.emailRow}>
                  <input
                    style={{ ...s.input, flex: 1 }}
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleEmail()}
                  />
                  <button
                    style={{ ...s.btn, ...s.btnSuccess, width: "auto", padding: "10px 20px", fontSize: "14px", opacity: sending || !email ? 0.7 : 1 }}
                    onClick={handleEmail}
                    disabled={sending || !email}
                  >
                    {sending && <span style={s.spinner} />}
                    {sending ? "Sending…" : "Send"}
                  </button>
                </div>
                {emailSent  && <div style={s.success}>✅ Email sent! Check your inbox.</div>}
                {emailError && <div style={s.error}>⚠️ {emailError}</div>}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
