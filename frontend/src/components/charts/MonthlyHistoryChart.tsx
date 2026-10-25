"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts"
import { formatCurrency } from "@/lib/constants"
import type { MonthlyHistoryPoint } from "@/types"

interface MonthlyHistoryChartProps {
  data: MonthlyHistoryPoint[]
  visible?: boolean
}

export function MonthlyHistoryChart({ data, visible = true }: MonthlyHistoryChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No data available
      </div>
    )
  }

  const chartData = data.map((d) => ({
    name: `${d.month.toString().padStart(2, "0")}/${d.year}`,
    Income: d.income,
    Expenses: d.expense,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis
          tickFormatter={(v) =>
            visible
              ? new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  notation: "compact",
                }).format(Number(v))
              : ""
          }
        />
        <Tooltip
          formatter={(value) => (visible ? formatCurrency(Number(value)) : "$ ••••")}
        />
        <Legend />
        <Bar dataKey="Income" fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Expenses" fill="#ef4444" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
