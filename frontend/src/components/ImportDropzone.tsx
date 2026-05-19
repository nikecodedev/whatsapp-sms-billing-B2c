import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { importDebtors, ImportResult } from '../api/debtors'

interface Props {
  onSuccess: (result: ImportResult) => void
}

export default function ImportDropzone({ onSuccess }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted.length) return
    setLoading(true)
    setError(null)
    try {
      const result = await importDebtors(accepted[0])
      onSuccess(result)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Erro ao importar arquivo')
    } finally {
      setLoading(false)
    }
  }, [onSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
    },
    multiple: false,
  })

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-brand-400 bg-white'}`}
      >
        <input {...getInputProps()} />
        <p className="text-4xl mb-3">📂</p>
        {loading ? (
          <p className="text-sm text-gray-500">Importando...</p>
        ) : isDragActive ? (
          <p className="text-sm text-brand-600 font-medium">Solte o arquivo aqui</p>
        ) : (
          <>
            <p className="text-sm font-medium text-gray-700">Arraste sua planilha ou clique para selecionar</p>
            <p className="text-xs text-gray-400 mt-1">Suporta .xlsx, .xls e .csv</p>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
