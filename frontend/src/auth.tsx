import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

// Account state shared by the whole site. The backend issues a signed token on
// sign-up/login; we keep it in localStorage and send it as a Bearer header.

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  rank: string
  callsign: string
  email: string
  created_at: string
  password_changed_at: string | null
  password_age_days: number
  password_max_age_days: number
  password_change_due: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  ready: boolean
  login: (email: string, password: string) => Promise<User>
  register: (data: { first_name: string; last_name: string; email: string; password: string }) => Promise<User>
  changePassword: (current_password: string, new_password: string) => Promise<User>
  logout: () => void
}

const TOKEN_KEY = 'cc_token'
const AuthContext = createContext<AuthState | null>(null)

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function saveToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Storage blocked: the session just won't survive a reload.
  }
}

async function post<T>(url: string, body: unknown, token?: string | null): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail ?? `Request failed (${res.status})`)
  return data as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(readToken)
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  // On load, ask the backend who the saved token belongs to.
  useEffect(() => {
    if (!token) {
      setReady(true)
      return
    }
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => setUser(d.user))
      .catch(() => {
        saveToken(null)
        setToken(null)
      })
      .finally(() => setReady(true))
    // only on first load
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function signIn(data: { token: string; user: User }): User {
    saveToken(data.token)
    setToken(data.token)
    setUser(data.user)
    return data.user
  }

  const value: AuthState = {
    user,
    token,
    ready,
    login: async (email, password) => signIn(await post('/api/auth/login', { email, password })),
    register: async (data) => signIn(await post('/api/auth/register', data)),
    changePassword: async (current_password, new_password) =>
      signIn(await post('/api/auth/change-password', { current_password, new_password }, token)),
    logout: () => {
      saveToken(null)
      setToken(null)
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
