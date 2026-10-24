import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import DanBadge from '../components/DanBadge'

function stockLabel(quantity: number): string {
  if (quantity === 0) return 'Sold out'
  if (quantity <= 5) return `Only ${quantity} left`
  return `${quantity} left`
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message))
  }, [productId])

  if (error) {
    return (
      <section className="section">
        <p className="status error">{error}.</p>
        <Link to="/products">← Back to all products</Link>
      </section>
    )
  }
  if (!product) return <p className="status section">Loading…</p>

  const available = product.inventory.filter((s) => s.quantity > 0)

  return (
    <section className="section">
      <Link to="/products" className="back-link">← Return to Base: All Products</Link>
      <div className="detail">
        <div className="detail-image">
          <div className="detail-stage">
            <img src={product.image_url} alt={product.name} />
            <DanBadge size="large" />
          </div>
          <p className="dan-caption">✈ Handsome Dan approves this {product.garment_type.toLowerCase()}</p>
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.fun_name}</h1>
          <p className="real-name">{product.name}</p>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="blurb">{product.fun_blurb}</p>

          <h3>Summary</h3>
          <p>{product.description}</p>
          {product.colors.length > 0 && (
            <div className="color-chips">
              {product.colors.map((c) => (
                <span key={c} className="chip">{c}</span>
              ))}
            </div>
          )}

          <h3>Best Way to Wear It</h3>
          <p>{product.best_use}</p>

          {/* Price and sizes presented as a boarding pass (Problem 10 design) */}
          <div className="boarding-pass" aria-label="Boarding pass: price and sizes">
            <div className="bp-main">
              <div className="bp-top">
                <span className="bp-airline">✈ CAMPUS CUSTOMS AIR</span>
                <span className="bp-class">BOARDING PASS</span>
              </div>
              <div className="bp-route">
                <div>
                  <span className="bp-label">FROM</span>
                  <strong>HVN</strong>
                  <span className="bp-sub">57 Broadway</span>
                </div>
                <span className="bp-plane" aria-hidden="true">✈</span>
                <div>
                  <span className="bp-label">TO</span>
                  <strong>YOU</strong>
                  <span className="bp-sub">your closet</span>
                </div>
                <div className="bp-fare">
                  <span className="bp-label">FARE</span>
                  <strong>{formatPrice(product.price)}</strong>
                </div>
              </div>

              <h3>Sizes Available</h3>
              {available.length > 0 ? (
                <p>{available.map((s) => s.size).join(' · ')}</p>
              ) : (
                <p>Sold out in every size right now.</p>
              )}

              <h3>Sizes Left</h3>
              <div className="size-grid">
                {product.inventory.map((s, i) => (
                  <div
                    key={s.size}
                    className={`size-box${s.quantity === 0 ? ' sold-out' : s.quantity <= 5 ? ' low' : ''}`}
                    style={{ animationDelay: `${300 + i * 90}ms` }}
                  >
                    <span className="size-name">{s.size}</span>
                    <span className="size-qty">{stockLabel(s.quantity)}</span>
                  </div>
                ))}
              </div>
              <p className="total-stock">{product.total_stock} in stock across all sizes</p>
            </div>
            <div className="bp-stub" aria-hidden="true">
              <span className="bp-label">FLIGHT</span>
              <strong>{product.product_id.slice(0, 3).toUpperCase()}-{product.inventory.length}{Math.round(product.price)}</strong>
              <span className="bp-label">GATE</span>
              <strong>57</strong>
              <span className="barcode" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
