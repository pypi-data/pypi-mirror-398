"use client"

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react"
import { personaExecutionApi } from "@/lib/api-client"
import { RunStatusResponse, ActiveExecutionsResponse } from "@/types/api"
import { toast } from "sonner"

// Completion listener callback type
type CompletionListener = (execution: RunStatusResponse) => void

interface ExecutionContextType {
  activeExecutions: RunStatusResponse[]
  isPolling: boolean
  isStatusBarExpanded: boolean
  expandedExecutionIds: string[]
  startExecution: (scenarioId: string) => Promise<void>
  refreshExecutions: () => Promise<void>
  toggleStatusBar: () => void
  toggleExecutionExpanded: (runId: string) => void
  onExecutionComplete: (listener: CompletionListener) => () => void
}

const ExecutionContext = createContext<ExecutionContextType | undefined>(undefined)

const POLL_INTERVAL = 3000 // 3 seconds for real-time feeling

export function ExecutionProvider({ children }: { children: React.ReactNode }) {
  const [activeExecutions, setActiveExecutions] = useState<RunStatusResponse[]>([])
  const [isPolling, setIsPolling] = useState(false)
  const [isStatusBarExpanded, setIsStatusBarExpanded] = useState(false)
  const [expandedExecutionIds, setExpandedExecutionIds] = useState<string[]>([])
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)
  const completionListenersRef = useRef<Set<CompletionListener>>(new Set())

  // Fetch active executions from backend
  const fetchActiveExecutions = useCallback(async () => {
    try {
      const response = await personaExecutionApi.getActiveExecutions()
      if (mountedRef.current) {
        setActiveExecutions(response.executions)
      }
      return response.executions
    } catch (error) {
      console.error("Error fetching active executions:", error)
      return []
    }
  }, [])

  // Poll for updates
  const pollExecutions = useCallback(async () => {
    const executions = await fetchActiveExecutions()

    // Check for completed executions and show notifications
    for (const execution of executions) {
      if (["completed", "partial_failure", "failed"].includes(execution.status)) {
        const name = execution.scenario_name || "Scenario"

        if (execution.status === "completed") {
          toast.success(`${name} completed`, {
            description: `All ${execution.total_tasks} tasks completed successfully`
          })
        } else if (execution.status === "partial_failure") {
          toast.warning(`${name} completed with errors`, {
            description: `${execution.completed_tasks}/${execution.total_tasks} tasks succeeded`
          })
        } else {
          toast.error(`${name} failed`, {
            description: `${execution.failed_tasks} tasks failed`
          })
        }

        // Notify completion listeners
        completionListenersRef.current.forEach(listener => {
          try {
            listener(execution)
          } catch (e) {
            console.error("Error in completion listener:", e)
          }
        })

        // Acknowledge completion
        try {
          await personaExecutionApi.acknowledgeCompletion(execution.run_id)
        } catch (e) {
          console.error("Error acknowledging completion:", e)
        }
      }
    }
  }, [fetchActiveExecutions])

  // Start/stop polling based on active executions
  useEffect(() => {
    const hasActive = activeExecutions.some(e => e.status === "in_progress")

    if (hasActive && !pollIntervalRef.current) {
      setIsPolling(true)
      pollIntervalRef.current = setInterval(pollExecutions, POLL_INTERVAL)
    } else if (!hasActive && pollIntervalRef.current) {
      setIsPolling(false)
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [activeExecutions, pollExecutions])

  // Initial fetch on mount
  useEffect(() => {
    mountedRef.current = true
    fetchActiveExecutions()

    return () => {
      mountedRef.current = false
    }
  }, [fetchActiveExecutions])

  // Start a new execution
  const startExecution = useCallback(async (scenarioId: string) => {
    try {
      const response = await personaExecutionApi.run(scenarioId)

      toast.success("Scenario execution started", {
        description: `Running ${response.task_count} tasks in background`
      })

      // Immediately fetch to get the new execution in the list
      await fetchActiveExecutions()

      // Auto-expand status bar when starting new execution
      setIsStatusBarExpanded(true)
      if (response?.run_id) {
        setExpandedExecutionIds(prev => [...prev, response.run_id])
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to start execution"
      toast.error(errorMessage)
      throw error
    }
  }, [fetchActiveExecutions])

  const toggleStatusBar = useCallback(() => {
    setIsStatusBarExpanded(prev => !prev)
  }, [])

  const toggleExecutionExpanded = useCallback((runId: string) => {
    setExpandedExecutionIds(prev =>
      prev.includes(runId)
        ? prev.filter(id => id !== runId)
        : [...prev, runId]
    )
  }, [])

  // Register a completion listener and return unsubscribe function
  const onExecutionComplete = useCallback((listener: CompletionListener) => {
    completionListenersRef.current.add(listener)
    return () => {
      completionListenersRef.current.delete(listener)
    }
  }, [])

  const value: ExecutionContextType = {
    activeExecutions,
    isPolling,
    isStatusBarExpanded,
    expandedExecutionIds,
    startExecution,
    refreshExecutions: async () => { await fetchActiveExecutions() },
    toggleStatusBar,
    toggleExecutionExpanded,
    onExecutionComplete
  }

  return (
    <ExecutionContext.Provider value={value}>
      {children}
    </ExecutionContext.Provider>
  )
}

export function useExecutions() {
  const context = useContext(ExecutionContext)
  if (context === undefined) {
    throw new Error("useExecutions must be used within an ExecutionProvider")
  }
  return context
}
