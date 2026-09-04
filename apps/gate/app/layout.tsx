import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Gate review — conversation.farm',
  description: 'Review gates for the convo pipeline. Edits the queue file in git.',
  robots: { index: false, follow: false },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
