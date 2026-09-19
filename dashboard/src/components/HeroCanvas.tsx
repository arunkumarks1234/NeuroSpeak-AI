import React, { useRef, useState, useEffect } from 'react';
import { useMousePhysics } from '@/hooks/useMousePhysics';

export default function HeroCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { lerpedPos } = useMousePhysics();
  const [frameIndex, setFrameIndex] = useState(1);
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

  useEffect(() => {
    if (dimensions.width > 0) {
      const progress = relativeX / dimensions.width;
      const index = Math.floor(progress * 191) + 1;
      setFrameIndex(Math.max(1, Math.min(index, 192)));
    }
  }, [relativeX, dimensions.width]);

  const centerX = dimensions.width / 2;
  const centerY = dimensions.height / 2;
  const offsetX = relativeX - centerX;
  const offsetY = relativeY - centerY;

  const rotateX = dimensions.height > 0 ? -(offsetY / dimensions.height) * 16 : 0;
  const rotateY = dimensions.width > 0 ? (offsetX / dimensions.width) * 16 : 0;

  const shiftRatioX = dimensions.width > 0 ? offsetX / centerX : 0;
  const shiftRatioY = dimensions.height > 0 ? offsetY / centerY : 0;

  const padNum = String(frameIndex).padStart(3, '0');
  const imgSrc = `/assets/neurospeak/ezgif-frame-${padNum}.jpg`;

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-[400px] lg:h-[500px] rounded-3xl overflow-hidden bg-white/5 backdrop-blur-2xl border border-white/10 shadow-xl flex items-center justify-center group"
      style={{
        perspective: '1200px',
        boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.15)'
      }}
    >
      <div 
        className="w-full h-full relative"
        style={{
          transformStyle: 'preserve-3d',
          transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
          transition: 'transform 0.05s linear'
        }}
      >
        {/* Layer 1: Background Grid */}
        <div 
          className="absolute inset-[-10%] w-[120%] h-[120%] opacity-20 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)',
            backgroundSize: '32px 32px',
            transform: `translate3d(${shiftRatioX * 5}px, ${shiftRatioY * 5}px, -50px)`
          }}
        />

        {/* Layer 2: Main Image */}
        <div 
          className="absolute inset-4 lg:inset-8 rounded-2xl overflow-hidden border border-[rgba(255,255,255,0.08)] bg-black/50 shadow-2xl"
          style={{
            transform: `translate3d(${shiftRatioX * 15}px, ${shiftRatioY * 15}px, 20px)`
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img 
            src={imgSrc} 
            alt="NeuroSpeak AI Stream" 
            className="w-full h-full object-cover mix-blend-screen opacity-90 transition-opacity duration-75"
          />
        </div>

        {/* Layer 3: Overlay Mesh */}
        <div 
          className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.15),transparent_60%)] mix-blend-overlay"
          style={{
            transform: `translate3d(${shiftRatioX * 25}px, ${shiftRatioY * 25}px, 60px)`
          }}
        />
      </div>
      
      {/* Decorative corners */}
      <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-[var(--color-neural-indigo)] opacity-50" />
      <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-[var(--color-synaptic-cyan)] opacity-50" />
      <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-[var(--color-neural-indigo)] opacity-50" />
      <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-[var(--color-synaptic-cyan)] opacity-50" />
    </div>
  );
}
