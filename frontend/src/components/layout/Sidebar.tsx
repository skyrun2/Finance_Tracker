"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  ArrowLeftRight,
  Banknote,
  Tags,
  Target,
  TrendingUp,
  Upload,
  Eye,
  EyeOff,
} from "lucide-react"
import { useVisibility } from "@/hooks/use-visibility"

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/accounts", label: "Accounts", icon: Banknote },
  { href: "/investments", label: "Investments", icon: TrendingUp },
  { href: "/categories", label: "Categories", icon: Tags },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/imports", label: "Import", icon: Upload },
]

export function Sidebar() {
  const pathname = usePathname()
  const { visible, toggle } = useVisibility()

  return (
    <aside className="w-64 border-r bg-card flex flex-col h-screen">
      <div className="p-6 border-b flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">finance</h1>
          <p className="text-sm text-muted-foreground">Financial Management</p>
        </div>
        <button
          onClick={toggle}
          className="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground"
          title={visible ? "Hide values" : "Show values"}
        >
          {visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname === href
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
