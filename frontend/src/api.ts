import type { PriceHistoryEntry, Product } from './types'

const BASE = ''  // requests go to /api, proxied by Vite dev server or nginx in production

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${BASE}/api/products`)
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.status}`)
  return res.json()
}

export async function fetchPriceHistory(
  setNumber: string,
  days = 30,
): Promise<PriceHistoryEntry[]> {
  const res = await fetch(`${BASE}/api/products/${encodeURIComponent(setNumber)}/history?days=${days}`)
  if (!res.ok) throw new Error(`Failed to fetch history for ${setNumber}: ${res.status}`)
  return res.json()
}
