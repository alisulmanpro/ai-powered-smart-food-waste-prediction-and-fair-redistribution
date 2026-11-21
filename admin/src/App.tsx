import { useEffect, useState, type FormEvent } from 'react'
import { api, API_URL, hasToken, setToken, type Me } from './api/client'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking...')
  const [me, setMe] = useState<Me | null>(null)
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin12345')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .health()
      .then((h) => setApiStatus(`API ${h.status}, database ${h.database}`))
      .catch(() => setApiStatus(`API not reachable at ${API_URL}`))
    if (hasToken()) api.me().then(setMe).catch(() => setToken(null))
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.login(email, password)
      setMe(await api.me())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  function logout() {
    setToken(null)
    setMe(null)
  }

  return (
    <div className="page">
      <h1>Food Waste Admin Panel</h1>
      <p className="muted">{apiStatus}</p>

      {me ? (
        <div className="card">
          <p>
            Signed in as <strong>{me.name}</strong> ({me.role})
          </p>
          <p className="muted">Build the admin screens from here (see docs/implementation.md, section 9).</p>
          <button onClick={logout}>Sign out</button>
        </div>
      ) : (
        <form className="card" onSubmit={onSubmit}>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          </label>
          <label>
            Password
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Sign in</button>
        </form>
      )}
    </div>
  )
}
