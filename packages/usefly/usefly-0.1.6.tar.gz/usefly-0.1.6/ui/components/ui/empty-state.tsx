"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileQuestion, AlertCircle, Search, Plus } from "lucide-react"
import { cn } from "@/lib/utils"

export type EmptyStateVariant = "default" | "no-data" | "no-results" | "error"

interface EmptyStateProps {
    title: string
    description?: string
    variant?: EmptyStateVariant
    icon?: React.ReactNode
    action?: {
        label: string
        onClick: () => void
    }
    className?: string
}

const variantIcons: Record<EmptyStateVariant, React.ReactNode> = {
    default: <FileQuestion className="w-12 h-12 text-muted-foreground/50" />,
    "no-data": <Plus className="w-12 h-12 text-muted-foreground/50" />,
    "no-results": <Search className="w-12 h-12 text-muted-foreground/50" />,
    error: <AlertCircle className="w-12 h-12 text-amber-500/50" />,
}

/**
 * Reusable empty state component for consistent UX across the app.
 * Use this whenever displaying an empty list, no results, or error states.
 */
export function EmptyState({
    title,
    description,
    variant = "default",
    icon,
    action,
    className,
}: EmptyStateProps) {
    const displayIcon = icon ?? variantIcons[variant]

    return (
        <Card className={cn("p-12", className)}>
            <div className="flex flex-col items-center justify-center text-center">
                {displayIcon && (
                    <div className="mb-4">
                        {displayIcon}
                    </div>
                )}
                <p className="text-lg font-medium text-foreground mb-2">{title}</p>
                {description && (
                    <p className="text-sm text-muted-foreground max-w-md">{description}</p>
                )}
                {action && (
                    <Button
                        onClick={action.onClick}
                        className="mt-4"
                        variant="outline"
                    >
                        {action.label}
                    </Button>
                )}
            </div>
        </Card>
    )
}
