import { useCallback, useEffect, useMemo, useState } from 'react'
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
  { key: 'coolshop',   label: 'Coolshop',   priceKey: 'coolshopPriceIsk',   urlKey: 'coolshopUrl' },
  { key: 'kubbabudin', label: 'Kubbabúðin', priceKey: 'kubbabudinPriceIsk', urlKey: 'kubbabudinUrl' },
  { key: 'boozt',      label: 'Boozt',      priceKey: 'booztPriceIsk',      urlKey: 'booztUrl' },
  { key: 'hagkaup',    label: 'Hagkaup',    priceKey: 'hagkaupPriceIsk',    urlKey: 'hagkaupUrl' },
  { key: 'kidsworld',  label: 'Kidsworld',  priceKey: 'kidsworldPriceIsk',  urlKey: 'kidsworldUrl' },
  { key: 'elko',       label: 'Elko',       priceKey: 'elkoPriceIsk',       urlKey: 'elkoUrl' },
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
        p.legoSetNumber.toLowerCase().includes(q) ||
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
        return count >= 2 && (p.numParts ?? 0) > 0
      }
      if (selectedPreset === 'bricklinkLiquid') {
        return (p.bricklink6mSalesCountNew ?? 0) >= 10
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

  const allThemesCount = useMemo(
    () => allProducts.filter((p) => matchesQuery(p) && matchesStore(p) && matchesPreset(p)).length,
    [allProducts, matchesQuery, matchesStore, matchesPreset],
  )

  // ── Fully filtered + sorted result set ───────────────────────────────────
  const filteredProducts = useMemo(() => {
    let rows = allProducts.filter(
      (p) => matchesQuery(p) && matchesStore(p) && matchesTheme(p) && matchesPreset(p),
    )

    rows = [...rows].sort((a, b) => {
      switch (sortBy) {
        case 'value':
          return (b.piecesPerKr ?? 0) - (a.piecesPerKr ?? 0)
        case 'priceAsc':
          return (a.lowestPriceIsk ?? Infinity) - (b.lowestPriceIsk ?? Infinity)
        case 'priceDesc':
          return (b.lowestPriceIsk ?? 0) - (a.lowestPriceIsk ?? 0)
        case 'ratioAsc':
          return (
            (a.lowestPriceVsBricklinkAvgRatio ?? Infinity) -
            (b.lowestPriceVsBricklinkAvgRatio ?? Infinity)
          )
        case 'sixMonthDiff':
          return (
            (a.priceDiffFromSixMonthLowPct ?? Infinity) -
            (b.priceDiffFromSixMonthLowPct ?? Infinity)
          )
        case 'bricklinkSales':
          return (b.bricklink6mSalesCountNew ?? 0) - (a.bricklink6mSalesCountNew ?? 0)
        default:
          return 0
      }
    })

    return topN === 'all' ? rows : rows.slice(0, Number(topN))
  }, [allProducts, matchesQuery, matchesStore, matchesTheme, matchesPreset, sortBy, topN])

  const selectedThemeStillValid =
    selectedTheme === 'all' || themeOptions.some((t) => t.name === selectedTheme)

  useEffect(() => {
    if (!selectedThemeStillValid) {
      setSelectedTheme('all')
    }
  }, [selectedThemeStillValid])

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
        selectedTheme={selectedTheme}
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
        allThemesCount={allThemesCount}
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
              <ProductCard key={p.legoSetNumber} product={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
