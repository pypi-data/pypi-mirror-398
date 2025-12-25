"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Check, TrendingUp, Zap, Target, AlertCircle } from "lucide-react"
import { StarterChart } from "./starter-pack-data"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts"

interface ChartCardProps {
  chart: StarterChart
  isSelected: boolean
  onToggleSelect: () => void
}

const COLORS = ["oklch(0.55 0.2 280)", "oklch(0.65 0.15 280)", "oklch(0.75 0.1 280)", "oklch(0.45 0.2 280)", "oklch(0.35 0.2 280)"]

const getCategoryIcon = (category: StarterChart["category"]) => {
  switch (category) {
    case "Engagement":
      return <TrendingUp className="w-4 h-4" />
    case "Conversion":
      return <Target className="w-4 h-4" />
    case "Activation":
      return <Zap className="w-4 h-4" />
    case "Friction":
      return <AlertCircle className="w-4 h-4" />
  }
}

const getCategoryColor = (category: StarterChart["category"]) => {
  switch (category) {
    case "Engagement":
      return "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20"
    case "Conversion":
      return "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20"
    case "Activation":
      return "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20"
    case "Friction":
      return "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20"
  }
}

export function ChartCard({ chart, isSelected, onToggleSelect }: ChartCardProps) {
  const [isFlipped, setIsFlipped] = useState(false)

  const renderMiniChart = () => {
    switch (chart.chartType) {
      case "line":
        const lineData = chart.sampleData.labels?.map((label, i) => ({
          name: label,
          value: chart.sampleData.values?.[i] || 0,
        }))
        return (
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.85 0 0)" opacity={0.3} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="oklch(0.7 0 0)" />
              <YAxis tick={{ fontSize: 10 }} stroke="oklch(0.7 0 0)" />
              <Line type="monotone" dataKey="value" stroke="oklch(0.55 0.2 280)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )

      case "funnel":
        return (
          <div className="space-y-1 py-2">
            {chart.sampleData.steps?.slice(0, 4).map((step, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="truncate">{step.name}</span>
                  <span className="font-semibold">{step.percentage}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-1.5">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{ width: `${step.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )

      case "bar":
        return (
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chart.sampleData.data}>
              <Bar dataKey="value" fill="oklch(0.55 0.2 280)" radius={[4, 4, 0, 0]} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            </BarChart>
          </ResponsiveContainer>
        )

      case "pie":
        return (
          <ResponsiveContainer width="100%" height={120}>
            <PieChart>
              <Pie
                data={chart.sampleData.data}
                cx="50%"
                cy="50%"
                innerRadius={25}
                outerRadius={50}
                paddingAngle={2}
                dataKey="value"
              >
                {chart.sampleData.data?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        )
    }
  }

  return (
    <div className="perspective-1000 h-[320px]">
      <div
        className={`relative w-full h-full transition-transform duration-500 transform-style-3d ${
          isFlipped ? "rotate-y-180" : ""
        }`}
        style={{
          transformStyle: "preserve-3d",
          transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)",
        }}
      >
        {/* Front of Card */}
        <Card
          className={`absolute inset-0 backface-hidden border-2 transition-all cursor-pointer ${
            isSelected
              ? "border-primary shadow-lg shadow-primary/20"
              : "border-border hover:border-primary/50"
          }`}
          style={{ backfaceVisibility: "hidden" }}
        >
          <CardContent className="p-5 flex flex-col h-full" onClick={() => setIsFlipped(!isFlipped)}>
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-base mb-1 truncate">{chart.name}</h3>
                <p className="text-xs text-muted-foreground line-clamp-2">{chart.description}</p>
              </div>
              {/* Selection Checkbox */}
              <div className="ml-2 flex-shrink-0">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onToggleSelect()
                  }}
                  className={`w-6 h-6 rounded-md border-2 transition-all flex items-center justify-center ${
                    isSelected
                      ? "bg-primary border-primary"
                      : "border-muted-foreground/30 hover:border-primary hover:bg-primary/5"
                  }`}
                >
                  {isSelected && <Check className="w-4 h-4 text-primary-foreground" />}
                </button>
              </div>
            </div>

            {/* Category Badge */}
            <Badge variant="outline" className={`w-fit mb-3 ${getCategoryColor(chart.category)}`}>
              {getCategoryIcon(chart.category)}
              <span className="ml-1">{chart.category}</span>
            </Badge>

            {/* Mini Chart */}
            <div className="flex-1 flex items-center justify-center min-h-0">
              {renderMiniChart()}
            </div>

            {/* Click hint */}
            <div className="text-center mt-3">
              <p className="text-xs text-muted-foreground">Click to learn more</p>
            </div>
          </CardContent>
        </Card>

        {/* Back of Card */}
        <Card
          className="absolute inset-0 backface-hidden border-2 border-primary rotate-y-180 cursor-pointer"
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
          }}
        >
          <CardContent className="p-5 flex flex-col h-full overflow-y-auto" onClick={() => setIsFlipped(!isFlipped)}>
            <div className="space-y-3 flex-1">
              {/* Title */}
              <div>
                <h3 className="font-semibold text-base mb-1">{chart.name}</h3>
                <Badge variant="outline" className={`w-fit ${getCategoryColor(chart.category)}`}>
                  {getCategoryIcon(chart.category)}
                  <span className="ml-1">{chart.category}</span>
                </Badge>
              </div>

              {/* Why It Matters */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                  Why It Matters
                </h4>
                <p className="text-sm">{chart.whyItMatters}</p>
              </div>

              {/* Events Collected */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                  Events Tracked
                </h4>
                <ul className="text-sm space-y-0.5">
                  {chart.eventsCollected.map((event, i) => (
                    <li key={i} className="flex items-start">
                      <span className="text-primary mr-1.5">•</span>
                      <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{event}</code>
                    </li>
                  ))}
                </ul>
              </div>

              {/* How to Measure */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                  How to Measure
                </h4>
                <p className="text-sm">{chart.howToMeasure}</p>
              </div>
            </div>

            {/* Select Button */}
            <div className="mt-4 pt-3 border-t">
              <Button
                variant={isSelected ? "outline" : "default"}
                size="sm"
                className="w-full"
                onClick={(e) => {
                  e.stopPropagation()
                  onToggleSelect()
                }}
              >
                {isSelected ? (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Selected
                  </>
                ) : (
                  "Select This Chart"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
