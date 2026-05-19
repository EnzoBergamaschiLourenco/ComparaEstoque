import { useContext, useState, useMemo } from 'react'
import { Search } from 'lucide-react'
import { CanteenDataContext } from '@/components/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'

export default function Estoque() {
  const context = useContext(CanteenDataContext)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('Todas')

  const items = context?.items || []
  const loading = context?.loading || false

  const categories = useMemo(() => {
    const cats = new Set(items.map((item) => item.category))
    return ['Todas', ...Array.from(cats)]
  }, [items])

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesCategory = categoryFilter === 'Todas' || item.category === categoryFilter
      return matchesSearch && matchesCategory
    })
  }, [items, searchTerm, categoryFilter])

  if (!context) return null

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Em Estoque':
        return (
          <Badge
            variant="default"
            className="bg-primary/20 text-primary hover:bg-primary/30 border-0"
          >
            Normal
          </Badge>
        )
      case 'Baixo':
        return (
          <Badge
            variant="outline"
            className="bg-yellow-500/20 text-yellow-700 hover:bg-yellow-500/30 border-0"
          >
            Baixo
          </Badge>
        )
      case 'Sem Estoque':
        return (
          <Badge
            variant="destructive"
            className="bg-destructive/20 text-destructive hover:bg-destructive/30 border-0"
          >
            Esgotado
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Gestão de Estoque</h2>
        <p className="text-muted-foreground">Acompanhe a quantidade disponível e evite faltas.</p>
      </div>

      <Card className="shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle>Inventário Atual</CardTitle>
          <div className="flex flex-col sm:flex-row gap-4 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar item..."
                className="pl-8"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="w-full sm:w-[200px]">
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[300px]">Item</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[200px]">Nível (Ref: 50)</TableHead>
                  <TableHead className="text-right">Quantidade</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-5 w-32" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-5 w-20" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-24 rounded-full" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-2 w-full" />
                      </TableCell>
                      <TableCell className="text-right">
                        <Skeleton className="h-5 w-8 ml-auto" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : filteredItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      Nenhum item encontrado.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredItems.map((item) => (
                    <TableRow key={item.id} className="group transition-colors">
                      <TableCell className="font-medium">{item.name}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell>{getStatusBadge(item.status)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress
                            value={Math.min((item.quantity / 50) * 100, 100)}
                            className={`h-2 ${item.quantity <= 10 ? '[&>div]:bg-yellow-500' : item.quantity === 0 ? '[&>div]:bg-destructive' : ''}`}
                          />
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-semibold">{item.quantity} un</TableCell>
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
