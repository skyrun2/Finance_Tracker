import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "@/components/layout/Providers"
import { Sidebar } from "@/components/layout/Sidebar"

export const metadata: Metadata = {
  title: "finance",
  description: "Personal finance tracker",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex font-sans">
        <Providers>
          <Sidebar />
          <main className="flex-1 p-8 overflow-auto bg-muted/30">{children}</main>
        </Providers>
      </body>
    </html>
  )
}
