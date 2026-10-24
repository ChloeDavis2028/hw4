import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, formatPrice, type Product } from '../api'
import DanBadge from '../components/DanBadge'

// Number of color themes defined as .theme-0 ... .theme-5 in index.css
const CARD_THEMES = 6
const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

// Flight search (usability F1): category chips map onto the catalogue's messy garment_type labels.
const CATEGORIES: { label: string; test: (g: string) => boolean }[] = [
  { label: 'Hoodies', test: (g) => g.includes('hood') },
  { label: 'Crewnecks', test: (g) => g.includes('crewneck') },
  { label: 'Tees', test: (g) => g.includes('t-shirt') },
  { label: 'Quarter-Zips', test: (g) => g.includes('quarter-zip') },
  { label: 'Fleece & Jackets', test: (g) => g.includes('fleece') || g.includes('jacket') },
  { label: 'Long-Sleeve & More', test: (g) => g.includes('long-sleeve') || g.includes('mockneck') },
]

// Lowercase text a shopper might search for, with "1 4 zip" spelled the way people say it.
function searchText(p: Product): string {
  return [p.name, p.fun_name, p.garment_type, p.colors.join(' '), p.search_tags.join(' ')]
    .join(' ')
    .toLowerCase()
    .replace(/\b1 4 zip\b/g, 'quarter zip 1/4 zip')
}

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string | null>(null)
  const [under40, setUnder40] = useState(false)
  const [size, setSize] = useState('')

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const shown = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    const cat = CATEGORIES.find((c) => c.label === category)
    return products.filter((p) => {
      const g = p.garment_type.toLowerCase()
      if (cat && !cat.test(g)) return false
      if (under40 && p.price >= 40) return false
      if (size && !p.inventory.some((s) => s.size === size && s.quantity > 0)) return false
      const text = searchText(p)
      return words.every((w) => text.includes(w))
    })
  }, [products, query, category, under40, size])

  const filtering = Boolean(query || category || under40 || size)
  function clearAll() {
    setQuery('')
    setCategory(null)
    setUnder40(false)
    setSize('')
  }

  return (
    <section className="section">
      <p className="eyebrow">Products</p>
      <h1>The Whole Bulldog Wardrobe</h1>
      <p className="lede">
        Every piece below comes straight from our catalogue. Prices are pulled live, so what you see is
        what you pay.
      </p>

      {loading && <p className="status">Loading the racks…</p>}
      {error && (
        <p className="status error">
          {error}. Is the backend running? (uvicorn main:app --reload --port 8000)
        </p>
      )}

      {!loading && !error && (
        <>
          <div className="flight-search" role="search">
            <label className="search-box">
              <span aria-hidden="true">🔎</span>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search the hangar: saybrook, bulldog, navy, hockey…"
                aria-label="Search products"
              />
            </label>
            <div className="chip-row" aria-label="Filter by category">
              {CATEGORIES.map((c) => (
                <button
                  key={c.label}
                  className={`chip-btn${category === c.label ? ' on' : ''}`}
                  onClick={() => setCategory(category === c.label ? null : c.label)}
                  aria-pressed={category === c.label}
                >
                  {c.label}
                </button>
              ))}
              <button
                className={`chip-btn value${under40 ? ' on' : ''}`}
                onClick={() => setUnder40(!under40)}
                aria-pressed={under40}
              >
                💸 Under $40
              </button>
              <label className="size-pick">
                In stock in
                <select value={size} onChange={(e) => setSize(e.target.value)} aria-label="Only show sizes in stock">
                  <option value="">any size</option>
                  {SIZES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <p className="count">
            ✈ {shown.length} {filtering ? `of ${products.length} items match` : 'items cleared for takeoff'}
            {filtering && (
              <button className="link-btn" onClick={clearAll}>Clear Filters</button>
            )}
          </p>

          {shown.length === 0 ? (
            <div className="empty-radar">
              <p>📡 No contacts on radar for that search.</p>
              <p>Try fewer filters, or radio Chloe in the corner. She can search by budget, color and size for you.</p>
              <button className="btn btn-gold" onClick={clearAll}>Clear Filters</button>
            </div>
          ) : (
            <div className="product-grid">
              {shown.map((p, i) => (
                <Link
                  to={`/products/${p.product_id}`}
                  className={`product-card theme-${i % CARD_THEMES}`}
                  key={p.product_id}
                  style={{ animationDelay: `${Math.min(i, 12) * 60}ms` }}
                >
                  <div className="product-image">
                    <img src={p.image_url} alt={p.name} loading="lazy" />
                    <DanBadge />
                    <span className="price-tag">{formatPrice(p.price)}</span>
                  </div>
                  <div className="product-body">
                    <h3 className="fun-name">{p.fun_name}</h3>
                    <p className="real-name">{p.name}</p>
                    <p className="blurb">{p.fun_blurb}</p>
                    <span className="card-cta">
                      <span className="cta-plane" aria-hidden="true">✈</span> Fly In for a Closer Look →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
