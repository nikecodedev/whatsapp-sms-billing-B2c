import { clsx } from 'clsx'

interface Props {
  label: string
  value: string | number
  sub?: string
  color?: 'default' | 'green' | 'blue' | 'amber' | 'red'
}

const colorMap = {
  default: 'bg-white border-gray-200',
  green: 'bg-emerald-50 border-emerald-200',
  blue: 'bg-blue-50 border-blue-200',
  amber: 'bg-amber-50 border-amber-200',
  red: 'bg-red-50 border-red-200',
}

const valueColorMap = {
  default: 'text-gray-900',
  green: 'text-emerald-700',
  blue: 'text-blue-700',
  amber: 'text-amber-700',
  red: 'text-red-700',
}

export default function StatCard({ label, value, sub, color = 'default' }: Props) {
  return (
    <div className={clsx('rounded-xl border p-5 shadow-sm', colorMap[color])}>
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      <p className={clsx('text-3xl font-bold', valueColorMap[color])}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}
