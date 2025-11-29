"use client"

import type React from "react"
import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import { Search } from "lucide-react"
import type Globe from "react-globe.gl"

interface GlobeVizProps {
  onCountryClick: (countryCode: string, countryName: string) => void
  selectedCountryCode?: string | null
}

interface CountryFeature {
  type: "Feature"
  properties: {
    ISO_A2: string
    ADMIN: string
  }
  geometry: any
  bbox?: number[]
}

interface GeoJsonData {
  type: "FeatureCollection"
  features: CountryFeature[]
}

export default function GlobeViz({ onCountryClick, selectedCountryCode }: GlobeVizProps) {
  const globeRef = useRef<any>(null)
  
  const [countries, setCountries] = useState<GeoJsonData>({ type: "FeatureCollection", features: [] })
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null)
  const [GlobeComponent, setGlobeComponent] = useState<typeof Globe | null>(null)

  // Search State
  const [searchQuery, setSearchQuery] = useState("")
  const [isSearchActive, setIsSearchActive] = useState(false)

  useEffect(() => {
    import("react-globe.gl").then((mod) => {
      setGlobeComponent(() => mod.default)
    })
  }, [])

  useEffect(() => {
    fetch(
      "https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson",
    )
      .then((res) => res.json())
      .then(setCountries)
  }, [])

  useEffect(() => {
    if (globeRef.current) {
      const controls = globeRef.current.controls()
      if (controls) {
        controls.autoRotate = true
        controls.autoRotateSpeed = 0.5
        controls.enableZoom = true
      }
    }
  }, [GlobeComponent])

  const handlePolygonClick = useCallback(
    (polygon: object) => {
      const feature = polygon as CountryFeature
      const countryCode = feature.properties?.ISO_A2
      const countryName = feature.properties?.ADMIN

      if (countryCode && countryName) {
        // Stop auto-rotation on click
        if (globeRef.current) {
          const controls = globeRef.current.controls()
          if (controls) {
            controls.autoRotate = false
          }
        }

        // Zoom to country
        if (feature.bbox && globeRef.current) {
          const [minLng, minLat, maxLng, maxLat] = feature.bbox
          const lat = (minLat + maxLat) / 2
          const lng = (minLng + maxLng) / 2
          globeRef.current.pointOfView({ lat, lng, altitude: 1.5 }, 2000)
        }

        onCountryClick(countryCode, countryName)
        setSearchQuery("") 
        setIsSearchActive(false)
      }
    },
    [onCountryClick],
  )

  const handlePolygonHover = useCallback((polygon: object | null) => {
    const feature = polygon as CountryFeature | null
    setHoveredCountry(feature?.properties?.ISO_A2 || null)
  }, [])

  const getPolygonCapColor = useCallback(
    (polygon: object) => {
      const feature = polygon as CountryFeature
      const code = feature.properties?.ISO_A2
      
      if (code === hoveredCountry || code === selectedCountryCode) {
        return "rgba(0, 200, 255, 0.7)" // Bright Cyan for Selected/Hovered
      }
      return "rgba(100, 100, 150, 0.6)" // Default Blue
    },
    [hoveredCountry, selectedCountryCode],
  )

  const getPolygonSideColor = useCallback(() => {
    return "rgba(50, 50, 80, 0.4)"
  }, [])

  const getPolygonStrokeColor = useCallback(() => {
    return "#334155"
  }, [])

  // Filter countries for search
  const filteredCountries = useMemo(() => {
    if (!searchQuery) return []
    return countries.features
      .filter((feature) => 
        feature.properties.ADMIN.toLowerCase().includes(searchQuery.toLowerCase())
      )
      .slice(0, 5) 
  }, [countries, searchQuery])

  if (!GlobeComponent) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      {/* SEARCH BAR */}
      <div className="absolute left-6 top-24 z-50 w-72">
        <div className="relative group">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-cyan-400" />
          </div>
          <input
            type="text"
            className="block w-full rounded-lg border border-slate-700 bg-black/60 p-2.5 pl-10 text-sm text-white placeholder-gray-400 backdrop-blur-md focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="Search country..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setIsSearchActive(true)
            }}
            onFocus={() => setIsSearchActive(true)}
          />
        </div>

        {isSearchActive && searchQuery && filteredCountries.length > 0 && (
          <ul className="mt-2 divide-y divide-slate-700 rounded-lg border border-slate-700 bg-black/80 backdrop-blur-md">
            {filteredCountries.map((feature) => (
              <li key={feature.properties.ISO_A2}>
                <button
                  className="w-full px-4 py-2 text-left text-sm text-gray-200 transition-colors hover:bg-cyan-500/20 hover:text-cyan-400"
                  onClick={() => handlePolygonClick(feature)}
                >
                  {feature.properties.ADMIN}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <GlobeComponent
        ref={globeRef}
        globeImageUrl="https://unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundImageUrl="https://unpkg.com/three-globe/example/img/night-sky.png"
        polygonsData={countries.features}
        polygonCapColor={getPolygonCapColor}
        polygonSideColor={getPolygonSideColor}
        polygonStrokeColor={getPolygonStrokeColor}
        polygonAltitude={(d) => {
          const feature = d as CountryFeature
          const code = feature.properties?.ISO_A2
          return (code === hoveredCountry || code === selectedCountryCode) ? 0.06 : 0.01
        }}
        onPolygonClick={handlePolygonClick}
        onPolygonHover={handlePolygonHover}
        polygonsTransitionDuration={300}
        atmosphereColor="rgba(0, 150, 255, 0.3)"
        atmosphereAltitude={0.25}
      />
    </div>
  )
}
