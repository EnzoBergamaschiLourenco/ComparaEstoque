import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from 'recharts'
import { SaleEvent } from '@/hooks/use-canteen-data'

interface DashboardChartsProps {
  sales: SaleEvent[]
}

export function DashboardCharts({ sales }: DashboardChartsProps) {
  const chartData = useMemo(() => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() - i)
      return d.toISOString().split('T')[0]
    }).reverse()

    return last7Days.map((date) => {
      const daySales = sales.filter((s) => s.date === date)
      return {
        date: date.substring(5).replace('-', '/'), // format MM/DD
        vendas: daySales.reduce((acc, s) => acc + s.quantity, 0),
      }
    })
  }, [sales])

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Tendência de Vendas</CardTitle>
        <CardDescription>Volume de itens vendidos nos últimos 7 dias</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{ vendas: { label: 'Vendas', color: 'hsl(var(--primary))' } }}
          className="h-[300px] w-full"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tickMargin={10} />
              <YAxis axisLine={false} tickLine={false} tickMargin={10} />
              <ChartTooltip
                content={<ChartTooltipContent indicator="dot" />}
                cursor={{ stroke: 'hsl(var(--border))' }}
              />
              <Line
                type="monotone"
                dataKey="vendas"
                stroke="var(--color-vendas)"
                strokeWidth={3}
                dot={{ r: 4, fill: 'var(--color-vendas)' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
