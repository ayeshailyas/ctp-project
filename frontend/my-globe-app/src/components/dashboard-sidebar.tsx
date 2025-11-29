"use client"

import { useState, useEffect } from "react"
import { X, TrendingUp, BarChart3, MousePointerClick, Sparkles, Layers } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Cell } from "recharts"
import { getCountryData, getCountryFlag, type CountryStats } from "@/data/country-data"

interface DashboardSidebarProps {
  countryCode: string | null
  countryName: string | null
  onClose: () => void
}

export default function DashboardSidebar({ countryCode, countryName, onClose }: DashboardSidebarProps) {
  const isOpen = countryCode !== null
  const data: CountryStats | null = countryCode ? getCountryData(countryCode) : null
  const flag = countryCode ? getCountryFlag(countryCode) : "🌍"

  // STATE 1: View Mode ('volume' = Standard, 'unique' = Hidden Gems)
  const [viewMode, setViewMode] = useState<'volume' | 'unique'>('volume')
  
  // STATE 2: Which bar is currently selected?
  const [activeSubfield, setActiveSubfield] = useState<string | null>(null)

  // Reset selection when country or view mode changes
  useEffect(() => {
    if (viewMode === 'volume' && data?.topSubfields?.length) {
      setActiveSubfield(data.topSubfields[0].name)
    } else if (viewMode === 'unique' && data?.uniqueSubfields?.length) {
      setActiveSubfield(data.uniqueSubfields[0].name)
    }
  }, [countryCode, data, viewMode])

  // Helper: Get the current dataset based on view mode
  const currentChartData = viewMode === 'volume' ? data?.topSubfields : data?.uniqueSubfields
  const activeColor = viewMode === 'volume' ? "#06b6d4" : "#a855f7" // Cyan vs Purple
  const activeLabel = viewMode === 'volume' ? "Most Research" : "Most Unique"

  // Get trend data (Gracefully handle if we don't have trends for a niche unique topic)
  const activeTrendData = (data && activeSubfield) ? data.trends[activeSubfield] || [] : []

  return (
    <div
      className={`fixed right-0 top-0 z-50 h-screen w-full max-w-md transform overflow-y-auto bg-black/80 backdrop-blur-md transition-transform duration-300 ease-out ${
        isOpen ? "translate-x-0" : "translate-x-full"
      }`}
    >
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{flag}</span>
            <h2 className="text-2xl font-bold text-white">{data?.countryName || countryName || "Unknown"}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {data ? (
          <>
            {/* TOGGLE SWITCH */}
            <div className="mb-6 flex w-full rounded-lg bg-slate-900 p-1 border border-slate-800">
              <button
                onClick={() => setViewMode('volume')}
                className={`flex flex-1 items-center justify-center gap-2 rounded-md py-2 text-sm font-medium transition-all ${
                  viewMode === 'volume' 
                    ? "bg-slate-800 text-cyan-400 shadow-sm" 
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Layers className="h-4 w-4" />
                By Volume
              </button>
              <button
                onClick={() => setViewMode('unique')}
                className={`flex flex-1 items-center justify-center gap-2 rounded-md py-2 text-sm font-medium transition-all ${
                  viewMode === 'unique' 
                    ? "bg-slate-800 text-purple-400 shadow-sm" 
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Sparkles className="h-4 w-4" />
                Specialization
              </button>
            </div>

            {/* INTERACTIVE Bar Chart */}
            <div className="mb-8 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="mb-4 flex items-center justify-between">
                <div className={`flex items-center gap-2 ${viewMode === 'volume' ? 'text-cyan-400' : 'text-purple-400'}`}>
                  <BarChart3 className="h-5 w-5" />
                  <h3 className="text-lg font-semibold">{activeLabel}</h3>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <MousePointerClick className="h-3 w-3" />
                    <span>Click bars to filter</span>
                </div>
              </div>
              
              <div className="h-[400px] w-full cursor-pointer">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={currentChartData}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    onClick={(data) => {
                        if (data && data.activePayload && data.activePayload[0]) {
                            setActiveSubfield(data.activePayload[0].payload.name);
                        }
                    }}
                  >
                    <XAxis type="number" hide />
                    <YAxis 
                        type="category" 
                        dataKey="name" 
                        tick={{ fill: "#94a3b8", fontSize: 11 }} 
                        width={120} 
                    />
                    <Tooltip
                      cursor={{fill: 'transparent'}}
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#fff" }}
                      formatter={(value: number, name: string, props: any) => {
                        if (viewMode === 'unique') {
                           // Show score for unique mode
                           return [`${props.payload.score}x Global Avg`, "Specialization Score"]
                        }
                        return [value.toLocaleString(), "Total Works"]
                      }}
                    />
                    <Bar 
                      dataKey={viewMode === 'volume' ? "totalWorks" : "score"} 
                      radius={[0, 4, 4, 0]}
                    >
                        {currentChartData?.map((entry, index) => (
                            <Cell 
                                key={`cell-${index}`} 
                                fill={entry.name === activeSubfield ? activeColor : "#334155"} 
                                className="transition-all duration-300 hover:opacity-80"
                            />
                        ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* TREND Line Chart */}
            <div className="animate-in fade-in duration-700">
              <div className="mb-4 flex items-center gap-2 text-emerald-400">
                <TrendingUp className="h-5 w-5" />
                <h3 className="text-lg font-semibold">Growth Trend</h3>
              </div>
              
              <p className="mb-4 text-sm text-gray-400">
                Tracking: <span className="font-bold text-white">{activeSubfield}</span>
              </p>

              <div className="h-64 w-full">
                {activeTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={activeTrendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis
                        dataKey="year"
                        tick={{ fill: "#94a3b8", fontSize: 12 }}
                        tickFormatter={(year) => `'${String(year).slice(-2)}`}
                      />
                      <YAxis
                        tick={{ fill: "#94a3b8", fontSize: 12 }}
                        tickFormatter={(value) => (value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value)}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#fff" }}
                        formatter={(value: number) => [value.toLocaleString(), "Works"]}
                        labelFormatter={(label) => `Year: ${label}`}
                      />
                      <Line
                        type="monotone"
                        dataKey="volume"
                        stroke="#10b981"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6, fill: "#34d399" }}
                        animationDuration={1000}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900/50">
                     <p className="text-sm text-gray-500">Historical trend data not available</p>
                     <p className="text-xs text-gray-600">for this specific topic.</p>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4 text-6xl opacity-50">🗺️</div>
                <h3 className="mb-2 text-xl font-semibold text-white">Select a Country</h3>
                <p className="text-gray-400">Click on the globe to explore data.</p>
            </div>
        )}
      </div>
    </div>
  )
}
