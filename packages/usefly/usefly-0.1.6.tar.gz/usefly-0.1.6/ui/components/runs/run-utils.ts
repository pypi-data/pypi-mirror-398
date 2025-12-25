"use client"

import {
  MousePointer,
  ArrowDown,
  Navigation,
  Type,
  Search,
  ArrowLeft,
  Clock,
  Upload,
  GitBranch as TabsIcon,
  X,
  FileText,
  Keyboard,
  Eye,
  Camera,
  ChevronDown,
  CheckCircle2,
  LucideIcon,
} from "lucide-react"
import type { PersonaRun } from "@/types/api"

// Types
export interface DerivedMetrics {
  totalActions: number
  pagesVisited: number
  actionsPerPage: Record<string, number>
  averageActionsPerPage: number
  actionTypeBreakdown: Record<string, number>
  timePerPage: Record<string, number>
  successRate: number
  completionRate: number
}

// Event Type to Icon Mapping
export const EVENT_ICON_MAP: Record<string, LucideIcon> = {
  click: MousePointer,
  scroll: ArrowDown,
  navigate: Navigation,
  input: Type,
  search: Search,
  go_back: ArrowLeft,
  wait: Clock,
  upload_file: Upload,
  switch_tab: TabsIcon,
  close_tab: X,
  extract: FileText,
  send_keys: Keyboard,
  find_text: Eye,
  screenshot: Camera,
  dropdown_options: ChevronDown,
  select_dropdown: ChevronDown,
  done: CheckCircle2,
}

// Event Type to Color Mapping (Tailwind classes)
export const EVENT_COLOR_MAP: Record<string, string> = {
  click: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  scroll: "bg-teal-500/10 text-teal-600 border-teal-500/20",
  navigate: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  input: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
  search: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  go_back: "bg-gray-500/10 text-gray-600 border-gray-500/20",
  wait: "bg-slate-500/10 text-slate-600 border-slate-500/20",
  upload_file: "bg-green-500/10 text-green-600 border-green-500/20",
  switch_tab: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  close_tab: "bg-red-500/10 text-red-600 border-red-500/20",
  extract: "bg-violet-500/10 text-violet-600 border-violet-500/20",
  send_keys: "bg-pink-500/10 text-pink-600 border-pink-500/20",
  find_text: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  screenshot: "bg-lime-500/10 text-lime-600 border-lime-500/20",
  dropdown_options: "bg-fuchsia-500/10 text-fuchsia-600 border-fuchsia-500/20",
  select_dropdown: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  done: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
}

// Get event description from event data
export function getEventDescription(event: any): string {
  switch (event.type) {
    case "click":
      return `Clicked element${event.interacted_element?.text ? `: "${event.interacted_element.text}"` : ""}`
    case "scroll":
      return `Scrolled ${event.direction || "down"} (${event.pages || 1} pages)`
    case "navigate":
      return `Navigated to ${event.target_url || event.url}`
    case "input":
      return `Typed: "${event.text || ""}"`
    case "search":
      return `Searched for: "${event.query || ""}"`
    case "go_back":
      return "Navigated back"
    case "wait":
      return `Waited ${event.seconds || 3}s`
    case "upload_file":
      return `Uploaded file: ${event.path || ""}`
    case "switch_tab":
      return "Switched tab"
    case "close_tab":
      return "Closed tab"
    case "extract":
      return `Extracted: "${event.query || ""}"`
    case "send_keys":
      return `Sent keys: ${event.keys || ""}`
    case "find_text":
      return `Found text: "${event.text || ""}"`
    case "screenshot":
      return "Took screenshot"
    case "dropdown_options":
      return "Checked dropdown options"
    case "select_dropdown":
      return `Selected: "${event.text || ""}"`
    case "done":
      return `Completed: ${event.text || ""}`
    default:
      return event.type || "Unknown action"
  }
}

// Metrics Calculation Functions

export function calculateActionsPerPage(
  events: any[]
): Record<string, number> {
  const pageActions: Record<string, number> = {}
  events.forEach((event) => {
    if (event.url) {
      pageActions[event.url] = (pageActions[event.url] || 0) + 1
    }
  })
  return pageActions
}

