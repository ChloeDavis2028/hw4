import { useEffect, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { C130 } from './Icons'
import { useAuth } from '../auth'

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]
// Guests see these; a logged-in pilot already has wings, so they get their pilot chip and Log Out instead.
const GUEST_LINKS = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account' },
]

// On phones (usability F5) the links fold behind a "Flight menu" button so products get the
// screen; on wider screens they always show. The menu closes after every page change.
export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => setMenuOpen(false), [pathname])

  return (
    <header className="navbar-wrap">
      <div className="navbar">
        <NavLink to="/" className="brand" aria-label="Campus Customs home">
          <C130 className="brand-plane" />
          <span className="brand-text">
            <span className="brand-top">YALE</span>
            <span className="brand-bottom">Campus Customs</span>
          </span>
        </NavLink>
        <button
          className="menu-toggle"
          onClick={() => setMenuOpen((o) => !o)}
          aria-expanded={menuOpen}
          aria-controls="main-nav"
        >
          {menuOpen ? '✕ Close' : '☰ Flight Menu'}
        </button>
        <nav id="main-nav" className={`nav-links${menuOpen ? ' open' : ''}`} aria-label="Main">
          {(user ? LINKS : [...LINKS, ...GUEST_LINKS]).map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                `nav-link${isActive ? ' active' : ''}${link.to === '/create-account' ? ' nav-cta' : ''}`
              }
            >
              {link.label}
            </NavLink>
          ))}
          {user && (
            <NavLink to="/account" className={({ isActive }) => `nav-link pilot-chip${isActive ? ' active' : ''}`}>
              ✈ {user.rank} {user.first_name}
            </NavLink>
          )}
          {user && (
            <button
              type="button"
              className="nav-link nav-logout"
              onClick={() => {
                logout()
                navigate('/')
              }}
            >
              Log Out
            </button>
          )}
        </nav>
      </div>
    </header>
  )
}
