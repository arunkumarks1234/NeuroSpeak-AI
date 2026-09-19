'use client';

import React, { useRef, useEffect } from 'react';
import { useMousePhysics } from '@/hooks/useMousePhysics';

export default function WaveformVisualizer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { lerpedPos } = useMousePhysics();
  const lastPos = useRef({ x: 0, y: 0 });
  const velocity = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    const resize = () => {
      // Setup for high DPI displays
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    window.addEventListener('resize', resize);
    resize();

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      // Calculate pseudo-velocity based on lerpedPos change
      const dx = lerpedPos.x - lastPos.current.x;
      const dy = lerpedPos.y - lastPos.current.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      // Smooth velocity
      velocity.current = velocity.current * 0.9 + Math.min(dist * 0.5, 50) * 0.1;
      lastPos.current = { x: lerpedPos.x, y: lerpedPos.y };

      ctx.clearRect(0, 0, width, height);
      
      // Draw 3 overlaying waves for depth
      const waves = [
        { amp: 20 + velocity.current, freq: 0.02, phase: time * 0.05, color: 'rgba(6, 182, 212, 0.5)' }, // Cyan
        { amp: 15 + velocity.current * 0.8, freq: 0.03, phase: time * 0.07 + 2, color: 'rgba(79, 70, 229, 0.5)' }, // Indigo
        { amp: 10 + velocity.current * 0.5, freq: 0.04, phase: time * 0.09 + 4, color: 'rgba(168, 85, 247, 0.4)' }, // Violet
      ];

      waves.forEach(w => {
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        
        for (let i = 0; i < width; i += 2) {
          // Add a window function (hanning-like) so edges taper to zero
          const windowFunc = Math.sin((i / width) * Math.PI);
          const y = height / 2 + Math.sin(i * w.freq + w.phase) * w.amp * windowFunc;
          ctx.lineTo(i, y);
        }
        
        ctx.strokeStyle = w.color;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.stroke();
      });

      time++;
      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationId);
    };
  }, [lerpedPos.x, lerpedPos.y]); // update dependencies

  return (
    <div className="w-full h-full min-h-[150px] relative glass-panel rounded-2xl p-4 overflow-hidden flex flex-col justify-between">
      <div className="flex justify-between items-center z-10">
        <h3 className="text-sm font-semibold tracking-wider text-[var(--color-synaptic-cyan)]">Neural Telemetry</h3>
        <div className="flex gap-1 items-center">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-synaptic-cyan)] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-synaptic-cyan)]"></span>
          </span>
          <span className="text-xs text-gray-400 font-mono ml-2">LIVE</span>
        </div>
      </div>
      
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none mt-4">
        <canvas 
          ref={canvasRef} 
          className="w-full h-full"
          style={{ filter: 'drop-shadow(0 0 8px rgba(79,70,229,0.5))' }}
        />
      </div>
      
      <div className="z-10 flex justify-between text-xs font-mono text-gray-500 mt-auto pt-2">
        <span>0.00 Hz</span>
        <span>10.00 kHz</span>
      </div>
    </div>
  );
}
