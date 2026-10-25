export interface Account {
  id: string
  name: string
  type: "CHECKING" | "SAVINGS" | "CREDIT_CARD" | "INVESTMENT"
  balance: number
  currency: string
  color: string | null
  include_in_dashboard: boolean
  is_active: boolean
  created_at: string
}

export interface Category {
  id: string
  name: string
  type: "INCOME" | "EXPENSE"
  icon: string | null
  color: string | null
  is_system: boolean
  is_active: boolean
  created_at: string
  spending: number
}

export interface Transaction {
  id: string
  account_id: string
  category_id: string | null
  subcategory_id: string | null
  description: string
  original_description: string | null
  amount: number
  type: "INCOME" | "EXPENSE" | "TRANSFER"
  status: string
  transaction_date: string
  due_date: string | null
  payment_date: string | null
  is_recurring: boolean
  fingerprint: string | null
  import_id: string | null
  notes: string | null
  created_at: string
  account_name: string | null
  category_name: string | null
}

export interface Investment {
  id: string
  name: string
  description: string | null
  current_value: number
  invested_value: number
  type: "CDI" | "CDI_PLUS" | "CRYPTO"
  is_active: boolean
}

export interface Goal {
  id: string
  category_id: string | null
  name: string
  target_amount: number
  current_amount: number
  month: string | null
  year: number
  type: "MONTHLY" | "YEARLY" | "CUSTOM"
  deadline: string | null
  is_active: boolean
  created_at: string
}

export interface DashboardSummary {
  total_balance: number
  monthly_income: number
  monthly_expense: number
  balance_diff: number
  investment_balance: number
  recent_transactions: Transaction[]
  expenses_by_category: { name: string; total: string }[]
}

export interface MonthlyHistoryPoint {
  month: number
  year: number
  income: number
  expense: number
  balance: number
}

export interface InvestmentHistory {
  id: string
  investment_id: string
  value: number
  date: string
}

export interface InvestmentFlow {
  month: number
  year: number
  applied: number
  redeemed: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
}
