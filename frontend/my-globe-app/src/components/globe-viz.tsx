
"use client"

import type React from "react"

import { useEffect, useRef, useState, useCallback } from "react"
import type Globe from "react-globe.gl"

interface GlobeVizProps {
  onCountryClick: (countryCode: string, countryName: string) => void
}

interface CountryFeature {
  properties: {
    ISO_A2: string
    ADMIN: string
  }
  bbox?: number[]
}

interface GeoJsonData {
  features: CountryFeature[]
}

export default function GlobeViz({ onCountryClick }: GlobeVizProps) {
  const globeRef = useRef<React.ComponentRef<typeof Globe> | null>(null)
  const [countries, setCountries] = useState<GeoJsonData>({ features: [] })
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null)
  const [GlobeComponent, setGlobeComponent] = useState<typeof Globe | null>(null)

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
          globeRef.current.pointOfView({ lat, lng, altitude: 1.5 }, 1000)
        }

        onCountryClick(countryCode, countryName)
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
      if (code === hoveredCountry) {
        return "rgba(0, 200, 255, 0.7)"
      }
      return "rgba(100, 100, 150, 0.6)"
    },
    [hoveredCountry],
  )

  const getPolygonSideColor = useCallback(() => {
    return "rgba(50, 50, 80, 0.4)"
  }, [])

  const getPolygonStrokeColor = useCallback(() => {
    return "#334155"
  }, [])

  if (!GlobeComponent) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <GlobeComponent
      ref={globeRef}
      globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
      backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
      polygonsData={countries.features}
      polygonCapColor={getPolygonCapColor}
      polygonSideColor={getPolygonSideColor}
      polygonStrokeColor={getPolygonStrokeColor}
      polygonAltitude={(d) => {
        const feature = d as CountryFeature
        return feature.properties?.ISO_A2 === hoveredCountry ? 0.06 : 0.01
      }}
      onPolygonClick={handlePolygonClick}
      onPolygonHover={handlePolygonHover}
      polygonsTransitionDuration={300}
      atmosphereColor="rgba(0, 150, 255, 0.3)"
      atmosphereAltitude={0.25}
    />
  )
}
