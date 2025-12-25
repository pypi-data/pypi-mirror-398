"use client"

import { useExecutions } from "@/contexts/execution-context"
import { RunStatusResponse, TaskProgressStatus } from "@/types/api"
import { ChevronUp, ChevronDown, Loader2, CheckCircle2, XCircle, Clock, Globe, Sparkles, Save } from "lucide-react"
import { cn } from "@/lib/utils"

function formatAction(action: string | undefined): string {
  if (!action) return ""
  return action.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())
}

interface ExtendedTaskProgress extends TaskProgressStatus {
  phase?: string;
}

function TaskProgressItem({ task }: { task: TaskProgressStatus }) {
  const statusIcons = {
    pending: <Clock className="w-3 h-3 text-muted-foreground" />,
    running: <Loader2 className="w-3 h-3 animate-spin text-blue-500" />,
    completed: <CheckCircle2 className="w-3 h-3 text-green-500" />,
    failed: <XCircle className="w-3 h-3 text-red-500" />
  }

  return (
    <div className="flex items-center gap-2 text-xs py-1">
      {statusIcons[task.status]}
      <span className="font-medium min-w-[100px]">{task.persona}</span>
      {task.status === "running" && (
        <span className="text-muted-foreground">
          Step {task.current_step}/{task.max_steps}
          {task.current_action && ` - ${formatAction(task.current_action)}`}
        </span>
      )}
      {task.status === "completed" && (
        <span className="text-green-600">Done</span>
      )}
      {task.status === "failed" && (
        <span className="text-red-600 truncate max-w-[200px]">
          {task.error || "Failed"}
        </span>
      )}
    </div>
  )
}

