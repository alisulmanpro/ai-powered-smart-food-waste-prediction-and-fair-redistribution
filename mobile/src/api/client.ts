import { Platform } from 'react-native'
import * as SecureStore from 'expo-secure-store'

// Phone/emulator cannot reach "localhost" of your laptop. Set EXPO_PUBLIC_API_URL in mobile/.env
// (see .env.example). The fallbacks below only work for the Android emulator / web.
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000')
const API_PREFIX = '/api/v1'
const TOKEN_KEY = 'access_token'

export type Me = {
  id: number
  name: string
  email: string
  role: 'donor' | 'recipient' | 'admin'
  is_active: boolean
}

// Tokens are kept in the device keystore, passwords are never stored (NFR-SC-06).
// SecureStore has no web implementation, so fall back to memory there.
let memoryToken: string | null = null
const canUseSecureStore = Platform.OS !== 'web'

export async function getToken(): Promise<string | null> {
  return canUseSecureStore ? SecureStore.getItemAsync(TOKEN_KEY) : memoryToken
}

export async function setToken(token: string | null): Promise<void> {
  if (!canUseSecureStore) {
    memoryToken = token
    return
  }
  if (token) await SecureStore.setItemAsync(TOKEN_KEY, token)
  else await SecureStore.deleteItemAsync(TOKEN_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = await getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
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
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
    })
    await setToken(data.access_token)
  },
  async register(name: string, email: string, password: string, role: 'donor' | 'recipient') {
    return request<Me>('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role }),
    })
  },
}
