import { api } from './client'

export interface Campaign {
  id: string
  name: string
  description: string | null
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled'
  max_whatsapp_attempts: number
  max_sms_attempts: number
  max_call_attempts: number
  contact_interval_hours: number
  created_at: string
}

export interface CampaignStats {
  campaign_id: string
  campaign_name: string
  total_debtors: number
  contacts_sent: number
  delivered: number
  responded: number
  paid: number
  failed: number
  recovery_rate: number
}

export interface CampaignCreate {
  name: string
  description?: string
  max_whatsapp_attempts?: number
  max_sms_attempts?: number
  max_call_attempts?: number
  contact_interval_hours?: number
}

export const fetchCampaigns = () =>
  api.get<Campaign[]>('/campaigns/').then(r => r.data)

export const createCampaign = (data: CampaignCreate) =>
  api.post<Campaign>('/campaigns/', data).then(r => r.data)

export const launchCampaign = (id: string) =>
  api.post(`/campaigns/${id}/launch`).then(r => r.data)

export const pauseCampaign = (id: string) =>
  api.post<Campaign>(`/campaigns/${id}/pause`).then(r => r.data)

export const fetchCampaignStats = (id: string) =>
  api.get<CampaignStats>(`/campaigns/${id}/stats`).then(r => r.data)
