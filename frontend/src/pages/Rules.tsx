import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import { useRules, useCategories } from '../api/hooks';
import api from '../api/client';

export default function Rules() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useRules();
  const { data: categories = [] } = useCategories();

  const [keyword, setKeyword] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [priority, setPriority] = useState('0');
  const [submitting, setSubmitting] = useState(false);

  // The API may return { rules, defaults } or just an array
  const rules = Array.isArray(data) ? data : ((data as any)?.rules ?? []);
  const defaults: Record<string, string[]> = Array.isArray(data)
    ? {}
    : ((data as any)?.defaults ?? {});

  async function handleAdd() {
    if (!keyword.trim() || !categoryId) return;
    setSubmitting(true);
    try {
      await api.post('/api/rules', {
        keyword: keyword.trim().toLowerCase(),
        category_id: Number(categoryId),
        priority: Number(priority),
      });
      await queryClient.invalidateQueries({ queryKey: ['rules'] });
      setKeyword('');
      setCategoryId('');
      setPriority('0');
    } catch {
      alert('Erro ao adicionar regra');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Remover esta regra?')) return;
    try {
      await api.delete(`/api/rules/${id}`);
      await queryClient.invalidateQueries({ queryKey: ['rules'] });
    } catch {
      alert('Erro ao remover');
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Add form */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-3">Nova Regra</h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs text-gray-400 mb-1">Keyword</label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="ex: uber, netflix"
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs text-gray-400 mb-1">Categoria</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            >
              <option value="">Selecione</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="w-28">
            <label className="block text-xs text-gray-400 mb-1">Prioridade</label>
            <input
              type="number"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-[#16213e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
            />
          </div>
          <button
            onClick={handleAdd}
            disabled={submitting || !keyword.trim() || !categoryId}
            className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg px-4 py-2 flex items-center gap-1 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> Adicionar
          </button>
        </div>
      </div>

      {/* Rules table */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-4">Regras do Banco</h3>
        {isLoading ? (
          <p className="text-gray-500 text-center py-6">Carregando...</p>
        ) : rules.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Nenhuma regra personalizada</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                <th className="py-2 px-2">Keyword</th>
                <th className="py-2 px-2">Categoria</th>
                <th className="py-2 px-2">Prioridade</th>
                <th className="py-2 px-2">Origem</th>
                <th className="py-2 px-2 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r: any) => (
                <tr
                  key={r.id}
                  className="border-b border-[#2a2a4a] hover:bg-[#1e2a4a]"
                >
                  <td className="py-2 px-2 text-gray-200 font-mono">{r.keyword}</td>
                  <td className="py-2 px-2 text-gray-300">{r.category_name}</td>
                  <td className="py-2 px-2 text-gray-400">{r.priority}</td>
                  <td className="py-2 px-2 text-gray-400 text-xs">{r.source}</td>
                  <td className="py-2 px-2">
                    <button
                      onClick={() => handleDelete(r.id)}
                      className="bg-red-600/20 text-red-400 hover:bg-red-600/30 p-1.5 rounded-lg"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Default keywords */}
      {Object.keys(defaults).length > 0 && (
        <div className="bg-[#1a1a2e] rounded-xl p-5">
          <h3 className="text-gray-200 font-semibold mb-4">
            Keywords Padrão por Categoria
          </h3>
          <div className="space-y-3">
            {Object.entries(defaults).map(([category, keywords]) => (
              <div key={category}>
                <p className="text-gray-300 text-sm font-medium mb-1">
                  {category}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {keywords.map((kw) => (
                    <span
                      key={kw}
                      className="bg-[#16213e] border border-[#2a2a4a] text-gray-400 text-xs px-2 py-0.5 rounded-full"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
