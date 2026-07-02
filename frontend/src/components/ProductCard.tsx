import { useState } from 'react'
import { BarChart2, ExternalLink, TrendingDown, TrendingUp } from 'lucide-react'
import type { Product } from '../types'
import { PriceHistoryChart } from './PriceHistoryChart'

interface Props {
  product: Product
}

const STORES = [
  { key: 'coolshop',   label: 'Coolshop',     priceKey: 'coolshopPriceIsk',   urlKey: 'coolshopUrl' },
  { key: 'kubbabudin', label: 'Kubbabúðin',   priceKey: 'kubbabudinPriceIsk', urlKey: 'kubbabudinUrl' },
  { key: 'boozt',      label: 'Boozt',        priceKey: 'booztPriceIsk',      urlKey: 'booztUrl' },
  { key: 'hagkaup',    label: 'Hagkaup',      priceKey: 'hagkaupPriceIsk',    urlKey: 'hagkaupUrl' },
  { key: 'kidsworld',  label: 'Kidsworld',    priceKey: 'kidsworldPriceIsk',  urlKey: 'kidsworldUrl' },
  { key: 'elko',       label: 'Elko',         priceKey: 'elkoPriceIsk',       urlKey: 'elkoUrl' },
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
    product.bricklinkThumbnailUrl ||
    product.bricklinkImageUrl ||
    product.displayImageUrl

  const diff = product.priceDiffFromSixMonthLowPct
  const isAtLow = diff !== null && diff !== undefined && Math.abs(diff) < 0.5

  const activeStores = STORES.filter((s) => product[s.priceKey] != null)

  const lowestStoreInfo = STORES.find((s) => s.key === product.lowestPriceStore)
  const productUrl = lowestStoreInfo ? product[lowestStoreInfo.urlKey] : null

  const blAvgISK = product.bricklink6mAvgPriceNewIsk
    ? Math.round(product.bricklink6mAvgPriceNewIsk * 1.24)
    : null

  return (
    <article className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden hover:shadow-md transition-shadow">
      {/* Image */}
      {imageUrl && (
        <div className="bg-gray-50 border-b border-gray-100 h-44 flex items-center justify-center p-3">
          <img
            src={imageUrl}
            alt={product.name ?? product.legoSetNumber}
            className="max-h-full max-w-full object-contain"
            loading="lazy"
          />
        </div>
      )}

      <div className="p-4 flex flex-col gap-3 flex-1">
        {/* Header badges */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-mono bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded font-semibold">
            {product.legoSetNumber}
          </span>
          {product.theme && (
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              {product.theme}
            </span>
          )}
          {product.numParts != null && product.numParts > 0 && (
            <span className="text-xs text-gray-400">{product.numParts.toLocaleString()} pcs</span>
          )}
        </div>

        {/* Name */}
        <h3 className="font-semibold text-gray-900 text-sm leading-snug">
          {product.name ?? 'Unknown'}
        </h3>

        {/* Best price + link */}
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-emerald-600">{fmtISK(product.lowestPriceIsk)}</span>
          {product.lowestPriceStore && (
            <span className="text-xs text-gray-500">
              @ {STORE_LABEL[product.lowestPriceStore] ?? product.lowestPriceStore}
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
                {product.sixMonthLowIsk && (
                  <span className="text-amber-500">({fmtISK(product.sixMonthLowIsk)})</span>
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
              {product.piecesPerKr != null ? product.piecesPerKr.toFixed(4) : '—'}
            </dd>
          </div>
          {blAvgISK != null && (
            <div>
              <dt className="text-gray-400">BrickLink avg (incl. VAT)</dt>
              <dd className="font-semibold">{fmtISK(blAvgISK)}</dd>
            </div>
          )}
          {product.lowestPriceVsBricklinkAvgRatio != null && (
            <div>
              <dt className="text-gray-400">Price / BL ratio</dt>
              <dd className="font-semibold">{product.lowestPriceVsBricklinkAvgRatio.toFixed(3)}</dd>
            </div>
          )}
          {product.bricklink6mSalesCountNew != null && (
            <div>
              <dt className="text-gray-400">BL 6M sales</dt>
              <dd className="font-semibold">{product.bricklink6mSalesCountNew}</dd>
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

        {showHistory && <PriceHistoryChart setNumber={product.legoSetNumber} />}
      </div>
    </article>
  )
}
