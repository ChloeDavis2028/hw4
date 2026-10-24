import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductCard } from './api'

// Products Chloe put on "radar" from the latest chat answer. The chat widget fills
// this; the RadarResults panel shows it at the top of whatever page is open.

interface Results {
  cards: ProductCard[]
  question: string
}

interface ChatResultsState extends Results {
  show: (cards: ProductCard[], question: string) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<Results>({ cards: [], question: '' })
  const value: ChatResultsState = {
    ...results,
    show: (cards, question) => setResults({ cards, question }),
    clear: () => setResults({ cards: [], question: '' }),
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
