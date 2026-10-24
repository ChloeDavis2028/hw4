import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { C130 } from './Icons'

// Where the C-130 is "landing" for each route.
function destination(pathname: string): string {
  if (pathname === '/') return 'Home Base'
  if (pathname === '/products') return 'Products'
  if (pathname.startsWith('/products/')) return 'your item'
  if (pathname === '/about') return 'About Us'
  if (pathname === '/login') return 'Log In'
  if (pathname === '/create-account') return 'Create Account'
  return 'Home Base'
}

// Every page change sends a C-130 across the top of the screen with a "now arriving" call.
export default function FlightOverlay() {
  const { pathname } = useLocation()
  const [flight, setFlight] = useState(0)
  const first = useRef(true)

  useEffect(() => {
    window.scrollTo(0, 0)
    if (first.current) {
      first.current = false
      return
    }
    setFlight((f) => f + 1)
  }, [pathname])

  if (flight === 0) return null

  return (
    <div className="flight-overlay" key={flight} aria-hidden="true">
      <div className="flight-path">
        <span className="contrail" />
        <C130 className="flight-plane" />
      </div>
      <div className="arrival-call">✈ Now arriving: {destination(pathname)}</div>
    </div>
  )
}
