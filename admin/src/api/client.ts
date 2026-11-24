export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const API_PREFIX = '/api/v1'

export type Me = {
  id: number
  name: string
  email: string
  role: 'donor' | 'recipient' | 'admin'
  is_active: boolean
  email_verified: boolean
}

let accessToken: string | null = localStorage.getItem('access_token')

export function setToken(token: string | null) {
  accessToken = token
  if (token) localStorage.setItem('access_token', token)
  else localStorage.removeItem('access_token')
}

export function hasToken() {
  return accessToken !== null
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  const res = await fetch(`${API_URL}${API_PREFIX}${path}`, { ...init, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; database: string }>('/health'),
  me: () => request<Me>('/users/me'),
  async login(email: string, password: string) {
    // OAuth2 password flow: form-encoded, the email goes in "username"
    const data = await request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username: email, password }),
    })
    setToken(data.access_token)
  },
}
