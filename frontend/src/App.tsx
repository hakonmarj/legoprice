import { useCallback, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Blocks } from 'lucide-react'
import { fetchProducts } from './api'
import { Filters } from './components/Filters'
import { ProductCard } from './components/ProductCard'
import type { PresetKey, Product, SortKey, StoreOption, ThemeOption } from './types'

// ── Store definitions (single source of truth) ───────────────────────────────
const STORES: Array<{
  key: string
  label: string
  priceKey: keyof Product
  urlKey: keyof Product
}> = [
  { key: 'coolshop',   label: 'Coolshop',   priceKey: 'coolshop_price_isk',   urlKey: 'coolshop_url' },
  { key: 'kubbabudin', label: 'Kubbabúðin', priceKey: 'kubbabudin_price_isk', urlKey: 'kubbabudin_url' },
  { key: 'boozt',      label: 'Boozt',      priceKey: 'boozt_price_isk',      urlKey: 'boozt_url' },
  { key: 'hagkaup',    label: 'Hagkaup',    priceKey: 'hagkaup_price_isk',    urlKey: 'hagkaup_url' },
  { key: 'kidsworld',  label: 'Kidsworld',  priceKey: 'kidsworld_price_isk',  urlKey: 'kidsworld_url' },
  { key: 'elko',       label: 'Elko',       priceKey: 'elko_price_isk',       urlKey: 'elko_url' },
]

export default function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStore, setSelectedStore] = useState('all')
  const [selectedTheme, setSelectedTheme] = useState('all')
  const [selectedPreset, setSelectedPreset] = useState<PresetKey>('all')
  const [sortBy, setSortBy] = useState<SortKey>('value')
  const [topN, setTopN] = useState('all')

  const { data: allProducts = [], isLoading, isError } = useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
  })

  // ── Filter predicates (each independent so counts stay accurate) ─────────
  const matchesQuery = useCallback(
    (p: Product): boolean => {
      if (!searchQuery) return true
      const q = searchQuery.toLowerCase()
      return (
        p.lego_set_number.toLowerCase().includes(q) ||
        (p.name ?? '').toLowerCase().includes(q)
      )
    },
    [searchQuery],
  )

  const matchesStore = useCallback(
    (p: Product): boolean => {
      if (selectedStore === 'all') return true
      const info = STORES.find((s) => s.key === selectedStore)
      return info ? p[info.priceKey] != null : true
    },
    [selectedStore],
  )

  const matchesTheme = useCallback(
    (p: Product): boolean => {
      if (selectedTheme === 'all') return true
      return p.theme === selectedTheme
    },
    [selectedTheme],
  )

  const matchesPreset = useCallback(
    (p: Product): boolean => {
      if (selectedPreset === 'strictValue') {
        const count = STORES.filter((s) => p[s.priceKey] != null).length
        return count >= 2 && (p.num_parts ?? 0) > 0
      }
      if (selectedPreset === 'bricklinkLiquid') {
        return (p.bricklink_6m_sales_count_new ?? 0) >= 10
      }
      return true
    },
    [selectedPreset],
  )

  // ── Store options: count ignores current store selection ─────────────────
  // "If I click Coolshop, how many products would I see?"
  const storeOptions = useMemo((): StoreOption[] =>
    STORES.map((store) => ({
      ...store,
      count: allProducts.filter(
        (p) =>
          matchesQuery(p) &&
          matchesTheme(p) &&
          matchesPreset(p) &&
          p[store.priceKey] != null,
      ).length,
    })),
    [allProducts, matchesQuery, matchesTheme, matchesPreset],
  )

  // ── Theme options: count ignores current theme selection ──────────────────
  // "If I click Star Wars while Coolshop is selected, how many sets appear?"
  const themeOptions = useMemo((): ThemeOption[] => {
    const map = new Map<string, number>()
    allProducts
      .filter((p) => matchesQuery(p) && matchesStore(p) && matchesPreset(p))
      .forEach((p) => {
        if (p.theme) map.set(p.theme, (map.get(p.theme) ?? 0) + 1)
      })
    // Hide themes with zero matches (they simply won't appear)
    return [...map.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([name, count]) => ({ name, count }))
  }, [allProducts, matchesQuery, matchesStore, matchesPreset])

  // ── Fully filtered + sorted result set ───────────────────────────────────
  const filteredProducts = useMemo(() => {
    let rows = allProducts.filter(
      (p) => matchesQuery(p) && matchesStore(p) && matchesTheme(p) && matchesPreset(p),
    )

    rows = [...rows].sort((a, b) => {
      switch (sortBy) {
        case 'value':
          return (b.pieces_per_kr ?? 0) - (a.pieces_per_kr ?? 0)
        case 'priceAsc':
          return (a.lowest_price_isk ?? Infinity) - (b.lowest_price_isk ?? Infinity)
        case 'priceDesc':
          return (b.lowest_price_isk ?? 0) - (a.lowest_price_isk ?? 0)
        case 'ratioAsc':
          return (
            (a.lowest_price_vs_bricklink_avg_ratio ?? Infinity) -
            (b.lowest_price_vs_bricklink_avg_ratio ?? Infinity)
          )
        case 'sixMonthDiff':
          return (
            (a.price_diff_from_six_month_low_pct ?? Infinity) -
            (b.price_diff_from_six_month_low_pct ?? Infinity)
          )
        case 'bricklinkSales':
          return (b.bricklink_6m_sales_count_new ?? 0) - (a.bricklink_6m_sales_count_new ?? 0)
        default:
          return 0
      }
    })

    return topN === 'all' ? rows : rows.slice(0, Number(topN))
  }, [allProducts, matchesQuery, matchesStore, matchesTheme, matchesPreset, sortBy, topN])

  // Ensure selected theme is still valid; reset if its count dropped to 0
  const selectedThemeStillValid =
    selectedTheme === 'all' || themeOptions.some((t) => t.name === selectedTheme)

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <Blocks className="text-yellow-500 shrink-0" size={24} />
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-tight">LEGO Iceland Price Browser</h1>
          <p className="text-xs text-gray-500">Live prices from 6 Icelandic stores · 6-month price history</p>
        </div>
      </header>

      {/* Filter bar */}
      <Filters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedStore={selectedStore}
        storeOptions={storeOptions}
        onStoreChange={setSelectedStore}
        selectedTheme={selectedThemeStillValid ? selectedTheme : 'all'}
        themeOptions={themeOptions}
        onThemeChange={setSelectedTheme}
        selectedPreset={selectedPreset}
        onPresetChange={setSelectedPreset}
        sortBy={sortBy}
        onSortChange={setSortBy}
        topN={topN}
        onTopNChange={setTopN}
        totalCount={allProducts.length}
        filteredCount={filteredProducts.length}
      />

      {/* Content */}
      <main className="flex-1 px-4 py-4">
        {isLoading && (
          <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
            Loading products…
          </div>
        )}

        {isError && (
          <div className="flex items-center justify-center h-64 text-red-500 text-sm">
            Failed to load products. Is the backend running?
          </div>
        )}

        {!isLoading && !isError && filteredProducts.length === 0 && (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            No products match the current filters.
          </div>
        )}

        {!isLoading && !isError && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredProducts.map((p) => (
              <ProductCard key={p.lego_set_number} product={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
