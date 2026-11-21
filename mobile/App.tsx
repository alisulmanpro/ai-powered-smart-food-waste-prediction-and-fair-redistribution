import { StatusBar } from 'expo-status-bar'
import { useEffect, useState } from 'react'
import { Button, StyleSheet, Text, TextInput, View } from 'react-native'
import { api, API_URL, getToken, setToken, type Me } from './src/api/client'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking...')
  const [me, setMe] = useState<Me | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .health()
      .then((h) => setApiStatus(`API ${h.status}, database ${h.database}`))
      .catch(() => setApiStatus(`API not reachable at ${API_URL}`))
    getToken().then((t) => {
      if (t) api.me().then(setMe).catch(() => setToken(null))
    })
  }, [])

  async function onLogin() {
    setError(null)
    try {
      await api.login(email.trim(), password)
      setMe(await api.me())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  async function onLogout() {
    await setToken(null)
    setMe(null)
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Food Waste Redistribution</Text>
      <Text style={styles.muted}>{apiStatus}</Text>

      {me ? (
        <View style={styles.card}>
          <Text>
            Signed in as {me.name} ({me.role})
          </Text>
          <Button title="Sign out" onPress={onLogout} />
        </View>
      ) : (
        <View style={styles.card}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            autoCapitalize="none"
            keyboardType="email-address"
            value={email}
            onChangeText={setEmail}
          />
          <TextInput
            style={styles.input}
            placeholder="Password"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />
          {error && <Text style={styles.error}>{error}</Text>}
          <Button title="Sign in" onPress={onLogin} />
        </View>
      )}
      <StatusBar style="auto" />
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f7fa', padding: 24, justifyContent: 'center' },
  title: { fontSize: 22, fontWeight: '600', marginBottom: 8 },
  muted: { color: '#616e7c', marginBottom: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, gap: 12 },
  input: { borderWidth: 1, borderColor: '#cbd2d9', borderRadius: 8, padding: 10, fontSize: 16 },
  error: { color: '#c53030' },
})
