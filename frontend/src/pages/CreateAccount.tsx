import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import WhizWheel from '../components/WhizWheel'

// New pilots: saved straight into the users table with a hashed password.
export default function CreateAccount() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const typed = Object.values(form).join('').length
  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Those passwords do not match. Try again?')
      return
    }
    setBusy(true)
    try {
      // "confirm" is only checked here in the browser; the server gets the four account fields.
      const { first_name, last_name, email, password } = form
      await register({ first_name, last_name, email, password })
      navigate('/account')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section form-page">
      <p className="eyebrow">New Pilots</p>
      <h1>Join the Campus Customs Crew</h1>
      <p className="lede">
        Spin up your whiz wheel and earn your wings: every new pilot gets a rank and a radio callsign. Already flying with us? <Link to="/login">Returning pilots log in here</Link>.
      </p>
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="pilot-card-head">
          <WhizWheel turns={typed} label="ENLIST" />
          <p>Every field you fill turns the dial. Your password is hashed before it ever touches the database.</p>
        </div>
        <div className="form-row">
          <label>
            First name
            <input value={form.first_name} onChange={update('first_name')} autoComplete="given-name" required />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update('last_name')} autoComplete="family-name" required />
          </label>
        </div>
        <label>
          Email
          <input type="email" value={form.email} onChange={update('email')} autoComplete="email" required />
        </label>
        <label>
          Password <span className="hint">(at least 8 characters)</span>
          <input type="password" value={form.password} onChange={update('password')} autoComplete="new-password" minLength={8} required />
        </label>
        <label>
          Confirm password
          <input type="password" value={form.confirm} onChange={update('confirm')} autoComplete="new-password" minLength={8} required />
        </label>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? 'Filing your flight plan…' : 'Create Account'}
        </button>
        {error && <p className="status error" role="alert">{error}</p>}
      </form>
    </section>
  )
}
