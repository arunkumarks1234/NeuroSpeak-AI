'use client';

import React from 'react';
import { Gamepad2, Shield, Star, Zap } from 'lucide-react';

export default function QuestsPage() {
  const quests = [
    { title: 'Vowel Voyager', desc: 'Hold /a/ and /e/ for 5 seconds.', xp: 200, status: 'completed' },
    { title: 'Plosive Punch', desc: 'Accurately articulate 10 /p/ and /b/ sounds.', xp: 350, status: 'active' },
    { title: 'Fricative Flow', desc: 'Navigate the pitch-controlled obstacle course using /s/ and /f/.', xp: 500, status: 'locked' }
  ];

  return (
    <div className="w-full min-h-screen py-8 px-4 md:px-8 flex flex-col gap-8">
      <header className="w-full max-w-7xl mx-auto relative z-10">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
          Articulation Quests
        </h1>
        <p className="text-amber-400 mt-2 text-sm uppercase tracking-widest font-semibold flex items-center gap-2">
          <Star className="w-4 h-4 fill-current" /> Daily Challenges & XP
        </p>
      </header>

      <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 relative z-10">
        
        <div className="col-span-1 lg:col-span-2 flex flex-col gap-6">
          {quests.map((q, i) => (
            <div key={i} className={`p-6 rounded-2xl border backdrop-blur-xl flex justify-between items-center ${
              q.status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/30 opacity-70' :
              q.status === 'active' ? 'bg-[var(--color-neural-indigo)]/20 border-[var(--color-neural-indigo)]/50' :
              'bg-white/5 border-white/10 opacity-50 grayscale'
            }`}>
              <div className="flex flex-col gap-2">
                <h3 className="font-bold text-lg">{q.title}</h3>
                <p className="text-sm text-gray-400">{q.desc}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className="font-mono text-amber-400 font-bold">+{q.xp} XP</span>
                <button className={`px-4 py-2 rounded-lg font-mono text-xs ${
                  q.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                  q.status === 'active' ? 'bg-[var(--color-synaptic-cyan)] text-black font-bold' :
                  'bg-white/10 text-gray-400'
                }`}>
                  {q.status === 'completed' ? 'CLAIMED' : q.status === 'active' ? 'START QUEST' : 'LOCKED'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-1 flex flex-col gap-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <h2 className="text-lg font-bold tracking-wide mb-6">Player Stats</h2>
            
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-amber-400" />
                <span className="text-gray-400 font-semibold">Total XP</span>
              </div>
              <span className="font-mono text-xl font-bold">4,200</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-[var(--color-synaptic-cyan)]" />
                <span className="text-gray-400 font-semibold">Streak Shields</span>
              </div>
              <span className="font-mono text-xl font-bold text-[var(--color-synaptic-cyan)]">2 / 3</span>
            </div>
            
            <div className="mt-8 relative w-full h-32 bg-black/40 rounded-xl overflow-hidden border border-white/5 flex items-center justify-center">
               <Gamepad2 className="w-12 h-12 text-white/20" />
               <span className="absolute bottom-2 text-xs font-mono text-gray-500 tracking-widest">MINIGAME PREVIEW</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
