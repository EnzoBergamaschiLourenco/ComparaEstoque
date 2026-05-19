import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LucideIcon } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

interface KpiCardProps {
  title: string
  value: string | number
  description: string
  icon: LucideIcon
  loading?: boolean
  trend?: 'up' | 'down' | 'neutral'
}

export function KpiCard({ title, value, description, icon: Icon, loading, trend }: KpiCardProps) {
  return (
    <Card className="shadow-sm transition-all hover:shadow-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div
          className={`p-2 rounded-full ${trend === 'down' ? 'bg-destructive/10 text-destructive' : 'bg-primary/10 text-primary'}`}
        >
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-1/2" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        ) : (
          <>
            <div className="text-2xl font-bold tracking-tight">{value}</div>
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
