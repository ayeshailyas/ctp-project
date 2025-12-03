"use client"

import { useState, useEffect } from "react"
import { X, TrendingUp, BarChart3, MousePointerClick, Sparkles, Layers, FileText, ExternalLink, Quote, ChevronRight } from "lucide-react"
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

  const [viewMode, setViewMode] = useState<'volume' | 'unique'>('volume')
  const [activeSubfield, setActiveSubfield] = useState<string | null>(null)
  const [showPapers, setShowPapers] = useState(false)

  useEffect(() => {
    if (viewMode === 'volume' && data?.topSubfields?.length) {
      setActiveSubfield(data.topSubfields[0].name)
      setShowPapers(false)
    } else if (viewMode === 'unique' && data?.uniqueSubfields?.length) {
      setActiveSubfield(data.uniqueSubfields[0].name)
      setShowPapers(false)
    }
  }, [countryCode, data, viewMode])

  const currentChartData = viewMode === 'volume' ? data?.topSubfields : data?.uniqueSubfields
  const activeColor = viewMode === 'volume' ? "#06b6d4" : "#a855f7" 
  const activeLabel = viewMode === 'volume' ? "Most Research" : "Most Unique"
  const activeTrendData = (data && activeSubfield) ? data.trends[activeSubfield] || [] : []
  
  const activeItem = currentChartData?.find(item => item.name === activeSubfield)
  const activePapers = activeItem?.topPapers || []

  const handleBarClick = (data: any) => {
    if (data && data.activePayload && data.activePayload[0]) {
        const clickedName = data.activePayload[0].payload.name
        setActiveSubfield(clickedName)
        setShowPapers(true)
    }
  }

  return (
    <>
      <div 
        className={`fixed top-0 z-40 h-screen w-96 border-r border-l border-slate-800 bg-black/95 backdrop-blur-xl transition-all duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] ${
           isOpen && showPapers 
             ? "translate-x-0 right-[42rem] opacity-100 shadow-2xl" 
             : "translate-x-20 right-[42rem] opacity-0 pointer-events-none" 
        }`}
      >
        <div className="flex h-full flex-col p-6">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
             <div className="flex items-center gap-2 text-indigo-400">
                <FileText className="h-6 w-6" /> 
                <h3 className="text-lg font-bold text-white">Top Papers</h3> 
             </div>
             <button 
               onClick={() => setShowPapers(false)}
               className="rounded-full p-1 text-slate-500 hover:bg-slate-800 hover:text-white"
             >
               <ChevronRight className="h-6 w-6" />
             </button>
          </div>

          <div className="mb-4 shrink-0">
             <p className="text-sm font-semibold uppercase tracking-wider text-slate-500">Subject</p> 
             <h4 className="text-2xl font-bold text-indigo-200">{activeSubfield}</h4> 
          </div>

          {/* Paper List */}
          <div className="flex-1 overflow-y-auto pr-2 pb-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-slate-700">
            <div className="space-y-4">
                {activePapers && activePapers.length > 0 ? (
                  activePapers.map((paper, i) => (
                    <div 
                      key={i} 
                      className="group relative flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition-all hover:border-indigo-500/50 hover:bg-indigo-950/20"
                    >
                       <div className="flex items-start justify-between gap-3">
                          {/* Title:*/}
                          <h5 className="text-base font-medium text-slate-200 leading-snug group-hover:text-indigo-300 transition-colors">
                            {paper.title}
                          </h5>
                       </div>
                       
                       <div className="flex items-center justify-between pt-2">
                          {/* Metadata:*/}
                          <div className="flex items-center gap-3 text-sm text-slate-500">
                             <span className="flex items-center gap-1 rounded bg-slate-800 px-2 py-0.5">
                               {paper.year}
                             </span>
                             <span className="flex items-center gap-1 text-indigo-400">
                               <Quote className="h-3 w-3 fill-current" />
                               {paper.cited_by_count.toLocaleString()}
                             </span>
                          </div>
                          
                          {paper.doi && (
                            <a 
                              href={paper.doi} 
                              target="_blank" 
                              rel="noreferrer"
                              className="text-slate-500 hover:text-white transition-colors"
                              title="Read on OpenAlex"
                            >
                              <ExternalLink className="h-5 w-5" />
                            </a>
                          )}
                       </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-center text-slate-600">
                    <p className="text-base">No specific paper data available.</p>
                  </div>
                )}
            </div>
          </div>
          
          <div className="mt-4 border-t border-slate-800 pt-4 text-center text-xs text-slate-600 shrink-0"> 
            Top 10 most cited papers in the last 20 years.
          </div>
        </div>
      </div>


      <div
        className={`fixed right-0 top-0 z-50 h-screen w-full max-w-2xl transform overflow-y-auto bg-black/95 backdrop-blur-xl transition-transform duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] ${
          isOpen ? "translate-x-0 shadow-2xl" : "translate-x-full"
        }`}
      >
        <div className="p-8"> 
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-5xl">{flag}</span> 
              <div>
                 {/* Country Name:*/}
                <h2 className="text-3xl font-bold text-white">{countryName || data?.countryName || "Unknown"}</h2>
                <p className="text-lg text-slate-400">Research Ecosystem</p> 
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-2 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
            >
              <X className="h-8 w-8" />
            </button>
          </div>

          {data ? (
            <>
              {/* TOGGLE SWITCH*/}
              <div className="mb-8 flex w-full rounded-xl bg-slate-900 p-1.5 border border-slate-800">
                <button
                  onClick={() => setViewMode('volume')}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-3 text-base font-medium transition-all ${
                    viewMode === 'volume' 
                      ? "bg-slate-800 text-cyan-400 shadow-sm" 
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Layers className="h-5 w-5" />
                  By Volume
                </button>
                <button
                  onClick={() => setViewMode('unique')}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-3 text-base font-medium transition-all ${
                    viewMode === 'unique' 
                      ? "bg-slate-800 text-purple-400 shadow-sm" 
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Sparkles className="h-5 w-5" />
                  Specialization
                </button>
              </div>

              {/* BAR CHART */}
              <div className="mb-10 animate-in fade-in slide-in-from-right-4 duration-500">
                <div className="mb-6 flex items-center justify-between">
                  <div className={`flex items-center gap-2 ${viewMode === 'volume' ? 'text-cyan-400' : 'text-purple-400'}`}>
                    <BarChart3 className="h-6 w-6" />
                    <h3 className="text-xl font-semibold">{activeLabel}</h3> 
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-500 animate-pulse"> 
                      <MousePointerClick className="h-4 w-4" />
                      <span>Click bars to view Top Papers</span>
                  </div>
                </div>
                
                <div className="h-[450px] w-full cursor-pointer"> 
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={currentChartData}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      onClick={handleBarClick}
                    >
                      <XAxis type="number" hide />
                      <YAxis 
                          type="category" 
                          dataKey="name" 
                          tick={{ fill: "#94a3b8", fontSize: 13, fontWeight: 500 }} 
                          width={220} 
                      />
                      <Tooltip
                        cursor={{fill: 'transparent'}}
                        contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#fff", fontSize: "14px" }}
                        itemStyle={{ color: "#e2e8f0" }} 
                        formatter={(value: number, name: string, props: any) => {
                          if (viewMode === 'unique') {
                             return [`${props.payload.score}x Global Avg`, "Specialization Score"]
                          }
                          return [value.toLocaleString(), "Total Works"]
                        }}
                      />
                      <Bar 
                        dataKey={viewMode === 'volume' ? "totalWorks" : "score"} 
                        radius={[0, 4, 4, 0]}
                        barSize={32} 
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

              {/* TREND CHART */}
              <div className="animate-in fade-in duration-700">
                <div className="mb-4 flex items-center gap-2 text-emerald-400">
                  <TrendingUp className="h-6 w-6" />
                  <h3 className="text-xl font-semibold">Growth Trend</h3> 
                </div>
                
                <p className="mb-6 text-base text-gray-400"> 
                  Tracking: <span className="font-bold text-white">{activeSubfield}</span>
                </p>

                <div className="h-72 w-full"> 
                  {activeTrendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={activeTrendData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
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
                          contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#fff", fontSize: "14px" }}
                          itemStyle={{ color: "#e2e8f0" }}
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
                       <p className="text-base text-gray-500">Historical trend data not available</p>
                       <p className="text-sm text-gray-600">for this specific topic.</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="mb-4 text-7xl opacity-50">🗺️</div>
                  <h3 className="mb-2 text-2xl font-semibold text-white">Select a Country</h3>
                  <p className="text-lg text-gray-400">Click on the globe to explore data.</p>
              </div>
          )}
        </div>
      </div>
    </>
  )
}
