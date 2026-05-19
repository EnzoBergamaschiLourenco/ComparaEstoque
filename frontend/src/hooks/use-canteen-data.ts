import { useState, useEffect, useCallback } from 'react'

export interface LocalItem {
  id: string
  name: string
  category: string
}

export interface MergedItem extends LocalItem {
  quantity: number
  unitCost: number
  sellingPrice: number
  salesVolume: number
  profitMargin: number
  totalProfit: number
  status: 'Em Estoque' | 'Baixo' | 'Sem Estoque'
}

export interface SaleEvent {
  id: string
  itemId: string
  quantity: number
  date: string
}

const MOCK_LOCAL_ITEMS: LocalItem[] = [
  { id: '1', name: 'Coxinha de Frango', category: 'Salgados' },
  { id: '2', name: 'Pastel de Queijo', category: 'Salgados' },
  { id: '3', name: 'Suco de Laranja', category: 'Bebidas' },
  { id: '4', name: 'Refrigerante Lata', category: 'Bebidas' },
  { id: '5', name: 'Bolo de Chocolate', category: 'Doces' },
  { id: '6', name: 'Pão de Queijo', category: 'Salgados' },
  { id: '7', name: 'Hambúrguer', category: 'Lanches' },
  { id: '8', name: 'Água Mineral', category: 'Bebidas' },
]

function generateMockData() {
  const stock = MOCK_LOCAL_ITEMS.map((item, index) => ({
    itemId: item.id,
    quantity: index === 3 ? 0 : index === 5 ? 5 : Math.floor(Math.random() * 40) + 10,
  }))

  const finance = MOCK_LOCAL_ITEMS.map((item) => {
    const cost = Math.random() * 3 + 1
    return {
      itemId: item.id,
      unitCost: cost,
      sellingPrice: cost * (Math.random() * 1.5 + 1.5),
    }
  })

  const sales: SaleEvent[] = []
  const today = new Date()
  for (let i = 0; i < 50; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() - Math.floor(Math.random() * 7))
    sales.push({
      id: `s${i}`,
      itemId: MOCK_LOCAL_ITEMS[Math.floor(Math.random() * MOCK_LOCAL_ITEMS.length)].id,
      quantity: Math.floor(Math.random() * 5) + 1,
      date: d.toISOString().split('T')[0],
    })
  }

  return {
    stock,
    finance,
    sales: sales.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
  }
}

export function useCanteenData() {
  const [items, setItems] = useState<MergedItem[]>([])
  const [sales, setSales] = useState<SaleEvent[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 800))

    const { stock, finance, sales: mockSales } = generateMockData()

    const merged = MOCK_LOCAL_ITEMS.map((local) => {
      const stockData = stock.find((s) => s.itemId === local.id)
      const financeData = finance.find((f) => f.itemId === local.id)

      const qty = stockData?.quantity || 0
      const cost = financeData?.unitCost || 0
      const price = financeData?.sellingPrice || 0
      const itemSales = mockSales
        .filter((s) => s.itemId === local.id)
        .reduce((acc, s) => acc + s.quantity, 0)

      const profitMargin = price > 0 ? ((price - cost) / price) * 100 : 0
      const totalProfit = (price - cost) * itemSales

      let status: MergedItem['status'] = 'Em Estoque'
      if (qty === 0) status = 'Sem Estoque'
      else if (qty <= 10) status = 'Baixo'

      return {
        ...local,
        quantity: qty,
        unitCost: cost,
        sellingPrice: price,
        salesVolume: itemSales,
        profitMargin,
        totalProfit,
        status,
      }
    })

    setItems(merged)
    setSales(mockSales)
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { items, sales, loading, syncData: fetchData }
}
