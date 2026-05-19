import { useEffect, useState } from 'react'
import { fetchCampaigns, createCampaign, launchCampaign, pauseCampaign, Campaign, CampaignCreate } from '../api/campaigns'
import StatusBadge from '../components/StatusBadge'

const defaultForm: CampaignCreate = {
  name: '',
  description: '',
  max_whatsapp_attempts: 2,
  max_sms_attempts: 2,
  max_call_attempts: 1,
  contact_interval_hours: 48,
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CampaignCreate>(defaultForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [actionId, setActionId] = useState<string | null>(null)

  const load = () => fetchCampaigns().then(setCampaigns).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createCampaign(form)
      setShowForm(false)
      setForm(defaultForm)
      load()
    } finally {
      setSaving(false)
    }
  }

  const handleLaunch = async (id: string) => {
    setActionId(id)
    try { await launchCampaign(id); load() } finally { setActionId(null) }
  }

  const handlePause = async (id: string) => {
    setActionId(id)
    try { await pauseCampaign(id); load() } finally { setActionId(null) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Campanhas</h2>
        <button
          onClick={() => setShowForm(v => !v)}
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Nova Campanha
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm space-y-4">
          <h3 className="font-semibold text-gray-800">Nova Campanha</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nome *</label>
              <input
                required
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                placeholder="Ex: Cobrança Julho 2025"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Intervalo entre tentativas (horas)</label>
              <input
                type="number"
                min={24}
                value={form.contact_interval_hours}
                onChange={e => setForm(f => ({ ...f, contact_interval_hours: Number(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tentativas WhatsApp</label>
              <input
                type="number"
                min={1}
                max={5}
                value={form.max_whatsapp_attempts}
                onChange={e => setForm(f => ({ ...f, max_whatsapp_attempts: Number(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tentativas SMS</label>
              <input
                type="number"
                min={1}
                max={5}
                value={form.max_sms_attempts}
                onChange={e => setForm(f => ({ ...f, max_sms_attempts: Number(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Descrição</label>
              <textarea
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                rows={2}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-5 py-2 rounded-lg disabled:opacity-50 transition-colors"
            >
              {saving ? 'Criando...' : 'Criar Campanha'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-4xl mb-3">📣</p>
          <p>Nenhuma campanha criada ainda.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Nome</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="text-left px-5 py-3">WA / SMS / Call</th>
                <th className="text-left px-5 py-3">Intervalo</th>
                <th className="text-left px-5 py-3">Criada em</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {campaigns.map(c => (
                <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900">{c.name}</td>
                  <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-5 py-3 text-gray-500">
                    {c.max_whatsapp_attempts} / {c.max_sms_attempts} / {c.max_call_attempts}
                  </td>
                  <td className="px-5 py-3 text-gray-500">{c.contact_interval_hours}h</td>
                  <td className="px-5 py-3 text-gray-400">
                    {new Date(c.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {c.status === 'draft' || c.status === 'paused' ? (
                      <button
                        disabled={actionId === c.id}
                        onClick={() => handleLaunch(c.id)}
                        className="text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded-lg disabled:opacity-50 transition-colors"
                      >
                        {actionId === c.id ? '...' : 'Lançar'}
                      </button>
                    ) : c.status === 'active' ? (
                      <button
                        disabled={actionId === c.id}
                        onClick={() => handlePause(c.id)}
                        className="text-xs bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-lg disabled:opacity-50 transition-colors"
                      >
                        {actionId === c.id ? '...' : 'Pausar'}
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
