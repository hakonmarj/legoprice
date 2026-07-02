export interface Product {
  lego_set_number: string
  name: string | null
  theme: string | null
  num_parts: number | null
  display_image_url: string | null
  bricklink_image_url: string | null
  bricklink_thumbnail_url: string | null
  bricklink_name: string | null

  // Current prices (ISK integers)
  lowest_price_isk: number | null
  lowest_price_store: string | null
  coolshop_price_isk: number | null
  kubbabudin_price_isk: number | null
  boozt_price_isk: number | null
  hagkaup_price_isk: number | null
  kidsworld_price_isk: number | null
  elko_price_isk: number | null

  // Store URLs
  coolshop_url: string | null
  kubbabudin_url: string | null
  boozt_url: string | null
  hagkaup_url: string | null
  kidsworld_url: string | null
  elko_url: string | null

  // Value metrics
  pieces_per_kr: number | null
  bricklink_6m_avg_price_new_usd: number | null
  bricklink_6m_avg_price_new_isk: number | null
  lowest_price_vs_bricklink_avg_ratio: number | null
  bricklink_6m_sales_count_new: number | null

  // 6-month historical comparison
  six_month_low_isk: number | null
  six_month_low_store: string | null
  price_diff_from_six_month_low_pct: number | null
}

export interface PriceHistoryEntry {
  captured_at: string
  lowest_price_isk: number | null
  lowest_price_store: string | null
  coolshop_price_isk: number | null
  kubbabudin_price_isk: number | null
  boozt_price_isk: number | null
  hagkaup_price_isk: number | null
  kidsworld_price_isk: number | null
  elko_price_isk: number | null
}

export interface StoreOption {
  key: string
  label: string
  priceKey: keyof Product
  urlKey: keyof Product
  count: number
}

export interface ThemeOption {
  name: string
  count: number
}

export type SortKey =
  | 'value'
  | 'priceAsc'
  | 'priceDesc'
  | 'ratioAsc'
  | 'bricklinkSales'
  | 'sixMonthDiff'

export type PresetKey = 'all' | 'strictValue' | 'bricklinkLiquid'
