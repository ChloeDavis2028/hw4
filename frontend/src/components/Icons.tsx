// Hand-drawn SVG icons for the aviation theme. They use currentColor so CSS sets the color.

interface IconProps {
  className?: string
  title?: string
}

// C-130 Hercules seen from above, nose pointing right: high straight wing, four propeller engines.
export function C130({ className, title }: IconProps) {
  const engines = [24, 46, 94, 116]
  return (
    <svg viewBox="0 0 200 140" className={className} role={title ? 'img' : undefined} aria-hidden={title ? undefined : true}>
      {title && <title>{title}</title>}
      <g fill="currentColor">
        {/* fuselage with rounded nose */}
        <rect x="22" y="62" width="150" height="16" rx="8" />
        <ellipse cx="172" cy="70" rx="14" ry="7" />
        {/* tail plane */}
        <rect x="22" y="38" width="14" height="64" rx="4" />
        {/* main wing */}
        <rect x="98" y="6" width="18" height="128" rx="5" />
        {/* engines */}
        {engines.map((y) => (
          <rect key={y} x="112" y={y - 4} width="16" height="8" rx="4" />
        ))}
      </g>
      {/* spinning propellers */}
      <g className="props" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
        {engines.map((y) => (
          <line key={y} x1="131" y1={y - 10} x2="131" y2={y + 10} />
        ))}
      </g>
    </svg>
  )
}

export function Headset({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
      <rect x="2.5" y="13" width="4" height="7" rx="1.5" />
      <rect x="17.5" y="13" width="4" height="7" rx="1.5" />
      <path d="M19.5 20c0 1.5-2 2.5-5 2.5h-2" />
    </svg>
  )
}
