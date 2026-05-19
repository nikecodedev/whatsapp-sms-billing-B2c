import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'

const nav = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/campaigns', label: 'Campanhas', icon: '📣' },
  { to: '/debtors', label: 'Devedores', icon: '👥' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-60 bg-brand-900 text-white flex flex-col py-8 px-4 shrink-0">
        <div className="mb-10 px-2">
          <h1 className="text-2xl font-bold tracking-wide text-white">QUESH</h1>
          <p className="text-xs text-brand-100 mt-1">Cobrança Inteligente</p>
        </div>

        <nav className="flex flex-col gap-1">
          {nav.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-brand-100 hover:bg-brand-700 hover:text-white'
                )
              }
            >
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto px-2 text-xs text-brand-100/60">
          v1.0.0 MVP
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-8">
        {children}
      </main>
    </div>
  )
}
