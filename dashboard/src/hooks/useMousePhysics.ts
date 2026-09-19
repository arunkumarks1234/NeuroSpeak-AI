'use client';

import { useState, useEffect, useRef } from 'react';

export function useMousePhysics() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [lerpedPos, setLerpedPos] = useState({ x: 0, y: 0 });

  const requestRef = useRef<number | null>(null);
  const targetPos = useRef({ x: 0, y: 0 });
  const currentPos = useRef({ x: 0, y: 0 });

  // Lerp factor
  const LERP_FACTOR = 0.12;

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      targetPos.current = { x: e.clientX, y: e.clientY };
      setMousePos({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);

    const animate = () => {
      // Apply Lerp
      currentPos.current.x += (targetPos.current.x - currentPos.current.x) * LERP_FACTOR;
      currentPos.current.y += (targetPos.current.y - currentPos.current.y) * LERP_FACTOR;

      setLerpedPos({
        x: currentPos.current.x,
        y: currentPos.current.y,
      });

      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, []);

  return { mousePos, lerpedPos };
}
