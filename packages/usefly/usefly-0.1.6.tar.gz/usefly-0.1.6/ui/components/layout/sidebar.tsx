"use client"

import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import { BarChart3, FileText, Sparkles, Settings, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/scenarios", label: "Scenarios", icon: Sparkles },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/runs", label: "Runs", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
]

const wipItems = [
  { href: "/metrics", label: "Metrics", icon: BarChart3 },
]


export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-border bg-sidebar pt-6 flex flex-col">
      {/* Logo */}
      <div className="px-6 pb-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-sidebar-foreground">
          <Image
            src="/favicon.png"
            alt="Usefly Logo"
            width={32}
            height={32}
            className="w-8 h-8 rounded-lg"
          />
          Usefly
        </Link>
      </div>


      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-4">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50",
              )}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </Link>
          )
        })}

        {/* Work in Progress Section */}
        <div className="pt-6">
          <div className="px-4 pb-2">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Work in Progress
            </span>
          </div>
          {wipItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-2 rounded-md text-sm font-medium",
                  "text-muted-foreground/50 hover:text-muted-foreground hover:bg-sidebar-accent/30"
                )}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </div>
      </nav>


    </aside>
  )
}
