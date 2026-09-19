'use client';

import React, { useRef, useState, useEffect } from 'react';
import { useMousePhysics } from '@/hooks/useMousePhysics';

interface HUDFrameProps {
  children: React.ReactNode;
  className?: string;
  showGrid?: boolean;
}

export default function HUDFrame({ children, className = '', showGrid = true }: HUDFrameProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { lerpedPos } = useMousePhysics();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0, left: 0, top: 0 });

  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setDimensions({ width: rect.width, height: rect.height, left: rect.left, top: rect.top });
      
      const handleResize = () => {
        const r = containerRef.current?.getBoundingClientRect();
        if (r) setDimensions({ width: r.width, height: r.height, left: r.left, top: r.top });
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  const relativeX = Math.max(0, Math.min(lerpedPos.x - dimensions.left, dimensions.width));
  const relativeY = Math.max(0, Math.min(lerpedPos.y - dimensions.top, dimensions.height));

  const centerX = dimensions.width / 2;
  const centerY = dimensions.height / 2;
  const offsetX = relativeX - centerX;
  const offsetY = relativeY - centerY;

  const rotateX = dimensions.height > 0 ? -(offsetY / dimensions.height) * 8 : 0;
  const rotateY = dimensions.width > 0 ? (offsetX / dimensions.width) * 8 : 0;

  return (
    <div 
      ref={containerRef}
      className={`relative w-full aspect-video rounded-xl bg-black overflow-hidden flex items-center justify-center ${className}`}
      style={{
        perspective: '1200px',
        boxShadow: '0 0 30px rgba(0,0,0,0.8) inset, 0 10px 40px -10px rgba(79,70,229,0.3)'
      }}
    >
      <div 
        className="w-full h-full relative"
        style={{
          transformStyle: 'preserve-3d',
          transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(0.95)`,
          transition: 'transform 0.05s linear'
        }}
      >
        {/* Layer 1: Optional Grid */}
        {showGrid && (
          <div 
            className="absolute inset-0 w-full h-full opacity-10 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.5) 1px, transparent 0)',
              backgroundSize: '24px 24px',
              transform: `translateZ(-50px)`
            }}
          />
        )}

        {/* Layer 2: Main Content */}
        <div 
          className="absolute inset-0 z-10 rounded-lg overflow-hidden border border-[rgba(255,255,255,0.1)]"
          style={{ transform: 'translateZ(0px)' }}
        >
          {children}
        </div>

        {/* HUD Targeting Brackets */}
        <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-[var(--color-synaptic-cyan)] opacity-70 z-20 transition-all duration-300 transform -translate-x-1 -translate-y-1" style={{ transform: 'translateZ(20px)' }} />
        <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-[var(--color-neural-indigo)] opacity-70 z-20 transition-all duration-300 transform translate-x-1 -translate-y-1" style={{ transform: 'translateZ(20px)' }} />
        <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-[var(--color-neural-indigo)] opacity-70 z-20 transition-all duration-300 transform -translate-x-1 translate-y-1" style={{ transform: 'translateZ(20px)' }} />
        <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-[var(--color-synaptic-cyan)] opacity-70 z-20 transition-all duration-300 transform translate-x-1 translate-y-1" style={{ transform: 'translateZ(20px)' }} />
        
        {/* Reticle Overlay */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-30 z-20 mix-blend-screen" style={{ transform: 'translateZ(40px)' }}>
          <div className="w-[40%] h-[40%] border border-[var(--color-signal-violet)]/30 rounded-full border-dashed" />
          <div className="absolute w-[2px] h-[5%] bg-[var(--color-synaptic-cyan)]/50 top-1/4" />
          <div className="absolute w-[2px] h-[5%] bg-[var(--color-synaptic-cyan)]/50 bottom-1/4" />
          <div className="absolute w-[5%] h-[2px] bg-[var(--color-synaptic-cyan)]/50 left-1/4" />
          <div className="absolute w-[5%] h-[2px] bg-[var(--color-synaptic-cyan)]/50 right-1/4" />
        </div>
      </div>
    </div>
  );
}
