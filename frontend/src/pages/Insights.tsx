import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import {
  Info,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import {
  useInsights,
  useTopExpenses,
  useTrends,
  usePersons,
  useRecurring,
} from '../api/hooks';
import type { RecurringTransaction } from '../types';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
}

const typeConfig: Record<
  string,
  { bg: string; border: string; text: string; icon: React.ReactNode }
> = {
  info: {
    bg: 'bg-blue-600/15',
    border: 'border-blue-600/30',
    text: 'text-blue-300',
    icon: <Info className="w-5 h-5 text-blue-400" />,
  },
  warning: {
    bg: 'bg-yellow-600/15',
    border: 'border-yellow-600/30',
    text: 'text-yellow-300',
    icon: <AlertTriangle className="w-5 h-5 text-yellow-400" />,
  },
  danger: {
    bg: 'bg-red-600/15',
    border: 'border-red-600/30',
    text: 'text-red-300',
    icon: <AlertCircle className="w-5 h-5 text-red-400" />,
  },
  success: {
    bg: 'bg-green-600/15',
    border: 'border-green-600/30',
    text: 'text-green-300',
    icon: <CheckCircle className="w-5 h-5 text-green-400" />,
  },
};

export default function Insights() {
  const [person, setPerson] = useState('');
  const [month, setMonth] = useState(getCurrentMonth());

  const { data: persons = [] } = usePersons();
  const params = { person: person || undefined, month };

  const { data: insights = [], isLoading: loadingInsights } = useInsights(params);
  const { data: topExpenses = [], isLoading: loadingTop } = useTopExpenses({
    ...params,
    top_n: 10,
  });
  const { data: trends, isLoading: loadingTrends } = useTrends(params);
  const { data: recurring = [], isLoading: loadingRecurring } = useRecurring({
    person: person || undefined,
    months: 6,
  });
  const recurringItems = recurring as RecurringTransaction[];

  const trendsData: { category: string; change: number }[] = Array.isArray(trends)
    ? trends
    : [];

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
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Mês</label>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
        </div>
      </div>

      {/* Insight cards */}
      <div className="space-y-3">
        {loadingInsights ? (
          <p className="text-gray-500 text-center py-6">Carregando insights...</p>
        ) : insights.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Nenhum insight disponível</p>
        ) : (
          insights.map((ins, i) => {
            const cfg = typeConfig[ins.type] ?? typeConfig.info;
            return (
              <div
                key={i}
                className={`${cfg.bg} border ${cfg.border} rounded-xl p-4 flex items-start gap-3`}
              >
                {cfg.icon}
                <p className={`${cfg.text} text-sm`}>{ins.text}</p>
              </div>
            );
          })
        )}
      </div>

      {/* Top expenses */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-4">Maiores Gastos</h3>
        {loadingTop ? (
          <p className="text-gray-500 text-center py-6">Carregando...</p>
        ) : topExpenses.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Sem dados</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                <th className="py-2 px-2">Data</th>
                <th className="py-2 px-2">Descrição</th>
                <th className="py-2 px-2 text-right">Valor</th>
                <th className="py-2 px-2">Categoria</th>
              </tr>
            </thead>
            <tbody>
              {topExpenses.map((t) => (
                <tr
                  key={t.id}
                  className="border-b border-[#2a2a4a] hover:bg-[#1e2a4a]"
                >
                  <td className="py-2 px-2 text-gray-300">{t.date}</td>
                  <td className="py-2 px-2 text-gray-200 max-w-xs truncate">
                    {t.description}
                  </td>
                  <td className="py-2 px-2 text-right text-red-400 font-medium">
                    {fmt.format(t.amount)}
                  </td>
                  <td className="py-2 px-2 text-gray-300">
                    {t.category_name ?? '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Trends chart */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-4">
          Tendências por Categoria (% variação)
        </h3>
        {loadingTrends ? (
          <p className="text-gray-500 text-center py-6">Carregando...</p>
        ) : trendsData.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Sem dados de tendência</p>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, trendsData.length * 36)}>
            <BarChart data={trendsData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" tick={{ fill: '#9ca3af' }} unit="%" />
              <YAxis
                type="category"
                dataKey="category"
                tick={{ fill: '#9ca3af' }}
                width={120}
              />
              <Tooltip
                formatter={(value) => `${Number(value).toFixed(1)}%`}
                contentStyle={{
                  backgroundColor: '#16213e',
                  border: '1px solid #2a2a4a',
                  borderRadius: 8,
                  color: '#e5e7eb',
                }}
              />
              <Bar dataKey="change" radius={[0, 4, 4, 0]}>
                {trendsData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.change <= 0 ? '#22c55e' : '#ef4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recurring transactions */}
      <div className="bg-[#1a1a2e] rounded-xl p-5">
        <h3 className="text-gray-200 font-semibold mb-4">Gastos Recorrentes</h3>
        {loadingRecurring ? (
          <p className="text-gray-500 text-center py-6">Carregando...</p>
        ) : recurringItems.length === 0 ? (
          <p className="text-gray-500 text-center py-6">Nenhum gasto recorrente detectado</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left border-b border-[#2a2a4a]">
                  <th className="py-2 px-2">Padrao</th>
                  <th className="py-2 px-2">Categoria</th>
                  <th className="py-2 px-2 text-right">Valor Medio</th>
                  <th className="py-2 px-2 text-right">Frequencia</th>
                  <th className="py-2 px-2">Ultimo Mes</th>
                </tr>
              </thead>
              <tbody>
                {recurringItems.map((r, i) => (
                  <tr
                    key={i}
                    className={`border-b border-[#2a2a4a] hover:bg-[#1e2a4a] transition-colors ${
                      r.is_missing_current ? 'bg-yellow-600/10' : ''
                    }`}
                  >
                    <td className="py-2 px-2 text-gray-200 flex items-center gap-2">
                      {r.is_missing_current && (
                        <span title="Ausente no mês atual"><AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0" /></span>
                      )}
                      {r.amount_changed && !r.is_missing_current && (
                        <span title="Valor alterado"><Info className="w-4 h-4 text-blue-400 flex-shrink-0" /></span>
                      )}
                      <span className="truncate max-w-xs">{r.pattern}</span>
                    </td>
                    <td className="py-2 px-2 text-gray-300">{r.category_name || '-'}</td>
                    <td className="py-2 px-2 text-right text-red-400 font-medium">
                      {fmt.format(Math.abs(r.avg_amount))}
                    </td>
                    <td className="py-2 px-2 text-right text-gray-300">{r.frequency}x</td>
                    <td className="py-2 px-2 text-gray-300">{r.last_seen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
