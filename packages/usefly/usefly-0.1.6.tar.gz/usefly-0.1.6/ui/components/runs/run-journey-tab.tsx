"use client"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ArrowRight, Globe, Zap, MapPin } from "lucide-react"
import { DerivedMetrics, formatUrl, getFullDecodedUrl } from "./run-utils"

interface RunJourneyTabProps {
  journeyPath: string[]
  events: any[]
  metrics: DerivedMetrics
}

// Extract journey path from events if not provided
function extractJourneyFromEvents(events: any[]): string[] {
  const urls: string[] = []
  let lastUrl = ""

  for (const event of events) {
    if (event.url && event.url !== lastUrl) {
      urls.push(event.url)
      lastUrl = event.url
    }
  }

  return urls
}

export function RunJourneyTab({
  journeyPath,
  events,
  metrics,
}: RunJourneyTabProps) {
  // Use provided journeyPath or extract from events
  const journey = journeyPath && journeyPath.length > 0
    ? journeyPath
    : extractJourneyFromEvents(events)

  // Get unique pages in order
  const uniquePages = Array.from(new Set(journey))

  if (journey.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <p>No journey data available for this run</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Full Journey Timeline */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-4 h-4" />
          <p className="text-sm font-medium">Navigation Timeline</p>
          <Badge variant="secondary" className="ml-auto">
            {journey.length} steps
          </Badge>
        </div>
        <div className="space-y-2">
          {journey.map((url, idx) => (
            <div key={idx} className="flex items-center gap-3">
              {/* Step number */}
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-medium flex items-center justify-center">
                {idx + 1}
              </div>
              {/* URL */}
              <div
                className="flex-1 text-sm truncate p-2 bg-muted rounded-md"
                title={getFullDecodedUrl(url)}
              >
                {formatUrl(url)}
              </div>
              {/* Arrow to next (if not last) */}
              {idx < journey.length - 1 && (
                <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Unique Pages Summary */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-4 h-4" />
          <p className="text-sm font-medium">Unique Pages Visited</p>
          <Badge variant="outline" className="ml-auto">
            {uniquePages.length} pages
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          {uniquePages.map((url, idx) => (
            <Badge
              key={idx}
              variant="outline"
              className="text-xs max-w-xs truncate"
              title={getFullDecodedUrl(url)}
            >
              {formatUrl(url)}
            </Badge>
          ))}
        </div>
      </Card>

      {/* Journey Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Pages Visited</p>
          <p className="text-3xl font-bold mt-2">{metrics.pagesVisited}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Avg Actions/Page</p>
          <p className="text-3xl font-bold mt-2">
            {metrics.averageActionsPerPage.toFixed(1)}
          </p>
        </Card>
      </div>

      {/* Actions Per Page */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4" />
          <p className="text-sm font-medium">Actions Per Page</p>
        </div>
        <div className="space-y-2">
          {Object.entries(metrics.actionsPerPage)
            .sort(([, a], [, b]) => b - a)
            .map(([url, count]) => (
              <div
                key={url}
                className="flex items-center justify-between p-3 bg-muted rounded-md border"
              >
                <span className="text-sm truncate flex-1 mr-2" title={getFullDecodedUrl(url)}>
                  {formatUrl(url)}
                </span>
                <Badge variant="secondary" className="flex-shrink-0">
                  {count} action{count !== 1 ? "s" : ""}
                </Badge>
              </div>
            ))}
        </div>
      </Card>

      {/* Steps Per Page (if available) */}
      {Object.keys(metrics.timePerPage).length > 0 && (
        <Card className="p-4">
          <p className="text-sm font-medium mb-4">Steps Per Page</p>
          <div className="space-y-2">
            {Object.entries(metrics.timePerPage)
              .sort(([, a], [, b]) => b - a)
              .map(([url, steps]) => (
                <div
                  key={url}
                  className="flex items-center justify-between p-3 bg-muted rounded-md border"
                >
                  <span className="text-sm truncate flex-1 mr-2" title={getFullDecodedUrl(url)}>
                    {formatUrl(url)}
                  </span>
                  <Badge variant="outline" className="flex-shrink-0">
                    {Math.round(steps)} step{Math.round(steps) !== 1 ? "s" : ""}
                  </Badge>
                </div>
              ))}
          </div>
        </Card>
      )}
    </div>
  )
}

