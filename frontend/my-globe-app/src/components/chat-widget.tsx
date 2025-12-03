"use client"

import { useState, useRef, useEffect } from "react"
import { MessageSquare, Send, X, Bot, Sparkles, ChevronRight } from "lucide-react"
import type { CountryStats } from "@/data/country-data"

interface ChatWidgetProps {
  countryData: CountryStats | null
}

interface Message {
  role: 'user' | 'bot'
  text: string
}

// Pre-made questions
const SUGGESTIONS = [
  "What is the #1 research field?",
  "What makes this country unique?",
  "Summarize the growth trends",
  "Any notable recent papers?",
]

export default function ChatWidget({ countryData }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: "Hi! Click a country and ask me about its research ecosystem." }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  
  const [showSuggestions, setShowSuggestions] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isOpen])

  const handleSend = async (textOverride?: string) => {
    const textToSend = textOverride || input
    if (!textToSend.trim()) return

    setInput("")
    setShowSuggestions(false)
    setMessages(prev => [...prev, { role: 'user', text: textToSend }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: textToSend, 
          countryData: countryData 
        })
      })
      
      const data = await res.json()
      
      if (data.response) {
        setMessages(prev => [...prev, { role: 'bot', text: data.response }])
      } else {
        throw new Error("No response")
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', text: "Connection error. Please try again." }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed bottom-6 left-6 z-50 flex flex-col items-start">
      {/* CHAT WINDOW */}
      {isOpen && (
        <div className="relative mb-4 h-[650px] w-[450px] flex flex-col overflow-hidden rounded-2xl border border-slate-700 bg-black/95 shadow-2xl backdrop-blur-xl animate-in slide-in-from-bottom-5">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-700 bg-slate-900/50 p-5 shrink-0">
            <div className="flex items-center gap-3 text-cyan-400">
              <Bot className="h-6 w-6" />
              <span className="text-lg font-bold text-white">Research Assistant</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-5 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-700">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`mb-6 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] rounded-xl px-4 py-3 text-base leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-900/20'
                      : 'bg-slate-800 text-slate-200 border border-slate-700'
                  }`}
                >
                    <div dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br/>') }} />
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1 rounded-xl bg-slate-800 px-4 py-3">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 delay-100"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 delay-200"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div 
             className={`absolute bottom-20 left-4 right-4 z-10 flex flex-col gap-2 rounded-xl border border-slate-700 bg-slate-900/90 p-3 shadow-xl backdrop-blur-md transition-all duration-300 ease-out origin-bottom ${
               showSuggestions 
                 ? "opacity-100 scale-100 translate-y-0 pointer-events-auto" 
                 : "opacity-0 scale-95 translate-y-4 pointer-events-none"
             }`}
          >
              <div className="mb-2 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Quick Questions
              </div>
              {SUGGESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  disabled={isLoading}
                  className="flex items-center justify-between w-full rounded-lg bg-slate-800/50 px-4 py-3 text-left text-sm text-cyan-200 transition-all hover:bg-cyan-900/40 hover:text-cyan-100 hover:pl-5 disabled:opacity-50"
                >
                  <span>{q}</span>
                  <ChevronRight className="h-4 w-4 opacity-50" />
                </button>
              ))}
          </div>

          {/* INPUT AREA */}
          <div className="border-t border-slate-800 bg-slate-900/30 p-4 relative z-20">
            <div className="flex gap-3">
              {/* Toggle Suggestions Button */}
              <button
                onClick={() => setShowSuggestions(!showSuggestions)}
                className={`rounded-lg p-3 transition-all duration-300 ${
                  showSuggestions 
                    ? "bg-cyan-500 text-white rotate-180" 
                    : "bg-slate-800 text-cyan-400 hover:bg-slate-700"
                }`}
                title="Quick Questions"
              >
                {showSuggestions ? <X className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
              </button>

              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                onFocus={() => setShowSuggestions(false)}
                placeholder="Ask the Research Assistant..."
                className="flex-1 rounded-lg border border-slate-700 bg-black/50 px-4 py-3 text-base text-white focus:border-cyan-500 focus:outline-none placeholder:text-slate-500"
              />
              <button
                onClick={() => handleSend()}
                disabled={isLoading}
                className="rounded-lg bg-cyan-600 p-3 text-white transition-colors hover:bg-cyan-500 disabled:opacity-50 shadow-lg shadow-cyan-900/20"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CHAT TOGGLE BUTTON */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-cyan-600 text-white shadow-2xl transition-transform hover:scale-105 hover:bg-cyan-500 ring-4 ring-black/50"
      >
        {isOpen ? <X className="h-8 w-8" /> : <MessageSquare className="h-8 w-8" />}
      </button>
    </div>
  )
}
