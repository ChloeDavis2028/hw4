// Shapes returned by the FastAPI backend (backend/main.py).

export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  fun_name: string
  fun_blurb: string
  best_use: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
}

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch('/api/products')
  if (!res.ok) throw new Error(`Could not load products (${res.status})`)
  return res.json()
}

export async function fetchProduct(productId: string): Promise<Product> {
  const res = await fetch(`/api/products/${encodeURIComponent(productId)}`)
  if (res.status === 404) throw new Error('We could not find that product')
  if (!res.ok) throw new Error(`Could not load product (${res.status})`)
  return res.json()
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}

// A product Chloe found, sent with her chat reply (POST /api/chat -> products[]).
// Every field comes from the database via the backend, never from the AI model.
export interface ProductCard {
  product_id: string
  name: string
  fun_name: string
  price: number
  garment_type: string
  short_info: string
  image_url: string
  reel_url: string
  detail_url: string
  sizes_in_stock: string[]
}
