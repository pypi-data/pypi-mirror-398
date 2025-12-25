"use client"

import { Card } from "@/components/ui/card"
import { AlertCircle, MousePointer, Edit3, Navigation, Zap, Download } from "lucide-react"
import type { ReplayEvent, ReplaySession } from "./mock-replay-data"

interface EventLogProps {
  events: ReplayEvent[]
  session: ReplaySession
  currentTime: number
}

export function EventLog({ events, session, currentTime }: EventLogProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case "click":
        return <MousePointer className="w-4 h-4" />
      case "input":
        return <Edit3 className="w-4 h-4" />
      case "navigate":
        return <Navigation className="w-4 h-4" />
      case "scroll":
        return <Zap className="w-4 h-4" />
      case "error":
        return <AlertCircle className="w-4 h-4" />
      case "load":
        return <Download className="w-4 h-4" />
      default:
        return null
    }
  }

  const getEventColor = (type: string) => {
    const colors: Record<string, string> = {
      click: "bg-blue-500/10 text-blue-500 border-blue-500/20",
      scroll: "bg-teal-500/10 text-teal-500 border-teal-500/20",
      input: "bg-purple-500/10 text-purple-500 border-purple-500/20",
      navigate: "bg-amber-500/10 text-amber-500 border-amber-500/20",
      error: "bg-red-500/10 text-red-500 border-red-500/20",
      load: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    }
    return colors[type] || "bg-gray-500/10 text-gray-500 border-gray-500/20"
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <Card className="p-6 bg-card border-border">
      <div className="mb-4">
        <h3 className="font-semibold">Event Log</h3>
        <p className="text-xs text-muted-foreground mt-1">
          {events.length} events recorded ({events.length} completed, {session.events.length - events.length} remaining)
        </p>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">No events yet. Press play to start.</p>
        ) : (
          events.map((event, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
              <div className={`mt-0.5 p-2 rounded-md border ${getEventColor(event.type)}`}>
                {getEventIcon(event.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium capitalize">
                  {event.type} on {event.element}
                </p>
                {event.value && <p className="text-xs text-muted-foreground mt-1">{event.value}</p>}
              </div>
              <div className="text-xs text-muted-foreground whitespace-nowrap">{formatTime(event.timestamp)}</div>
            </div>
          ))
        )}
      </div>
    </Card>
  )
}