// Phase indicators for scenario analysis
function AnalysisPhaseIndicator({ phase, currentStep, maxSteps }: { phase: string, currentStep: number, maxSteps: number }) {
  const phases = [
    { key: "crawling", label: "Exploring Website", icon: Globe },
    { key: "generating_tasks", label: "Generating Personas", icon: Sparkles },
    { key: "saving", label: "Saving Scenario", icon: Save },
  ]

  const currentPhaseIndex = phases.findIndex(p => p.key === phase)

  return (
    <div className="space-y-2">
      {phases.map((p, idx) => {
        const Icon = p.icon
        const isActive = p.key === phase
        const isCompleted = idx < currentPhaseIndex
        const isPending = idx > currentPhaseIndex

        return (
          <div key={p.key} className="flex items-center gap-2 text-xs">
            {isCompleted ? (
              <CheckCircle2 className="w-3 h-3 text-green-500" />
            ) : isActive ? (
              <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
            ) : (
              <Clock className="w-3 h-3 text-muted-foreground" />
            )}
            <Icon className={cn("w-3 h-3", isActive ? "text-blue-500" : isCompleted ? "text-green-500" : "text-muted-foreground")} />
            <span className={cn("font-medium", isPending && "text-muted-foreground")}>{p.label}</span>
            {isActive && phase === "crawling" && (
              <span className="text-muted-foreground">
                Step {currentStep}/{maxSteps}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function ExecutionItem({ execution, isExpanded, onToggle }: { execution: RunStatusResponse, isExpanded: boolean, onToggle: () => void }) {
  const isAnalysis = execution.run_type === "scenario_analysis"
  const runningTasks = execution.task_progress.filter(t => t.status === "running")

  // For analysis, get phase from first task progress
  const analysisPhase = isAnalysis && execution.task_progress[0]
    ? (execution.task_progress[0] as ExtendedTaskProgress).phase || "crawling"
    : null
  const analysisStep = isAnalysis && execution.task_progress[0]
    ? execution.task_progress[0].current_step
    : 0
  const analysisMaxSteps = isAnalysis && execution.task_progress[0]
    ? execution.task_progress[0].max_steps
    : 30

  // Calculate progress based on type
  let progress = 0
  let progressLabel = ""

  if (isAnalysis) {
    // For analysis, progress is based on phases
    const phaseProgress: Record<string, number> = {
      "crawling": 33,
      "generating_tasks": 66,
      "saving": 90,
      "completed": 100
    }
    progress = phaseProgress[analysisPhase || "crawling"] || 0
    progressLabel = formatAction(analysisPhase || "crawling")
  } else {
    // For persona runs, progress is based on tasks
    progress = execution.total_tasks > 0
      ? Math.round(((execution.completed_tasks + execution.failed_tasks) / execution.total_tasks) * 100)
      : 0
    progressLabel = `${execution.completed_tasks + execution.failed_tasks}/${execution.total_tasks}`
  }

  return (
    <div className={cn("border-l-2 pl-3 py-1", isAnalysis ? "border-purple-500" : "border-blue-500")}>
      <div
        className="flex items-center gap-2 cursor-pointer hover:bg-accent/50 rounded px-1 -ml-1"
        onClick={onToggle}
      >
        <Loader2 className={cn("w-3 h-3 animate-spin flex-shrink-0", isAnalysis ? "text-purple-500" : "text-blue-500")} />
        <span className="font-medium text-sm truncate max-w-[150px]">
          {execution.scenario_name || "Running"}
        </span>
        {isAnalysis ? (
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Globe className="w-3 h-3" />
            {progressLabel}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">
            {progressLabel}
          </span>
        )}
        <div className="flex-1 h-1.5 bg-secondary rounded-full min-w-[60px] max-w-[100px]">
          <div
            className={cn("h-full rounded-full transition-all", isAnalysis ? "bg-purple-500" : "bg-blue-500")}
            style={{ width: `${progress}%` }}
          />
        </div>
        {isExpanded ? (
          <ChevronDown className="w-3 h-3 text-muted-foreground" />
        ) : (
          <ChevronUp className="w-3 h-3 text-muted-foreground" />
        )}
      </div>

      {isExpanded && (
        <div className="mt-2 pl-5 space-y-0.5 max-h-[200px] overflow-y-auto">
          {isAnalysis ? (
            <AnalysisPhaseIndicator
              phase={analysisPhase || "crawling"}
              currentStep={analysisStep}
              maxSteps={analysisMaxSteps}
            />
          ) : (
            execution.task_progress.map((task) => (
              <TaskProgressItem key={task.task_index} task={task} />
            ))
          )}
          {execution.logs.length > 0 && (
            <div className="mt-2 pt-2 border-t border-border">
              <div className="text-xs text-muted-foreground font-medium mb-1">Recent Activity</div>
              <div className="space-y-0.5 text-xs text-muted-foreground max-h-[80px] overflow-y-auto">
                {execution.logs.slice(-5).map((log, i) => (
                  <div key={i} className="truncate">{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ExecutionStatusBar() {
  const { activeExecutions, isStatusBarExpanded, toggleStatusBar, expandedExecutionIds, toggleExecutionExpanded } = useExecutions()

  // Only show active (in_progress) executions
  const inProgressExecutions = activeExecutions.filter(e => e.status === "in_progress")

  if (inProgressExecutions.length === 0) {
    return null
  }

  // Calculate overall stats
  const totalTasks = inProgressExecutions.reduce((sum, e) => sum + e.total_tasks, 0)
  const completedTasks = inProgressExecutions.reduce((sum, e) => sum + e.completed_tasks + e.failed_tasks, 0)

  // Get all running tasks for summary
  const runningTasks = inProgressExecutions.flatMap(e =>
    e.task_progress.filter(t => t.status === "running")
  )

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-background border-t shadow-lg">
      {/* Collapsed bar */}
      <div
        className={cn(
          "flex items-center gap-3 px-4 py-2 cursor-pointer hover:bg-accent/50 transition-colors",
          isStatusBarExpanded && "border-b"
        )}
        onClick={toggleStatusBar}
      >
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="font-medium text-sm">
            {inProgressExecutions.length} Active
          </span>
        </div>

        <div className="h-4 w-px bg-border" />

        {/* Summary of running executions */}
        <div className="flex-1 flex items-center gap-4 overflow-x-auto text-sm">
          {inProgressExecutions.slice(0, 3).map(execution => {
            const isAnalysis = execution.run_type === "scenario_analysis"
            const phase = isAnalysis && execution.task_progress[0]
              ? (execution.task_progress[0] as ExtendedTaskProgress).phase || "crawling"
              : null

            return (
              <div key={execution.run_id} className="flex items-center gap-2 whitespace-nowrap">
                {isAnalysis && <Globe className="w-3 h-3 text-purple-500" />}
                <span className="text-muted-foreground">{execution.scenario_name}:</span>
                {isAnalysis ? (
                  <span className="text-purple-600">{formatAction(phase || "crawling")}</span>
                ) : (
                  <span>{execution.completed_tasks + execution.failed_tasks}/{execution.total_tasks}</span>
                )}
              </div>
            )
          })}
          {inProgressExecutions.length > 3 && (
            <span className="text-muted-foreground">
              +{inProgressExecutions.length - 3} more
            </span>
          )}
        </div>

        {/* Current action preview */}
        {runningTasks.length > 0 && runningTasks[0].current_action && (
          <>
            <div className="h-4 w-px bg-border" />
            <span className="text-xs text-muted-foreground hidden md:block truncate max-w-[200px]">
              {runningTasks[0].persona}: {formatAction(runningTasks[0].current_action)}
            </span>
          </>
        )}

        <div className="flex items-center gap-1 text-muted-foreground">
          {isStatusBarExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronUp className="w-4 h-4" />
          )}
        </div>
      </div>

      {/* Expanded panel */}
      {isStatusBarExpanded && (
        <div className="max-h-[300px] overflow-y-auto p-4 space-y-3">
          {inProgressExecutions.map(execution => (
            <ExecutionItem
              key={execution.run_id}
              execution={execution}
              isExpanded={expandedExecutionIds.includes(execution.run_id)}
              onToggle={() => toggleExecutionExpanded(execution.run_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
