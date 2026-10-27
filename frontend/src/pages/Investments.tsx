import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import { useInvestments, usePersons } from '../api/hooks';
import api from '../api/client';
import type { Investment } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

const TYPES = [
  { value: 'renda_fixa', label: 'Renda Fixa' },
  { value: 'caixinha', label: 'Caixinha' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'poupanca', label: 'Poupança' },
  { value: 'outro', label: 'Outro' },
];

function getCurrentDate() {
  return new Date().toISOString().slice(0, 10);
}

export default function Investments() {
  const queryClient = useQueryClient();
  const [filterPerson, setFilterPerson] = useState('');

  const { data: persons = [] } = usePersons();
  const { data: investments = [], isLoading } = useInvestments({
    person: filterPerson || undefined,
  });

  const [form, setForm] = useState({
    name: '',
    type: 'renda_fixa',
    balance: '',
    date: getCurrentDate(),
    person: '',
    institution: '',
  });
  const [submitting, setSubmitting] = useState(false);

  async function handleAdd() {
    if (!form.name || !form.balance) return;
    setSubmitting(true);
    try {
      await api.post('/api/investments', {
        name: form.name,
        type: form.type,
        balance: parseFloat(form.balance),
        date: form.date,
        person: form.person || null,
        institution: form.institution || null,
      });
      await queryClient.invalidateQueries({ queryKey: ['investments'] });
      setForm({
        name: '',
        type: 'renda_fixa',
        balance: '',
        date: getCurrentDate(),
        person: '',
        institution: '',
      });
    } catch {
      alert('Erro ao adicionar investimento');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Remover este registro?')) return;
    try {
      await api.delete(`/api/investments/${id}`);
      await queryClient.invalidateQueries({ queryKey: ['investments'] });
    } catch {
      alert('Erro ao remover');
    }
  }

  // Group investments by person
  const byPerson = investments.reduce<Record<string, Investment[]>>((acc, inv) => {
    const key = inv.person || 'Sem pessoa';
    if (!acc[key]) acc[key] = [];
    acc[key].push(inv);
    return acc;
  }, {});

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Add form */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-3">Novo Investimento</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Nome</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: CDB Nubank"
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
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Saldo (R$)</label>
            <input
              type="number"
              step="0.01"
              value={form.balance}
              onChange={(e) => setForm({ ...form, balance: e.target.value })}
              placeholder="0,00"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Data</label>
            <input
              type="date"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
            <input
              type="text"
              value={form.person}
              onChange={(e) => setForm({ ...form, person: e.target.value })}
              placeholder="Nome"
              list="inv-persons"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
            <datalist id="inv-persons">
              {persons.map((p) => (
                <option key={p} value={p} />
              ))}
            </datalist>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Instituição</label>
            <input
              type="text"
              value={form.institution}
              onChange={(e) => setForm({ ...form, institution: e.target.value })}
              placeholder="Ex: Nubank"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
        </div>
        <div className="mt-3">
          <button
            onClick={handleAdd}
            disabled={submitting || !form.name || !form.balance}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 flex items-center gap-1 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> Adicionar
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Filtrar Pessoa</label>
          <select
            value={filterPerson}
            onChange={(e) => setFilterPerson(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todas</option>
            {persons.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Investments grouped by person */}
      {isLoading ? (
        <p className="text-gray-500 text-center py-6">Carregando...</p>
      ) : investments.length === 0 ? (
        <p className="text-gray-500 text-center py-6">Nenhum investimento cadastrado</p>
      ) : (
        Object.entries(byPerson).map(([personName, items]) => {
          const total = items.reduce((s, inv) => s + inv.balance, 0);
          return (
            <div key={personName} className="bg-[#1a1a2e] rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-gray-200 font-semibold">{personName}</h3>
                <span className="text-indigo-400 font-bold">
                  Total: {fmt.format(total)}
                </span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                    <th className="py-2 px-2">Nome</th>
                    <th className="py-2 px-2">Tipo</th>
                    <th className="py-2 px-2">Instituição</th>
                    <th className="py-2 px-2">Data</th>
                    <th className="py-2 px-2 text-right">Saldo</th>
                    <th className="py-2 px-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((inv) => (
                    <tr
                      key={inv.id}
                      className="border-b border-[#2a2a4a] hover:bg-[#1e2a4a]"
                    >
                      <td className="py-2 px-2 text-gray-200">{inv.name}</td>
                      <td className="py-2 px-2 text-gray-400 capitalize">
                        {TYPES.find((t) => t.value === inv.type)?.label ?? inv.type}
                      </td>
                      <td className="py-2 px-2 text-gray-400">
                        {inv.institution ?? '-'}
                      </td>
                      <td className="py-2 px-2 text-gray-400">{inv.date}</td>
                      <td className="py-2 px-2 text-right text-green-400 font-medium">
                        {fmt.format(inv.balance)}
                      </td>
                      <td className="py-2 px-2">
                        <button
                          onClick={() => handleDelete(inv.id)}
                          className="bg-red-600/20 text-red-400 hover:bg-red-600/30 p-1.5 rounded-lg"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })
      )}
    </div>
  );
}
