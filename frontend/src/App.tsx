import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  LayoutDashboard,
  ArrowLeftRight,
  PiggyBank,
  Lightbulb,
  Upload,
  BookOpen,
  TrendingUp,
  Coins,
  Menu,
  X,
  Table2,
  Target,
} from 'lucide-react';

import Overview from './pages/Overview';
import Transactions from './pages/Transactions';
import BudgetPage from './pages/Budget';
import InsightsPage from './pages/Insights';
import UploadPage from './pages/Upload';
import RulesPage from './pages/Rules';
import InvestmentsPage from './pages/Investments';
import PivotPage from './pages/Pivot';
import PlanningPage from './pages/Planning';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,
      retry: 1,
    },
  },
});

const navItems = [
  { to: '/', label: 'Visão Geral', icon: LayoutDashboard },
  { to: '/transacoes', label: 'Transações', icon: ArrowLeftRight },
  { to: '/orcamento', label: 'Orçamento', icon: PiggyBank },
  { to: '/insights', label: 'Insights', icon: Lightbulb },
  { to: '/pivot', label: 'Tabela Dinamica', icon: Table2 },
  { to: '/planejamento', label: 'Planejamento', icon: Target },
  { to: '/upload', label: 'Importar', icon: Upload },
  { to: '/regras', label: 'Regras', icon: BookOpen },
  { to: '/investimentos', label: 'Investimentos', icon: TrendingUp },
];

function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 z-50 h-full w-60
          bg-[#1a1a2e] border-r border-[#2a2a4a]
          flex flex-col
          transition-transform duration-300 ease-in-out
          lg:translate-x-0
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-6 border-b border-[#2a2a4a]">
          <Coins className="w-7 h-7 text-[#6366f1]" />
          <span className="text-xl font-bold text-gray-100 tracking-tight">
            DashFinanceira
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? 'bg-[#6366f1]/15 text-[#818cf8]'
                    : 'text-gray-400 hover:bg-[#16213e] hover:text-gray-200'
                }`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-[#2a2a4a] text-xs text-gray-500">
          DashFinanceira v2.0
        </div>
      </aside>
    </>
  );
}

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0f0f1a]">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content area */}
      <div className="lg:ml-60">
        {/* Header */}
        <header className="sticky top-0 z-30 flex items-center h-14 px-4 bg-[#0f0f1a]/80 backdrop-blur-md border-b border-[#2a2a4a]">
          <button
            className="lg:hidden p-2 -ml-2 text-gray-400 hover:text-gray-200 transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            {sidebarOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/transacoes" element={<Transactions />} />
            <Route path="/orcamento" element={<BudgetPage />} />
            <Route path="/insights" element={<InsightsPage />} />
            <Route path="/pivot" element={<PivotPage />} />
            <Route path="/planejamento" element={<PlanningPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/regras" element={<RulesPage />} />
            <Route path="/investimentos" element={<InvestmentsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
