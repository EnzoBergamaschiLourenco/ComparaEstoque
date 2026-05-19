import { RefreshCw, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { useToast } from '@/hooks/use-toast'
import { useState } from 'react'

interface AppHeaderProps {
  onSync: () => Promise<void>
}

export function AppHeader({ onSync }: AppHeaderProps) {
  const { toast } = useToast()
  const [syncing, setSyncing] = useState(false)

  const handleSync = async () => {
    setSyncing(true)
    try {
      await onSync()
      toast({
        title: 'Sincronização concluída',
        description: 'Os dados mais recentes foram carregados.',
      })
    } catch (error) {
      toast({
        title: 'Erro na sincronização',
        description: 'Não foi possível buscar os dados.',
        variant: 'destructive',
      })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 shadow-sm">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <h1 className="text-lg font-semibold tracking-tight hidden sm:block">Visão Geral</h1>
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSync}
          disabled={syncing}
          className="hidden sm:flex transition-transform active:scale-95"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
          Sincronizar Dados
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSync}
          disabled={syncing}
          className="sm:hidden"
        >
          <RefreshCw className={`h-5 w-5 ${syncing ? 'animate-spin' : ''}`} />
        </Button>

        <div className="h-8 w-px bg-border mx-2" />

        <Avatar className="h-9 w-9 border border-border">
          <AvatarImage
            src="https://img.usecurling.com/ppl/thumbnail?gender=female&seed=1"
            alt="Perfil"
          />
          <AvatarFallback>
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      </div>
    </header>
  )
}
