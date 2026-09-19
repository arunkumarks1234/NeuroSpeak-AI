"use client";

import { useRef, useEffect, useCallback } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

// ── Waveform Ring ─────────────────────────────────────────────────────────────
function WaveformRing({
  analyser,
  radius,
  color,
}: {
  analyser: React.MutableRefObject<AnalyserNode | null>;
  radius: number;
  color: string;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const dataRef = useRef<Uint8Array | null>(null);

  const SEGMENTS = 128;

  const geometry = useRef(new THREE.BufferGeometry());
  const positions = useRef(new Float32Array(SEGMENTS * 3));

  useEffect(() => {
    if (analyser.current) {
      dataRef.current = new Uint8Array(analyser.current.frequencyBinCount);
    }
  }, [analyser]);

  useFrame(() => {
    if (!analyser.current || !dataRef.current) {
      // Idle animation
      for (let i = 0; i < SEGMENTS; i++) {
        const angle = (i / SEGMENTS) * Math.PI * 2;
        positions.current[i * 3] = Math.cos(angle) * radius;
        positions.current[i * 3 + 1] = Math.sin(angle) * radius;
        positions.current[i * 3 + 2] = Math.sin(Date.now() * 0.001 + i * 0.2) * 0.05;
      }
    } else {
      analyser.current.getByteFrequencyData(dataRef.current);
      for (let i = 0; i < SEGMENTS; i++) {
        const dataIndex = Math.floor((i / SEGMENTS) * dataRef.current.length);
        const value = (dataRef.current[dataIndex] / 255) * 1.5;
        const angle = (i / SEGMENTS) * Math.PI * 2;
        const r = radius + value * 0.8;
        positions.current[i * 3] = Math.cos(angle) * r;
        positions.current[i * 3 + 1] = Math.sin(angle) * r;
        positions.current[i * 3 + 2] = value * 0.3;
      }
    }

    geometry.current.setAttribute(
      "position",
      new THREE.BufferAttribute(positions.current, 3)
    );
    geometry.current.setDrawRange(0, SEGMENTS);
    geometry.current.attributes.position.needsUpdate = true;
  });

  return (
    <points geometry={geometry.current}>
      <pointsMaterial
        color={color}
        size={0.04}
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

// ── Central Pulse Sphere ───────────────────────────────────────────────────────
function PulseSphere({
  analyser,
}: {
  analyser: React.MutableRefObject<AnalyserNode | null>;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const dataRef = useRef<Uint8Array | null>(null);

  useEffect(() => {
    if (analyser.current) {
      dataRef.current = new Uint8Array(analyser.current.frequencyBinCount);
    }
  }, [analyser]);

  useFrame((state) => {
    if (!meshRef.current) return;

    let amplitude = 0;
    if (analyser.current && dataRef.current) {
      analyser.current.getByteTimeDomainData(dataRef.current);
      const sum = dataRef.current.reduce((a, b) => a + Math.abs(b - 128), 0);
      amplitude = sum / dataRef.current.length / 128;
    }

    const t = state.clock.elapsedTime;
    const scale = 0.3 + amplitude * 0.8 + Math.sin(t * 2) * 0.03;
    meshRef.current.scale.setScalar(scale);

    const mat = meshRef.current.material as THREE.MeshStandardMaterial;
    const intensity = 0.3 + amplitude * 2;
    mat.emissiveIntensity = intensity;
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[0.5, 32, 32]} />
      <meshStandardMaterial
        color="#6366f1"
        metalness={0.9}
        roughness={0.1}
        emissive="#818cf8"
        emissiveIntensity={0.5}
        transparent
        opacity={0.9}
      />
    </mesh>
  );
}

// ── Scene ────────────────────────────────────────────────────────────────────
function WaveScene({
  analyser,
  scoreColor,
}: {
  analyser: React.MutableRefObject<AnalyserNode | null>;
  scoreColor: string;
}) {
  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[0, 0, 3]} color={scoreColor} intensity={3} />
      <pointLight position={[3, 3, 1]} color="#8b5cf6" intensity={2} />

      <PulseSphere analyser={analyser} />
      <WaveformRing analyser={analyser} radius={1.2} color={scoreColor} />
      <WaveformRing analyser={analyser} radius={1.8} color="#8b5cf6" />
      <WaveformRing analyser={analyser} radius={2.4} color="#06b6d4" />
    </>
  );
}

// ── Main Export ──────────────────────────────────────────────────────────────
export default function WaveformVisualizer({
  analyser,
  scoreColor = "#6366f1",
  className = "",
}: {
  analyser: React.MutableRefObject<AnalyserNode | null>;
  scoreColor?: string;
  className?: string;
}) {
  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 55 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <WaveScene analyser={analyser} scoreColor={scoreColor} />
      </Canvas>
    </div>
  );
}
