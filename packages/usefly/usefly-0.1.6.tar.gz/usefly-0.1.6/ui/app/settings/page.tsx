"use client"

import Link from "next/link"
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { toast } from "sonner"
import { Settings as SettingsIcon, Loader, Save, ChevronLeft } from "lucide-react"
import { formatModelName } from "@/lib/utils"
import { systemConfigApi } from "@/lib/api-client"
import { SystemConfig } from "@/types/api"
import { AppLayout } from "@/components/layout/app-layout"
import { useSettings } from "@/contexts/settings-context"

const formSchema = z.object({
  provider: z.string().min(1, "Provider is required"),
  model_name: z.string().min(1, "Model name is required"),
  api_key: z.string().min(1, "API key is required"),
  use_thinking: z.boolean(),
  max_steps: z.number().min(10).max(100),
  max_browser_workers: z.number().min(1).max(10),
})

type FormData = z.infer<typeof formSchema>

const providerModels = {
  openai: [
    // GPT-5.2 series (latest)
    "gpt-5.2-pro",
    "gpt-5.2",
    // GPT-5.1 series
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-mini",
    // GPT-5 series
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    // GPT-4.1 series
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    // O-series reasoning models
    "o4-mini",
    "o3",
    "o3-mini",
    "o1",
    "o1-mini",
    "o1-preview",
    // GPT-4o series
    "gpt-4o",
    "gpt-4o-mini",
    "chatgpt-4o-latest",
    // Legacy models
    "gpt-4-turbo",
    "gpt-4",
  ],
  claude: [
    // Claude 4.5 series (latest)
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20250929",
    // Claude 4 series
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    // Claude 3.5 series
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
  ],
  groq: [
    // Llama 4 models (latest)
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    // Other verified models
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
  ],
  google: [
    // Gemini 3 (latest)
    "gemini-3-pro-preview",
    // Gemini 2.5 series
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    // Gemini 2.0 series
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    // Gemma 3 models
    "gemma-3-27b-it",
    "gemma-3-12b",
    "gemma-3-4b",
  ],
} as const

