import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import { useBudgets, useCategories, usePersons } from '../api/hooks';
import api from '../api/client';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
}

function barColor(pct: number) {
  if (pct > 100) return 'bg-red-500';
  if (pct >= 80) return 'bg-yellow-500';
  if (pct >= 50) return 'bg-blue-500';
  return 'bg-green-500';
}

export default function Budget() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(getCurrentMonth());
  const [person, setPerson] = useState('');
  const [newCategoryId, setNewCategoryId] = useState('');
  const [newAmount, setNewAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { data: persons = [] } = usePersons();
  const { data: categories = [] } = useCategories();
  const { data: budgets = [], isLoading } = useBudgets({
    month,
    person: person || undefined,
  });

  async function handleAdd() {
    if (!newCategoryId || !newAmount) return;
    setSubmitting(true);
    try {
      await api.post('/api/budgets', {
        category_id: Number(newCategoryId),
        month,
        limit_amount: parseFloat(newAmount),
        person: person || null,
      });
      await queryClient.invalidateQueries({ queryKey: ['budgets'] });
      setNewCategoryId('');
      setNewAmount('');
    } catch {
      alert('Erro ao adicionar orçamento');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Remover este orçamento?')) return;
    try {
      await api.delete(`/api/budgets/${id}`);
      await queryClient.invalidateQueries({ queryKey: ['budgets'] });
    } catch {
      alert('Erro ao remover');
    }
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Mês</label>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
          <select
            value={person}
            onChange={(e) => setPerson(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todas</option>
            {persons.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Add form */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-3">Novo Orçamento</h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs text-gray-400 mb-1">Categoria</label>
            <select
              value={newCategoryId}
              onChange={(e) => setNewCategoryId(e.target.value)}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="">Selecione</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="w-40">
            <label className="block text-xs text-gray-400 mb-1">Limite (R$)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={newAmount}
              onChange={(e) => setNewAmount(e.target.value)}
              placeholder="0,00"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <button
            onClick={handleAdd}
            disabled={submitting || !newCategoryId || !newAmount}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 flex items-center gap-1 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> Adicionar
          </button>
        </div>
      </div>

      {/* Budget list */}
      <div className="space-y-3">
        {isLoading ? (
          <p className="text-gray-500 text-center py-6">Carregando...</p>
        ) : budgets.length === 0 ? (
          <p className="text-gray-500 text-center py-6">
            Nenhum orçamento definido para este mês
          </p>
        ) : (
          budgets.map((b) => {
            const pct = Math.min(b.percentage, 150);
            return (
              <div
                key={b.id}
                className="bg-[#1a1a2e] rounded-xl p-4 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-gray-200 font-medium">
                      {b.category_name}
                    </span>
                    {b.person && (
                      <span className="text-gray-500 text-xs ml-2">
                        ({b.person})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-400">
                      {fmt.format(Math.abs(b.spent))} / {fmt.format(b.limit_amount)}
                    </span>
                    <button
                      onClick={() => handleDelete(b.id)}
                      className="bg-red-600/20 text-red-400 hover:bg-red-600/30 p-1.5 rounded-lg"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="w-full bg-[#0f0f1a] rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(b.percentage)}`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
                <div className="text-right text-xs">
                  <span
                    className={
                      b.percentage > 100
                        ? 'text-red-400'
                        : b.percentage >= 80
                          ? 'text-yellow-400'
                          : 'text-gray-400'
                    }
                  >
                    {b.percentage.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
