import { StatusBar } from 'expo-status-bar'
import { useEffect, useState } from 'react'
import { ActivityIndicator, StyleSheet, View } from 'react-native'
import { ApiError, API_URL, api, getToken, setToken, type Me } from './src/api/client'
import { ErrorBanner } from './src/components/ui'
import AuthScreen from './src/screens/AuthScreen'
import HomeScreen from './src/screens/HomeScreen'

export default function App() {
  const [booting, setBooting] = useState(true)
  const [me, setMe] = useState<Me | null>(null)
  const [apiOffline, setApiOffline] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function boot() {
      api.health().catch(() => {
        if (!cancelled) setApiOffline(true)
      })
      const token = await getToken()
      if (token) {
        try {
          const user = await api.me()
          if (!cancelled) setMe(user)
        } catch (err) {
          if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
            await setToken(null)
          }
        }
      }
      if (!cancelled) setBooting(false)
    }
    boot()
    return () => {
      cancelled = true
    }
  }, [])

  async function onLogout() {
    await setToken(null)
    setMe(null)
  }

  return (
    <View style={styles.root}>
      {apiOffline ? (
        <View style={styles.bannerWrap}>
          <ErrorBanner message={`Cannot reach the API at ${API_URL}. Check your connection.`} />
        </View>
      ) : null}
      {booting ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#2f855a" />
        </View>
      ) : me ? (
        <HomeScreen me={me} onLogout={onLogout} />
      ) : (
        <AuthScreen onAuthed={setMe} />
      )}
      <StatusBar style="auto" />
    </View>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f5f7fa' },
  bannerWrap: { paddingTop: 48, paddingHorizontal: 16 },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },
})
