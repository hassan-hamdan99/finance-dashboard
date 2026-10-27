import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Sprout } from 'lucide-react';
import { usePlanning, usePersons, useCategories } from '../api/hooks';
import api from '../api/client';
import type { PlanningTarget } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
}

export default function Planning() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(getCurrentMonth());
  const [person, setPerson] = useState('');

  const { data: persons = [] } = usePersons();
  const { data: categories = [] } = useCategories();
  const { data, isLoading } = usePlanning({
    month,
    person: person || undefined,
  });

  const targets = (data as PlanningTarget[] | undefined) ?? [];

  const [form, setForm] = useState({
    name: '',
    category_id: '',
    target_amount: '',
    type: 'expense',
    person: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  async function handleSeed() {
    setSeeding(true);
    try {
      await api.post('/api/planning/seed', { month });
      await queryClient.invalidateQueries({ queryKey: ['planning'] });
    } catch {
      alert('Erro ao semear metas');
    } finally {
      setSeeding(false);
    }
  }

  async function handleAdd() {
    if (!form.name || !form.target_amount) return;
    setSubmitting(true);
    try {
      await api.post('/api/planning', {
        name: form.name,
        category_id: form.category_id ? Number(form.category_id) : null,
        target_amount: parseFloat(form.target_amount),
        type: form.type,
        person: form.person || null,
        month,
      });
      await queryClient.invalidateQueries({ queryKey: ['planning'] });
      setForm({ name: '', category_id: '', target_amount: '', type: 'expense', person: '' });
    } catch {
      alert('Erro ao criar meta');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Remover esta meta?')) return;
    try {
      await api.delete(`/api/planning/${id}`);
      await queryClient.invalidateQueries({ queryKey: ['planning'] });
    } catch {
      alert('Erro ao remover');
    }
  }

  function getProgressColor(target: PlanningTarget): string {
    if (target.type === 'income' || target.type === 'savings') {
      return target.percentage >= 100 ? 'bg-green-500' : target.percentage >= 80 ? 'bg-yellow-500' : 'bg-red-500';
    }
    // expense: under budget is good
    if (target.percentage <= 80) return 'bg-green-500';
    if (target.percentage <= 100) return 'bg-yellow-500';
    return 'bg-red-500';
  }

  function getProgressTextColor(target: PlanningTarget): string {
    if (target.type === 'income' || target.type === 'savings') {
      return target.percentage >= 100 ? 'text-green-400' : target.percentage >= 80 ? 'text-yellow-400' : 'text-red-400';
    }
    if (target.percentage <= 80) return 'text-green-400';
    if (target.percentage <= 100) return 'text-yellow-400';
    return 'text-red-400';
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header with month selector */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Mes</label>
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
        {targets.length === 0 && (
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 flex items-center gap-2 disabled:opacity-50"
          >
            <Sprout className="w-4 h-4" />
            {seeding ? 'Semeando...' : 'Semear metas padrao'}
          </button>
        )}
      </div>

      {/* Add target form */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-3">Nova Meta</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Nome</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: Limite Mercado"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Categoria</label>
            <select
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="">Nenhuma</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Valor Meta (R$)</label>
            <input
              type="number"
              step="0.01"
              value={form.target_amount}
              onChange={(e) => setForm({ ...form, target_amount: e.target.value })}
              placeholder="0,00"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tipo</label>
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="expense">Despesa</option>
              <option value="income">Receita</option>
              <option value="savings">Economia</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
            <input
              type="text"
              value={form.person}
              onChange={(e) => setForm({ ...form, person: e.target.value })}
              placeholder="Nome"
              list="plan-persons"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
            <datalist id="plan-persons">
              {persons.map((p) => (
                <option key={p} value={p} />
              ))}
            </datalist>
          </div>
        </div>
        <div className="mt-3">
          <button
            onClick={handleAdd}
            disabled={submitting || !form.name || !form.target_amount}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 flex items-center gap-1 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> Adicionar
          </button>
        </div>
      </div>

      {/* Target cards */}
      {isLoading ? (
        <div className="text-gray-400 text-center py-10">Carregando...</div>
      ) : targets.length === 0 ? (
        <div className="text-gray-500 text-center py-10">
          Nenhuma meta para este mes
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {targets.map((t) => {
            const barWidth = Math.min(t.percentage, 100);
            return (
              <div
                key={t.id}
                className="bg-[#1a1a2e] rounded-xl p-5 space-y-3 border border-[#2a2a4a]"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-gray-200 font-medium">{t.name}</h4>
                    {t.category_name && (
                      <span className="text-xs text-gray-400">{t.category_name}</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(t.id)}
                    className="bg-red-600/20 text-red-400 hover:bg-red-600/30 p-1.5 rounded-lg"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-[#16213e] rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getProgressColor(t)}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">
                    {fmt.format(Math.abs(t.actual_amount))} / {fmt.format(t.target_amount)}
                  </span>
                  <span className={`font-bold ${getProgressTextColor(t)}`}>
                    {t.percentage.toFixed(0)}%
                  </span>
                </div>

                {t.person && (
                  <span className="inline-block text-xs bg-[#16213e] text-gray-400 px-2 py-0.5 rounded">
                    {t.person}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
