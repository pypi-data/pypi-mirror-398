"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Loader2, Play, Plus, Pencil, Trash2, Sparkles, X, Check, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { scenarioApi, crawlerApi } from "@/lib/api-client"
import { Scenario, CrawlerAnalysisResponse, CreateScenarioRequest } from "@/types/api"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { GeneratePersonasDialog } from "./generate-personas-dialog"

// Available personas for e-commerce and SaaS contexts
const AVAILABLE_PERSONAS = [
  "First-time Visitor",
  "Web Shopper",
  "Mobile Shopper",
  "Power User",
  "Free Trial User",
  "Demo Requester",
  "Subscription Manager",
  "Support Seeker",
  "Feature Explorer",
]

interface Task {
  number: number
  persona: string
  starting_url: string
  goal: string
  steps: string
  stop?: string
}

interface ScenarioPersonasModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: 'create' | 'edit'
  scenario?: Scenario
  analysisResult?: CrawlerAnalysisResponse
  createFormData?: {
    name: string
    website_url: string
    description?: string
    metrics: string[]
    email: string
  }
  onSave?: (scenarioId: string) => void
  onUpdate?: (scenarioId: string) => void
  onDelete?: (scenarioId: string) => void
  onRun?: (scenario: Scenario) => Promise<void>
}

