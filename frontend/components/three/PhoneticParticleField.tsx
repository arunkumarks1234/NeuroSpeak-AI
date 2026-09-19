"use client";

import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Text, Float, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

// ── Mouse tracking store ─────────────────────────────────────────────────────
let mouseX = 0;
let mouseY = 0;

if (typeof window !== "undefined") {
  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
  });
}

// ── IPA phoneme characters ───────────────────────────────────────────────────
const PHONEMES = [
  "æ", "ɛ", "ɪ", "ɒ", "ʌ", "ʊ", "iː", "uː", "ɔː",
  "eɪ", "aɪ", "ɔɪ", "oʊ", "aʊ", "p", "b", "t", "d",
  "k", "g", "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ",
  "h", "m", "n", "ŋ", "l", "r", "j", "w", "tʃ", "dʒ",
];

const COLORS = [
  "#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b",
  "#ec4899", "#a5b4fc", "#67e8f9", "#34d399",
];

// ── Single Phoneme Particle ───────────────────────────────────────────────────
function PhonemeParticle({
  position,
  phoneme,
  color,
  speed,
  offset,
}: {
  position: [number, number, number];
  phoneme: string;
  color: string;
  speed: number;
  offset: number;
}) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime * speed + offset;

    // Orbiting motion
    groupRef.current.position.y = position[1] + Math.sin(t * 0.7) * 0.8;
    groupRef.current.position.x =
      position[0] + Math.cos(t * 0.5) * 0.3 + mouseX * 0.3;
    groupRef.current.position.z =
      position[2] + Math.sin(t * 0.3) * 0.2 + mouseY * 0.2;

    // Rotate to face camera
    groupRef.current.rotation.y = Math.sin(t * 0.4) * 0.3;

    // Pulse scale
    const pulse = 1 + Math.sin(t * 2) * 0.1;
    groupRef.current.scale.setScalar(pulse);
  });

  return (
    <group ref={groupRef} position={position}>
      {/* Glow sphere behind text */}
      <mesh>
        <sphereGeometry args={[0.25, 16, 16]} />
        <meshStandardMaterial
          color={color}
          transparent
          opacity={0.08}
          roughness={0}
          metalness={0.5}
        />
      </mesh>
      <Text
        fontSize={0.3}
        color={color}
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.ttf"
      >
        {phoneme}
      </Text>
    </group>
  );
}

// ── Particle Field ───────────────────────────────────────────────────────────
function ParticleField() {
  const particles = useMemo(() => {
    return Array.from({ length: 40 }, (_, i) => ({
      id: i,
      phoneme: PHONEMES[i % PHONEMES.length],
      color: COLORS[i % COLORS.length],
      position: [
        (Math.random() - 0.5) * 14,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 6 - 2,
      ] as [number, number, number],
      speed: 0.3 + Math.random() * 0.4,
      offset: Math.random() * Math.PI * 2,
    }));
  }, []);

  return (
    <>
      {particles.map((p) => (
        <PhonemeParticle key={p.id} {...p} />
      ))}
    </>
  );
}

// ── Central Neurosphere ───────────────────────────────────────────────────────
function Neurosphere() {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(1.4, 5);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      const z = pos.getZ(i);
      const noise =
        0.08 * Math.sin(x * 3 + y * 2) * Math.cos(z * 2 + x);
      pos.setXYZ(i, x * (1 + noise), y * (1 + noise), z * (1 + noise));
    }
    geo.computeVertexNormals();
    return geo;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const t = state.clock.elapsedTime;

    // Mouse-tracked rotation
    meshRef.current.rotation.y += (mouseX * 0.5 - meshRef.current.rotation.y) * 0.05;
    meshRef.current.rotation.x += (mouseY * 0.3 - meshRef.current.rotation.x) * 0.05;
    meshRef.current.rotation.z = Math.sin(t * 0.2) * 0.1;

    // Color pulse
    if (materialRef.current) {
      const hue = (t * 0.05) % 1;
      materialRef.current.emissive.setHSL(hue, 0.6, 0.1);
    }
  });

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial
        ref={materialRef}
        color="#4338ca"
        metalness={0.8}
        roughness={0.15}
        emissive="#3730a3"
        emissiveIntensity={0.3}
        wireframe={false}
      />
    </mesh>
  );
}

// ── Orbit Ring ───────────────────────────────────────────────────────────────
function OrbitRing({ radius, speed, color }: { radius: number; speed: number; color: string }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.z = state.clock.elapsedTime * speed;
    groupRef.current.rotation.x = 0.4 + mouseY * 0.2;
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <torusGeometry args={[radius, 0.015, 16, 120]} />
        <meshStandardMaterial color={color} metalness={1} roughness={0} transparent opacity={0.6} />
      </mesh>
    </group>
  );
}

// ── Scene Setup ──────────────────────────────────────────────────────────────
function Scene() {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.2} />
      <pointLight position={[5, 5, 5]} color="#6366f1" intensity={3} />
      <pointLight position={[-5, -3, 3]} color="#8b5cf6" intensity={2} />
      <pointLight position={[0, 0, 6]} color="#06b6d4" intensity={1.5} />
      <hemisphereLight groundColor="#050810" color="#4338ca" intensity={0.5} />

      {/* Fog */}
      <fog attach="fog" args={["#050810", 12, 25]} />

      {/* Central sphere */}
      <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
        <Neurosphere />
      </Float>

      {/* Orbit rings */}
      <OrbitRing radius={2.2} speed={0.4} color="#6366f1" />
      <OrbitRing radius={2.8} speed={-0.25} color="#8b5cf6" />
      <OrbitRing radius={3.4} speed={0.15} color="#06b6d4" />

      {/* Phoneme particles */}
      <ParticleField />
    </>
  );
}

// ── Main Export ──────────────────────────────────────────────────────────────
export default function PhoneticParticleField({ className = "" }: { className?: string }) {
  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
