import type { Metadata } from 'next';
import './globals.css';
import Navigation from '@/components/Navigation';
import MicroCursor from '@/components/MicroCursor';
import PageTransition from '@/components/PageTransition';

export const metadata: Metadata = {
  title: 'NeuroSpeak AI Platform',
  description: 'Gamified Dysarthric Speech Therapy & Dual-Stream Multilingual Assistive Intelligence Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[var(--color-neuro-obsidian)] text-white font-sans overflow-x-hidden min-h-screen">
        <MicroCursor />
        
        {/* Global ambient light cone */}
        <div className="fixed top-[-10%] left-1/2 -translate-x-1/2 w-[80vw] h-[80vh] rounded-[100%] bg-[var(--color-neural-indigo)]/10 blur-[120px] pointer-events-none z-[-1]" />

        <div className="flex w-full h-screen">
          <Navigation />
          
          {/* Main Content Area - padded left to account for sidebar */}
          <main className="flex-1 ml-20 md:ml-64 relative overflow-y-auto overflow-x-hidden">
            <PageTransition>
              {children}
            </PageTransition>
          </main>
        </div>
      </body>
    </html>
  );
}
