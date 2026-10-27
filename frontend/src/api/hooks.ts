import { useQuery } from '@tanstack/react-query';
import api from './client';
import type {
  Category,
  DashboardData,
  TransactionsResponse,
  Insight,
  Transaction,
  Budget,
  CategoryRule,
  Investment,
} from '../types';

export function useCategories() {
  return useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => api.get('/api/categories').then((r) => r.data),
  });
}

export function useDashboard(params: {
  months?: number;
  person?: string;
  month?: string;
  categories?: string;
}) {
  return useQuery<DashboardData>({
    queryKey: ['dashboard', params],
    queryFn: () =>
      api.get('/api/analytics/dashboard', { params }).then((r) => r.data),
  });
}

export function useTransactions(params: {
  page?: number;
  per_page?: number;
  person?: string;
  category_id?: number;
  month?: string;
  search?: string;
  type?: string;
  subdivision?: string;
}) {
  return useQuery<TransactionsResponse>({
    queryKey: ['transactions', params],
    queryFn: () =>
      api.get('/api/transactions', { params }).then((r) => r.data),
  });
}

export function usePersons() {
  return useQuery<string[]>({
    queryKey: ['persons'],
    queryFn: () =>
      api.get('/api/transactions/persons').then((r) => r.data),
  });
}

export function useInsights(params: { person?: string; month?: string }) {
  return useQuery<Insight[]>({
    queryKey: ['insights', params],
    queryFn: () =>
      api.get('/api/analytics/insights', { params }).then((r) => r.data),
  });
}

export function useTopExpenses(params: {
  person?: string;
  month?: string;
  top_n?: number;
}) {
  return useQuery<Transaction[]>({
    queryKey: ['top-expenses', params],
    queryFn: () =>
      api.get('/api/analytics/top-expenses', { params }).then((r) => r.data),
  });
}

export function useTrends(params: { person?: string; month?: string }) {
  return useQuery({
    queryKey: ['trends', params],
    queryFn: () =>
      api.get('/api/analytics/trends', { params }).then((r) => r.data),
  });
}

export function useBudgets(params: { month?: string; person?: string }) {
  return useQuery<Budget[]>({
    queryKey: ['budgets', params],
    queryFn: () =>
      api.get('/api/budgets', { params }).then((r) => r.data),
  });
}

export function useRules() {
  return useQuery<CategoryRule[]>({
    queryKey: ['rules'],
    queryFn: () => api.get('/api/rules').then((r) => r.data),
  });
}

export function useInvestments(params?: { person?: string }) {
  return useQuery<Investment[]>({
    queryKey: ['investments', params],
    queryFn: () =>
      api.get('/api/investments', { params }).then((r) => r.data),
  });
}

export function useRecurring(params: { person?: string; months?: number }) {
  return useQuery({
    queryKey: ['recurring', params],
    queryFn: () => api.get('/api/analytics/recurring', { params }).then(r => r.data),
  });
}

export function usePivot(params: { months?: number; person?: string }) {
  return useQuery({
    queryKey: ['pivot', params],
    queryFn: () => api.get('/api/analytics/pivot', { params }).then(r => r.data),
  });
}

export function usePlanning(params: { month?: string; person?: string }) {
  return useQuery({
    queryKey: ['planning', params],
    queryFn: () => api.get('/api/planning', { params }).then(r => r.data),
  });
}
