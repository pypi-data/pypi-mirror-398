"use client"

import { useState } from "react"
import { ChevronDown, AlertCircle, CheckCircle2, Clock } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { RunDetailsModal } from "./run-details-modal"
import type { PersonaRun } from "@/types/api"
import { getPersonaLabel } from "./mock-data"

interface RunTableProps {
  runs: PersonaRun[]
}

export function RunTable({ runs }: RunTableProps) {
  const [selectedRun, setSelectedRun] = useState<PersonaRun | null>(null)

  const getStatusIcon = (isDone: boolean, errorType?: string) => {
    if (errorType && errorType !== "") {
      return <AlertCircle className="w-4 h-4 text-red-500" />
    }
    if (isDone) {
      return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
    }
    return <Clock className="w-4 h-4 text-blue-500 animate-spin" />
  }

  const getStatusBadge = (run: PersonaRun) => {
    const hasError = run.error_type && run.error_type !== ""
    const isSuccess = run.is_done && run.judgement_data?.verdict === true
    const isGoalNotMet = run.is_done && run.judgement_data?.verdict === false

    if (hasError) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30 cursor-help">Error</Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Technical error occurred during execution</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    if (isSuccess) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30 cursor-help">Success</Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Agent successfully completed its goal</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    if (isGoalNotMet) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30 cursor-help">Goal Not Met</Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Agent completed but did not achieve its goal</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    if (!run.is_done) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 hover:bg-blue-500/30 cursor-help">In Progress</Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Agent is still running</p>
          </TooltipContent>
        </Tooltip>
      )
    }
    return <Badge variant="secondary">Unknown</Badge>
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  return (
    <TooltipProvider>
      <Card className="border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card/50">
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Persona</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Platform</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Progress</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Duration</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Timestamp</th>
                <th className="px-6 py-4 text-left font-medium text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedRun(run)}
                >
                  <td className="px-6 py-4 font-medium">{getPersonaLabel(run.persona_type)}</td>
                  <td className="px-6 py-4">
                    <Badge variant="outline" className="capitalize">
                      {run.platform}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(run.is_done, run.error_type)}
                      {getStatusBadge(run)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${run.total_steps > 0 ? (run.steps_completed / run.total_steps) * 100 : 0}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {run.steps_completed}/{run.total_steps}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-muted-foreground">{run.duration_seconds ? Math.round(run.duration_seconds * 10) / 10 : 0}s</td>
                  <td className="px-6 py-4 text-muted-foreground text-xs">{formatDate(run.timestamp)}</td>
                  <td className="px-6 py-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedRun(run)
                      }}
                    >
                      <ChevronDown className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {selectedRun && <RunDetailsModal run={selectedRun} onClose={() => setSelectedRun(null)} />}
    </TooltipProvider>
  )
}
