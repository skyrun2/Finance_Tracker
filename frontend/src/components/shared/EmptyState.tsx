import { cn } from "@/lib/utils"
import { Inbox } from "lucide-react"

interface EmptyStateProps {
  message?: string
  className?: string
}

export function EmptyState({ message = "No records found", className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 text-muted-foreground", className)}>
      <Inbox className="h-12 w-12 mb-4" />
      <p className="text-lg font-medium">{message}</p>
    </div>
  )
}
