"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ExpensePieChart } from "@/components/charts/ExpensePieChart"
import { MonthlyHistoryChart } from "@/components/charts/MonthlyHistoryChart"
import { formatCurrency, formatDate } from "@/lib/constants"
import { api } from "@/services/api"
import type { DashboardSummary, MonthlyHistoryPoint } from "@/types"
import { ArrowDown, ArrowUp, Wallet, TrendingUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useVisibility } from "@/hooks/use-visibility"

export default function DashboardPage() {
  const { data, isLoading } = useQuery<DashboardSummary>({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/api/v1/dashboard/summary"),
  })
  const { data: history } = useQuery<MonthlyHistoryPoint[]>({
    queryKey: ["dashboard-history"],
    queryFn: () => api.get("/api/v1/dashboard/monthly-history?months=100"),
  })
  const { visible } = useVisibility()
  const mask = (v: string) => (visible ? v : "$ ••••")

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  const cards = [
    {
      title: "Monthly Balance",
      value: mask(formatCurrency(data?.total_balance ?? 0)),
      icon: Wallet,
      color: (data?.total_balance ?? 0) >= 0 ? "text-green-600" : "text-red-600",
    },
    {
      title: "Investments",
      value: mask(formatCurrency(data?.investment_balance ?? 0)),
      icon: TrendingUp,
      color: "text-purple-600",
    },
    {
      title: "Monthly Income",
      value: mask(formatCurrency(data?.monthly_income ?? 0)),
      icon: ArrowUp,
      color: "text-green-600",
    },
    {
      title: "Monthly Expenses",
      value: mask(formatCurrency(data?.monthly_expense ?? 0)),
      icon: ArrowDown,
      color: "text-red-600",
    },
  ]

  return (
    <div className="space-y-6 max-w-7xl">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <Card key={card.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {card.title}
                </CardTitle>
                <Icon className={`h-5 w-5 ${card.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Expenses by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ExpensePieChart data={data?.expenses_by_category ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Monthly History</CardTitle>
          </CardHeader>
          <CardContent>
            <MonthlyHistoryChart data={history ?? []} visible={visible} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Account</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data?.recent_transactions ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                    No transactions found
                  </TableCell>
                </TableRow>
              ) : (
                data?.recent_transactions.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>{formatDate(t.transaction_date)}</TableCell>
                    <TableCell className="font-medium">{t.description}</TableCell>
                    <TableCell>{t.account_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{t.category_name || "Uncategorized"}</Badge>
                    </TableCell>
                    <TableCell className={`text-right font-medium ${t.type === "EXPENSE" ? "text-red-600" : "text-green-600"}`}>
                      {visible
                        ? (t.type === "EXPENSE" ? "-" : "+") + formatCurrency(t.amount)
                        : "$ ••••"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
