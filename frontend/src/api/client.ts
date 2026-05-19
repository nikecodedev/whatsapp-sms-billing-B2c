import axios from 'axios'

const TENANT_ID = import.meta.env.VITE_TENANT_ID || ''

export const api = axios.create({
  baseURL: `/api/v1/tenants/${TENANT_ID}`,
  headers: { 'Content-Type': 'application/json' },
})

export const setTenant = (tenantId: string) => {
  api.defaults.baseURL = `/api/v1/tenants/${tenantId}`
}
