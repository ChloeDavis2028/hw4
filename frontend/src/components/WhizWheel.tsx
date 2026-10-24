// An E6B "whiz wheel" flight computer. The inner disc turns as the pilot types,
// like dialing in a calculation. Purely decorative.

interface Props {
  turns: number
  label?: string
}

const OUTER = Array.from({ length: 36 }, (_, i) => i * 10)
const INNER = Array.from({ length: 12 }, (_, i) => i * 30)

export default function WhizWheel({ turns, label = 'E6B' }: Props) {
  return (
    <div className="whiz" aria-hidden="true">
      <svg viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="96" className="whiz-outer" />
        {OUTER.map((deg) => (
          <line
            key={deg}
            x1="100" y1="6" x2="100" y2={deg % 30 === 0 ? 20 : 13}
            className="whiz-tick"
            transform={`rotate(${deg} 100 100)`}
          />
        ))}
        {INNER.map((deg, i) => (
          <text key={deg} x="100" y="34" className="whiz-num" transform={`rotate(${deg} 100 100)`}>
            {(i + 1) * 10}
          </text>
        ))}
        <g className="whiz-inner" style={{ transform: `rotate(${turns * 17}deg)` }}>
          <circle cx="100" cy="100" r="58" />
          {INNER.map((deg, i) => (
            <text key={deg} x="100" y="58" className="whiz-inner-num" transform={`rotate(${deg} 100 100)`}>
              {i * 5}
            </text>
          ))}
          <line x1="100" y1="100" x2="100" y2="46" className="whiz-needle" />
        </g>
        <circle cx="100" cy="100" r="22" className="whiz-hub" />
        <text x="100" y="104" className="whiz-label">{label}</text>
      </svg>
    </div>
  )
}
