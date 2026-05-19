import { api } from './client'

export interface DashboardStats {
  total_debtors: number
  active_campaigns: number
  contacts_sent_today: number
  contacts_sent_total: number
  payments_pending: number
  payments_confirmed: number
  total_collected: string
  total_outstanding: string
  recovery_rate: number
}

export const fetchDashboard = () =>
  api.get<DashboardStats>('/dashboard/').then(r => r.data)
