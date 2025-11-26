"use client"

import { useState, useEffect } from "react"
import { X, TrendingUp, BarChart3, MousePointerClick } from "lucide-react"
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

  // STATE: Track which subfield is currently selected
  const [activeSubfield, setActiveSubfield] = useState<string | null>(null)

  // EFFECT: When country changes, reset selection to the top #1 subfield
  useEffect(() => {
    if (data?.topSubfields && data.topSubfields.length > 0) {
      setActiveSubfield(data.topSubfields[0].name)
    }
  }, [countryCode, data])

  // Get trend data for the active subfield, or empty list if missing
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
                        {/* INTERACTIVE Bar Chart */}
            <div className="mb-8">
              <div className="mb-4 flex items-center justify-between text-cyan-400">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  <h3 className="text-lg font-semibold">Top 10 Research Areas</h3>
                </div>
                {/* ... hint text ... */}
              </div>
              
              {/* CHANGE THIS LINE BELOW: h-64 -> h-[500px] */}
              <div className="h-[500px] w-full cursor-pointer">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.topSubfields}
                    layout="vertical"
                    // Adjust margins to make sure long names fit
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
                    />
                    <Bar dataKey="totalWorks" radius={[0, 4, 4, 0]}>
                        {data.topSubfields.map((entry, index) => (
                            <Cell 
                                key={`cell-${index}`} 
                                fill={entry.name === activeSubfield ? "#06b6d4" : "#334155"} 
                                className="transition-all duration-300 hover:opacity-80"
                            />
                        ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* DYNAMIC Line Chart */}
            <div className="animate-in fade-in duration-500">
              <div className="mb-4 flex items-center gap-2 text-emerald-400">
                <TrendingUp className="h-5 w-5" />
                <h3 className="text-lg font-semibold">Growth Trend</h3>
              </div>
              
              <p className="mb-4 text-sm text-gray-400">
                Showing data for: <span className="font-bold text-white">{activeSubfield}</span>
              </p>

              <div className="h-64 w-full">
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
              </div>
            </div>
          </>
        ) : (
            <div className="text-center text-gray-500 mt-20">No data available</div>
        )}
      </div>
    </div>
  )
}