export function calculateSuccessRate(run: PersonaRun): number {
  if (!run.is_done) return 0
  if (run.error_type) return 0
  return 100
}

export function calculateTimePerPage(
  events: any[]
): Record<string, number> {
  const pageTime: Record<string, { start: number; end: number }> = {}

  events.forEach((event, idx) => {
    if (event.url && event.type === "navigate") {
      if (!pageTime[event.url]) {
        pageTime[event.url] = { start: idx, end: idx }
      }
      pageTime[event.url].end = idx
    }
  })

  // Convert to step counts
  return Object.entries(pageTime).reduce(
    (acc, [url, times]) => {
      acc[url] = times.end - times.start
      return acc
    },
    {} as Record<string, number>
  )
}

export function calculateActionTypeBreakdown(events: any[]): Record<string, number> {
  const breakdown: Record<string, number> = {}
  events.forEach((event) => {
    if (event.type) {
      breakdown[event.type] = (breakdown[event.type] || 0) + 1
    }
  })
  return breakdown
}

export function calculateDerivedMetrics(run: PersonaRun): DerivedMetrics {
  const events = run.events || []
  const uniquePages = new Set(events.map((e) => e.url).filter(Boolean))

  return {
    totalActions: events.length,
    pagesVisited: uniquePages.size,
    actionsPerPage: calculateActionsPerPage(events),
    averageActionsPerPage:
      uniquePages.size > 0 ? events.length / uniquePages.size : 0,
    actionTypeBreakdown: calculateActionTypeBreakdown(events),
    timePerPage: calculateTimePerPage(events),
    successRate: calculateSuccessRate(run),
    completionRate:
      run.total_steps > 0 ? (run.steps_completed / run.total_steps) * 100 : 0,
  }
}

// Format URL for display
export function formatUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    // Decode the pathname separately to handle multi-byte characters
    const pathname = decodeURIComponent(urlObj.pathname)
    return urlObj.hostname + (pathname !== "/" ? pathname : "")
  } catch {
    // If URL parsing fails, return the URL as-is
    return url
  }
}

// Get full decoded URL for title/hover
export function getFullDecodedUrl(url: string): string {
  try {
    return decodeURIComponent(url)
  } catch {
    return url
  }
}

// Format date for display
export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return dateString
  }
}

// Format duration in seconds to human readable format
export function formatDuration(seconds?: number): string {
  if (!seconds) return "0s"
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

// Get status badge configuration
// Centralized status labels and descriptions
export const STATUS_LABELS = {
  SUCCESS: {
    label: "Success",
    tooltip: "Agent successfully completed its goal",
    className: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  },
  GOAL_NOT_MET: {
    label: "Goal Not Met",
    tooltip: "Agent completed but did not achieve its goal",
    className: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  },
  ERROR: {
    label: "Error",
    tooltip: "Technical error occurred during execution",
    className: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  },
  IN_PROGRESS: {
    label: "In Progress",
    tooltip: "Agent is still running",
    className: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  },
  UNKNOWN: {
    label: "Unknown",
    tooltip: "Status could not be determined",
    className: "bg-gray-500/10 text-gray-600 border-gray-500/20",
  },
} as const

export type StatusType = keyof typeof STATUS_LABELS

export function getStatusConfig(run: PersonaRun): {
  label: string
  tooltip: string
  className: string
  type: StatusType
} {
  // Error (purple): execution didn't complete (is_done = false)
  if (!run.is_done) {
    return { ...STATUS_LABELS.ERROR, type: "ERROR" }
  }

  // Goal Not Met (amber): completed but task failed
  const verdict = run.judgement_data?.verdict
  const failureReason = run.judgement_data?.failure_reason
  if (run.is_done && (verdict === false || failureReason)) {
    return { ...STATUS_LABELS.GOAL_NOT_MET, type: "GOAL_NOT_MET" }
  }

  // Success (green): completed successfully
  if (run.is_done && verdict === true && !failureReason) {
    return { ...STATUS_LABELS.SUCCESS, type: "SUCCESS" }
  }

  // Fallback (gray)
  return { ...STATUS_LABELS.UNKNOWN, type: "UNKNOWN" }
}

