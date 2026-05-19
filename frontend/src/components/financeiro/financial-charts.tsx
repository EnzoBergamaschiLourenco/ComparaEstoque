import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Area,
  AreaChart,
} from 'recharts'
import { MergedItem, SaleEvent } from '@/hooks/use-canteen-data'
import { formatCurrency } from '@/lib/formatters'

interface FinancialChartsProps {
  items: MergedItem[]
  sales: SaleEvent[]
  days: number
}

export function FinancialCharts({ items, sales, days }: FinancialChartsProps) {
  // Chart 1: Sales by Item (Bar)
  const salesByItemData = useMemo(() => {
    return items
      .map((item) => ({
        name: item.name,
        vendas: item.salesVolume,
      }))
      .sort((a, b) => b.vendas - a.vendas)
      .slice(0, 7) // Top 7
  }, [items])

  // Chart 2: Revenue Trend (Area)
  const revenueTrendData = useMemo(() => {
    const dates = Array.from({ length: days }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() - i)
      return d.toISOString().split('T')[0]
    }).reverse()

    return dates.map((date) => {
      const daySales = sales.filter((s) => s.date === date)
      const revenue = daySales.reduce((acc, s) => {
        const item = items.find((i) => i.id === s.itemId)
        return acc + s.quantity * (item?.sellingPrice || 0)
      }, 0)

      return {
        date: date.substring(5).replace('-', '/'),
        receita: revenue,
      }
    })
  }, [sales, items, days])

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Top Produtos Vendidos</CardTitle>
          <CardDescription>Volume de unidades no período</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{ vendas: { label: 'Unidades', color: 'hsl(var(--primary))' } }}
            className="h-[250px] w-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={salesByItemData}
                margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tickMargin={10}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis axisLine={false} tickLine={false} tickMargin={10} />
                <ChartTooltip
                  content={<ChartTooltipContent />}
                  cursor={{ fill: 'hsl(var(--muted))' }}
                />
                <Bar
                  dataKey="vendas"
                  fill="var(--color-vendas)"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={50}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Evolução da Receita</CardTitle>
          <CardDescription>Receita bruta diária</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{ receita: { label: 'Receita (R$)', color: 'hsl(var(--secondary))' } }}
            className="h-[250px] w-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={revenueTrendData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorReceita" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-receita)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--color-receita)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tickMargin={10} />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tickMargin={10}
                  tickFormatter={(v) => `R$ ${v}`}
                />
                <ChartTooltip
                  content={
                    <ChartTooltipContent formatter={(value) => formatCurrency(Number(value))} />
                  }
                />
                <Area
                  type="monotone"
                  dataKey="receita"
                  stroke="var(--color-receita)"
                  fillOpacity={1}
                  fill="url(#colorReceita)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}
