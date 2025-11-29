"use client"

import { useState } from "react"
import dynamic from "next/dynamic"
import { Globe2 } from "lucide-react"
import DashboardSidebar from "@/components/dashboard-sidebar"
import ChatWidget from "@/components/chat-widget" 
import { getCountryData } from "@/data/country-data" 

const GlobeViz = dynamic(() => import("@/components/globe-viz"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-slate-950">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
    </div>
  ),
})

export default function Home() {
  const [selectedCountry, setSelectedCountry] = useState<{
    code: string
    name: string
  } | null>(null)

  const handleCountryClick = (countryCode: string, countryName: string) => {
    setSelectedCountry({ code: countryCode, name: countryName })
  }

  const handleCloseSidebar = () => {
    setSelectedCountry(null)
  }

  // Get the full data object for the chat to use as context
  const countryData = selectedCountry ? getCountryData(selectedCountry.code) : null

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-slate-950">
      {/* Globe Background */}
      <div className="absolute inset-0">
        <GlobeViz 
          onCountryClick={handleCountryClick} 
          selectedCountryCode={selectedCountry?.code}
        />
      </div>

      {/* Title Overlay */}
      <div className="pointer-events-none absolute left-6 top-6 z-40">
        <div className="flex items-center gap-3">
          <Globe2 className="h-8 w-8 text-cyan-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Global Research Trends</h1>
            <p className="text-sm text-gray-400">Powered by OpenAlex • Click a country to explore</p>
          </div>
        </div>
      </div>

      {/* Dashboard Sidebar */}
      <DashboardSidebar
        countryCode={selectedCountry?.code || null}
        countryName={selectedCountry?.name || null}
        onClose={handleCloseSidebar}
      />

      {/* AI Chat Widget */}
      <ChatWidget countryData={countryData} />

      {/* Hint */}
      {!selectedCountry && (
        <div className="pointer-events-none absolute bottom-6 left-1/2 z-40 -translate-x-1/2 animate-pulse">
          <div className="rounded-full bg-black/50 px-4 py-2 text-sm text-gray-300 backdrop-blur-sm">
            Hover and click on any country to view research data
          </div>
        </div>
      )}
    </main>
  )
}
