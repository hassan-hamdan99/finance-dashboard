import { useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Download,
} from 'lucide-react';
import { useDashboard, usePersons, useCategories } from '../api/hooks';

const fmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function getCurrentMonth() {
  return new Date().toISOString().slice(0, 7);
}

export default function Overview() {
  const [person, setPerson] = useState('');
  const [month, setMonth] = useState(getCurrentMonth());
  const [months, setMonths] = useState(6);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const { data: persons = [] } = usePersons();
  const { data: categories = [] } = useCategories();
  const { data, isLoading } = useDashboard({
    person: person || undefined,
    month,
    months,
    categories: selectedCategories.length
      ? selectedCategories.join(',')
      : undefined,
  });

  const kpis = data?.kpis;
  const categoryBreakdown = data?.category_breakdown ?? [];
  const monthlySummary = data?.monthly_summary ?? [];

  function toggleCategory(name: string) {
    setSelectedCategories((prev) =>
      prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name],
    );
  }

  return (
    <div className="space-y-6">
      {/* Filter bar */}
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
          <label className="block text-xs text-gray-400 mb-1">Mês</label>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Período</label>
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg px-3 py-2 text-gray-200"
          >
            <option value={3}>3 meses</option>
            <option value={6}>6 meses</option>
            <option value={12}>12 meses</option>
            <option value={24}>24 meses</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">&nbsp;</label>
          <button
            onClick={() =>
              window.open(
                `/api/export/excel?months=${months}${person ? `&person=${encodeURIComponent(person)}` : ''}`,
              )
            }
            className="flex items-center gap-2 border border-[#2a2a4a] text-gray-300 hover:bg-[#1e2a4a] rounded-lg px-4 py-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            Exportar Excel
          </button>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs text-gray-400 mb-1">Categorias</label>
          <div className="flex flex-wrap gap-1">
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => toggleCategory(c.name)}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  selectedCategories.includes(c.name)
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-[#1a1a2e] border-[#2a2a4a] text-gray-400 hover:border-gray-500'
                }`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="text-gray-400 text-center py-10">Carregando...</div>
      ) : kpis ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              icon={<TrendingDown className="w-5 h-5" />}
              label="Total Gastos"
              value={fmt.format(Math.abs(kpis.total_gastos))}
              color="text-red-400"
              iconBg="bg-red-600/20"
            />
            <KPICard
              icon={<TrendingUp className="w-5 h-5" />}
              label="Total Receitas"
              value={fmt.format(kpis.total_receitas)}
              color="text-green-400"
              iconBg="bg-green-600/20"
            />
            <KPICard
              icon={<Wallet className="w-5 h-5" />}
              label="Saldo"
              value={fmt.format(kpis.saldo)}
              color={kpis.saldo >= 0 ? 'text-green-400' : 'text-red-400'}
              iconBg={kpis.saldo >= 0 ? 'bg-green-600/20' : 'bg-red-600/20'}
            />
            <KPICard
              icon={
                kpis.variacao_gastos <= 0 ? (
                  <ArrowDownRight className="w-5 h-5" />
                ) : (
                  <ArrowUpRight className="w-5 h-5" />
                )
              }
              label="Variação Gastos"
              value={`${kpis.variacao_gastos >= 0 ? '+' : ''}${kpis.variacao_gastos.toFixed(1)}%`}
              color={kpis.variacao_gastos <= 0 ? 'text-green-400' : 'text-red-400'}
              iconBg={
                kpis.variacao_gastos <= 0 ? 'bg-green-600/20' : 'bg-red-600/20'
              }
            />
          </div>

          {/* Charts Row: Pie + Bar */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie chart */}
            <div className="bg-[#1a1a2e] rounded-xl p-5">
              <h3 className="text-gray-200 font-semibold mb-4">
                Gastos por Categoria
              </h3>
              {categoryBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryBreakdown}
                      dataKey="total"
                      nameKey="category"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(props: any) =>
                        `${props.name} ${((props.percent || 0) * 100).toFixed(0)}%`
                      }
                    >
                      {categoryBreakdown.map((entry, i) => (
                        <Cell key={i} fill={entry.color || '#6366f1'} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => fmt.format(Math.abs(Number(value)))}
                      contentStyle={{
                        backgroundColor: '#16213e',
                        border: '1px solid #2a2a4a',
                        borderRadius: 8,
                        color: '#e5e7eb',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-500 text-center py-10">Sem dados</p>
              )}
            </div>

            {/* Bar chart */}
            <div className="bg-[#1a1a2e] rounded-xl p-5">
              <h3 className="text-gray-200 font-semibold mb-4">
                Gastos vs Receitas
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlySummary}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="month" tick={{ fill: '#9ca3af' }} />
                  <YAxis tick={{ fill: '#9ca3af' }} />
                  <Tooltip
                    formatter={(value) => fmt.format(Math.abs(Number(value)))}
                    contentStyle={{
                      backgroundColor: '#16213e',
                      border: '1px solid #2a2a4a',
                      borderRadius: 8,
                      color: '#e5e7eb',
                    }}
                  />
                  <Legend />
                  <Bar
                    dataKey="gastos"
                    name="Gastos"
                    fill="#ef4444"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="receitas"
                    name="Receitas"
                    fill="#22c55e"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Saldo evolution */}
          <div className="bg-[#1a1a2e] rounded-xl p-5">
            <h3 className="text-gray-200 font-semibold mb-4">
              Evolução do Saldo
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlySummary}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="month" tick={{ fill: '#9ca3af' }} />
                <YAxis tick={{ fill: '#9ca3af' }} />
                <Tooltip
                  formatter={(value) => fmt.format(Number(value))}
                  contentStyle={{
                    backgroundColor: '#16213e',
                    border: '1px solid #2a2a4a',
                    borderRadius: 8,
                    color: '#e5e7eb',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="saldo"
                  name="Saldo"
                  stroke="#818cf8"
                  strokeWidth={2}
                  dot={{ fill: '#818cf8', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : (
        <div className="text-gray-500 text-center py-10">
          Nenhum dado encontrado
        </div>
      )}
    </div>
  );
}

function KPICard({
  icon,
  label,
  value,
  color,
  iconBg,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  iconBg: string;
}) {
  return (
    <div className="bg-[#16213e] rounded-xl p-5 flex items-center gap-4">
      <div className={`${iconBg} ${color} p-3 rounded-lg`}>{icon}</div>
      <div>
        <p className="text-gray-400 text-sm">{label}</p>
        <p className={`text-xl font-bold ${color}`}>{value}</p>
      </div>
    </div>
  );
}
