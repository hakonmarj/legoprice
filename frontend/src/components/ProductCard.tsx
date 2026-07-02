import { useState } from 'react'
import { BarChart2, ExternalLink, TrendingDown, TrendingUp } from 'lucide-react'
import type { Product } from '../types'
import { PriceHistoryChart } from './PriceHistoryChart'

interface Props {
  product: Product
}

const STORES = [
  { key: 'coolshop',   label: 'Coolshop',     priceKey: 'coolshop_price_isk',   urlKey: 'coolshop_url' },
  { key: 'kubbabudin', label: 'Kubbabúðin',   priceKey: 'kubbabudin_price_isk', urlKey: 'kubbabudin_url' },
  { key: 'boozt',      label: 'Boozt',        priceKey: 'boozt_price_isk',      urlKey: 'boozt_url' },
  { key: 'hagkaup',    label: 'Hagkaup',      priceKey: 'hagkaup_price_isk',    urlKey: 'hagkaup_url' },
  { key: 'kidsworld',  label: 'Kidsworld',    priceKey: 'kidsworld_price_isk',  urlKey: 'kidsworld_url' },
  { key: 'elko',       label: 'Elko',         priceKey: 'elko_price_isk',       urlKey: 'elko_url' },
] as const

const STORE_LABEL: Record<string, string> = Object.fromEntries(STORES.map((s) => [s.key, s.label]))

function fmtISK(isk: number | null | undefined): string {
  if (isk == null) return '—'
  return `${isk.toLocaleString('is-IS')} kr`
}

export function ProductCard({ product }: Props) {
  const [showHistory, setShowHistory] = useState(false)
  const [showStores, setShowStores] = useState(false)

  const imageUrl =
    product.bricklink_thumbnail_url ||
    product.bricklink_image_url ||
    product.display_image_url

  const diff = product.price_diff_from_six_month_low_pct
  const isAtLow = diff !== null && diff !== undefined && Math.abs(diff) < 0.5

  const activeStores = STORES.filter((s) => product[s.priceKey] != null)

  const lowestStoreInfo = STORES.find((s) => s.key === product.lowest_price_store)
  const productUrl = lowestStoreInfo ? product[lowestStoreInfo.urlKey] : null

  const blAvgISK = product.bricklink_6m_avg_price_new_isk
    ? Math.round(product.bricklink_6m_avg_price_new_isk * 1.24)
    : null

  return (
    <article className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden hover:shadow-md transition-shadow">
      {/* Image */}
      {imageUrl && (
        <div className="bg-gray-50 border-b border-gray-100 h-44 flex items-center justify-center p-3">
          <img
            src={imageUrl}
            alt={product.name ?? product.lego_set_number}
            className="max-h-full max-w-full object-contain"
            loading="lazy"
          />
        </div>
      )}

      <div className="p-4 flex flex-col gap-3 flex-1">
        {/* Header badges */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-mono bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded font-semibold">
            {product.lego_set_number}
          </span>
          {product.theme && (
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              {product.theme}
            </span>
          )}
          {product.num_parts != null && product.num_parts > 0 && (
            <span className="text-xs text-gray-400">{product.num_parts.toLocaleString()} pcs</span>
          )}
        </div>

        {/* Name */}
        <h3 className="font-semibold text-gray-900 text-sm leading-snug">
          {product.name ?? 'Unknown'}
        </h3>

        {/* Best price + link */}
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-emerald-600">{fmtISK(product.lowest_price_isk)}</span>
          {product.lowest_price_store && (
            <span className="text-xs text-gray-500">
              @ {STORE_LABEL[product.lowest_price_store] ?? product.lowest_price_store}
            </span>
          )}
          {productUrl && (
            <a
              href={productUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto text-blue-500 hover:text-blue-700"
              title="View product"
            >
              <ExternalLink size={14} />
            </a>
          )}
        </div>

        {/* 6-month low badge */}
        {diff !== null && diff !== undefined && (
          <div>
            {isAtLow ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                <TrendingDown size={11} />
                At 6-month low
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                <TrendingUp size={11} />
                +{diff.toFixed(1)}% vs 6M low
                {product.six_month_low_isk && (
                  <span className="text-amber-500">({fmtISK(product.six_month_low_isk)})</span>
                )}
              </span>
            )}
          </div>
        )}

        {/* Value metrics grid */}
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs border-t border-gray-100 pt-3">
          <div>
            <dt className="text-gray-400">Pieces/ISK</dt>
            <dd className="font-semibold">
              {product.pieces_per_kr != null ? product.pieces_per_kr.toFixed(4) : '—'}
            </dd>
          </div>
          {blAvgISK != null && (
            <div>
              <dt className="text-gray-400">BrickLink avg (incl. VAT)</dt>
              <dd className="font-semibold">{fmtISK(blAvgISK)}</dd>
            </div>
          )}
          {product.lowest_price_vs_bricklink_avg_ratio != null && (
            <div>
              <dt className="text-gray-400">Price / BL ratio</dt>
              <dd className="font-semibold">{product.lowest_price_vs_bricklink_avg_ratio.toFixed(3)}</dd>
            </div>
          )}
          {product.bricklink_6m_sales_count_new != null && (
            <div>
              <dt className="text-gray-400">BL 6M sales</dt>
              <dd className="font-semibold">{product.bricklink_6m_sales_count_new}</dd>
            </div>
          )}
        </dl>

        {/* Store prices toggle */}
        {activeStores.length > 0 && (
          <div className="border-t border-gray-100 pt-2">
            <button
              onClick={() => setShowStores((s) => !s)}
              className="text-xs text-gray-500 hover:text-gray-700 font-medium flex items-center gap-1"
            >
              {showStores ? '▾' : '▸'} Store prices ({activeStores.length})
            </button>
            {showStores && (
              <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1.5">
                {activeStores.map((store) => (
                  <div key={store.key} className="flex justify-between text-xs">
                    <span className="text-gray-500">
                      {product[store.urlKey] ? (
                        <a
                          href={product[store.urlKey] as string}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline text-blue-500"
                        >
                          {store.label}
                        </a>
                      ) : (
                        store.label
                      )}
                    </span>
                    <span className="font-semibold">{fmtISK(product[store.priceKey] as number)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Price history toggle */}
        <button
          onClick={() => setShowHistory((h) => !h)}
          className="mt-auto pt-2 border-t border-gray-100 flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          <BarChart2 size={12} />
          {showHistory ? 'Hide' : 'Show'} 30-day price history
        </button>

        {showHistory && <PriceHistoryChart setNumber={product.lego_set_number} />}
      </div>
    </article>
  )
}
