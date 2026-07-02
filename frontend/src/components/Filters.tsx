import { Search, SlidersHorizontal } from 'lucide-react'
import type { PresetKey, SortKey, StoreOption, ThemeOption } from '../types'

interface Props {
  searchQuery: string
  onSearchChange: (v: string) => void

  selectedStore: string
  storeOptions: StoreOption[]
  onStoreChange: (v: string) => void

  selectedTheme: string
  themeOptions: ThemeOption[]
  onThemeChange: (v: string) => void

  selectedPreset: PresetKey
  onPresetChange: (v: PresetKey) => void

  sortBy: SortKey
  onSortChange: (v: SortKey) => void

  topN: string
  onTopNChange: (v: string) => void

  totalCount: number
  filteredCount: number
  allThemesCount: number
}

export function Filters({
  searchQuery,
  onSearchChange,
  selectedStore,
  storeOptions,
  onStoreChange,
  selectedTheme,
  themeOptions,
  onThemeChange,
  selectedPreset,
  onPresetChange,
  sortBy,
  onSortChange,
  topN,
  onTopNChange,
  totalCount,
  filteredCount,
  allThemesCount,
}: Props) {
  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3 space-y-3">
      {/* Search row */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={15} />
        <input
          type="text"
          placeholder="Search set number or name…"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      {/* Filter row */}
      <div className="flex items-center gap-2 flex-wrap">
        <SlidersHorizontal size={14} className="text-gray-400 shrink-0" />

        {/* Store filter */}
        <select
          value={selectedStore}
          onChange={(e) => onStoreChange(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
        >
          <option value="all">All stores ({totalCount})</option>
          {storeOptions.map((s) => (
            <option key={s.key} value={s.key}>
              {s.label} ({s.count})
            </option>
          ))}
        </select>

        {/* Theme filter */}
        <select
          value={selectedTheme}
          onChange={(e) => onThemeChange(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white max-w-[180px]"
        >
          <option value="all">All themes ({allThemesCount})</option>
          {themeOptions.map((t) => (
            <option key={t.name} value={t.name}>
              {t.name} ({t.count})
            </option>
          ))}
        </select>

        {/* Preset */}
        <select
          value={selectedPreset}
          onChange={(e) => onPresetChange(e.target.value as PresetKey)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
        >
          <option value="all">All sets</option>
          <option value="strictValue">Value focus (2+ stores)</option>
          <option value="bricklinkLiquid">BrickLink liquid (sales ≥ 10)</option>
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as SortKey)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
        >
          <option value="value">Best value (pieces/ISK)</option>
          <option value="priceAsc">Lowest price</option>
          <option value="priceDesc">Highest price</option>
          <option value="ratioAsc">Price/BL ratio (asc)</option>
          <option value="sixMonthDiff">6M low diff (asc)</option>
          <option value="bricklinkSales">BL sales (desc)</option>
        </select>

        {/* Top N */}
        <select
          value={topN}
          onChange={(e) => onTopNChange(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
        >
          <option value="all">All results</option>
          <option value="25">Top 25</option>
          <option value="50">Top 50</option>
          <option value="100">Top 100</option>
        </select>

        <span className="ml-auto text-xs text-gray-400">
          {filteredCount} of {totalCount} sets
        </span>
      </div>
    </div>
  )
}
