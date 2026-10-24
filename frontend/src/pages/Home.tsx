import { Link } from 'react-router-dom'
import { C130 } from '../components/Icons'
import DeparturesBoard from '../components/DeparturesBoard'
import HallOfFlight from '../components/HallOfFlight'

const CATEGORIES = [
  { title: 'Tees', note: 'Light, easy layers for warm days on Old Campus.' },
  { title: 'Crewnecks', note: 'The classic sweatshirt for lectures and late nights.' },
  { title: 'Hoodies', note: 'Hood up for the walk down Hillhouse in November.' },
  { title: 'Quarter-Zips & Fleece', note: 'Polished enough for a case interview, warm enough for the Bowl.' },
]

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-text">
          <p className="eyebrow">Wheels Up, Bulldogs</p>
          <h1>Wear Your Bulldog Spirit Every Day</h1>
          <p className="phonetic" aria-label="YALE in the pilot's phonetic alphabet: Yankee, Alpha, Lima, Echo">
            <span>Y</span>ankee · <span>A</span>lpha · <span>L</span>ima · <span>E</span>cho
          </p>
          <p>
            From your first week on campus to the reunion you swear you won't cry at, Campus Customs has
            the Yale gear that shows where your heart lives. Climb aboard our C-130, cruise from rack to
            rack, and land on a soft new favorite for yourself or the crew cheering you on back home.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary">✈ Fly to the Gear</Link>
            <Link to="/about" className="btn btn-ghost">Meet the Crew</Link>
          </div>
          <p className="all-aboard">
            🎫 All aboard: Yale students, families, alumni, New Haven neighbors and every aviation fan. No Yale ID required.
          </p>
        </div>
        <div className="hero-sky" aria-hidden="true">
          <span className="cloud cloud-1" />
          <span className="cloud cloud-2" />
          <C130 className="hero-plane" />
          <span className="runway" />
        </div>
      </section>

      <DeparturesBoard />

      <section className="section">
        <h2>Find Your Fit</h2>
        <div className="category-grid">
          {CATEGORIES.map((c) => (
            <Link to="/products" key={c.title} className="category-card">
              <h3>{c.title}</h3>
              <p>{c.note}</p>
            </Link>
          ))}
        </div>
      </section>

      <HallOfFlight />

      <section className="section split">
        <div>
          <h2>Something for Every Corner of Yale</h2>
          <p>
            Rep your residential college, your team, or your grad school. We carry designs for Saybrook,
            Pierson, Davenport and more, plus sports picks from hockey to sailing and pieces for the
            professional schools.
          </p>
        </div>
        <div>
          <h2>Questions? Radio Chloe</h2>
          <p>
            Pop on a headset and call Chloe, our air-traffic controller in the bottom corner. She checks live
            prices and sizes from the stockroom, puts matching gear on your radar, and remembers you if you log in.
          </p>
        </div>
      </section>
    </>
  )
}
