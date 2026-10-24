// "Dan approved" badge: a round crop of the real Handsome Dan XIX (Kingman) photo.
// Photo by Joeshmonobody, CC BY-SA 4.0, via Wikimedia Commons (credited in the footer and on About).

export const DAN_PHOTO = '/brand/handsome-dan-kingman.jpg'

interface Props {
  size?: 'small' | 'large'
}

export default function DanBadge({ size = 'small' }: Props) {
  return (
    <span className={`dan-badge dan-badge-${size}`}>
      {/* zoomed in on Dan's face: the photo is shown as a background so it can be cropped tightly */}
      <span className="dan-face" role="img" aria-label="Handsome Dan" style={{ backgroundImage: `url(${DAN_PHOTO})` }} />
      <span className="dan-badge-label">Dan approved</span>
    </span>
  )
}
