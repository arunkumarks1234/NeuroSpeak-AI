'use client';

import React, { useState } from 'react';
import HeroCanvas from '@/components/HeroCanvas';
import BentoGrid, { BentoCard } from '@/components/BentoGrid';
import WaveformVisualizer from '@/components/WaveformVisualizer';
import { SystemHardwareCard, SpeechSynthesizerCard } from '@/components/MetricsCards';

export default function Dashboard() {
  const [streak] = useState(14);
  const [xp] = useState(4200);

  return (
    <div className="w-full min-h-screen py-8 px-4 md:px-8 flex flex-col gap-8">
      
      {/* Header */}
      <header className="w-full max-w-7xl mx-auto relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl md:text-5xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
            Patient Command Hub
          </h1>
          <p className="text-[var(--color-synaptic-cyan)] mt-2 text-sm uppercase tracking-widest font-semibold flex items-center gap-2">
            Patient ID: NS-9982 • Dr. Aris Thorne
          </p>
        </div>
        <div className="flex gap-4">
          <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-mono backdrop-blur-md flex items-center gap-2 text-orange-400">
            🔥 {streak} Day Streak
          </div>
          <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-mono backdrop-blur-md flex items-center gap-2 text-[var(--color-signal-violet)]">
            ✨ {xp} XP
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <BentoGrid>
        {/* Central Hero Canvas */}
        <div className="col-span-1 md:col-span-12 lg:col-span-8 flex flex-col gap-6">
          <HeroCanvas />
        </div>

        {/* Right Side Cards */}
        <div className="col-span-1 md:col-span-12 lg:col-span-4 flex flex-col gap-6">
          <BentoCard className="flex-1">
            <SystemHardwareCard />
          </BentoCard>
          
          <BentoCard className="flex-1">
            <SpeechSynthesizerCard />
          </BentoCard>
        </div>

        {/* Bottom Wide Visualizer */}
        <BentoCard className="col-span-1 md:col-span-12 h-64">
          <WaveformVisualizer />
        </BentoCard>
      </BentoGrid>
    </div>
  );
}
