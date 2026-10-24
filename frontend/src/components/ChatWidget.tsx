import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { Headset } from './Icons'
import type { ProductCard } from '../api'
import { useAuth, type User } from '../auth'
import { useChatResults } from '../chatResults'

interface ChatMessage {
  role: 'user' | 'assistant' | 'divider'
  content: string
  time?: string // Zulu (UTC) time, the way pilots and controllers log radio calls
}

// "2026-10-24 13:42:05" (UTC from the database) or now -> "1342Z"
function zulu(utc?: string): string {
  const d = utc ? new Date(utc.replace(' ', 'T') + 'Z') : new Date()
  return `${String(d.getUTCHours()).padStart(2, '0')}${String(d.getUTCMinutes()).padStart(2, '0')}Z`
}

interface ChatAnswer {
  reply: string
  products: ProductCard[]
}

interface PageContext {
  path: string
  product_id: string | null
  recent_product_ids: string[]
}


function greeting(user: User | null): ChatMessage {
  return {
    role: 'assistant',
    content: user
      ? `${user.callsign}, Yale Tower, welcome back, ${user.rank} ${user.first_name}! Radio check loud and clear. Ask me about gear, prices or sizes. Over.`
      : 'Yale Tower, this is Chloe. Radio check loud and clear! Ask me about our gear, prices or sizes. Over.',
  }
}

function productIdFrom(pathname: string): string | null {
  const m = pathname.match(/^\/products\/([^/]+)$/)
  return m ? decodeURIComponent(m[1]) : null
}

// Which page is open (so "this one" means the product on screen), plus the last few item
// pages visited (so "the one I looked at before" works too).
function pageContext(pathname: string, recent: string[]): PageContext {
  return { path: pathname, product_id: productIdFrom(pathname), recent_product_ids: recent }
}

// Sends the pilot's message, the page they're on and (for guests) this visit's recent lines to FastAPI.
// Logged-in pilots send their token instead; the backend loads and saves their flight log.
async function sendToBackend(
  message: string,
  history: ChatMessage[],
  page: PageContext,
  token: string | null,
): Promise<ChatAnswer> {
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({
        message,
        page,
        history: token
          ? []
          : history.filter((m) => m.role !== 'divider').slice(1).slice(-8).map(({ role, content }) => ({ role, content })),
      }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) return { reply: `Bulldog, Yale Tower, ${data.detail ?? 'radio trouble, say again.'} Over.`, products: [] }
    return { reply: data.reply, products: data.products ?? [] }
  } catch {
    return {
      reply: 'Bulldog, Yale Tower, no signal from the tower. Check that the backend is running and say again. Over.',
      products: [],
    }
  }
}

export default function ChatWidget() {
  const { user, token, ready } = useAuth()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting(null)])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const recentRef = useRef<string[]>([]) // item pages visited this visit, newest first
  const { show: showResults } = useChatResults()

  // Follow the shopper: remember the last 5 item pages they opened.
  useEffect(() => {
    const id = productIdFrom(pathname)
    if (id) recentRef.current = [id, ...recentRef.current.filter((x) => x !== id)].slice(0, 5)
  }, [pathname])

  // Reload the flight log whenever the pilot changes: saved chats from the database for
  // logged-in pilots; guests start fresh.
  useEffect(() => {
    if (!ready) return
    if (!user || !token) {
      // Guests can chat, but nothing is kept after they leave: only logged-in pilots get a flight log.
      try {
        localStorage.removeItem('cc_guest_flight_log') // clear any log saved by an earlier version
      } catch {
        // storage blocked: nothing to clear
      }
      setMessages([greeting(null)])
      return
    }
    let cancelled = false
    fetch('/api/chat/history', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: { turns: { role: 'user' | 'assistant'; content: string; created_at: string }[] }) => {
        if (cancelled) return
        const past = d.turns.map((t) => ({ role: t.role, content: t.content, time: zulu(t.created_at) }))
        // Say "welcome back" only after a real break (30+ minutes since the last call),
        // so reloading a page mid-chat doesn't make Chloe greet the pilot again.
        const last = d.turns[d.turns.length - 1]?.created_at
        const onBreak = !last || Date.now() - new Date(last.replace(' ', 'T') + 'Z').getTime() > 30 * 60 * 1000
        setMessages(
          past.length
            ? [
                { role: 'divider', content: `📜 Flight log restored: ${past.length} transmissions` },
                ...past,
                ...(onBreak ? [greeting(user)] : []),
              ]
            : [greeting(user)],
        )
      })
      .catch(() => !cancelled && setMessages([greeting(user)]))
    return () => {
      cancelled = true
    }
  }, [ready, user?.id, token]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, open])

  async function handleSend(e: FormEvent) {
    e.preventDefault()
    const text = draft.trim()
    if (!text || sending) return
    setDraft('')
    const history = messages
    setMessages((m) => [...m, { role: 'user', content: text, time: zulu() }])
    setSending(true)
    const { reply, products } = await sendToBackend(text, history, pageContext(pathname, recentRef.current), token)
    setMessages((m) => [...m, { role: 'assistant', content: reply, time: zulu() }])
    if (products.length) showResults(products, text) // put the matches on the page
    setSending(false)
  }

  return (
    <div className="chat-root">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Chat with Chloe">
          <div className="chat-header">
            <Headset className="chat-headset" />
            <div className="chat-title">
              <strong>Chloe · Yale Tower</strong>
              <span>
                <i className="live-dot" /> 122.8 · {user ? `Callsign: ${user.callsign}` : 'Guest pilot'}
              </span>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>
          <div className="radio-grill" aria-hidden="true" />
          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) =>
              m.role === 'divider' ? (
                <div key={i} className="chat-divider">{m.content}</div>
              ) : (
                <div key={i} className={`chat-bubble ${m.role}`}>
                  <span className="callsign">
                    {m.role === 'assistant' ? 'CHLOE · YALE TOWER' : user ? user.callsign.toUpperCase() : 'YOU'}
                    {m.time && <span className="zulu"> · {m.time}</span>}
                  </span>
                  {m.content}
                </div>
              ),
            )}
            {sending && <div className="chat-bubble assistant typing">📡 Transmitting…</div>}
          </div>
          <form className="chat-input" onSubmit={handleSend}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Push to talk: hoodies under $70, sizes, Handsome Dan…"
              aria-label="Chat message"
            />
            <button type="submit" className="ptt" disabled={!draft.trim() || sending}>📻 Transmit</button>
          </form>
        </div>
      )}
      <button
        className="chat-launcher"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat with Chloe'}
      >
        {open ? '×' : (
          <>
            <Headset className="launcher-headset" />
            Radio Chloe
          </>
        )}
      </button>
    </div>
  )
}
