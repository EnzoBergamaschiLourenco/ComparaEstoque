import { Outlet } from 'react-router-dom'
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { AppHeader } from '@/components/layout/app-header'
import { useCanteenData } from '@/hooks/use-canteen-data'
import { createContext } from 'react'

// Create a context to share the data globally since it's fetched once
export const CanteenDataContext = createContext<ReturnType<typeof useCanteenData> | null>(null)

export default function Layout() {
  const canteenData = useCanteenData()

  return (
    <CanteenDataContext.Provider value={canteenData}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="overflow-hidden bg-slate-50/50 dark:bg-background">
          <AppHeader onSync={canteenData.syncData} />
          <main className="flex-1 p-4 md:p-6 lg:p-8 animate-fade-in w-full max-w-7xl mx-auto">
            <Outlet />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </CanteenDataContext.Provider>
  )
}
