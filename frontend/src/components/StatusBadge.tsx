import { clsx } from 'clsx'

const statusConfig: Record<string, { label: string; classes: string }> = {
  draft:     { label: 'Rascunho',    classes: 'bg-gray-100 text-gray-600' },
  active:    { label: 'Ativo',       classes: 'bg-green-100 text-green-700' },
  paused:    { label: 'Pausado',     classes: 'bg-amber-100 text-amber-700' },
  completed: { label: 'Concluído',   classes: 'bg-blue-100 text-blue-700' },
  cancelled: { label: 'Cancelado',   classes: 'bg-red-100 text-red-600' },
  scheduled: { label: 'Agendado',    classes: 'bg-sky-100 text-sky-700' },
  sent:      { label: 'Enviado',     classes: 'bg-indigo-100 text-indigo-700' },
  delivered: { label: 'Entregue',    classes: 'bg-green-100 text-green-700' },
  failed:    { label: 'Falhou',      classes: 'bg-red-100 text-red-600' },
  responded: { label: 'Respondido',  classes: 'bg-purple-100 text-purple-700' },
  paid:      { label: 'Pago',        classes: 'bg-emerald-100 text-emerald-700' },
  pending:   { label: 'Pendente',    classes: 'bg-amber-100 text-amber-700' },
  confirmed: { label: 'Confirmado',  classes: 'bg-green-100 text-green-700' },
  overdue:   { label: 'Vencido',     classes: 'bg-red-100 text-red-600' },
}

export default function StatusBadge({ status }: { status: string }) {
  const cfg = statusConfig[status] ?? { label: status, classes: 'bg-gray-100 text-gray-600' }
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', cfg.classes)}>
      {cfg.label}
    </span>
  )
}
