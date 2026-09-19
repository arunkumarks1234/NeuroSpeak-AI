'use client';

import React, { useEffect, useState } from 'react';
import { ActivitySquare, TrendingUp, Users } from 'lucide-react';

export default function ClinicalPortalPage() {
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/doctor/patients/NS-9982/analytics')
      .then(res => res.json())
      .then(data => setAnalytics(data))
      .catch(err => console.error("Failed to load analytics", err));
  }, []);

  return (
    <div className="w-full min-h-screen py-8 px-4 md:px-8 flex flex-col gap-8">
      <header className="w-full max-w-7xl mx-auto relative z-10 flex justify-between items-end">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
            Clinical Analytics Portal
          </h1>
          <p className="text-[var(--color-neural-indigo)] mt-2 text-sm uppercase tracking-widest font-semibold flex items-center gap-2">
            <Users className="w-4 h-4" /> Doctor View
          </p>
        </div>
        <div className="px-4 py-2 rounded-xl bg-[var(--color-neural-indigo)]/20 border border-[var(--color-neural-indigo)]/50 text-[var(--color-neural-indigo)] font-mono text-sm font-bold">
          Dr. Aris Thorne
        </div>
      </header>

      <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10">
        
        {/* Patient Selection & Overview */}
        <div className="col-span-1 flex flex-col gap-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl h-full">
            <h2 className="text-lg font-bold tracking-wide mb-6">Patient: NS-9982</h2>
            
            <div className="flex flex-col gap-4">
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <span className="text-xs text-gray-500 font-mono uppercase">Primary Diagnosis</span>
                <p className="mt-1 font-semibold text-white">Spastic Dysarthria</p>
              </div>
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <span className="text-xs text-gray-500 font-mono uppercase">Last Session Notes</span>
                <p className="mt-1 text-sm text-gray-300 leading-relaxed">
                  Patient showed marked improvement in bilabial plosives. Recommended increasing lip articulation quests frequency.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Historical Analytics Chart */}
        <div className="col-span-1 flex flex-col gap-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold tracking-wide">Speech Intelligibility Index</h2>
            </div>
            
            <div className="flex-1 flex items-end gap-2 mt-4 bg-black/20 p-4 rounded-xl border border-white/5 h-48">
              {!analytics ? (
                <div className="w-full h-full flex items-center justify-center text-gray-500 font-mono text-sm">
                  LOADING TELEMETRY...
                </div>
              ) : (
                analytics.historical_clarity.map((score: number, idx: number) => (
                  <div key={idx} className="flex-1 flex flex-col justify-end items-center gap-2 group">
                    <span className="text-[10px] font-mono text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      {score.toFixed(0)}
                    </span>
                    <div 
                      className="w-full bg-gradient-to-t from-emerald-500/20 to-emerald-400 rounded-t-sm transition-all duration-500 hover:brightness-125"
                      style={{ height: `${score}%` }}
                    />
                    <span className="text-[10px] text-gray-600 font-mono whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
                      {analytics.dates[idx].split('-')[2]}
                    </span>
                  </div>
                ))
              )}
            </div>
            
            <div className="mt-4 flex justify-between items-center px-2">
              <span className="text-xs text-gray-500 font-mono">Past 7 Days</span>
              <span className="text-xs text-emerald-400 font-mono">Target: >85%</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
