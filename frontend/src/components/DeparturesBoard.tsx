import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'

// An airport "departures board" of real products: one flight per category, plus
// "LAST CALL" for the items with the least stock. Prices and status come from the
// live catalogue; letters flip into place like a split-flap board.

interface Flight {
  product: Product
  flight: string
  status: 'BOARDING' | 'LAST CALL' | 'ON TIME'
}

const FAMILIES: { label: string; test: (g: string) => boolean }[] = [
  { label: 'hoodie', test: (g) => g.includes('hood') },
  { label: 'crewneck', test: (g) => g.includes('crewneck') },
  { label: 'tee', test: (g) => g.includes('t-shirt') },
  { label: 'quarter-zip', test: (g) => g.includes('quarter-zip') },
  { label: 'fleece', test: (g) => g.includes('fleece') || g.includes('jacket') },
]

function flightNo(id: string): string {
  let h = 0
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return `CC${100 + (h % 900)}`
}

function pickFlights(products: Product[]): Flight[] {
  const used = new Set<string>()
  const flights: Flight[] = []
  // Last call: the two items closest to selling out (but not sold out).
  for (const p of [...products].filter((p) => p.total_stock > 0).sort((a, b) => a.total_stock - b.total_stock).slice(0, 2)) {
    used.add(p.product_id)
    flights.push({ product: p, flight: flightNo(p.product_id), status: 'LAST CALL' })
  }
  // Boarding: the best-stocked item in each category.
  for (const fam of FAMILIES) {
    const best = products
      .filter((p) => fam.test(p.garment_type.toLowerCase()) && !used.has(p.product_id))
      .sort((a, b) => b.total_stock - a.total_stock)[0]
    if (best) {
      used.add(best.product_id)
      flights.push({ product: best, flight: flightNo(best.product_id), status: best.total_stock > 40 ? 'BOARDING' : 'ON TIME' })
    }
  }
  return flights
}

function Flap({ text, delay }: { text: string; delay: number }) {
  return (
    <span className="flaps" aria-label={text}>
      {text.split('').map((ch, i) => (
        <span key={i} className="flap" style={{ animationDelay: `${delay + i * 35}ms` }} aria-hidden="true">
          {ch === ' ' ? ' ' : ch}
        </span>
      ))}
    </span>
  )
}

function zulu(): string {
  const d = new Date()
  return `${String(d.getUTCHours()).padStart(2, '0')}${String(d.getUTCMinutes()).padStart(2, '0')}Z`
}

export default function DeparturesBoard() {
  const [flights, setFlights] = useState<Flight[]>([])
  const [clock, setClock] = useState(zulu())

  useEffect(() => {
    fetchProducts().then((p) => setFlights(pickFlights(p))).catch(() => setFlights([]))
    const t = setInterval(() => setClock(zulu()), 30000)
    return () => clearInterval(t)
  }, [])

  if (!flights.length) return null

  return (
    <section className="departures" aria-label="Departures board: featured products">
      <div className="departures-head">
        <span className="dep-title">✈ DEPARTURES</span>
        <span className="dep-meta">NEW HAVEN · HVN · GATE 57 BROADWAY</span>
        <span className="dep-clock">{clock}</span>
      </div>
      <div className="dep-row dep-labels" aria-hidden="true">
        <span>FLIGHT</span>
        <span>DESTINATION</span>
        <span>FARE</span>
        <span>STATUS</span>
      </div>
      {flights.map((f, row) => (
        <Link to={`/products/${f.product.product_id}`} className="dep-row" key={f.product.product_id}>
          <span className="dep-flight"><Flap text={f.flight} delay={row * 120} /></span>
          <span className="dep-dest"><Flap text={f.product.name.toUpperCase().slice(0, 28)} delay={row * 120 + 150} /></span>
          <span className="dep-fare"><Flap text={`$${f.product.price.toFixed(0)}`} delay={row * 120 + 300} /></span>
          <span className={`dep-status ${f.status === 'LAST CALL' ? 'last' : f.status === 'BOARDING' ? 'boarding' : ''}`}>
            {f.status}
            {f.status === 'LAST CALL' && <small> · {f.product.total_stock} left</small>}
          </span>
        </Link>
      ))}
      <p className="dep-foot">Fares and stock are live from our stockroom. Tap a flight to board.</p>
    </section>
  )
}
