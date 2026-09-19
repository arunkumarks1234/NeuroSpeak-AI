'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Cpu, Zap, BrainCircuit } from 'lucide-react';

interface TelemetryData {
  latency: number;
  bandwidth: string;
  modelStatus: string;
  confidence: number;
}

export function SystemHardwareCard() {
  const [data, setData] = useState<TelemetryData | null>(null);

  useEffect(() => {
    // Poll telemetry data every second
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('/api/neurospeak/telemetry');
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error("Failed to fetch telemetry", e);
      }
    };
    
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-[var(--color-neural-indigo)]/20 rounded-lg">
          <Cpu className="w-5 h-5 text-[var(--color-neural-indigo)]" />
        </div>
        <h2 className="text-lg font-bold text-white tracking-wide">System Hardware</h2>
      </div>

      <div className="grid grid-cols-2 gap-4 flex-grow">
        <div className="bg-black/30 rounded-xl p-4 flex flex-col justify-between border border-white/5">
          <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold">Latency</span>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-2xl font-mono text-[var(--color-synaptic-cyan)]">
              {data ? data.latency : '--'}
            </span>
            <span className="text-xs text-gray-500">ms</span>
          </div>
        </div>
        
        <div className="bg-black/30 rounded-xl p-4 flex flex-col justify-between border border-white/5">
          <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold">Bandwidth</span>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-2xl font-mono text-[var(--color-signal-violet)]">
              {data ? data.bandwidth : '--'}
            </span>
          </div>
        </div>
        
        <div className="bg-black/30 rounded-xl p-4 col-span-2 border border-white/5 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-neural-indigo)]/10 to-transparent pointer-events-none" />
          <div className="relative z-10 flex justify-between items-center">
            <div className="flex flex-col">
              <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold">Model Status</span>
              <span className="text-sm text-white mt-1 font-mono">{data ? data.modelStatus : 'INITIALIZING...'}</span>
            </div>
            <Activity className="w-6 h-6 text-[var(--color-synaptic-cyan)] opacity-70" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function SpeechSynthesizerCard() {
  const [metrics, setMetrics] = useState({ accuracy: 0, snr: 0, activePhoneme: '' });

  useEffect(() => {
    // Poll synthesizer data
    const fetchSynthesis = async () => {
      try {
        const res = await fetch('/api/neurospeak/synthesize', { method: 'POST' });
        const json = await res.json();
        setMetrics(json);
      } catch (e) {
        console.error("Failed to fetch synthesis", e);
      }
    };
    
    fetchSynthesis();
    const interval = setInterval(fetchSynthesis, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-[var(--color-signal-violet)]/20 rounded-lg">
          <BrainCircuit className="w-5 h-5 text-[var(--color-signal-violet)]" />
        </div>
        <h2 className="text-lg font-bold text-white tracking-wide">Speech Synthesizer</h2>
      </div>

      <div className="flex flex-col gap-4 flex-grow">
        <div className="flex justify-between items-end border-b border-white/10 pb-3">
          <span className="text-sm text-gray-400">Transcription Accuracy</span>
          <span className="text-xl font-mono text-emerald-400">{metrics.accuracy.toFixed(1)}%</span>
        </div>
        
        <div className="flex justify-between items-end border-b border-white/10 pb-3">
          <span className="text-sm text-gray-400">Signal-to-Noise Ratio</span>
          <span className="text-xl font-mono text-white">{metrics.snr} dB</span>
        </div>

        <div className="mt-auto pt-2 bg-black/40 rounded-xl p-4 border border-white/5 flex items-center justify-between">
          <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold flex items-center gap-2">
            <Zap className="w-3 h-3 text-amber-400" /> Active Phoneme
          </span>
          <div className="bg-white/10 px-3 py-1 rounded font-mono text-[var(--color-synaptic-cyan)] text-lg">
            /{metrics.activePhoneme || ' '}/
          </div>
        </div>
      </div>
    </div>
  );
}
