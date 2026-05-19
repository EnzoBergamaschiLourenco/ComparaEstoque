import { useContext, useMemo } from 'react'
import { Package, TrendingUp, DollarSign, AlertTriangle } from 'lucide-react'
import { CanteenDataContext } from '@/components/Layout'
import { KpiCard } from '@/components/dashboard/kpi-card'
import { DashboardCharts } from '@/components/dashboard/dashboard-charts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { formatCurrency, formatDate } from '@/lib/formatters'

export default function Index() {
  const context = useContext(CanteenDataContext)

  const items = context?.items || []
  const sales = context?.sales || []
  const loading = context?.loading || false

  const kpis = useMemo(() => {
    const totalItems = items.reduce((acc, item) => acc + item.quantity, 0)
    const lowStock = items.filter((item) => item.quantity <= 10).length

    const todayStr = new Date().toISOString().split('T')[0]
    const salesToday = sales.filter((s) => s.date === todayStr)
    const salesTodayVolume = salesToday.reduce((acc, s) => acc + s.quantity, 0)

    const revenueEst = items.reduce((acc, item) => acc + item.quantity * item.sellingPrice, 0)

    return { totalItems, lowStock, salesTodayVolume, revenueEst }
  }, [items, sales])

  const recentActivity = useMemo(() => {
    return sales.slice(0, 5).map((s) => {
      const item = items.find((i) => i.id === s.itemId)
      return { ...s, itemName: item?.name || 'Desconhecido' }
    })
  }, [sales, items])

  if (!context) return null

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Bem-vindo(a) de volta! Aqui está o resumo da sua cantina hoje.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Total Itens em Estoque"
          value={kpis.totalItems}
          description="Itens disponíveis fisicamente"
          icon={Package}
          loading={loading}
        />
        <KpiCard
          title="Vendas Hoje"
          value={kpis.salesTodayVolume}
          description="Unidades vendidas hoje"
          icon={TrendingUp}
          loading={loading}
        />
        <KpiCard
          title="Receita Estimada"
          value={formatCurrency(kpis.revenueEst)}
          description="Valor total do estoque atual"
          icon={DollarSign}
          loading={loading}
        />
        <KpiCard
          title="Alertas de Estoque Baixo"
          value={kpis.lowStock}
          description="Itens abaixo do mínimo (10)"
          icon={AlertTriangle}
          loading={loading}
          trend={kpis.lowStock > 0 ? 'down' : 'neutral'}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <div className="md:col-span-4 lg:col-span-5">
          <DashboardCharts sales={sales} />
        </div>

        <Card className="md:col-span-3 lg:col-span-2 shadow-sm">
          <CardHeader>
            <CardTitle>Atividade Recente</CardTitle>
            <CardDescription>Últimas 5 vendas registradas</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-muted animate-pulse" />
                    <div className="space-y-1 flex-1">
                      <div className="h-4 w-3/4 bg-muted rounded animate-pulse" />
                      <div className="h-3 w-1/2 bg-muted rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start justify-between border-b pb-3 last:border-0 last:pb-0"
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">Venda: {activity.itemName}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(activity.date)}</p>
                    </div>
                    <div className="font-medium text-sm text-primary">+{activity.quantity} un</div>
                  </div>
                ))}
                {recentActivity.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    Nenhuma atividade recente.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
