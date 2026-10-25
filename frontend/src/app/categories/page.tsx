"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"
import type { Category } from "@/types"
import { CATEGORY_TYPES, COLORS } from "@/lib/constants"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"

export default function CategoriesPage() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: "", type: "EXPENSE", color: "#ef4444" })
  const now = new Date()
  const month = now.getMonth() + 1
  const year = now.getFullYear()

  const { data: categories, isLoading } = useQuery<Category[]>({
    queryKey: ["categories", month, year],
    queryFn: () => api.get(`/api/v1/categories?month=${month}&year=${year}`),
  })

  const createMutation = useMutation({
    mutationFn: (body: unknown) => api.post("/api/v1/categories", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Category created")
      setOpen(false)
      setForm({ name: "", type: "EXPENSE", color: "#ef4444" })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/categories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Category deleted")
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate(form)
  }

  const incomeCategories = categories?.filter((c) => c.type === "INCOME") ?? []
  const expenseCategories = categories?.filter((c) => c.type === "EXPENSE") ?? []

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Categories" />
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Categories" description="Organize your transactions">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button><Plus className="h-4 w-4 mr-2" /> New Category</Button>} />
          <DialogContent>
            <DialogHeader><DialogTitle>New Category</DialogTitle></DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">Type</label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v || "EXPENSE" })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CATEGORY_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Color</label>
                <div className="flex gap-2 flex-wrap">
                  {COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setForm({ ...form, color })}
                      className={`w-8 h-8 rounded-full border-2 ${form.color === color ? "border-foreground" : "border-transparent"}`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Saving..." : "Save"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold mb-3 text-green-600">Income</h2>
          {incomeCategories.length === 0 ? (
            <EmptyState message="No income categories" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {incomeCategories.map((cat) => (
                <Card key={cat.id}>
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: cat.color ?? "#ccc" }} />
                      <div>
                        <span className="font-medium">{cat.name}</span>
                        {cat.is_system && <Badge variant="secondary">Default</Badge>}
                      </div>
                    </div>
                    {!cat.is_system && (
                      <Button variant="ghost" size="icon" onClick={() => deleteMutation.mutate(cat.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-3 text-red-600">Expenses</h2>
          {expenseCategories.length === 0 ? (
            <EmptyState message="No expense categories" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {expenseCategories.map((cat) => (
                <Card key={cat.id}>
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: cat.color ?? "#ccc" }} />
                      <div>
                        <span className="font-medium">{cat.name}</span>
                        {cat.is_system && <Badge variant="secondary">Default</Badge>}
                        {cat.spending > 0 && (
                          <div className="text-xs text-muted-foreground mt-0.5">
                            ${cat.spending.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        )}
                      </div>
                    </div>
                    {!cat.is_system && (
                      <Button variant="ghost" size="icon" onClick={() => deleteMutation.mutate(cat.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
