import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Search, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useTransactions, usePersons, useCategories } from '../api/hooks';
import api from '../api/client';
import type { Transaction } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

export default function Transactions() {
  const [person, setPerson] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [search, setSearch] = useState('');
  const [month, setMonth] = useState('');
  const [type, setType] = useState('');
  const [subdivision, setSubdivision] = useState('');
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Transaction | null>(null);

  const { data: persons = [] } = usePersons();
  const { data: categories = [] } = useCategories();

  const params = {
    page,
    per_page: 25,
    person: person || undefined,
    category_id: categoryId ? Number(categoryId) : undefined,
    search: search || undefined,
    month: month || undefined,
    type: type || undefined,
    subdivision: subdivision || undefined,
  };

  const { data, isLoading } = useTransactions(params);
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  const totalGastos = items
    .filter((t) => t.amount < 0)
    .reduce((s, t) => s + t.amount, 0);
  const totalReceitas = items
    .filter((t) => t.amount > 0)
    .reduce((s, t) => s + t.amount, 0);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
          <select
            value={person}
            onChange={(e) => { setPerson(e.target.value); setPage(1); }}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todas</option>
            {persons.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Categoria</label>
          <select
            value={categoryId}
            onChange={(e) => { setCategoryId(e.target.value); setPage(1); }}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todas</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Busca</label>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Descrição..."
              className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg pl-8 pr-3 py-2 text-gray-200"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Mês</label>
          <input
            type="month"
            value={month}
            onChange={(e) => { setMonth(e.target.value); setPage(1); }}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Tipo</label>
          <select
            value={type}
            onChange={(e) => { setType(e.target.value); setPage(1); }}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todos</option>
            <option value="gastos">Gastos</option>
            <option value="receitas">Receitas</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Subdivisão</label>
          <select
            value={subdivision}
            onChange={(e) => { setSubdivision(e.target.value); setPage(1); }}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todos</option>
            <option value="individual">Individual</option>
            <option value="conjunto">Conjunto</option>
          </select>
        </div>
      </div>

      {/* Summary bar */}
      <div className="flex gap-6 text-sm text-gray-400">
        <span>{total} transações</span>
        <span>
          Gastos:{' '}
          <span className="text-red-400 font-medium">
            {fmt.format(Math.abs(totalGastos))}
          </span>
        </span>
        <span>
          Receitas:{' '}
          <span className="text-green-400 font-medium">
            {fmt.format(totalReceitas)}
          </span>
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
              <th className="py-3 px-2">Data</th>
              <th className="py-3 px-2">Descrição</th>
              <th className="py-3 px-2 text-right">Valor</th>
              <th className="py-3 px-2">Categoria</th>
              <th className="py-3 px-2">Pessoa</th>
              <th className="py-3 px-2">Subdivisão</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center text-gray-500 py-10">
                  Carregando...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center text-gray-500 py-10">
                  Nenhuma transação encontrada
                </td>
              </tr>
            ) : (
              items.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setEditing({ ...t })}
                  className="border-b border-[#2a2a4a] hover:bg-[#1e2a4a] cursor-pointer transition-colors"
                >
                  <td className="py-2 px-2 text-gray-300">{t.date}</td>
                  <td className="py-2 px-2 text-gray-200 max-w-xs truncate">
                    {t.description}
                  </td>
                  <td
                    className={`py-2 px-2 text-right font-medium ${
                      t.amount < 0 ? 'text-red-400' : 'text-green-400'
                    }`}
                  >
                    {fmt.format(t.amount)}
                  </td>
                  <td className="py-2 px-2 text-gray-300">
                    {t.category_name ?? '-'}
                  </td>
                  <td className="py-2 px-2 text-gray-300">{t.person ?? '-'}</td>
                  <td className="py-2 px-2 text-gray-300">
                    {t.subdivision ?? '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-2 rounded-lg bg-[#1a1a2e] border border-[#2a2a4a] text-gray-400 disabled:opacity-30"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-gray-400 text-sm">
            {page} / {pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page === pages}
            className="p-2 rounded-lg bg-[#1a1a2e] border border-[#2a2a4a] text-gray-400 disabled:opacity-30"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Edit Modal */}
      {editing && (
        <EditModal
          transaction={editing}
          categories={categories}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}

function EditModal({
  transaction,
  categories,
  onClose,
}: {
  transaction: Transaction;
  categories: { id: number; name: string }[];
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    category_id: transaction.category_id ?? '',
    subcategory: transaction.subcategory ?? '',
    subdivision: transaction.subdivision ?? '',
    vendor: transaction.vendor ?? '',
    payment_method: transaction.payment_method ?? '',
    is_recurring: transaction.is_recurring,
    notes: transaction.notes ?? '',
  });
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await api.patch(`/api/transactions/${transaction.id}`, {
        ...form,
        category_id: form.category_id === '' ? null : Number(form.category_id),
        subdivision: form.subdivision || null,
        vendor: form.vendor || null,
        payment_method: form.payment_method || null,
        notes: form.notes || null,
        subcategory: form.subcategory || null,
      });
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      onClose();
    } catch {
      alert('Erro ao salvar');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl w-full max-w-lg p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-gray-200 font-semibold text-lg">
            Editar Transação
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-gray-400 text-sm truncate">{transaction.description}</p>
        <p className={`font-medium ${transaction.amount < 0 ? 'text-red-400' : 'text-green-400'}`}>
          {fmt.format(transaction.amount)}
        </p>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Categoria</label>
            <select
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="">Sem categoria</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Subcategoria</label>
            <input
              type="text"
              value={form.subcategory}
              onChange={(e) => setForm({ ...form, subcategory: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Subdivisão</label>
            <select
              value={form.subdivision}
              onChange={(e) => setForm({ ...form, subdivision: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="">-</option>
              <option value="individual">Individual</option>
              <option value="conjunto">Conjunto</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Fornecedor</label>
            <input
              type="text"
              value={form.vendor}
              onChange={(e) => setForm({ ...form, vendor: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pagamento</label>
            <input
              type="text"
              value={form.payment_method}
              onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div className="flex items-end gap-2">
            <label className="flex items-center gap-2 text-gray-300 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_recurring}
                onChange={(e) =>
                  setForm({ ...form, is_recurring: e.target.checked })
                }
                className="accent-indigo-500"
              />
              Recorrente
            </label>
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Notas</label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={2}
            className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-[#2a2a4a] text-gray-400 hover:bg-[#16213e]"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}
