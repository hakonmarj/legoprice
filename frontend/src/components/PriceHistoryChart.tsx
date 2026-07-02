import { useQuery } from '@tanstack/react-query'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fetchPriceHistory } from '../api'

interface Props {
  setNumber: string
}

const STORE_KEYS = ['coolshop', 'kubbabudin', 'boozt', 'hagkaup', 'kidsworld', 'elko'] as const
type StoreKey = (typeof STORE_KEYS)[number]

const STORE_COLORS: Record<StoreKey, string> = {
  coolshop: '#2563eb',
  kubbabudin: '#16a34a',
  boozt: '#9333ea',
  hagkaup: '#ea580c',
  kidsworld: '#db2777',
  elko: '#0891b2',
}

const STORE_LABELS: Record<StoreKey, string> = {
  coolshop: 'Coolshop',
  kubbabudin: 'Kubbabúðin',
  boozt: 'Boozt',
  hagkaup: 'Hagkaup',
  kidsworld: 'Kidsworld',
  elko: 'Elko',
}

const STORES: StoreKey[] = [...STORE_KEYS]
type StorePricePoint = Record<StoreKey, number | undefined> & { date: string }

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('is-IS', { month: 'short', day: 'numeric' })
}

export function PriceHistoryChart({ setNumber }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['history', setNumber],
    queryFn: () => fetchPriceHistory(setNumber, 30),
    staleTime: 10 * 60 * 1000,
  })

  if (isLoading)
    return <div className="h-40 flex items-center justify-center text-xs text-gray-400">Loading history…</div>

  if (isError || !data?.length)
    return (
      <div className="h-20 flex items-center justify-center text-xs text-gray-400">
        No price history available yet
      </div>
    )

  const chartData: StorePricePoint[] = data.map((entry) => ({
    date: formatDate(entry.capturedAt),
    coolshop: entry.coolshopPriceIsk ?? undefined,
    kubbabudin: entry.kubbabudinPriceIsk ?? undefined,
    boozt: entry.booztPriceIsk ?? undefined,
    hagkaup: entry.hagkaupPriceIsk ?? undefined,
    kidsworld: entry.kidsworldPriceIsk ?? undefined,
    elko: entry.elkoPriceIsk ?? undefined,
  }))

  const activeStores = STORES.filter((s) => chartData.some((d) => d[s] != null))

  return (
    <div className="mt-2">
      <p className="text-xs text-gray-500 mb-2">Price history (last 30 days, ISK)</p>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} width={52} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toLocaleString('is-IS')} kr`,
              STORE_LABELS[name as StoreKey] ?? name,
            ]}
          />
          <Legend
            formatter={(value) => STORE_LABELS[value as StoreKey] ?? value}
            iconSize={8}
            wrapperStyle={{ fontSize: 10 }}
          />
          {activeStores.map((store) => (
            <Line
              key={store}
              type="monotone"
              dataKey={store}
              stroke={STORE_COLORS[store]}
              dot={false}
              strokeWidth={1.5}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
