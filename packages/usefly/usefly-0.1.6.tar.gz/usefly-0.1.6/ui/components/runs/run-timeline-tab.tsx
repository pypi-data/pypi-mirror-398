"use client"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  EVENT_COLOR_MAP,
  EVENT_ICON_MAP,
  getEventDescription,
  formatUrl,
  getFullDecodedUrl,
} from "./run-utils"

interface RunTimelineTabProps {
  events: any[]
}

interface TimelineEventProps {
  event: any
  index: number
  totalEvents: number
}

function TimelineEvent({ event, index, totalEvents }: TimelineEventProps) {
  const colorClass = EVENT_COLOR_MAP[event.type] || EVENT_COLOR_MAP.click
  const IconComponent = EVENT_ICON_MAP[event.type]
  const isLast = index === totalEvents - 1

  return (
    <div className="flex gap-3">
      {/* Icon Column */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center border-2",
            colorClass
          )}
        >
          {IconComponent && <IconComponent className="w-5 h-5" />}
        </div>
        {!isLast && (
          <div className="w-0.5 h-12 bg-border my-2" />
        )}
      </div>

      {/* Content Column */}
      <div className="pb-3 flex-1 min-w-0 pt-1">
        <Card className="p-3 hover:bg-muted/50 transition-colors group/event">
          <div className="space-y-2">
            {/* Main content */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium leading-snug">
                  {getEventDescription(event)}
                </p>
              </div>
              <Badge
                variant="outline"
                className="text-xs capitalize flex-shrink-0"
              >
                {event.type}
              </Badge>
            </div>

            {/* URL and step info */}
            <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
              <span title={event.url ? getFullDecodedUrl(event.url) : ""}>
                Step {event.step}
                {event.url && ` • ${formatUrl(event.url)}`}
              </span>
            </div>

            {/* Hover details */}
            <div className="hidden group-hover/event:block pt-2 border-t space-y-1 text-xs text-muted-foreground">
              {event.coordinate_x !== undefined &&
                event.coordinate_y !== undefined && (
                  <p>
                    📍 Coordinates: ({event.coordinate_x}, {event.coordinate_y})
                  </p>
                )}
              {event.interacted_element?.text && (
                <p>🎯 Element: {event.interacted_element.text}</p>
              )}
              {event.interacted_element?.selector && (
                <p className="font-mono text-xs opacity-60 break-all">
                  {event.interacted_element.selector}
                </p>
              )}
              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <div className="mt-1 p-2 bg-muted rounded">
                  <p className="font-medium mb-1">Metadata:</p>
                  <pre className="text-xs overflow-auto">
                    {JSON.stringify(event.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export function RunTimelineTab({ events }: RunTimelineTabProps) {
  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <p>No events recorded for this run</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between sticky top-0 bg-background/95 backdrop-blur py-2 -mx-4 px-4">
        <h3 className="text-sm font-medium">Event Timeline</h3>
        <p className="text-xs text-muted-foreground">
          {events.length} event{events.length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="space-y-2">
        {events.map((event, idx) => (
          <TimelineEvent
            key={idx}
            event={event}
            index={idx}
            totalEvents={events.length}
          />
        ))}
      </div>
    </div>
  )
}
