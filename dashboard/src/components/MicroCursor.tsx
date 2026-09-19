'use client';

import React, { useEffect, useState } from 'react';
import { useMousePhysics } from '@/hooks/useMousePhysics';
import { Crosshair } from 'lucide-react';

export default function MicroCursor() {
  const { lerpedPos, mousePos } = useMousePhysics();
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const handleMouseOver = (e: MouseEvent) => {
      // Basic check for interactive elements
      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === 'img' ||
        target.tagName.toLowerCase() === 'canvas' ||
        target.closest('.group') || // Our cards have group class
        target.tagName.toLowerCase() === 'button' ||
        target.tagName.toLowerCase() === 'a'
      ) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener('mouseover', handleMouseOver);
    return () => window.removeEventListener('mouseover', handleMouseOver);
  }, []);

  return (
    <>
      {/* Outer Dampening Ring (follows lerped position) */}
      <div 
        className="fixed top-0 left-0 w-10 h-10 -ml-5 -mt-5 rounded-full border border-white/20 pointer-events-none z-[9998] transition-transform duration-300 ease-out"
        style={{
          transform: `translate3d(${lerpedPos.x}px, ${lerpedPos.y}px, 0) scale(${isHovering ? 1.5 : 1})`,
          backgroundColor: isHovering ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
          borderColor: isHovering ? 'rgba(6, 182, 212, 0.4)' : 'rgba(255, 255, 255, 0.2)'
        }}
      />
      
      {/* Primary Cursor Dot (follows raw mouse position) */}
      <div 
        className="fixed top-0 left-0 w-2 h-2 -ml-1 -mt-1 bg-white rounded-full pointer-events-none z-[9999] transition-all duration-200"
        style={{
          transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0)`,
          opacity: isHovering ? 0 : 1
        }}
      />

      {/* Reticle for Hover State */}
      <div
        className="fixed top-0 left-0 w-6 h-6 -ml-3 -mt-3 pointer-events-none z-[9999] transition-opacity duration-200 text-[var(--color-synaptic-cyan)]"
        style={{
          transform: `translate3d(${mousePos.x}px, ${mousePos.y}px, 0)`,
          opacity: isHovering ? 1 : 0
        }}
      >
        <Crosshair className="w-full h-full stroke-[1.5px]" />
      </div>
    </>
  );
}
