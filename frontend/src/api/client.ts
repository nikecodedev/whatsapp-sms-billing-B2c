import axios from 'axios'

// In dev, VITE_API_URL is empty -> relative paths -> the Vite proxy forwards them.
// In production, set VITE_API_URL to the deployed backend URL.
const API_BASE = import.meta.env.VITE_API_URL || ''
const TENANT_ID = import.meta.env.VITE_TENANT_ID || ''

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1/tenants/${TENANT_ID}`,
  headers: { 'Content-Type': 'application/json' },
})

export const setTenant = (tenantId: string) => {
  api.defaults.baseURL = `${API_BASE}/api/v1/tenants/${tenantId}`
}
