"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sparkles } from "lucide-react"
import { ChartCard } from "./chart-card"
import { SdkSnippetModal } from "./sdk-snippet-modal"
import { STARTER_PACK_CHARTS } from "./starter-pack-data"

export function StarterPackCatalog() {
  const [selectedCharts, setSelectedCharts] = useState<string[]>([])
  const [showSdkModal, setShowSdkModal] = useState(false)

  const toggleChart = (chartId: string) => {
    setSelectedCharts((prev) =>
      prev.includes(chartId)
        ? prev.filter((id) => id !== chartId)
        : [...prev, chartId]
    )
  }

  const handleStartMonitoring = () => {
    if (selectedCharts.length === 0) {
      return
    }
    setShowSdkModal(true)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Analytics Starter Pack</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Select the essential metrics to track when your feature goes live
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedCharts.length > 0 && (
            <Badge variant="secondary" className="px-3 py-1.5">
              {selectedCharts.length} {selectedCharts.length === 1 ? "chart" : "charts"} selected
            </Badge>
          )}
          <Button
            size="lg"
            onClick={handleStartMonitoring}
            disabled={selectedCharts.length === 0}
            className="gap-2"
          >
            <Sparkles className="w-4 h-4" />
            Start Monitoring
          </Button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-muted/30 border border-muted rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold mb-1">Why a Starter Pack?</h3>
            <p className="text-sm text-muted-foreground">
              Instead of overwhelming you with dozens of metrics, we've curated the essential charts that matter most.
              These 6 metrics give you a complete picture of engagement, conversion, and friction—everything you need
              to understand if your feature is working. Click any chart to learn more about what it measures.
            </p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {STARTER_PACK_CHARTS.map((chart) => (
          <ChartCard
            key={chart.id}
            chart={chart}
            isSelected={selectedCharts.includes(chart.id)}
            onToggleSelect={() => toggleChart(chart.id)}
          />
        ))}
      </div>

      {/* SDK Snippet Modal */}
      <SdkSnippetModal
        open={showSdkModal}
        onOpenChange={setShowSdkModal}
        selectedChartIds={selectedCharts}
      />
    </div>
  )
}
