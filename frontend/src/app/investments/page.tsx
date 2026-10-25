"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { api } from "@/services/api"
import type { Investment, InvestmentFlow, InvestmentHistory } from "@/types"
import { formatCurrency } from "@/lib/constants"
import { PageHeader } from "@/components/shared/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { TrendingUp, TrendingDown, Minus, PiggyBank, Bitcoin, Pencil } from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from "recharts"

const typeConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  CDI: { label: "CDB 100% CDI", color: "text-green-600", icon: PiggyBank },
  CDI_PLUS: { label: "CDB 82% CDI", color: "text-blue-600", icon: PiggyBank },
  CRYPTO: { label: "Cryptocurrency", color: "text-orange-600", icon: Bitcoin },
}

const CHART_COLORS = ["#22c55e", "#3b82f6", "#f97316"]

export default function InvestmentsPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")

  const { data: investments, isLoading } = useQuery<Investment[]>({
    queryKey: ["investments"],
    queryFn: () => api.get("/api/v1/investments"),
  })

  const { data: history } = useQuery<InvestmentHistory[]>({
    queryKey: ["investments-history"],
    queryFn: () => api.get("/api/v1/investments/history?months=12"),
  })

  const { data: flows } = useQuery<InvestmentFlow[]>({
    queryKey: ["investments-flows"],
    queryFn: () => api.get("/api/v1/investments/flows?months=2"),
  })

  const snapshotMutation = useMutation({
    mutationFn: ({ id, value }: { id: string; value: number }) =>
      api.post(`/api/v1/investments/${id}/snapshot`, { value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investments"] })
      queryClient.invalidateQueries({ queryKey: ["investments-history"] })
      setEditingId(null)
    },
  })

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Investments" />
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  const total_current = investments?.reduce((s, i) => s + i.current_value, 0) ?? 0
  const total_invested = investments?.reduce((s, i) => s + i.invested_value, 0) ?? 0
  const total_diff = total_current - total_invested
  const total_pct = total_invested > 0 ? (total_diff / total_invested) * 100 : 0

  // Build chart data per month from history
  const historyByMonth: Record<string, Record<string, number>> = {}
  const invNames: Record<string, string> = {}
  investments?.forEach((inv) => { invNames[inv.id] = inv.name })
  history?.forEach((h) => {
    const key = h.date.slice(0, 7)
    if (!historyByMonth[key]) historyByMonth[key] = {}
    historyByMonth[key][h.investment_id] = h.value
  })
  const chartData = Object.entries(historyByMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, values]) => ({
      month,
      ...values,
    }))

  return (
    <div className="space-y-6">
      <PageHeader title="Investments" description="Track your investments" />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(total_current)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Invested</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(total_invested)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Profit/Loss</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${total_diff >= 0 ? "text-green-600" : "text-red-600"}`}>
              {formatCurrency(total_diff)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Return</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${total_pct >= 0 ? "text-green-600" : "text-red-600"}`}>
              {total_pct >= 0 ? "+" : ""}{total_pct.toFixed(2)}%
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {investments?.map((inv) => {
          const cfg = typeConfig[inv.type] || { label: inv.type, color: "text-muted-foreground", icon: Minus }
          const Icon = cfg.icon
          const diff = inv.current_value - inv.invested_value
          const pct = inv.invested_value > 0 ? (diff / inv.invested_value) * 100 : 0
          const isEditing = editingId === inv.id

          return (
            <Card key={inv.id}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Icon className={`h-5 w-5 ${cfg.color}`} />
                  {inv.name}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingId(inv.id)
                    setEditValue(String(inv.current_value))
                  }}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Current Balance</p>
                  {isEditing ? (
                    <div className="flex items-center gap-2 mt-1">
                      <Input
                        type="number"
                        step="0.01"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="h-8"
                      />
                      <Button
                        size="sm"
                        onClick={() => {
                          const v = parseFloat(editValue)
                          if (!isNaN(v)) {
                            snapshotMutation.mutate({ id: inv.id, value: v })
                          }
                        }}
                      >
                        Save
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <p className={`text-2xl font-bold ${cfg.color}`}>{formatCurrency(inv.current_value)}</p>
                  )}
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Invested</span>
                  <span>{formatCurrency(inv.invested_value)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{diff >= 0 ? "Profit" : "Loss"}</span>
                  <span className={diff >= 0 ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                    {formatCurrency(diff)} ({pct >= 0 ? "+" : ""}{pct.toFixed(2)}%)
                  </span>
                </div>
                {inv.description && (
                  <p className="text-xs text-muted-foreground pt-2 border-t">{inv.description}</p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {flows && flows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Movements (Last 2 Months)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {flows.map((f) => (
                <div
                  key={`${f.month}-${f.year}`}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="font-medium">
                    {f.month.toString().padStart(2, "0")}/{f.year}
                  </div>
                  <div className="flex gap-6">
                    <div className="flex items-center gap-2 text-sm">
                      <TrendingDown className="h-4 w-4 text-red-600" />
                      <span className="text-muted-foreground">Withdrew</span>
                      <span className="font-semibold text-red-600">
                        {formatCurrency(f.redeemed)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="text-muted-foreground">Deposited</span>
                      <span className="font-semibold text-green-600">
                        {formatCurrency(f.applied)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Monthly Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(v) => formatCurrency(v)} />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Legend />
                {investments?.map((inv, idx) => (
                  <Line
                    key={inv.id}
                    type="monotone"
                    dataKey={inv.id}
                    name={inv.name}
                    stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
