// Real C-130 airdrops from Operation Christmas Drop. U.S. Air Force photos: public domain,
// credited anyway with a link to each Wikimedia Commons source page.
const CARGO_DROPS = [
  {
    src: '/brand/c130-drop-over-fais.jpg',
    alt: 'A C-130 Hercules flies low over the green island of Fais as a supply bundle floats down under its parachute',
    caption: 'A C-130 Hercules drops a bundle of donated goods to the island of Fais, December 8, 2015.',
    credit: 'U.S. Air Force photo by Senior Airman Katrina Brisbin',
    source: 'https://commons.wikimedia.org/wiki/File:US,_RAAF_and_JASDF_launch_Operation_Christmas_Drop_2015_151208-F-EP111-010.jpg',
  },
  {
    src: '/brand/c130-ramp-view-fassari.jpg',
    alt: 'View from the open cargo ramp of a C-130J as two bundles descend toward a turquoise lagoon',
    caption: 'From the open ramp of a C-130J, two bundles descend toward Fassari, December 10, 2024.',
    credit: 'U.S. Air Force photo by Senior Airman Natalie Doan',
    source: 'https://commons.wikimedia.org/wiki/File:36_AS_delivers_Christmas_bundles_during_OCD_2024_(8793350).jpg',
  },
  {
    src: '/brand/c130j-bundles-release.jpg',
    alt: 'Parachute bundles leave the ramp of a C-130J over the ocean near a forested island',
    caption: 'A C-130J Super Hercules releases a bundle over Oneop, December 3, 2023.',
    credit: 'U.S. Air Force photo by Senior Airman Brooklyn Golightly',
    source: 'https://commons.wikimedia.org/wiki/File:Operation_Christmas_Drop_23_begins_(8160709).jpg',
  },
]

export default function About() {
  return (
    <div className="about">
      <section className="section">
        <p className="eyebrow">About Us</p>
        <h1>A New Haven Shop with a Whole Lot of Blue in Its Blood</h1>
        <p>
          Campus Customs is the neighborhood spot for officially licensed Yale apparel. We set up shop on
          Broadway, just steps from the colleges, so students, families, alumni and visitors could find
          gear that feels as good as the memories that come with it.
        </p>
      </section>

      <section className="section about-grid">
        <div className="about-card">
          <h3>What We Believe</h3>
          <p>
            Merch should be comfortable enough to live in and sturdy enough to survive four years of
            dining-hall spills, Harvard-Yale tailgates and laundry-room adventures.
          </p>
        </div>
        <div className="about-card">
          <h3>Who We Serve</h3>
          <p>
            First-years, seniors, proud parents, grandparents, grad students and every alum who still
            hums "Bright College Years" in the shower. If Yale is part of your story, you belong here.
          </p>
        </div>
        <div className="about-card">
          <h3>What You'll Find</h3>
          <p>
            Tees, crewnecks, hoodies, quarter-zips and jackets, with designs for residential colleges,
            varsity sports and the professional schools.
          </p>
        </div>
      </section>

      <section className="section dan-section">
        <figure className="dan-photo">
          <img src="/brand/handsome-dan-kingman.jpg" alt="Handsome Dan XIX, a white English bulldog with a blue Y bandana, on Cross Campus" />
          <figcaption>
            Handsome Dan XIX ("Kingman") on Cross Campus, March 2022. Photo by{' '}
            <a href="https://commons.wikimedia.org/wiki/User:Joeshmonobody" target="_blank" rel="noreferrer">Joeshmonobody</a>,{' '}
            <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>, via{' '}
            <a href="https://commons.wikimedia.org/wiki/File:Handsome_Dan_Kingman.jpg" target="_blank" rel="noreferrer">Wikimedia Commons</a>.
          </figcaption>
        </figure>
        <div>
          <h2>Our Inspiration: Handsome Dan</h2>
          <p>
            Yale has had a bulldog mascot since 1889, and every Handsome Dan has the same job: look tough,
            stay lovable. The current Dan, Kingman, is our co-pilot: look for his "Dan Approved" badge on
            every product in the shop.
          </p>
        </div>
      </section>

      <section className="section cargo-drop">
        <p className="eyebrow">Inspired by Real Aircrews</p>
        <h2>The Real Cargo Drop</h2>
        <p>
          Every December since 1952, C-130 crews fly Operation Christmas Drop, the Department of Defense's
          longest-running humanitarian airlift. They parachute bundles of food, school supplies and gifts to remote islands
          across Micronesia. The cargo-drop reels on our product cards are a small salute to their work.
        </p>
        <div className="drop-gallery">
          {CARGO_DROPS.map((photo) => (
            <figure key={photo.src} className="drop-photo">
              <img src={photo.src} alt={photo.alt} loading="lazy" />
              <figcaption>
                {photo.caption}{' '}
                <a href={photo.source} target="_blank" rel="noreferrer">{photo.credit}</a>, public domain, via
                Wikimedia Commons.
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="section visit">
        <h2>Come Say Hello</h2>
        <p>
          Stop by <strong>57 Broadway, New Haven, CT 06511</strong>. Can't make it in person? Shop online
          any time, and if you need help with an order, our chat helper or{' '}
          <strong>orderdept@campuscustoms.com</strong> has your back.
        </p>
      </section>
    </div>
  )
}
