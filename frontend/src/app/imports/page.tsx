"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api"
import type { Account } from "@/types"
import { formatDateTime } from "@/lib/constants"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Upload,
  FileText,
  Landmark,
  CreditCard,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Eye,
  FileUp,
} from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"

interface ImportRecord {
  id: string
  account_id: string
  filename: string
  file_type: string
  status: string
  total_rows: number
  processed_rows: number
  error_rows: number
  summary: string | null
  created_at: string
  completed_at: string | null
  transaction_count: number
}

interface ImportDetail extends ImportRecord {
  error_log: Record<string, unknown> | null
  original_filename: string
}

interface PdfPreviewItem {
  transaction_date: string
  description: string
  amount: string
  installment_number: number | null
  total_installments: number | null
  is_fee: boolean
  is_payment: boolean
  is_reversal: boolean
  category_hint: string | null
}

interface PdfPreview {
  bank: string
  card_last_four: string | null
  closing_date: string | null
  due_date: string | null
  total_amount: string | null
  items_count: number
  items_sum: string
  items: PdfPreviewItem[]
  warnings: string[]
  is_valid: boolean
}

interface PdfPreviewResponse {
  file_path: string
  preview: PdfPreview
}

interface PdfConfirmResponse {
  import_id: string
  status: string
  summary: {
    saved: number
    duplicates: number
    errors: string[]
  }
}

const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  uploaded: { label: "Uploaded", variant: "outline" },
  processing: { label: "Processing", variant: "secondary" },
  completed: { label: "Completed", variant: "default" },
  error: { label: "Error", variant: "destructive" },
}

