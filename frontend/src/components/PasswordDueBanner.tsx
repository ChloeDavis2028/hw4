import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'

// Site-wide reminder once a logged-in pilot's password reaches the 180-day mark.
export default function PasswordDueBanner() {
  const { user } = useAuth()
  const { pathname } = useLocation()
  if (!user?.password_change_due || pathname === '/account') return null
  return (
    <div className="due-banner" role="status">
      ⚠ {user.rank} {user.first_name}, your password is {user.password_age_days} days old and due for its
      {' '}{user.password_max_age_days}-day check. <Link to="/account">Update it in your cockpit</Link>
    </div>
  )
}
