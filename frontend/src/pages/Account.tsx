import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

function formatDate(sqlDate: string | null): string {
  if (!sqlDate) return 'unknown'
  return new Date(sqlDate.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, {
    year: 'numeric', month: 'long', day: 'numeric',
  })
}

function addDays(sqlDate: string | null, days: number): string | null {
  if (!sqlDate) return null
  const d = new Date(sqlDate.replace(' ', 'T') + 'Z')
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 19).replace('T', ' ')
}

// The pilot's cockpit: account details plus the 180-day password schedule.
export default function Account() {
  const { user, ready, logout, changePassword } = useAuth()
  const navigate = useNavigate()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null)

  if (!ready) return <p className="status section">Loading your cockpit…</p>
  if (!user) return <Navigate to="/login" replace />

  const maxAge = user.password_max_age_days
  const age = user.password_age_days
  const daysLeft = Math.max(0, maxAge - age)
  const pct = Math.min(100, Math.round((age / maxAge) * 100))
  const dueDate = addDays(user.password_changed_at, maxAge)

  async function handleChange(e: FormEvent) {
    e.preventDefault()
    setNote(null)
    if (next !== confirm) {
      setNote({ ok: false, text: 'The new passwords do not match.' })
      return
    }
    try {
      await changePassword(current, next)
      setCurrent('')
      setNext('')
      setConfirm('')
      setNote({ ok: true, text: `Password updated. Your next check is in ${maxAge} days.` })
    } catch (err) {
      setNote({ ok: false, text: (err as Error).message })
    }
  }

  return (
    <section className="section">
      <p className="eyebrow">Your Cockpit</p>
      <h1>Welcome aboard, {user.rank} {user.first_name}!</h1>

      <div className="cockpit-grid">
        <div className="form-card">
          <h2>Pilot Record</h2>
          <dl className="pilot-record">
            <dt>Rank</dt><dd>{user.rank}</dd>
            <dt>Name</dt><dd>{user.first_name} {user.last_name}</dd>
            <dt>Email</dt><dd>{user.email}</dd>
            <dt>Enlisted</dt><dd>{formatDate(user.created_at)}</dd>
          </dl>
          <button
            className="btn btn-ghost"
            onClick={() => {
              logout()
              navigate('/login')
            }}
          >
            Log Out
          </button>
        </div>

        <div className={`form-card schedule${user.password_change_due ? ' due' : ''}`}>
          <h2>Password Maintenance Schedule</h2>
          <p>
            Like a pre-flight check, we ask every pilot to refresh their password every <strong>{maxAge} days</strong>.
            Change it sooner if you ever think someone else knows it.
          </p>
          <div className="fuel-gauge" aria-label={`Password is ${age} of ${maxAge} days old`}>
            <div className="fuel-fill" style={{ width: `${pct}%` }} />
          </div>
          <p className="gauge-caption">
            Last changed {formatDate(user.password_changed_at)} · {age} days ago ·{' '}
            {user.password_change_due ? (
              <strong>Change Due Now</strong>
            ) : (
              <>next check due {formatDate(dueDate)} ({daysLeft} days left)</>
            )}
          </p>

          <form className="change-form" onSubmit={handleChange}>
            <label>
              Current password
              <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required />
            </label>
            <label>
              New password
              <input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" minLength={8} required />
            </label>
            <label>
              Confirm new password
              <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" minLength={8} required />
            </label>
            <button type="submit" className="btn btn-primary">Change Password</button>
            {note && <p className={`status${note.ok ? ' ok' : ' error'}`} role="status">{note.text}</p>}
          </form>
        </div>
      </div>
    </section>
  )
}
