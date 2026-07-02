export interface Product {
  legoSetNumber: string
  name: string | null
  theme: string | null
  numParts: number | null
  displayImageUrl: string | null
  bricklinkImageUrl: string | null
  bricklinkThumbnailUrl: string | null
  bricklinkName: string | null

  // Current prices (ISK integers)
  lowestPriceIsk: number | null
  lowestPriceStore: string | null
  coolshopPriceIsk: number | null
  kubbabudinPriceIsk: number | null
  booztPriceIsk: number | null
  hagkaupPriceIsk: number | null
  kidsworldPriceIsk: number | null
  elkoPriceIsk: number | null

  // Store URLs
  coolshopUrl: string | null
  kubbabudinUrl: string | null
  booztUrl: string | null
  hagkaupUrl: string | null
  kidsworldUrl: string | null
  elkoUrl: string | null

  // Value metrics
  piecesPerKr: number | null
  bricklink6mAvgPriceNewUsd: number | null
  bricklink6mAvgPriceNewIsk: number | null
  lowestPriceVsBricklinkAvgRatio: number | null
  bricklink6mSalesCountNew: number | null

  // 6-month historical comparison
  sixMonthLowIsk: number | null
  sixMonthLowStore: string | null
  priceDiffFromSixMonthLowPct: number | null
}

export interface PriceHistoryEntry {
  capturedAt: string
  lowestPriceIsk: number | null
  lowestPriceStore: string | null
  coolshopPriceIsk: number | null
  kubbabudinPriceIsk: number | null
  booztPriceIsk: number | null
  hagkaupPriceIsk: number | null
  kidsworldPriceIsk: number | null
  elkoPriceIsk: number | null
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
