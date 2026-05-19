import { useContext, useState } from 'react'
import { Download } from 'lucide-react'
import { CanteenDataContext } from '@/components/Layout'
import { FinancialCharts } from '@/components/financeiro/financial-charts'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/hooks/use-toast'
import { formatCurrency, formatPercent } from '@/lib/formatters'

export default function Financeiro() {
  const context = useContext(CanteenDataContext)
  const [period, setPeriod] = useState('7')
  const { toast } = useToast()

  if (!context) return null

  const { items, sales, loading } = context

  const handleExport = () => {
    toast({
      title: 'Relatório Gerado',
      description: 'O arquivo CSV do financeiro está sendo baixado.',
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Vendas & Financeiro</h2>
          <p className="text-muted-foreground">
            Analise as margens de lucro e performance de vendas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Período" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Últimos 7 dias</SelectItem>
              <SelectItem value="15">Últimos 15 dias</SelectItem>
              <SelectItem value="30">Últimos 30 dias</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleExport} className="gap-2">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Exportar Relatório</span>
          </Button>
        </div>
      </div>

      <FinancialCharts items={items} sales={sales} days={parseInt(period)} />

      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Detalhamento Financeiro por Item</CardTitle>
          <CardDescription>
            Custo, preço, margem e lucro total baseado nas vendas simuladas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead>Item</TableHead>
                  <TableHead className="text-right">Custo Unit.</TableHead>
                  <TableHead className="text-right">Preço de Venda</TableHead>
                  <TableHead className="text-right">Margem de Lucro</TableHead>
                  <TableHead className="text-right">Un. Vendidas</TableHead>
                  <TableHead className="text-right text-primary">Lucro Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-5 w-32" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-16 ml-auto" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-16 ml-auto" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-16 ml-auto" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-12 ml-auto" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-20 ml-auto" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      Nenhum dado financeiro disponível.
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item) => (
                    <TableRow key={item.id} className="group transition-colors">
                      <TableCell className="font-medium">{item.name}</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatCurrency(item.unitCost)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(item.sellingPrice)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${item.profitMargin > 40 ? 'bg-primary/10 text-primary' : 'bg-yellow-500/10 text-yellow-700'}`}
                        >
                          {formatPercent(item.profitMargin)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">{item.salesVolume}</TableCell>
                      <TableCell className="text-right font-bold text-primary">
                        {formatCurrency(item.totalProfit)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
