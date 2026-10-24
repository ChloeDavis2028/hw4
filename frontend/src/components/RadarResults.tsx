import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { formatPrice } from '../api'
import { useChatResults } from '../chatResults'

// Product cards Chloe found, shown on the page as "radar contacts".
// Each card plays the product's promo reel and opens the item page when clicked.
// The panel folds into a slim bar when the shopper flies to another page, so the
// page they chose stays in view; one tap reopens it.
export default function RadarResults() {
  const { cards, question, clear } = useChatResults()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(true)
  const ref = useRef<HTMLElement>(null)

  // New contacts from Chloe: open the panel and bring it into view.
  useEffect(() => {
    if (!cards.length) return
    setOpen(true)
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [cards])

  // Flying to another page: fold the panel away.
  useEffect(() => {
    setOpen(false)
  }, [pathname])

  if (!cards.length) return null

  const count = `${cards.length} ${cards.length === 1 ? 'match' : 'matches'}`

  if (!open) {
    return (
      <section className="radar radar-folded" ref={ref}>
        <p className="radar-eyebrow">📡 {count} on radar for “{question}”</p>
        <div className="radar-actions">
          <button className="radar-close" onClick={() => setOpen(true)}>Show Contacts</button>
          <button className="radar-close" onClick={clear} aria-label="Clear radar contacts">Clear ×</button>
        </div>
      </section>
    )
  }

  return (
    <section className="radar" ref={ref} aria-live="polite">
      <div className="radar-head">
        <div>
          <p className="radar-eyebrow">📡 Radar Contacts from Chloe</p>
          <h2>
            {count} for “{question}”
          </h2>
        </div>
        <div className="radar-actions">
          <button className="radar-close" onClick={() => setOpen(false)}>Fold</button>
          <button className="radar-close" onClick={clear} aria-label="Clear radar contacts">Clear Radar ×</button>
        </div>
      </div>
      <div className="radar-grid">
        {cards.map((c, i) => (
          <Link to={c.detail_url} className="radar-card" key={c.product_id} style={{ animationDelay: `${i * 70}ms` }}>
            <div className="radar-reel">
              <img src={c.reel_url} alt={`Promo reel: ${c.name}`} loading="lazy" />
              <span className="radar-price">{formatPrice(c.price)}</span>
            </div>
            <div className="radar-body">
              <h3>{c.fun_name}</h3>
              <p className="real-name">{c.name}</p>
              <p className="radar-info">{c.short_info}</p>
              <p className="radar-sizes">
                {c.sizes_in_stock.length ? `In stock: ${c.sizes_in_stock.join(' · ')}` : 'Sold out in every size'}
              </p>
              <span className="card-cta">✈ Fly In for a Closer Look →</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
