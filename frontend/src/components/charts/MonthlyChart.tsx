"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { formatCurrency } from "@/lib/constants"

interface MonthlyChartProps {
  income: number
  expense: number
}

export function MonthlyChart({ income, expense }: MonthlyChartProps) {
  const data = [
    { name: "Income", value: income, fill: "#22c55e" },
    { name: "Expenses", value: expense, fill: "#ef4444" },
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <XAxis dataKey="name" />
        <YAxis
          tickFormatter={(v) =>
            new Intl.NumberFormat("en-US", {
              style: "currency",
              currency: "USD",
              notation: "compact",
            }).format(Number(v))
          }
        />
        <Tooltip formatter={(value) => formatCurrency(Number(value))} />
        <Legend />
        <Bar dataKey="value" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
