'use client';

import React, { useState } from 'react';
import HUDFrame from '@/components/HUDFrame';
import { Mic, Globe, Play, Square, Activity } from 'lucide-react';

export default function TranslatePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRecordToggle = async () => {
    if (isRecording) {
      setIsRecording(false);
      setIsProcessing(true);
      // Simulate hitting our FastAPI backend
      try {
        const res = await fetch('http://localhost:8000/api/v1/speech/decipher', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ audio_blob_base64: 'mock', source_language: 'kn' })
        });
        const data = await res.json();
        setResult(data);
      } catch (e) {
        console.error("Backend error", e);
      } finally {
        setIsProcessing(false);
      }
    } else {
      setIsRecording(true);
      setResult(null);
    }
  };

  return (
    <div className="w-full min-h-screen py-8 px-4 md:px-8 flex flex-col gap-8">
      <header className="w-full max-w-7xl mx-auto relative z-10">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
          Dysarthric Deciphering Suite
        </h1>
        <p className="text-[var(--color-synaptic-cyan)] mt-2 text-sm uppercase tracking-widest font-semibold flex items-center gap-2">
          Kannada ⇄ English
        </p>
      </header>

      <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10">
        
        {/* Input Column */}
        <div className="flex flex-col gap-6">
          <HUDFrame showGrid={true} className="h-64">
            <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-black/40 backdrop-blur-md">
              <button 
                onClick={handleRecordToggle}
                className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isRecording 
                  ? 'bg-red-500/20 text-red-500 border-2 border-red-500 animate-pulse' 
                  : 'bg-[var(--color-neural-indigo)]/20 text-[var(--color-neural-indigo)] border border-[var(--color-neural-indigo)] hover:bg-[var(--color-neural-indigo)]/40'
                }`}
              >
                {isRecording ? <Square className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
              </button>
              <span className="mt-4 text-sm font-mono text-gray-400">
                {isRecording ? 'RECORDING VERNACULAR DYSARTHRIC AUDIO...' : 'TAP TO RECORD'}
              </span>
            </div>
          </HUDFrame>
          
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <h3 className="text-sm font-semibold tracking-wider text-[var(--color-synaptic-cyan)] mb-4">Input Parameters</h3>
            <div className="flex justify-between items-center bg-black/30 p-4 rounded-xl border border-white/5">
              <span className="text-sm text-gray-400 font-mono">Source Language</span>
              <span className="text-white font-mono flex items-center gap-2">
                <Globe className="w-4 h-4 text-[var(--color-signal-violet)]" />
                Kannada (kn-IN)
              </span>
            </div>
          </div>
        </div>

        {/* Output Column */}
        <div className="flex flex-col gap-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl h-full flex flex-col relative overflow-hidden">
            {isProcessing && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm">
                <Activity className="w-12 h-12 text-[var(--color-synaptic-cyan)] animate-spin" />
                <span className="mt-4 font-mono text-sm tracking-widest text-[var(--color-synaptic-cyan)]">RUNNING INFERENCE MATRIX...</span>
              </div>
            )}
            
            <h3 className="text-sm font-semibold tracking-wider text-emerald-400 mb-6">Deciphered Matrix</h3>
            
            <div className="flex-1 flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <span className="text-xs text-gray-500 font-mono uppercase">Raw Phoneme Map</span>
                <div className="p-4 bg-black/40 rounded-xl font-mono text-gray-300 border border-white/5 text-lg min-h-[60px]">
                  {result ? result.active_phoneme : '...'}
                </div>
              </div>
              
              <div className="flex flex-col gap-2">
                <span className="text-xs text-gray-500 font-mono uppercase">Deciphered (Kannada)</span>
                <div className="p-4 bg-[var(--color-neural-indigo)]/10 rounded-xl font-sans text-white border border-[var(--color-neural-indigo)]/30 text-lg min-h-[60px]">
                  {result ? result.deciphered_text : '...'}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs text-gray-500 font-mono uppercase">Synthesized (English)</span>
                <div className="p-4 bg-emerald-500/10 rounded-xl font-sans text-white border border-emerald-500/30 text-lg min-h-[60px] flex justify-between items-center">
                  <span>{result ? result.translated_text : '...'}</span>
                  {result && (
                    <button className="p-2 rounded-full bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40 transition-colors">
                      <Play className="w-5 h-5 fill-current" />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {result && (
              <div className="mt-6 flex justify-between items-center border-t border-white/10 pt-4">
                <span className="text-xs text-gray-400 font-mono">Clarity Confidence</span>
                <span className="text-sm font-mono text-emerald-400">{result.clarity_score.toFixed(1)}%</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
