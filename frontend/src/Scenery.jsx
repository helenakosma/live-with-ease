// Night sky + Toronto skyline backdrop, matching the cover art.
// Everything is generated from a fixed seed so the scene is identical on every load.

const INK = "#05080c"
const SLATE = "#8ea6c1"
const BUTTER = "#efe7a5"
const CREAM = "#ffecc8"

function seeded(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/* ---------- stars ---------- */

const STAR_COLORS = [CREAM, "#ffffff", "#bcdcfa", "#f3d98b"]
const STARS = (() => {
  const r = seeded(7)
  return Array.from({ length: 170 }, () => ({
    left: `${(r() * 100).toFixed(2)}%`,
    top: `${(r() * 72).toFixed(2)}%`,
    size: 4 + r() * 6,
    color: STAR_COLORS[Math.floor(r() * STAR_COLORS.length)],
    opacity: 0.45 + r() * 0.55,
    twinkle: r() < 0.3,
    delay: `${(r() * 6).toFixed(2)}s`,
    duration: `${(3 + r() * 4).toFixed(2)}s`,
  }))
})()

export function Stars() {
  return (
    <div className="stars" aria-hidden="true">
      {STARS.map((st, i) => (
        <span
          key={i}
          className={st.twinkle ? "star twinkle" : "star"}
          style={{ left: st.left, top: st.top, fontSize: st.size, color: st.color, opacity: st.opacity, animationDelay: st.delay, animationDuration: st.duration }}
        >★</span>
      ))}
    </div>
  )
}

/* ---------- skyline ---------- */

const W = 1440
const H = 320
const CN_X = 760          // kept near the centre so it survives the crop on phones
const DOME = [600, 730]   // Rogers Centre sits at the CN Tower's feet, like the real thing

const rect = (x, y, w, h) => `M${x} ${y}h${w}v${h}h${-w}Z`

const LAYERS = [
  { fill: INK,    seed: 3, minW: 40, maxW: 95, minH: 120, maxH: 235, win: "#132131", lit: CREAM,     litP: 0.05, winP: 0.5 },
  { fill: SLATE,  seed: 5, minW: 34, maxW: 80, minH: 70,  maxH: 165, win: "#7690ad", lit: CREAM,     litP: 0.12, winP: 0.75 },
  { fill: BUTTER, seed: 9, minW: 40, maxW: 92, minH: 30,  maxH: 105, win: "#d9ce86", lit: "#fff8d8", litP: 0.08, winP: 0.7 },
]

const ROOFS = {
  0: ["flat", "setback", "setback", "spire", "antenna", "slant"],
  1: ["flat", "setback", "spire", "antenna", "slant", "tank", "dome"],
  2: ["flat", "flat", "peak", "tank", "setback", "antenna", "dome"],
}

function buildLayer(index) {
  const L = LAYERS[index]
  const r = seeded(L.seed)
  const between = (a, b) => a + r() * (b - a)
  const pick = arr => arr[Math.floor(r() * arr.length)]

  let body = "", win = "", lit = ""

  const windows = (x, top, w, h) => {
    if (h < 40 || r() > L.winP) return
    if (r() < 0.25) {
      // curtain-wall stripes
      for (let cx = x + 5; cx < x + w - 5; cx += 7) win += rect(cx, top + 8, 2, h - 8)
      return
    }
    const cols = Math.floor((w - 8) / 9), rows = Math.floor((h - 12) / 12)
    const offset = (w - cols * 9 + 4) / 2
    for (let c = 0; c < cols; c++) for (let rw = 0; rw < rows; rw++) {
      const shape = rect(x + offset + c * 9, top + 10 + rw * 12, 4, 6)
      if (r() < L.litP) lit += shape
      else win += shape
    }
  }

  let x = -12
  while (x < W + 12) {
    if (index === 2 && x >= DOME[0] - 20 && x < DOME[1]) {
      // Rogers Centre: low drum with a ribbed dome
      const [a, b] = DOME, mid = (a + b) / 2, top = H - 38
      body += rect(a, top, b - a, 38)
      body += `M${a} ${top}Q${mid} ${top - 46} ${b} ${top}Z`
      for (let i = 1; i < 6; i++) win += rect(a + ((b - a) / 6) * i - 1, top + 6, 2, 26)
      x = b
      continue
    }

    const w = Math.round(between(L.minW, L.maxW))
    let h = Math.round(between(L.minH, L.maxH))
    if (index === 0 && Math.abs(x + w / 2 - CN_X) < 70) h = Math.min(h, 150) // keep the CN Tower pod clear
    const top = H - h
    const roof = pick(ROOFS[index])

    body += rect(x, top, w, h)
    windows(x, top, w, h)

    if (roof === "flat") {
      body += rect(x - 2, top - 3, w + 4, 3)
    } else if (roof === "setback" || roof === "spire") {
      const w2 = Math.round(w * between(0.5, 0.75)), h2 = Math.round(between(12, 34))
      const x2 = x + (w - w2) / 2
      body += rect(x2, top - h2, w2, h2)
      let peak = top - h2
      if (r() < 0.6) {
        const w3 = Math.round(w2 * 0.55), h3 = Math.round(between(8, 20))
        body += rect(x + (w - w3) / 2, peak - h3, w3, h3)
        peak -= h3
      }
      if (roof === "spire") {
        const s = between(25, 55), m = x + w / 2
        body += `M${m - 3} ${peak}L${m} ${peak - s}L${m + 3} ${peak}Z`
      }
    } else if (roof === "antenna") {
      const ax = x + w * between(0.25, 0.75), ah = between(18, 42)
      body += rect(ax, top - ah, 2, ah) + rect(ax - 3, top - ah * 0.55, 8, 3)
    } else if (roof === "slant") {
      const rise = w * between(0.2, 0.45)
      body += r() < 0.5 ? `M${x} ${top}L${x} ${top - rise}L${x + w} ${top}Z` : `M${x} ${top}L${x + w} ${top - rise}L${x + w} ${top}Z`
    } else if (roof === "peak") {
      body += `M${x - 2} ${top}L${x + w / 2} ${top - w * 0.32}L${x + w + 2} ${top}Z`
    } else if (roof === "tank") {
      const tx = x + w * between(0.2, 0.55)
      body += rect(tx + 1, top - 8, 2, 8) + rect(tx + 11, top - 8, 2, 8)  // legs
      body += rect(tx, top - 20, 14, 12)                                // barrel
      body += `M${tx - 1} ${top - 20}L${tx + 7} ${top - 26}L${tx + 15} ${top - 20}Z`
    } else if (roof === "dome") {
      const dw = w * 0.6, dx = x + (w - dw) / 2
      body += `M${dx} ${top}Q${x + w / 2} ${top - dw * 0.7} ${dx + dw} ${top}Z` + rect(x + w / 2 - 1, top - dw * 0.42 - 8, 2, 8)
    }

    x += w + (r() < 0.2 ? -6 : 0)
  }

  return { body, win, lit, L }
}

function cnTower() {
  const c = CN_X
  return [
    `M${c - 10} ${H}L${c - 4.5} 118L${c + 4.5} 118L${c + 10} ${H}Z`, // main shaft
    `M${c - 4} 104L${c - 2.6} 74L${c + 2.6} 74L${c + 4} 104Z`,       // upper shaft
    `M${c - 21} 110Q${c} 122 ${c + 21} 110L${c + 16} 98Q${c} 92 ${c - 16} 98Z`, // main pod
    rect(c - 23, 108, 46, 3),                                          // observation deck ring
    `M${c - 7} 76Q${c} 80 ${c + 7} 76L${c + 5} 71Q${c} 69 ${c - 5} 71Z`,          // SkyPod
    `M${c - 1.8} 71L${c - 0.6} 10L${c + 0.6} 10L${c + 1.8} 71Z`,      // antenna
  ].join("")
}

const LAYER_DATA = LAYERS.map((_, i) => buildLayer(i))
const CN = cnTower()

export function Skyline() {
  return (
    <svg className="skyline" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMax slice" aria-hidden="true">
      <defs>
        <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4a90e2" stopOpacity="0" />
          <stop offset="1" stopColor="#4a90e2" stopOpacity="0.18" />
        </linearGradient>
      </defs>
      <rect x="0" y="60" width={W} height={H - 60} fill="url(#horizon)" />

      <path d={CN} fill={INK} />
      <circle cx={CN_X} cy="10" r="2" fill="#ff8a7a" className="beacon" />

      {LAYER_DATA.map(({ body, win, lit, L }, i) => (
        <g key={i}>
          <path d={body} fill={L.fill} />
          <path d={win} fill={L.win} />
          <path d={lit} fill={L.lit} />
        </g>
      ))}
      <rect x="0" y={H - 14} width={W} height="14" fill={BUTTER} />
    </svg>
  )
}