export function ScenarioPersonasModal({
  open,
  onOpenChange,
  mode,
  scenario,
  analysisResult,
  createFormData,
  onSave,
  onUpdate,
  onDelete,
  onRun,
}: ScenarioPersonasModalProps) {
  const router = useRouter()

  // State
  const [selectedTasks, setSelectedTasks] = useState<Set<number>>(new Set())
  const [localTasks, setLocalTasks] = useState<Task[]>([])
  const [tasksModified, setTasksModified] = useState(false)  // Track if tasks array changed
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)
  const [personaFilters, setPersonaFilters] = useState<Set<string>>(new Set())

  // Task editing state
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [showTaskEditor, setShowTaskEditor] = useState(false)
  const [personaPopoverOpen, setPersonaPopoverOpen] = useState(false)

  // Initialize tasks and selection
  useEffect(() => {
    if (!open) return

    if (mode === 'create' && analysisResult?.tasks) {
      setLocalTasks(analysisResult.tasks as Task[])
      setSelectedTasks(new Set(analysisResult.tasks.map((t: any) => t.number)))
      setTasksModified(false)
    } else if (mode === 'edit' && scenario) {
      setLocalTasks((scenario.tasks || []) as Task[])
      const selectedNumbers = scenario.tasks_metadata?.selected_task_numbers || []
      setSelectedTasks(new Set(selectedNumbers))
      setTasksModified(false)
    }
  }, [open, mode, analysisResult, scenario])

  const tasksMetadata = mode === 'create'
    ? analysisResult?.tasks_metadata
    : scenario?.tasks_metadata

  const crawlerSummary = mode === 'create'
    ? analysisResult?.crawler_summary
    : scenario?.crawler_final_result

  const toggleTask = (taskNumber: number) => {
    setSelectedTasks(prev => {
      const next = new Set(prev)
      if (next.has(taskNumber)) {
        next.delete(taskNumber)
      } else {
        next.add(taskNumber)
      }
      return next
    })
  }

  // Add new task
  const handleAddTask = () => {
    const newTaskNumber = localTasks.length > 0
      ? Math.max(...localTasks.map(t => t.number)) + 1
      : 1

    setEditingTask({
      number: newTaskNumber,
      persona: AVAILABLE_PERSONAS[0] || "Explorer",
      starting_url: scenario?.website_url || createFormData?.website_url || "",
      goal: "",
      steps: ""
    })
    setShowTaskEditor(true)
  }

  // Edit existing task
  const handleEditTask = (task: Task, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingTask({ ...task })
    setShowTaskEditor(true)
  }

  // Delete task
  const handleDeleteTask = (taskNumber: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setLocalTasks(prev => prev.filter(t => t.number !== taskNumber))
    setSelectedTasks(prev => {
      const next = new Set(prev)
      next.delete(taskNumber)
      return next
    })
    setTasksModified(true)
    toast.success("Persona deleted")
  }

  // Save edited task
  const handleSaveTask = () => {
    if (!editingTask) return

    if (!editingTask.goal.trim()) {
      toast.error("Goal is required")
      return
    }

    const isNew = !localTasks.find(t => t.number === editingTask.number)

    if (isNew) {
      setLocalTasks(prev => [...prev, editingTask])
      setSelectedTasks(prev => new Set([...prev, editingTask.number]))
    } else {
      setLocalTasks(prev => prev.map(t =>
        t.number === editingTask.number ? editingTask : t
      ))
    }

    setTasksModified(true)
    setShowTaskEditor(false)
    setEditingTask(null)
    toast.success(isNew ? "Persona added" : "Persona updated")
  }

  const handleSave = async () => {

    setIsSaving(true)
    try {
      if (mode === 'create') {
        // Create new scenario
        if (!analysisResult || !createFormData) {
          toast.error("Missing required data for scenario creation")
          return
        }

        const createRequest: CreateScenarioRequest = {
          name: createFormData.name,
          website_url: createFormData.website_url,
          description: createFormData.description || "",
          personas: ["crawler"],
          metrics: createFormData.metrics,
          email: createFormData.email,
          tasks: localTasks,
          selected_task_indices: Array.from(selectedTasks).map(taskNum =>
            localTasks.findIndex(t => t.number === taskNum)
          ),
          tasks_metadata: analysisResult.tasks_metadata || { total_tasks: 0, persona_distribution: {} },
          discovered_urls: [],
          crawler_final_result: analysisResult.crawler_summary || "",
          crawler_extracted_content: analysisResult.crawler_extracted_content || ""
        }

        const response = await crawlerApi.save(createRequest)

        toast.success("Scenario saved successfully!", {
          description: `Created scenario with ${selectedTasks.size} personas`
        })

        onSave?.(response.id)
        onOpenChange(false)
      } else {
        // Update existing scenario
        if (!scenario) {
          toast.error("Scenario not found")
          return
        }

        if (tasksModified) {
          // Tasks were added, edited, or deleted - use full update
          await scenarioApi.updateTasksFull(scenario.id, localTasks, Array.from(selectedTasks))
        } else {
          // Only selection changed - use simple update
          await scenarioApi.updateTasks(scenario.id, Array.from(selectedTasks))
        }

        toast.success("Scenario updated successfully!", {
          description: `Updated with ${selectedTasks.size} selected personas`
        })

        onUpdate?.(scenario.id)
        onOpenChange(false)
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Operation failed"
      toast.error(mode === 'create' ? "Save failed" : "Update failed", {
        description: errorMessage
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handlePlay = async () => {
    if (!scenario || !onRun) return

    setIsRunning(true)
    try {
      const currentSelected = scenario.tasks_metadata?.selected_task_numbers || []
      const newSelected = Array.from(selectedTasks)

      const hasSelectionChanged = currentSelected.length !== newSelected.length ||
        !currentSelected.every(n => newSelected.includes(n))

      if (tasksModified || hasSelectionChanged) {
        toast.info("Saving changes before running...")
        if (tasksModified) {
          await scenarioApi.updateTasksFull(scenario.id, localTasks, newSelected)
        } else {
          await scenarioApi.updateTasks(scenario.id, newSelected)
        }
      }

      await onRun(scenario)
      onOpenChange(false)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to run scenario"
      toast.error(errorMessage)
    } finally {
      setIsRunning(false)
    }
  }

  const handleDelete = async () => {
    if (!scenario) return

    setIsDeleting(true)
    try {
      await scenarioApi.delete(scenario.id)

      toast.success("Scenario deleted successfully")

      onDelete?.(scenario.id)
      setShowDeleteDialog(false)
      onOpenChange(false)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Delete failed"
      toast.error("Delete failed", {
        description: errorMessage
      })
    } finally {
      setIsDeleting(false)
    }
  }

  const handleTasksGenerated = async () => {
    if (mode === 'edit' && scenario) {
      try {
        const updated = await scenarioApi.get(scenario.id)
        setLocalTasks((updated.tasks || []) as Task[])
        const selectedNumbers = updated.tasks_metadata?.selected_task_numbers || []
        setSelectedTasks(new Set(selectedNumbers))
        toast.success("Tasks refreshed")
      } catch (error) {
        console.error("Failed to refresh tasks:", error)
      }
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-2xl">
              {mode === 'create' ? 'Scenario Analysis Complete' : 'Edit Scenario Personas to Run'}
            </DialogTitle>
            <DialogDescription>
              {mode === 'create'
                ? 'Review the generated personas and select which ones to include in your scenario'
                : 'Update persona selection or add new personas for this scenario'}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-6 pr-4">
            {!localTasks.length && (
              <Card className="border-amber-200 bg-amber-50">
                <CardHeader>
                  <CardTitle className="text-sm text-amber-900">No Personas Available</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-amber-800">
                  This scenario doesn't have any personas yet. Click "Add Persona" to create one.
                </CardContent>
              </Card>
            )}
            {/* Website Analysis Summary */}
            {crawlerSummary && (() => {
              // Parse crawlerSummary to extract context
              let context: { summary?: string; target_audience?: string; value_proposition?: string; vertical?: string } | null = null
              try {
                const parsed = typeof crawlerSummary === 'string' ? JSON.parse(crawlerSummary) : crawlerSummary
                context = parsed?.context || null
              } catch {
                // If parsing fails, context remains null
              }

              return context ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Website Analysis Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {context.summary && (
                      <div>
                        <p className="text-sm font-medium text-foreground">Summary</p>
                        <p className="text-sm text-muted-foreground">{context.summary}</p>
                      </div>
                    )}
                    {context.target_audience && (
                      <div>
                        <p className="text-sm font-medium text-foreground">Target Audience</p>
                        <p className="text-sm text-muted-foreground">{context.target_audience}</p>
                      </div>
                    )}
                    {context.value_proposition && (
                      <div>
                        <p className="text-sm font-medium text-foreground">Value Proposition</p>
                        <p className="text-sm text-muted-foreground">{context.value_proposition}</p>
                      </div>
                    )}
                    {context.vertical && (
                      <div>
                        <p className="text-sm font-medium text-foreground">Vertical</p>
                        <p className="text-sm text-muted-foreground">{context.vertical}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : null
            })()}

            {/* Persona Distribution - Filter */}
            {tasksMetadata?.persona_distribution && Object.keys(tasksMetadata.persona_distribution).length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">Filter by Persona Type</CardTitle>
                      <CardDescription className="mt-1">
                        Click to filter the personas list below
                      </CardDescription>
                    </div>
                    {personaFilters.size > 0 && (
                      <button
                        type="button"
                        onClick={() => setPersonaFilters(new Set())}
                        className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
                      >
                        Clear filters
                      </button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {Object.entries(tasksMetadata.persona_distribution).map(
                      ([persona, count]) => {
                        const isSelected = personaFilters.has(persona)
                        return (
                          <button
                            key={persona}
                            type="button"
                            onClick={() => {
                              setPersonaFilters(prev => {
                                const next = new Set(prev)
                                if (next.has(persona)) {
                                  next.delete(persona)
                                } else {
                                  next.add(persona)
                                }
                                return next
                              })
                            }}
                            className={cn(
                              "flex items-center justify-between p-3 rounded transition-all duration-150",
                              "border hover:border-primary/50 cursor-pointer",
                              isSelected
                                ? "bg-primary/10 border-primary ring-1 ring-primary/30"
                                : "bg-muted border-transparent hover:bg-muted/80"
                            )}
                          >
                            <span className={cn(
                              "text-sm font-medium",
                              isSelected && "text-primary"
                            )}>{persona}</span>
                            <Badge variant={isSelected ? "default" : "secondary"}>{String(count)}</Badge>
                          </button>
                        )
                      }
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Task Generation Error Warning */}
            {tasksMetadata?.error && (
              <Card className="border-amber-200 bg-amber-50">
                <CardHeader>
                  <CardTitle className="text-sm text-amber-900">Task Generation Warning</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-amber-800">
                  {tasksMetadata.error}
                </CardContent>
              </Card>
            )}

            {/* Tasks Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      Personas to Run ({localTasks.length})
                    </CardTitle>
                    <CardDescription>
                      {personaFilters.size > 0 ? (
                        <>
                          Showing {localTasks.filter(t => personaFilters.has(t.persona)).length} of {localTasks.length} personas
                          <span className="ml-1 text-primary">(filtered)</span>
                        </>
                      ) : (
                        <>Selected: {selectedTasks.size} of {localTasks.length}</>
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {mode === 'edit' && (
                      <Button
                        onClick={() => setShowGenerateDialog(true)}
                        size="sm"
                        variant="default"
                      >
                        <Sparkles className="w-4 h-4 mr-1" />
                        Generate More Personas
                      </Button>
                    )}
                    <Button onClick={handleAddTask} size="sm" variant="outline">
                      <Plus className="w-4 h-4 mr-1" />
                      Add Persona
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {localTasks
                  .filter((task: Task) =>
                    personaFilters.size === 0 || personaFilters.has(task.persona)
                  )
                  .map((task: Task) => (
                    <div
                      key={task.number}
                      className={cn(
                        "border rounded-lg p-4 transition-colors cursor-pointer group",
                        selectedTasks.has(task.number)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      )}
                      onClick={() => toggleTask(task.number)}
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={selectedTasks.has(task.number)}
                          onCheckedChange={() => toggleTask(task.number)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">Persona Run {task.number}</span>
                              <Badge variant="outline" className="text-xs">
                                {task.persona}
                              </Badge>
                            </div>
                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7"
                                onClick={(e) => handleEditTask(task, e)}
                              >
                                <Pencil className="w-3.5 h-3.5" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-destructive hover:text-destructive"
                                onClick={(e) => handleDeleteTask(task.number, e)}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>
                          <div className="space-y-1 text-sm">
                            <p className="text-muted-foreground">
                              <span className="font-medium">Starting URL:</span>{" "}
                              <span className="break-all">{task.starting_url}</span>
                            </p>
                            <p>
                              <span className="font-medium">Goal:</span> {task.goal}
                            </p>
                            <p className="text-muted-foreground">
                              <span className="font-medium">Steps:</span> {task.steps}
                            </p>
                            {task.stop && (
                              <p className="text-muted-foreground">
                                <span className="font-medium">Stop:</span> {task.stop}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </CardContent>
            </Card>
          </div>

          <DialogFooter className="mt-4 border-t pt-4">
            <div className="flex justify-between w-full">
              <div className="flex gap-2">
                {mode === 'edit' && (
                  <>
                    <Button
                      variant="default"
                      onClick={handlePlay}
                      disabled={isRunning || isSaving || selectedTasks.size === 0}
                    >
                      {isRunning ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Starting...
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Run Selected Personas
                        </>
                      )}
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => setShowDeleteDialog(true)}
                      disabled={isDeleting || isSaving || isRunning}
                    >
                      Delete Scenario
                    </Button>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  {mode === 'create' ? 'Cancel' : 'Close'}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isSaving || isRunning}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      {mode === 'create' ? 'Saving...' : 'Updating...'}
                    </>
                  ) : (
                    <>
                      {mode === 'create' ? `Save Scenario (${selectedTasks.size} personas)` : `Save Changes (${selectedTasks.size} personas)`}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Task Editor Dialog */}
      <Dialog open={showTaskEditor} onOpenChange={setShowTaskEditor}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingTask && localTasks.find(t => t.number === editingTask.number)
                ? 'Edit Persona'
                : 'Add New Persona'}
            </DialogTitle>
          </DialogHeader>
          {editingTask && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1.5 block">Persona</label>
                <Popover open={personaPopoverOpen} onOpenChange={setPersonaPopoverOpen}>
                  <PopoverTrigger asChild>
                    <div className="relative">
                      <Input
                        value={editingTask.persona}
                        onChange={(e) => setEditingTask({ ...editingTask, persona: e.target.value })}
                        onFocus={() => setPersonaPopoverOpen(true)}
                        placeholder="Type or select a persona..."
                        className="pr-8"
                      />
                      <ChevronsUpDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 opacity-50 pointer-events-none" />
                    </div>
                  </PopoverTrigger>
                  <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
                    <Command>
                      <CommandList className="max-h-48 overflow-y-auto">
                        <CommandGroup heading="Suggested Personas">
                          {AVAILABLE_PERSONAS
                            .filter((p) => p.toLowerCase().includes(editingTask.persona.toLowerCase()))
                            .map((p) => (
                            <CommandItem
                              key={p}
                              value={p}
                              onSelect={() => {
                                setEditingTask({ ...editingTask, persona: p })
                                setPersonaPopoverOpen(false)
                              }}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  editingTask.persona === p ? "opacity-100" : "opacity-0"
                                )}
                              />
                              {p}
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
                <p className="text-xs text-muted-foreground mt-1">
                  Select from suggestions or type your own custom persona
                </p>
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Starting URL</label>
                <Input
                  value={editingTask.starting_url}
                  onChange={(e) => setEditingTask({ ...editingTask, starting_url: e.target.value })}
                  placeholder="https://example.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Goal *</label>
                <Input
                  value={editingTask.goal}
                  onChange={(e) => setEditingTask({ ...editingTask, goal: e.target.value })}
                  placeholder="What should the persona accomplish?"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Steps</label>
                <Textarea
                  value={editingTask.steps}
                  onChange={(e) => setEditingTask({ ...editingTask, steps: e.target.value })}
                  placeholder="Describe the steps to complete the goal..."
                  rows={4}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setShowTaskEditor(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveTask}>
                  {localTasks.find(t => t.number === editingTask.number) ? 'Update Persona' : 'Add Persona'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Scenario</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this scenario? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex gap-3 justify-end">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Generate Tasks Dialog */}
      {mode === 'edit' && scenario && (
        <GeneratePersonasDialog
          open={showGenerateDialog}
          onOpenChange={setShowGenerateDialog}
          scenarioId={scenario.id}
          onSuccess={handleTasksGenerated}
        />
      )}
    </>
  )
}
