import { useEffect, useState } from 'react'
import { fetchDebtors, deactivateDebtor, Debtor, ImportResult } from '../api/debtors'
import ImportDropzone from '../components/ImportDropzone'

const formatBRL = (v: string) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const formatCPF = (cpf: string) =>
  cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')

export default function Debtors() {
  const [debtors, setDebtors] = useState<Debtor[]>([])
  const [loading, setLoading] = useState(true)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [showImport, setShowImport] = useState(false)
  const [removingId, setRemovingId] = useState<string | null>(null)

  const load = () => fetchDebtors().then(setDebtors).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleImportSuccess = (result: ImportResult) => {
    setImportResult(result)
    setShowImport(false)
    load()
  }

  const handleRemove = async (id: string) => {
    if (!confirm('Desativar este devedor?')) return
    setRemovingId(id)
    try { await deactivateDebtor(id); load() } finally { setRemovingId(null) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Devedores</h2>
        <button
          onClick={() => { setShowImport(v => !v); setImportResult(null) }}
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {showImport ? 'Fechar' : '+ Importar Planilha'}
        </button>
      </div>

      {showImport && (
        <div className="mb-6">
          <ImportDropzone onSuccess={handleImportSuccess} />
        </div>
      )}

      {importResult && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
          <p className="font-semibold text-green-800 mb-1">Importação concluída</p>
          <p className="text-green-700">
            {importResult.imported} importados · {importResult.skipped} ignorados · {importResult.total} total
          </p>
          {importResult.errors.length > 0 && (
            <ul className="mt-2 text-xs text-amber-700 list-disc list-inside">
              {importResult.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
              {importResult.errors.length > 5 && <li>...e mais {importResult.errors.length - 5} avisos</li>}
            </ul>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : debtors.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-4xl mb-3">👥</p>
          <p>Nenhum devedor cadastrado. Importe uma planilha para começar.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 text-xs text-gray-500">
            {debtors.length} devedores ativos
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Nome</th>
                <th className="text-left px-5 py-3">CPF</th>
                <th className="text-left px-5 py-3">Telefone</th>
                <th className="text-right px-5 py-3">Valor</th>
                <th className="text-left px-5 py-3">Vencimento</th>
                <th className="text-left px-5 py-3">Canal</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {debtors.map(d => (
                <tr key={d.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-900">{d.nome_completo}</td>
                  <td className="px-5 py-3 text-gray-500 font-mono text-xs">{formatCPF(d.cpf)}</td>
                  <td className="px-5 py-3 text-gray-500">{d.telefone}</td>
                  <td className="px-5 py-3 text-right font-semibold text-gray-900">{formatBRL(d.valor_divida)}</td>
                  <td className="px-5 py-3 text-gray-500">
                    {new Date(d.data_vencimento + 'T12:00:00').toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-5 py-3">
                    {d.canal_preferencial ? (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                        {d.canal_preferencial}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300">auto</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      disabled={removingId === d.id}
                      onClick={() => handleRemove(d.id)}
                      className="text-xs text-red-500 hover:text-red-700 disabled:opacity-40"
                    >
                      Remover
                    </button>
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
