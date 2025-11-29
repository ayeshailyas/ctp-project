"use client"

import { useState, useRef, useEffect } from "react"
import { MessageSquare, Send, X, Bot } from "lucide-react"
import type { CountryStats } from "@/data/country-data"

interface ChatWidgetProps {
  countryData: CountryStats | null
}

interface Message {
  role: 'user' | 'bot'
  text: string
}

export default function ChatWidget({ countryData }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: "Hi! I'm your Research AI. Click a country and ask me anything about its scientific output." }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isOpen])

  // Reset chat when country changes
  useEffect(() => {
    if (countryData) {
        setMessages(prev => [
            ...prev, 
            { role: 'bot', text: `I see you selected **${countryData.countryName}**. Ask me about their trends or unique specializations!` }
        ])
    }
  }, [countryData?.countryCode])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg = input
    setInput("")
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg, 
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
      setMessages(prev => [...prev, { role: 'bot', text: "Sorry, I'm having trouble connecting to the AI right now." }])
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
    // CHANGED: "right-6" -> "left-6" and "items-end" -> "items-start"
    <div className="fixed bottom-6 left-6 z-50 flex flex-col items-start">
      {/* CHAT WINDOW */}
      {isOpen && (
        <div className="mb-4 h-[500px] w-[350px] overflow-hidden rounded-xl border border-slate-700 bg-black/80 shadow-2xl backdrop-blur-md animate-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-700 bg-slate-900/50 p-4">
            <div className="flex items-center gap-2 text-cyan-400">
              <Bot className="h-5 w-5" />
              <span className="font-semibold text-white">Research Assistant</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex h-[380px] flex-col overflow-y-auto p-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-700">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white'
                      : 'bg-slate-800 text-gray-200'
                  }`}
                >
                    {/* Render basic markdown/text */}
                    <div dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br/>') }} />
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1 rounded-lg bg-slate-800 px-4 py-2">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 delay-100"></span>
                  <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 delay-200"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-slate-700 bg-slate-900/50 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about the data..."
                className="flex-1 rounded-md border border-slate-700 bg-black/50 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
              />
              <button
                onClick={handleSend}
                disabled={isLoading}
                className="rounded-md bg-cyan-600 p-2 text-white transition-colors hover:bg-cyan-500 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TOGGLE BUTTON */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-cyan-600 text-white shadow-lg transition-transform hover:scale-105 hover:bg-cyan-500"
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
      </button>
    </div>
  )
}