export default function SettingsPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [config, setConfig] = useState<SystemConfig | null>(null)
  const { refreshStatus } = useSettings()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      provider: "openai",
      model_name: "gpt-5",
      api_key: "",
      use_thinking: true,
      max_steps: 30,
      max_browser_workers: 3,
    },
  })

  const useThinking = watch("use_thinking")
  const selectedProvider = watch("provider") as keyof typeof providerModels

  // Fetch existing config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setLoading(true)
        const data = await systemConfigApi.get()
        setConfig(data)
        setValue("provider", data.provider || "openai")
        setValue("model_name", data.model_name)
        setValue("api_key", data.api_key)
        setValue("use_thinking", data.use_thinking)
        setValue("max_steps", data.max_steps || 30)
        setValue("max_browser_workers", data.max_browser_workers || 3)
      } catch (error) {
        // Config doesn't exist yet, use defaults
        console.log("No existing config found, using defaults")
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [setValue])

  const onSubmit = async (data: FormData) => {
    setSaving(true)

    try {
      const updated = await systemConfigApi.update(data)
      setConfig(updated)
      // Refresh the settings context to update the banner
      await refreshStatus()
      toast.success("Settings saved successfully!", {
        description: "System configuration has been updated.",
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to save settings"
      toast.error(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="container mx-auto py-8">
          <div className="flex items-center justify-center py-12">
            <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading settings...</span>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="container mx-auto py-8 max-w-3xl">
        <div className="mb-6">
          <Link href="/scenarios" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors">
            <ChevronLeft className="w-4 h-4" />
            Back
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <SettingsIcon className="w-6 h-6" />
            <h1 className="text-3xl font-bold">System Settings</h1>
          </div>
          <p className="text-muted-foreground">
            Configure the AI model and API settings for the crawler agent.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>AI Model Configuration</CardTitle>
            <CardDescription>
              Set the OpenAI model and API key for running website crawls.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Provider */}
              <div className="space-y-2">
                <Label htmlFor="provider" className="text-sm font-semibold">
                  AI Provider <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={selectedProvider}
                  onValueChange={(value) => {
                    setValue("provider", value)
                    // Reset model to first available model for this provider
                    const firstModel = providerModels[value as keyof typeof providerModels][0]
                    setValue("model_name", firstModel)
                  }}
                >
                  <SelectTrigger id="provider">
                    <SelectValue placeholder="Select a provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="claude">Anthropic (Claude)</SelectItem>
                    <SelectItem value="groq">Groq</SelectItem>
                    <SelectItem value="google">Google</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Choose the AI provider for your crawler agent
                </p>
              </div>

              {/* Model Name */}
              <div className="space-y-2">
                <Label htmlFor="model_name" className="text-sm font-semibold">
                  Model <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={watch("model_name")}
                  onValueChange={(value) => setValue("model_name", value)}
                >
                  <SelectTrigger id="model_name">
                    <SelectValue placeholder="Select a model">
                      {watch("model_name") ? formatModelName(watch("model_name")) : "Select a model"}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {providerModels[selectedProvider]?.map((model) => (
                      <SelectItem key={model} value={model}>
                        {formatModelName(model)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.model_name && (
                  <p className="text-sm text-destructive">{errors.model_name.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  The model to use for the crawler agent
                </p>
              </div>

              {/* API Key */}
              <div className="space-y-2">
                <Label htmlFor="api_key" className="text-sm font-semibold">
                  API Key <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="api_key"
                  type="password"
                  placeholder="Enter your API key..."
                  {...register("api_key")}
                  className={errors.api_key ? "border-destructive" : ""}
                />
                {errors.api_key && (
                  <p className="text-sm text-destructive">{errors.api_key.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Your API key for the selected provider
                </p>
              </div>

              {/* Max Steps */}
              <div className="space-y-2">
                <Label htmlFor="max_steps" className="text-sm font-semibold">
                  Max Browser Steps <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="max_steps"
                  type="number"
                  placeholder="30"
                  min="10"
                  max="100"
                  {...register("max_steps", { valueAsNumber: true })}
                  className={errors.max_steps ? "border-destructive" : ""}
                />
                {errors.max_steps && (
                  <p className="text-sm text-destructive">{errors.max_steps.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Maximum number of steps the browser agent can take (10-100)
                </p>
              </div>

              {/* Max Browser Workers */}
              <div className="space-y-2">
                <Label htmlFor="max_browser_workers" className="text-sm font-semibold">
                  Max Parallel Browser Workers <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="max_browser_workers"
                  type="number"
                  placeholder="3"
                  min="1"
                  max="10"
                  {...register("max_browser_workers", { valueAsNumber: true })}
                  className={errors.max_browser_workers ? "border-destructive" : ""}
                />
                {errors.max_browser_workers && (
                  <p className="text-sm text-destructive">{errors.max_browser_workers.message}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Number of browser tasks to run in parallel (1-10)
                </p>
              </div>

              {/* Use Thinking */}
              <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
                <div className="flex-1 space-y-1">
                  <Label htmlFor="use_thinking" className="text-sm font-semibold cursor-pointer">
                    Enable Thinking Mode
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Allow the AI to use extended thinking for complex decisions
                  </p>
                </div>
                <Switch
                  id="use_thinking"
                  checked={useThinking}
                  onCheckedChange={(checked) => setValue("use_thinking", checked)}
                />
              </div>

              {/* Save Button */}
              <div className="pt-4 flex justify-end gap-3">
                {config && (
                  <div className="flex-1 text-xs text-muted-foreground flex items-center">
                    Last updated: {new Date(config.updated_at).toLocaleString()}
                  </div>
                )}
                <Button
                  type="submit"
                  disabled={saving}
                  className="min-w-[120px]"
                >
                  {saving ? (
                    <>
                      <Loader className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Settings
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="mt-6 bg-muted/30 border-muted">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Important Notes</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>• The API key is stored securely and used only for crawler operations</p>
            <p>• Changes take effect immediately for new crawler runs</p>
            <p>• Thinking mode may increase API costs but improve analysis quality</p>
            <p>• Make sure your API key has sufficient credits for crawler operations</p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
