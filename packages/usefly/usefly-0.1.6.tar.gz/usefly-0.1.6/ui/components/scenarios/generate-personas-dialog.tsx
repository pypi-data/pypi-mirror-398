"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Loader2, Sparkles } from "lucide-react"
import { toast } from "sonner"
import { scenarioApi } from "@/lib/api-client"
import { GenerateMoreTasksRequest } from "@/types/api"

interface GeneratePersonasDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  scenarioId: string
  onSuccess: () => void
}

export function GeneratePersonasDialog({
  open,
  onOpenChange,
  scenarioId,
  onSuccess
}: GeneratePersonasDialogProps) {
  const [numTasks, setNumTasks] = useState(15)
  const [promptType, setPromptType] = useState<"original" | "friction">("friction")
  const [customPrompt, setCustomPrompt] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = async () => {
    console.log("handleGenerate called", { scenarioId, numTasks, promptType, customPrompt })

    // Validation
    if (numTasks < 1) {
      toast.error("Number of personas must be at least 1")
      return
    }

    setIsGenerating(true)
    try {
      const request: GenerateMoreTasksRequest = {
        num_tasks: numTasks,
        prompt_type: promptType,
        custom_prompt: customPrompt || undefined
      }

      const response = await scenarioApi.generateMoreTasks(scenarioId, request)

      toast.success("Personas generated successfully!", {
        description: `Generated ${response.new_tasks.length} new personas`
      })

      onSuccess()
      onOpenChange(false)

      // Reset form
      setNumTasks(15)
      setPromptType("friction")
      setCustomPrompt("")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Persona generation failed"
      toast.error("Generation failed", {
        description: errorMessage
      })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Generate More Personas
          </DialogTitle>
          <DialogDescription>
            Generate additional personas for this scenario using AI. New personas will be automatically selected.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Number of Personas */}
          <div className="space-y-2">
            <Label htmlFor="num-personas">
              Number of Personas
            </Label>
            <Input
              id="num-personas"
              type="number"
              min={1}
              value={numTasks}
              onChange={(e) => setNumTasks(parseInt(e.target.value) || 5)}
            />
            <p className="text-sm text-muted-foreground">
              Recommended: 3-8 personas for focused testing
            </p>
          </div>

          {/* Custom Prompt */}
          <div className="space-y-2">
            <Label htmlFor="custom-prompt">
              Custom Instructions (Optional)
            </Label>
            <Textarea
              id="custom-prompt"
              placeholder="Add specific instructions to customize task generation, e.g., 'Focus on mobile checkout flow' or 'Test international shipping scenarios'"
              rows={4}
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
            />
            <p className="text-sm text-muted-foreground">
              These instructions will be included in the prompt to tailor persona generation
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isGenerating}>
            Cancel
          </Button>
          <Button type="button" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate {numTasks} Personas
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
