"use client"

import { useState, useCallback } from "react"
import dynamic from "next/dynamic"
import { Globe2, ChevronRight } from "lucide-react"
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
  const [isIntro, setIsIntro] = useState(true)
  
  const [selectedCountry, setSelectedCountry] = useState<{
    code: string
    name: string
  } | null>(null)

  const handleCountryClick = useCallback((countryCode: string, countryName: string) => {
    setSelectedCountry({ code: countryCode, name: countryName })
  }, [])

  const handleCloseSidebar = () => {
    setSelectedCountry(null)
  }

  const rawCountryData = selectedCountry ? getCountryData(selectedCountry.code) : null
  const countryData = rawCountryData && selectedCountry 
    ? { ...rawCountryData, countryName: selectedCountry.name } 
    : null

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-slate-950">
      {/* Globe Background */}
      <div className="absolute inset-0">
        <GlobeViz 
          onCountryClick={handleCountryClick} 
          selectedCountryCode={selectedCountry?.code}
          isIntro={isIntro} 
        />
      </div>

      {/* ANIMATED TITLE CONTAINER*/}
      <div 
        className={`absolute top-6 left-6 z-40 transition-transform duration-1000 ease-[cubic-bezier(0.25,0.1,0.25,1)] will-change-transform ${
          isIntro 
            ? "translate-x-[calc(50vw-50%-24px)] translate-y-[calc(40vh-24px)] scale-125" 
            : "translate-x-0 translate-y-0 scale-100"
        }`}
      >
        <div className={`flex items-center gap-3 transition-all duration-1000 ${
            isIntro ? "flex-col" : "flex-row"
        }`}>
          <Globe2 
            className={`text-cyan-400 transition-all duration-1000 ${
              isIntro ? "h-20 w-20 mb-4" : "h-8 w-8"
            }`} 
          />
          <div className={`transition-all duration-1000 ${isIntro ? "text-center" : "text-left"}`}>
            <h1 className="text-2xl font-bold text-white whitespace-nowrap">
                Research Flow
            </h1>
            <p className={`text-gray-400 transition-all duration-1000 ${
               isIntro ? "text-sm mt-2 opacity-80" : "text-xs opacity-100"
            }`}>
              Powered by OpenAlex • {isIntro ? "3D Visualization" : "Click a country"}
            </p>
          </div>
        </div>

        {/* START BUTTON */}
        <div 
           className={`absolute left-1/2 -translate-x-1/2 mt-8 transition-all duration-500 ${
             isIntro ? "opacity-100 top-full pointer-events-auto" : "opacity-0 top-full pointer-events-none"
           }`}
        >
          <button 
            onClick={() => setIsIntro(false)}
            className="group whitespace-nowrap flex items-center gap-2 rounded-full bg-cyan-600/20 px-8 py-3 text-lg font-medium text-cyan-400 backdrop-blur-sm border border-cyan-500/50 hover:bg-cyan-500 hover:text-white transition-all hover:scale-105"
          >
            Start Exploring
            <ChevronRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </div>

      {/* UI LAYOUTS - Delayed fade in to prevent frame drops during movement */}
      <div className={`transition-opacity duration-700 delay-500 ${isIntro ? "opacity-0 pointer-events-none" : "opacity-100"}`}>
        <DashboardSidebar
          countryCode={selectedCountry?.code || null}
          countryName={selectedCountry?.name || null}
          onClose={handleCloseSidebar}
        />

        <ChatWidget countryData={countryData} />

        {!selectedCountry && (
          <div className="pointer-events-none absolute bottom-6 left-1/2 z-40 -translate-x-1/2 animate-pulse">
            <div className="rounded-full bg-black/50 px-4 py-2 text-sm text-gray-300 backdrop-blur-sm">
              Hover and click on any country to view research data
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
