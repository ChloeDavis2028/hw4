import { Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import Footer from './components/Footer'
import FlightOverlay from './components/FlightOverlay'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import ChatWidget from './components/ChatWidget'
import About from './pages/About'
import Login from './pages/Login'
import CreateAccount from './pages/CreateAccount'
import Account from './pages/Account'
import PasswordDueBanner from './components/PasswordDueBanner'
import RadarResults from './components/RadarResults'

function App() {
  const { pathname } = useLocation()
  return (
    <div className="app">
      <div className="announcement">
        ✈ Now boarding: official Yale gear, wheels up daily from 57 Broadway
      </div>
      <NavBar />
      <FlightOverlay />
      <PasswordDueBanner />
      <div className="page radar-wrap">
        <RadarResults />
      </div>
      {/* key restarts the "takeoff" entrance animation on every page change */}
      <main className="page page-enter" key={pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="/account" element={<Account />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}

export default App
