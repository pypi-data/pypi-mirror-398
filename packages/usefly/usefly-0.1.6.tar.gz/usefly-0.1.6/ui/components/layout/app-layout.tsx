import type React from "react"
import { Sidebar } from "./sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { MissingSettingsBanner } from "@/components/banners/missing-settings-banner"
import { ExecutionStatusBar } from "@/components/execution-status-bar"

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <MissingSettingsBanner />
        <div className="sticky top-0 z-50 flex justify-end px-6 py-4 bg-background/95 backdrop-blur border-b border-border">
          <ThemeToggle />
        </div>
        <div className="bg-background flex-1 pb-14">{children}</div>
      </main>
      <ExecutionStatusBar />
    </div>
  )
}
