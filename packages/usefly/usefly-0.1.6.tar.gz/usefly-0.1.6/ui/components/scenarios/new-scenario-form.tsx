"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"
import { crawlerApi, scenarioApi } from "@/lib/api-client"
import { useExecutions } from "@/contexts/execution-context"
import { Sparkles } from "lucide-react"
import { SCENARIO_ADJECTIVES } from "@/lib/constants"

// Generate a random scenario name from URL
const generateScenarioName = (url: string): string => {
  try {
    const urlObj = new URL(url)
    const hostname = urlObj.hostname
      .replace(/^www\./, '')
      .replace(/\.[^.]+$/, '') // Remove TLD

    const adjective = SCENARIO_ADJECTIVES[Math.floor(Math.random() * SCENARIO_ADJECTIVES.length)]
    return `${hostname} - ${adjective}`
  } catch {
    const adjective = SCENARIO_ADJECTIVES[Math.floor(Math.random() * SCENARIO_ADJECTIVES.length)]
    return `test - ${adjective}`
  }
}

export function NewScenarioForm() {
  const router = useRouter()
  const { refreshExecutions } = useExecutions()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [formData, setFormData] = useState({
    name: "",
    website_url: "",
    description: "",
    email: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.website_url) {
      toast.error("Please enter a website URL")
      return
    }

    // Auto-generate name if not provided
    const scenarioName = formData.name || generateScenarioName(formData.website_url)

    setIsSubmitting(true)

    try {
      // STEP 1: Create empty scenario first
      const createResponse = await scenarioApi.create({
        name: scenarioName,
        website_url: formData.website_url,
        description: formData.description || "",
        email: formData.email || "",
        personas: ["crawler"],
      })

      const scenarioId = createResponse.id

      try {
        // STEP 2: Start async analysis on the created scenario
        await crawlerApi.analyze({
          scenario_id: scenarioId,
          website_url: formData.website_url,
          description: formData.description || "",
          name: scenarioName,
          metrics: [],
          email: formData.email || "",
        })
      } catch (analyzeError) {
        // Cleanup orphaned scenario if analyze fails
        await scenarioApi.delete(scenarioId)
        throw analyzeError
      }

      toast.success("Scenario created and analysis started", {
        description: "Check the status bar below for progress"
      })

      // Refresh executions to show in status bar
      await refreshExecutions()

      // Navigate to scenarios page immediately
      router.push("/scenarios")
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to create scenario"
      toast.error("Failed to create scenario", {
        description: errorMessage,
      })
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <CardTitle>Create New Scenario</CardTitle>
          </div>
          <CardDescription>
            Enter your website URL and let AI agents explore your site to generate test scenarios.
            Analysis runs in the background - track progress in the status bar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">
                Scenario Name <span className="text-muted-foreground">(Optional)</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g., Homepage User Flow"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
              <p className="text-sm text-muted-foreground">
                Leave blank to auto-generate a name from your website URL
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="website_url">
                Website URL <span className="text-red-500">*</span>
              </Label>
              <Input
                id="website_url"
                type="url"
                placeholder="https://example.com"
                value={formData.website_url}
                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                required
              />
              <p className="text-sm text-muted-foreground">
                The URL of the website you want to test
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">
                Description <span className="text-muted-foreground">(Optional)</span>
              </Label>
              <Textarea
                id="description"
                placeholder="Describe what you want to test on this website..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-semibold">
                Email Address <span className="text-destructive">*</span>
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="your.email@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
              <p className="text-xs text-muted-foreground">
                We'll send the completed report to this email address.
              </p>
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/scenarios")}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Scenario
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
