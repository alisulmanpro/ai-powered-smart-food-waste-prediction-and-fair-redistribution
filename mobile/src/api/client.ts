import { Platform } from 'react-native'
import * as SecureStore from 'expo-secure-store'

// Phone/emulator cannot reach "localhost" of your laptop. Set EXPO_PUBLIC_API_URL in mobile/.env
// (see .env.example). The fallbacks below only work for the Android emulator / web.
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000')
const API_PREFIX = '/api/v1'
const TOKEN_KEY = 'access_token'

export type Role = 'donor' | 'recipient'
export type AnyRole = Role | 'admin'

export type User = {
  id: number
  name: string
  email: string
  role: AnyRole
  is_active: boolean
  email_verified: boolean
}

export type DonorProfile = {
  business_name: string
  business_type: string | null
  address: string | null
  latitude: number | null
  longitude: number | null
}

export type RecipientProfile = {
  organisation_name: string
  address: string | null
  latitude: number | null
  longitude: number | null
  capacity_units: number
  storage_types: string[]
  accepted_categories: string[]
  open_from: string | null
  open_to: string | null
  need_level: number
  verified: boolean
}

export type Me = User & {
  donor_profile: DonorProfile | null
  recipient_profile: RecipientProfile | null
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
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
  // Abort slow/unreachable requests so the UI shows an error instead of spinning forever.
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 15000)
  let res: Response
  try {
    res = await fetch(`${API_URL}${API_PREFIX}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(
        `Request timed out. Cannot reach the API at ${API_URL}. Check your connection.`,
        0,
      )
    }
    throw new ApiError(
      `Cannot reach the API at ${API_URL}. Check your connection.`,
      0,
    )
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = body.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? 'Invalid input').join('; ')
          : `Request failed (${res.status})`
    throw new ApiError(message, res.status)
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
  async register(name: string, email: string, password: string, role: Role) {
    return request<User>('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role }),
    })
  },
  verifyEmail: (token: string) =>
    request<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    }),
  resendVerification: (email: string) =>
    request<{ message: string }>('/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }),
}
