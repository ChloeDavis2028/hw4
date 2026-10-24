import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import WhizWheel from '../components/WhizWheel'

// The log-in flow starts here: returning pilots sign in, new pilots head to enlistment.
export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      navigate('/account')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section">
      <p className="eyebrow">Pilot Check-In</p>
      <h1>Which Pilot Are You Today?</h1>
      <p className="lede">Returning pilots sign in below. First flight with us? Enlist as a new pilot.</p>

      <div className="pilot-split">
        <form className="form-card pilot-card" onSubmit={handleSubmit}>
          <div className="pilot-card-head">
            <WhizWheel turns={email.length + password.length} />
            <div>
              <h2>Returning Pilots</h2>
              <p>Dial in your email and password to reach your cockpit.</p>
            </div>
          </div>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Checking instruments…' : 'Log In'}
          </button>
          {error && <p className="status error" role="alert">{error}</p>}
        </form>

        <div className="form-card pilot-card new-pilot">
          <h2>New Pilots</h2>
          <p>
            No account yet? Enlist in about a minute. You'll get a personal cockpit, and Chloe will remember
            you on your next flight.
          </p>
          <ul className="perk-list">
            <li>✈ Chloe greets you by name</li>
            <li>✈ Pick up your chats where you left off</li>
            <li>✈ Passwords locked down with salted hashing</li>
          </ul>
          <Link to="/create-account" className="btn btn-gold">Enlist as a New Pilot</Link>
        </div>
      </div>
    </section>
  )
}
