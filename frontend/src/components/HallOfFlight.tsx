import { Link } from 'react-router-dom'

// "Hall of Flight": pioneering women aviators, to inspire young flyers of every background.
const PIONEERS = [
  { name: 'Harriet Quimby', year: '1911', first: 'First American woman to earn a pilot\'s license. A year later she flew across the English Channel.' },
  { name: 'Bessie Coleman', year: '1921', first: 'First African American woman to earn a pilot\'s license. She had to go to France to train when U.S. schools turned her away.' },
  { name: 'Amelia Earhart', year: '1932', first: 'First woman to fly solo nonstop across the Atlantic.' },
  { name: 'Sally Ride', year: '1983', first: 'First American woman in space, aboard the Space Shuttle Challenger.' },
  { name: 'Eileen Collins', year: '1999', first: 'First woman to command a Space Shuttle mission, after being its first woman pilot in 1995.' },
]

export default function HallOfFlight() {
  return (
    <section className="section hall">
      <p className="eyebrow">Hall of Flight</p>
      <h2>They Cleared the Runway: Now It's Your Turn</h2>
      <p className="lede">
        Every pilot starts as a first-timer. These women flew first, often when people said they couldn't.
      </p>
      <ol className="hall-strip">
        {PIONEERS.map((p) => (
          <li key={p.name} className="hall-card">
            <span className="hall-year">{p.year}</span>
            <h3>{p.name}</h3>
            <p>{p.first}</p>
          </li>
        ))}
      </ol>
      <div className="future-flyers">
        <div>
          <strong>🪽 Future flyers welcome.</strong> Young aviators, first-years, families and dreamers: create an
          account to earn your wings. You'll get a pilot rank, your own radio callsign, and Chloe on the frequency.
        </div>
        <Link to="/create-account" className="btn btn-gold">Earn Your Wings</Link>
      </div>
    </section>
  )
}
