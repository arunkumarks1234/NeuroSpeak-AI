import React, { useRef, useState, useEffect } from 'react';
import { useMousePhysics } from '@/hooks/useMousePhysics';

interface BentoCardProps {
  children: React.ReactNode;
  className?: string;
}

export function BentoCard({ children, className = '' }: BentoCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const { mousePos } = useMousePhysics();
  const [glowStyle, setGlowStyle] = useState({});

  useEffect(() => {
    if (!cardRef.current) return;
    
    // Request animation frame for smooth tracking
    let rafId: number;
    
    const updateGlow = () => {
      if (cardRef.current) {
        const rect = cardRef.current.getBoundingClientRect();
        
        // Calculate center of glow relative to card
        const x = mousePos.x - rect.left;
        const y = mousePos.y - rect.top;
        
        // Only show glow if mouse is somewhat nearby (e.g. 400px radius)
        const isHovering = 
          mousePos.x > rect.left - 400 && 
          mousePos.x < rect.right + 400 && 
          mousePos.y > rect.top - 400 && 
          mousePos.y < rect.bottom + 400;

        if (isHovering) {
          setGlowStyle({
            background: `radial-gradient(400px circle at ${x}px ${y}px, rgba(79, 70, 229, 0.15), transparent 40%)`
          });
        } else {
          setGlowStyle({});
        }
      }
      rafId = requestAnimationFrame(updateGlow);
    };
    
    rafId = requestAnimationFrame(updateGlow);
    return () => cancelAnimationFrame(rafId);
  }, [mousePos]);

  return (
    <div 
      ref={cardRef}
      className={`relative rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 overflow-hidden group transition-colors duration-300 hover:border-white/20 ${className}`}
    >
      {/* Dynamic Proximity Glow */}
      <div 
        className="absolute inset-0 z-0 pointer-events-none transition-opacity duration-300 opacity-0 group-hover:opacity-100 mix-blend-screen"
        style={glowStyle}
      />
      
      {/* Content wrapper */}
      <div className="relative z-10 h-full w-full">
        {children}
      </div>
    </div>
  );
}

interface BentoGridProps {
  children: React.ReactNode;
}

export default function BentoGrid({ children }: BentoGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 w-full max-w-7xl mx-auto p-6 relative z-10">
      {children}
    </div>
  );
}
