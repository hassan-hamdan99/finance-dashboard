import { useState } from 'react';
import { usePivot, usePersons } from '../api/hooks';
import type { PivotData } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

export default function Pivot() {
  const [person, setPerson] = useState('');
  const [months, setMonths] = useState(6);

  const { data: persons = [] } = usePersons();
  const { data, isLoading } = usePivot({
    person: person || undefined,
    months,
  });

  const pivot = data as PivotData | undefined;
  const monthsList = pivot?.months ?? [];
  const categories = pivot?.categories ?? [];
  const monthTotals = pivot?.month_totals ?? {};
  const grandTotal = pivot?.grand_total ?? 0;

  // Find max value across all cells for opacity scaling
  const maxValue = Math.max(
    1,
    ...categories.flatMap((c) =>
      Object.values(c.values).map((v) => Math.abs(v)),
    ),
  );

  function cellOpacity(value: number): string {
    const ratio = Math.abs(value) / maxValue;
    if (ratio < 0.1) return '';
    return `rgba(99, 102, 241, ${(ratio * 0.25).toFixed(2)})`;
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Pessoa</label>
          <select
            value={person}
            onChange={(e) => setPerson(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value="">Todas</option>
            {persons.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Periodo</label>
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value={3}>3 meses</option>
            <option value={6}>6 meses</option>
            <option value={12}>12 meses</option>
          </select>
        </div>
      </div>

      {/* Pivot Table */}
      {isLoading ? (
        <div className="text-gray-400 text-center py-10">Carregando...</div>
      ) : categories.length === 0 ? (
        <div className="text-gray-500 text-center py-10">
          Nenhum dado encontrado
        </div>
      ) : (
        <div className="bg-[#1a1a2e] rounded-xl p-5 overflow-x-auto">
          <h3 className="text-gray-200 font-semibold mb-4">Tabela Dinamica</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                <th className="py-3 px-3 sticky left-0 bg-[#1a1a2e]">
                  Categoria
                </th>
                {monthsList.map((m) => (
                  <th key={m} className="py-3 px-3 text-right whitespace-nowrap">
                    {formatMonth(m)}
                  </th>
                ))}
                <th className="py-3 px-3 text-right font-bold">Total</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr
                  key={cat.name}
                  className="border-b border-[#2a2a4a] hover:bg-[#1e2a4a] transition-colors"
                >
                  <td className="py-2 px-3 sticky left-0 bg-[#1a1a2e] flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: cat.color || '#6366f1' }}
                    />
                    <span className="text-gray-200">{cat.name}</span>
                  </td>
                  {monthsList.map((m) => {
                    const val = cat.values[m] ?? 0;
                    const bg = cellOpacity(val);
                    return (
                      <td
                        key={m}
                        className="py-2 px-3 text-right text-gray-300 whitespace-nowrap"
                        style={bg ? { backgroundColor: bg } : undefined}
                      >
                        {val !== 0 ? fmt.format(Math.abs(val)) : '-'}
                      </td>
                    );
                  })}
                  <td className="py-2 px-3 text-right text-gray-200 font-medium whitespace-nowrap">
                    {fmt.format(Math.abs(cat.total))}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-[#2a2a4a]">
                <td className="py-3 px-3 sticky left-0 bg-[#1a1a2e] text-gray-200 font-semibold">
                  Total
                </td>
                {monthsList.map((m) => {
                  const val = monthTotals[m] ?? 0;
                  return (
                    <td
                      key={m}
                      className="py-3 px-3 text-right text-gray-200 font-semibold whitespace-nowrap"
                    >
                      {val !== 0 ? fmt.format(Math.abs(val)) : '-'}
                    </td>
                  );
                })}
                <td className="py-3 px-3 text-right text-indigo-400 font-bold whitespace-nowrap">
                  {fmt.format(Math.abs(grandTotal))}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}

function formatMonth(ym: string): string {
  const [year, month] = ym.split('-');
  const months = [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez',
  ];
  return `${months[parseInt(month, 10) - 1]} ${year.slice(2)}`;
}
