"use client"

import { AlertCircle, X } from "lucide-react"
import { useState } from "react"

export function Header() {
  const [dismissBanner, setDismissBanner] = useState(false)

  if (dismissBanner) return null

  return (
    <div className="sticky top-0 z-40 bg-background/95 backdrop-blur border-b border-border">
      <div className="px-6 py-3 flex items-start sm:items-center gap-4 bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 border-b border-primary/20">
        <div className="flex items-start sm:items-center gap-3 flex-1">
          <AlertCircle className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">Demo Mode Active</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              All data is simulated for demonstration purposes. This showcases how Usefly analyzes agentic user
              behavior across your SaaS or e-commerce app.
            </p>
          </div>
        </div>
        <button
          onClick={() => setDismissBanner(true)}
          className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors mt-0.5"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
