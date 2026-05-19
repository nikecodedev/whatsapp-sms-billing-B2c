import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import StatCard from '../components/StatCard'
import { fetchDashboard, DashboardStats } from '../api/dashboard'

const formatBRL = (v: string | number) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!stats) return <p className="text-red-500">Falha ao carregar dashboard.</p>

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total de Devedores" value={stats.total_debtors} />
        <StatCard label="Campanhas Ativas" value={stats.active_campaigns} color="blue" />
        <StatCard label="Contatos Hoje" value={stats.contacts_sent_today} color="amber" />
        <StatCard
          label="Taxa de Recuperação"
          value={`${stats.recovery_rate.toFixed(1)}%`}
          color={stats.recovery_rate >= 10 ? 'green' : 'default'}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pagamentos Pendentes" value={stats.payments_pending} color="amber" />
        <StatCard label="Pagamentos Confirmados" value={stats.payments_confirmed} color="green" />
        <StatCard label="Total Recuperado" value={formatBRL(stats.total_collected)} color="green" />
        <StatCard label="Total em Aberto" value={formatBRL(stats.total_outstanding)} color="red" />
      </div>

      {/* Contacts chart placeholder */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-base font-semibold text-gray-700 mb-4">Contatos Enviados</h3>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={[
            { day: 'Seg', contacts: 0 },
            { day: 'Ter', contacts: stats.contacts_sent_total },
            { day: 'Qua', contacts: 0 },
            { day: 'Qui', contacts: 0 },
            { day: 'Sex', contacts: stats.contacts_sent_today },
          ]}>
            <defs>
              <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="day" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Area type="monotone" dataKey="contacts" stroke="#6366f1" fill="url(#cg)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
