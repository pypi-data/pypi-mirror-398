"use client"

import Link from "next/link"
import { AlertTriangle, Settings, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSettings } from "@/contexts/settings-context"
import { useState } from "react"

export function MissingSettingsBanner() {
  const { isConfigured, isLoading } = useSettings()
  const [isDismissed, setIsDismissed] = useState(false)

  // Don't show if loading, configured, or dismissed
  if (isLoading || isConfigured || isDismissed) {
    return null
  }

  return (
    <div className="bg-amber-50 dark:bg-amber-950/50 border-b border-amber-200 dark:border-amber-800">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
              <span className="font-medium text-amber-800 dark:text-amber-200">
                Configuration Required
              </span>
              <span className="text-sm text-amber-700 dark:text-amber-300">
                Please configure your API key in settings to use the system.
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              asChild
              size="sm"
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              <Link href="/settings">
                <Settings className="h-4 w-4 mr-1.5" />
                Configure Settings
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsDismissed(true)}
              className="text-amber-600 hover:text-amber-800 hover:bg-amber-100 dark:text-amber-400 dark:hover:text-amber-200 dark:hover:bg-amber-900/50 h-8 w-8 p-0"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