export default function ImportsPage() {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState("bank")
  const [selectedAccount, setSelectedAccount] = useState("")
  const [selectedCard, setSelectedCard] = useState("")
  const [selectedPdfCard, setSelectedPdfCard] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [pdfPassword, setPdfPassword] = useState("")
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedImport, setSelectedImport] = useState<ImportDetail | null>(null)
  const [pdfPreview, setPdfPreview] = useState<PdfPreviewResponse | null>(null)
  const [pdfPreviewOpen, setPdfPreviewOpen] = useState(false)
  const [pdfConfirming, setPdfConfirming] = useState(false)

  const { data: importsData, isLoading } = useQuery<{ data: ImportRecord[]; total: number }>({
    queryKey: ["imports"],
    queryFn: () => api.get("/api/v1/imports"),
  })
  
  const { data: accounts } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => api.get("/api/v1/accounts"),
  })
  
  const bankAccounts = accounts?.filter((a) => a.type === "CHECKING" || a.type === "SAVINGS") ?? []
  const creditCards = accounts?.filter((a) => a.type === "CREDIT_CARD") ?? []
  

  const bankUploadMutation = useMutation({
    mutationFn: (formData: FormData) => api.upload("/api/v1/imports/bank-statement", formData),
    onSuccess: () => {
      invalidateAll()
      toast.success("Statement imported successfully")
      setFile(null)
    },
    onError: (err: Error) => toast.error(err.message || "Error importing"),
  })

  const cardUploadMutation = useMutation({
    mutationFn: (formData: FormData) => api.upload("/api/v1/imports/credit-card", formData),
    onSuccess: () => {
      invalidateAll()
      toast.success("Credit card bill imported successfully")
      setFile(null)
    },
    onError: (err: Error) => toast.error(err.message || "Error importing"),
  })

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ["imports"] })
    queryClient.invalidateQueries({ queryKey: ["transactions"] })
    queryClient.invalidateQueries({ queryKey: ["dashboard"] })
  }

  function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!file) { toast.error("Please select a file"); return }

    if (tab === "bank") {
      if (!selectedAccount) { toast.error("Please select an account"); return }
      const fd = new FormData()
      fd.append("file", file)
      fd.append("account_id", selectedAccount)
      bankUploadMutation.mutate(fd)
    } else {
      if (!selectedCard) { toast.error("Please select a credit card"); return }
      const fd = new FormData()
      fd.append("file", file)
      fd.append("account_id", selectedCard)
      cardUploadMutation.mutate(fd)
    }
  }

  async function handlePdfPreview() {
    if (!pdfFile) { toast.error("Please select a PDF file"); return }
    if (!selectedPdfCard) { toast.error("Please select a credit card"); return }

    const fd = new FormData()
    fd.append("file", pdfFile)
    if (pdfPassword) fd.append("password", pdfPassword)

    try {
      const result = await api.upload<PdfPreviewResponse>("/api/v1/imports/credit-card/pdf/preview", fd)
      setPdfPreview(result)
      setPdfPreviewOpen(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error processing PDF"
      toast.error(msg)
    }
  }

  async function handlePdfConfirm() {
    if (!pdfPreview) return
    setPdfConfirming(true)

    const fd = new FormData()
    fd.append("file_path", pdfPreview.file_path)
    fd.append("account_id", selectedPdfCard)
    if (pdfPassword) fd.append("password", pdfPassword)

    try {
      const result = await api.upload<PdfConfirmResponse>("/api/v1/imports/credit-card/pdf/confirm", fd)
      invalidateAll()
      toast.success(`${result.summary.saved} transactions imported!`)
      setPdfPreviewOpen(false)
      setPdfPreview(null)
      setPdfFile(null)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error confirming import"
      toast.error(msg)
    } finally {
      setPdfConfirming(false)
    }
  }

  async function handleViewDetail(importId: string) {
    try {
      const detail = await api.get<ImportDetail>(`/api/v1/imports/${importId}`)
      setSelectedImport(detail)
      setDetailOpen(true)
    } catch {
      toast.error("Error loading details")
    }
  }

  const isPending = bankUploadMutation.isPending || cardUploadMutation.isPending
  const imports = importsData?.data ?? []

  function formatLabel(item: PdfPreviewItem) {
    if (item.is_reversal) return "Reversal"
    if (item.is_fee) return "Fee"
    if (item.is_payment) return "Payment"
    return "Purchase"
  }

  function formatInstallment(item: PdfPreviewItem) {
    if (item.installment_number && item.total_installments) {
      return `${item.installment_number}/${item.total_installments}`
    }
    return "-"
  }

  return (
    <div>
      <PageHeader title="Import" description="Import bank statements and credit card bills" />

      <Card className="mb-8">
        <CardContent className="pt-6">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="mb-4">
              <TabsTrigger value="bank"><Landmark className="h-4 w-4 mr-2" /> Bank Statement</TabsTrigger>
              {/* <TabsTrigger value="card"><FileText className="h-4 w-4 mr-2" /> Credit Card CSV</TabsTrigger>
              <TabsTrigger value="pdf"><FileUp className="h-4 w-4 mr-2" /> Credit Card PDF</TabsTrigger> */}
            </TabsList>

            <TabsContent value="bank">
              <form onSubmit={handleUpload} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Account</label>
                    <Select value={selectedAccount} onValueChange={(v) => setSelectedAccount(v || "")}>
                      <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                      <SelectContent>
                        {bankAccounts.map((a) => {

                          return (
                            <SelectItem key={a.id} value={a.name}>
                              {a.name}
                            </SelectItem>
                          );
                        })}
                        {bankAccounts.length === 0 && (
                          <SelectItem value="_none" disabled>No checking accounts</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium mb-1 block">File (CSV or XLSX)</label>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:opacity-90"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={!file || isPending || !selectedAccount}>
                  {isPending ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Importing...</>
                  ) : (
                    <><Upload className="h-4 w-4 mr-2" /> Import</>
                  )}
                </Button>
              </form>
            </TabsContent>


            {/* Credit card imports are currently down */}
            {/* <TabsContent value="card">
              <form onSubmit={handleUpload} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Card</label>
                    <Select value={selectedCard} onValueChange={(v) => setSelectedCard(v || "")}>
                      <SelectTrigger><SelectValue placeholder="Select card" /></SelectTrigger>
                      <SelectContent>
                        {creditCards.map((a) => (
                          <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                        ))}
                        {creditCards.length === 0 && (
                          <SelectItem value="_none" disabled>No credit cards</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium mb-1 block">File (CSV)</label>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:opacity-90"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={!file || isPending || !selectedCard}>
                  {isPending ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Importing...</>
                  ) : (
                    <><Upload className="h-4 w-4 mr-2" /> Import</>
                  )}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="pdf">
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Card</label>
                    <Select value={selectedPdfCard} onValueChange={(v) => setSelectedPdfCard(v || "")}>
                      <SelectTrigger><SelectValue placeholder="Select card" /></SelectTrigger>
                      <SelectContent>
                        {creditCards.map((a) => (
                          <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                        ))}
                        {creditCards.length === 0 && (
                          <SelectItem value="_none" disabled>No credit cards</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm font-medium mb-1 block">PDF Bill</label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
                      className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:opacity-90"
                    />
                    <div className="mt-2">
                      <input
                        type="password"
                        placeholder="PDF password (if protected)"
                        value={pdfPassword}
                        onChange={(e) => setPdfPassword(e.target.value)}
                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      />
                    </div>
                  </div>
                </div>
                <Button
                  type="button"
                  onClick={handlePdfPreview}
                  disabled={!pdfFile || !selectedPdfCard}
                >
                  <Upload className="h-4 w-4 mr-2" /> Preview Bill
                </Button>
              </div>
            </TabsContent> */}
          </Tabs>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Import History</h2>
        {imports.length > 0 && (
          <Badge variant="outline">{importsData?.total ?? 0} record(s)</Badge>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : imports.length === 0 ? (
        <EmptyState message="No imports found" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Transactions</TableHead>
              <TableHead>Summary</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {imports.map((imp) => {
              const status = statusConfig[imp.status] || statusConfig.error
              return (
                <TableRow key={imp.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="truncate max-w-[200px]">{imp.filename}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{imp.file_type.toUpperCase()}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium">{imp.transaction_count}</span>
                    {imp.status === "completed" && imp.transaction_count > 0 && (
                      <CheckCircle2 className="h-4 w-4 text-green-500 inline ml-1" />
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                    {imp.summary || "-"}
                  </TableCell>
                  <TableCell className="text-muted-foreground whitespace-nowrap">
                    {formatDateTime(imp.created_at)}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon-sm" onClick={() => handleViewDetail(imp.id)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Import Details</DialogTitle>
          </DialogHeader>
          {selectedImport ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">File</p>
                  <p className="font-medium">{selectedImport.original_filename || selectedImport.filename}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Type</p>
                  <p className="font-medium">{selectedImport.file_type.toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <Badge variant={statusConfig[selectedImport.status]?.variant || "outline"}>
                    {statusConfig[selectedImport.status]?.label || selectedImport.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground">Transactions</p>
                  <p className="font-medium">{selectedImport.transaction_count}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Processed Rows</p>
                  <p className="font-medium">{selectedImport.processed_rows}/{selectedImport.total_rows}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Errors</p>
                  <p className="font-medium">{selectedImport.error_rows}</p>
                </div>
              </div>
              {selectedImport.summary && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Summary</p>
                  <pre className="text-sm bg-muted rounded-lg p-3 whitespace-pre-wrap font-mono">
                    {selectedImport.summary}
                  </pre>
                </div>
              )}
              {selectedImport.error_log && (
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Error Log</p>
                  <pre className="text-sm bg-destructive/10 rounded-lg p-3 whitespace-pre-wrap font-mono text-destructive">
                    {JSON.stringify(selectedImport.error_log, null, 2)}
                  </pre>
                </div>
              )}
              <div className="text-xs text-muted-foreground">
                Created at: {formatDateTime(selectedImport.created_at)}
                {selectedImport.completed_at && <> | Completed at: {formatDateTime(selectedImport.completed_at)}</>}
              </div>
            </div>
          ) : (
            <Skeleton className="h-40" />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={pdfPreviewOpen} onOpenChange={(open) => { if (!pdfConfirming) { setPdfPreviewOpen(open); if (!open) setPdfPreview(null) } }}>
        <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Bill Preview</DialogTitle>
          </DialogHeader>

          {pdfPreview && (
            <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
              <div className="flex flex-wrap gap-4 text-sm bg-muted/30 rounded-lg p-4">
                <div>
                  <p className="text-muted-foreground text-xs">Bank</p>
                  <p className="font-medium">{pdfPreview.preview.bank}</p>
                </div>
                {pdfPreview.preview.card_last_four && (
                  <div>
                    <p className="text-muted-foreground text-xs">Card Ending In</p>
                    <p className="font-medium">{pdfPreview.preview.card_last_four}</p>
                  </div>
                )}
                {pdfPreview.preview.closing_date && (
                  <div>
                    <p className="text-muted-foreground text-xs">Closing Date</p>
                    <p className="font-medium">{pdfPreview.preview.closing_date}</p>
                  </div>
                )}
                {pdfPreview.preview.due_date && (
                  <div>
                    <p className="text-muted-foreground text-xs">Due Date</p>
                    <p className="font-medium">{pdfPreview.preview.due_date}</p>
                  </div>
                )}
                {pdfPreview.preview.total_amount && (
                  <div>
                    <p className="text-muted-foreground text-xs">Total</p>
                    <p className="font-medium">${pdfPreview.preview.total_amount}</p>
                  </div>
                )}
                <div>
                  <p className="text-muted-foreground text-xs">Items</p>
                  <p className="font-medium">{pdfPreview.preview.items_count}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Sum</p>
                  <p className="font-medium">${pdfPreview.preview.items_sum}</p>
                </div>
              </div>

              {pdfPreview.preview.warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                  {pdfPreview.preview.warnings.map((w, i) => (
                    <p key={i} className="flex items-start gap-2">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}

              <div className="max-h-64 overflow-y-auto border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Installment</TableHead>
                      <TableHead>Type</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pdfPreview.preview.items.map((item, i) => (
                      <TableRow key={i}>
                        <TableCell className="whitespace-nowrap">{item.transaction_date}</TableCell>
                        <TableCell className="max-w-[240px] truncate">{item.description}</TableCell>
                        <TableCell className="font-mono text-right">${item.amount}</TableCell>
                        <TableCell>{formatInstallment(item)}</TableCell>
                        <TableCell>
                          <Badge variant={item.is_reversal ? "secondary" : item.is_fee ? "outline" : "default"}>
                            {formatLabel(item)}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          <DialogFooter className="mt-4 pt-4 border-t gap-2">
            <Button variant="outline" onClick={() => { setPdfPreviewOpen(false); setPdfPreview(null) }} disabled={pdfConfirming}>
              Cancel
            </Button>
            <Button onClick={handlePdfConfirm} disabled={pdfConfirming}>
              {pdfConfirming ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Importing...</>
              ) : (
                <><CheckCircle2 className="h-4 w-4 mr-2" /> Confirm Import</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
