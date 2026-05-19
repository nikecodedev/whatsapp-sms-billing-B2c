import { api } from './client'

export interface Debtor {
  id: string
  nome_completo: string
  cpf: string
  telefone: string
  email: string | null
  valor_divida: string
  data_vencimento: string
  descricao: string | null
  canal_preferencial: string | null
  permite_parcelamento: boolean
  is_active: boolean
  created_at: string
}

export interface ImportResult {
  total: number
  imported: number
  skipped: number
  errors: string[]
}

export const fetchDebtors = (skip = 0, limit = 50) =>
  api.get<Debtor[]>('/debtors/', { params: { skip, limit } }).then(r => r.data)

export const importDebtors = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<ImportResult>('/debtors/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const deactivateDebtor = (id: string) =>
  api.delete(`/debtors/${id}`)
