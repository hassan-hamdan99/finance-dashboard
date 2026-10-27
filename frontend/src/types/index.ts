export interface Category {
  id: number;
  name: string;
  color: string;
  type: string;
  icon: string;
}

export interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: number;
  category_id: number | null;
  category_name: string | null;
  category_color: string | null;
  subcategory: string | null;
  person: string | null;
  bank: string | null;
  vendor: string | null;
  payment_method: string | null;
  subdivision: string | null;
  is_recurring: boolean;
  notes: string | null;
}

export interface KPIs {
  total_gastos: number;
  total_receitas: number;
  saldo: number;
  variacao_gastos: number;
  num_transacoes: number;
  media_diaria: number;
  projecao_mensal: number;
}

export interface CategoryBreakdown {
  category: string;
  color: string;
  total: number;
}

export interface MonthSummary {
  month: string;
  gastos: number;
  receitas: number;
  saldo: number;
}

export interface DashboardData {
  ref_month: string;
  kpis: KPIs;
  category_breakdown: CategoryBreakdown[];
  monthly_summary: MonthSummary[];
}

export interface Insight {
  icon: string;
  text: string;
  type: string;
}

export interface Budget {
  id: number;
  category_id: number;
  category_name: string;
  month: string;
  limit_amount: number;
  person: string | null;
  spent: number;
  percentage: number;
}

export interface Investment {
  id: number;
  name: string;
  type: string;
  balance: number;
  date: string;
  person: string | null;
  institution: string | null;
  notes: string | null;
}

export interface CategoryRule {
  id: number;
  keyword: string;
  category_id: number;
  category_name: string;
  priority: number;
  source: string;
}

export interface TransactionPreview {
  date: string;
  description: string;
  amount: number;
  category_name: string | null;
  vendor: string | null;
  payment_method: string | null;
  is_duplicate: boolean;
}

export interface UploadPreview {
  filename: string;
  bank: string;
  new_count: number;
  dup_count: number;
  transactions: TransactionPreview[];
}

export interface TransactionsResponse {
  items: Transaction[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface RecurringTransaction {
  pattern: string;
  category_name: string;
  avg_amount: number;
  frequency: number;
  last_seen: string;
  months_seen: string[];
  is_missing_current: boolean;
  amount_changed: boolean;
}

export interface PivotData {
  months: string[];
  categories: {
    name: string;
    color: string;
    values: Record<string, number>;
    total: number;
  }[];
  month_totals: Record<string, number>;
  grand_total: number;
}

export interface PlanningTarget {
  id: number;
  name: string;
  category_name: string | null;
  target_amount: number;
  actual_amount: number;
  percentage: number;
  type: string;
  person: string | null;
  notes: string | null;
}
