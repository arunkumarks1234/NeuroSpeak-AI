"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Text } from "@react-three/drei";
import * as THREE from "three";

let mouseX = 0;
let mouseY = 0;
if (typeof window !== "undefined") {
  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
  });
}

function TargetRing({
  radius,
  speed,
  color,
  tubeRadius = 0.03,
}: {
  radius: number;
  speed: number;
  color: string;
  tubeRadius?: number;
}) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.z = state.clock.elapsedTime * speed;
    groupRef.current.rotation.x = 0.6 + mouseY * 0.3;
    groupRef.current.rotation.y += (mouseX * 0.5 - groupRef.current.rotation.y) * 0.05;
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <torusGeometry args={[radius, tubeRadius, 32, 200]} />
        <meshStandardMaterial
          color={color}
          metalness={1}
          roughness={0.05}
          transparent
          opacity={0.85}
          emissive={color}
          emissiveIntensity={0.4}
        />
      </mesh>
    </group>
  );
}

function PhonemeLabel({ phoneme, color }: { phoneme: string; color: string }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.rotation.y += (mouseX * 0.3 - groupRef.current.rotation.y) * 0.04;
    groupRef.current.position.y = Math.sin(t * 0.8) * 0.08;
    const pulse = 1 + Math.sin(t * 1.5) * 0.04;
    groupRef.current.scale.setScalar(pulse);
  });

  return (
    <group ref={groupRef}>
      {/* Glow halo */}
      <mesh>
        <sphereGeometry args={[0.7, 32, 32]} />
        <meshStandardMaterial
          color={color}
          transparent
          opacity={0.06}
          roughness={0}
          metalness={0.5}
        />
      </mesh>
      <Text
        fontSize={1.1}
        color={color}
        anchorX="center"
        anchorY="middle"
        font="/fonts/Inter-Bold.ttf"
      >
        {phoneme}
      </Text>
      <Text
        position={[0, -0.9, 0]}
        fontSize={0.22}
        color="rgba(148,163,184,0.8)"
        anchorX="center"
        anchorY="middle"
      >
        Target Phoneme
      </Text>
    </group>
  );
}

function Scene({
  phoneme,
  scoreColor,
}: {
  phoneme: string;
  scoreColor: string;
}) {
  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[0, 0, 4]} color={scoreColor} intensity={4} />
      <pointLight position={[4, 2, 2]} color="#8b5cf6" intensity={2} />
      <pointLight position={[-4, -2, 2]} color="#06b6d4" intensity={1.5} />

      <PhonemeLabel phoneme={phoneme} color={scoreColor} />

      <TargetRing radius={1.6} speed={0.5} color={scoreColor} />
      <TargetRing radius={2.2} speed={-0.3} color="#8b5cf6" tubeRadius={0.025} />
      <TargetRing radius={2.8} speed={0.2} color="#06b6d4" tubeRadius={0.018} />
    </>
  );
}

export default function PhonemeTarget({
  phoneme = "æ",
  scoreColor = "#6366f1",
  className = "",
}: {
  phoneme?: string;
  scoreColor?: string;
  className?: string;
}) {
  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 6], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <Scene phoneme={phoneme} scoreColor={scoreColor} />
      </Canvas>
    </div>
  );
}
