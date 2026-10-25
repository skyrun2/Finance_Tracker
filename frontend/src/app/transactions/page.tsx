"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"
import type { Transaction, PaginatedResponse, Account, Category } from "@/types"
import { formatCurrency, formatDate, TRANSACTION_TYPES } from "@/lib/constants"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Plus, Search, Trash2, Pencil } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"

export default function TransactionsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({
    account_id: "",
    category_id: "",
    description: "",
    amount: "",
    type: "EXPENSE",
    transaction_date: "",
  })

  const { data, isLoading } = useQuery<PaginatedResponse<Transaction>>({
    queryKey: ["transactions", page, search, typeFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), per_page: "50" })
      if (search) params.set("search", search)
      if (typeFilter) params.set("type", typeFilter)
      return api.get(`/api/v1/transactions?${params}`)
    },
  })

  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => api.get("/api/v1/accounts"),
  })

  const { data: categories } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: () => api.get("/api/v1/categories"),
  })

  const createMutation = useMutation({
    mutationFn: (body: unknown) => api.post("/api/v1/transactions", body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Transaction created")
      setOpen(false)
      resetForm()
    },
    onError: () => toast.error("Error creating transaction"),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      toast.success("Transaction deleted")
    },
  })

  function resetForm() {
    setForm({ account_id: "", category_id: "", description: "", amount: "", type: "EXPENSE", transaction_date: "" })
    setEditId(null)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate({
      ...form,
      amount: parseFloat(form.amount.replace(",", ".")),
      category_id: form.category_id || null,
    })
  }

  function handleDelete(id: string) {
    if (confirm("Delete this transaction?")) deleteMutation.mutate(id)
  }

  return (
    <div>
      <PageHeader title="Transactions" description="Complete transaction history">
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button><Plus className="h-4 w-4 mr-2" /> New Transaction</Button>} onClick={resetForm} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editId ? "Edit" : "New"} Transaction</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Description</label>
                <Input
                  required
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Amount</label>
                  <Input
                    required
                    type="number"
                    step="0.01"
                    value={form.amount}
                    onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Type</label>
                  <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v || "EXPENSE" })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TRANSACTION_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Account</label>
                  <Select value={form.account_id} onValueChange={(v) => setForm({ ...form, account_id: v || "" })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts?.map((a) => (
                        <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Category</label>
                  <Select value={form.category_id} onValueChange={(v) => setForm({ ...form, category_id: v || "" })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories?.map((c) => (
                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Date</label>
                <Input
                  required
                  type="date"
                  value={form.transaction_date}
                  onChange={(e) => setForm({ ...form, transaction_date: e.target.value })}
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Saving..." : "Save"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </PageHeader>

      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search transactions..."
            className="pl-10"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v || ""); setPage(1) }}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            {TRANSACTION_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (data?.data ?? []).length === 0 ? (
        <EmptyState message="No transactions found" />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Account</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="w-20"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.data.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{formatDate(t.transaction_date)}</TableCell>
                  <TableCell className="font-medium">{t.description}</TableCell>
                  <TableCell className="text-muted-foreground">{t.account_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{t.category_name || "Uncategorized"}</Badge>
                  </TableCell>
                  <TableCell className={`text-right font-medium ${t.type === "EXPENSE" ? "text-red-600" : "text-green-600"}`}>
                    {t.type === "EXPENSE" ? "-" : "+"}{formatCurrency(t.amount)}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(t.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-muted-foreground">
              Showing page {page} of {Math.ceil((data?.total ?? 0) / 50)}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Previous
              </Button>
              <Button variant="outline" size="sm" disabled={(data?.data ?? []).length < 50} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
