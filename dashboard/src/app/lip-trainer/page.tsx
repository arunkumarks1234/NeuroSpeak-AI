'use client';

import React, { useEffect, useRef, useState } from 'react';
import HUDFrame from '@/components/HUDFrame';
import { Camera, RefreshCw } from 'lucide-react';
// We simulate the MediaPipe import to prevent SSR breakages in Next.js
// In production, this would be imported dynamically or via script tags.

export default function LipTrainerPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isActive, setIsActive] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  useEffect(() => {
    let stream: MediaStream;
    let analysisInterval: NodeJS.Timeout;

    if (isActive) {
      navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
        .then((mediaStream) => {
          stream = mediaStream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
          
          // Mock the FastAPI /api/v1/vision/analyze-lip-frame call
          analysisInterval = setInterval(async () => {
            try {
              const res = await fetch('http://localhost:8000/api/v1/vision/analyze-lip-frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ landmarks: [], expected_phoneme: 'p' })
              });
              const data = await res.json();
              setAnalysis(data);
              drawMockLandmarks();
            } catch (e) {
              console.error(e);
            }
          }, 1000);
        })
        .catch((err) => {
          console.error("Camera access denied", err);
        });
    }

    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
      if (analysisInterval) clearInterval(analysisInterval);
    };
  }, [isActive]);

  const drawMockLandmarks = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#00F2FE';
    ctx.lineWidth = 2;
    
    // Draw a mock bounding box or lips around center
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    
    ctx.beginPath();
    ctx.ellipse(cx, cy + 50, 40, 20, 0, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = '#6366F1';
    // Draw some points
    for (let i = 0; i < 10; i++) {
      ctx.beginPath();
      ctx.arc(cx - 40 + (i * 8), cy + 50 + (Math.sin(i) * 10), 3, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  return (
    <div className="w-full min-h-screen py-8 px-4 md:px-8 flex flex-col gap-8">
      <header className="w-full max-w-7xl mx-auto relative z-10 flex justify-between items-end">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
            Lip Articulation Trainer
          </h1>
          <p className="text-[var(--color-signal-violet)] mt-2 text-sm uppercase tracking-widest font-semibold flex items-center gap-2">
            Target Phoneme: /p/ (Bilabial Plosive)
          </p>
        </div>
        <button 
          onClick={() => setIsActive(!isActive)}
          className={`px-4 py-2 rounded-xl border flex items-center gap-2 font-mono text-sm transition-all ${
            isActive 
            ? 'bg-red-500/20 text-red-400 border-red-500/30' 
            : 'bg-[var(--color-synaptic-cyan)]/20 text-[var(--color-synaptic-cyan)] border-[var(--color-synaptic-cyan)]/30'
          }`}
        >
          {isActive ? 'DEACTIVATE SENSOR' : 'ACTIVATE CAMERA'}
        </button>
      </header>

      <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 relative z-10">
        
        {/* Main Viewport */}
        <div className="col-span-1 lg:col-span-2 flex flex-col gap-6">
          <HUDFrame showGrid={!isActive} className="w-full">
            <div className="w-full h-full relative bg-black/50">
              {!isActive && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
                  <Camera className="w-12 h-12 mb-4 opacity-50" />
                  <span className="font-mono text-sm tracking-widest">FEED OFFLINE</span>
                </div>
              )}
              
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline 
                muted 
                className={`w-full h-full object-cover transition-opacity duration-500 ${isActive ? 'opacity-100' : 'opacity-0'}`}
              />
              <canvas 
                ref={canvasRef} 
                width={1280} 
                height={720}
                className="absolute inset-0 w-full h-full pointer-events-none"
              />
            </div>
          </HUDFrame>
        </div>

        {/* Real-time Telemetry */}
        <div className="col-span-1 flex flex-col gap-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <RefreshCw className={`w-5 h-5 text-[var(--color-synaptic-cyan)] ${isActive ? 'animate-spin' : ''}`} />
              <h2 className="text-lg font-bold tracking-wide">Live Diagnostics</h2>
            </div>

            <div className="flex flex-col gap-4 flex-grow">
              <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold">Aperture Error</span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-mono text-[var(--color-synaptic-cyan)]">
                    {analysis ? analysis.aperture_error.toFixed(2) : '--'}
                  </span>
                  <span className="text-xs text-gray-500">px</span>
                </div>
              </div>

              <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                <span className="text-xs text-gray-400 uppercase tracking-widest font-semibold">Roundness Deviation</span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-mono text-[var(--color-signal-violet)]">
                    {analysis ? analysis.roundness_error.toFixed(2) : '--'}
                  </span>
                  <span className="text-xs text-gray-500">px</span>
                </div>
              </div>

              <div className={`mt-auto p-4 rounded-xl border ${
                !analysis ? 'bg-black/30 border-white/5' : 
                analysis.is_correct ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'
              }`}>
                <span className="text-xs uppercase tracking-widest font-semibold text-gray-400">AI Feedback</span>
                <p className={`mt-2 font-medium ${!analysis ? 'text-gray-500' : analysis.is_correct ? 'text-emerald-400' : 'text-red-400'}`}>
                  {analysis ? analysis.feedback_message : 'Awaiting feed...'}
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
