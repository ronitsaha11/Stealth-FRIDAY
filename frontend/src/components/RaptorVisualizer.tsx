"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, MeshDistortMaterial, Float, Stars } from "@react-three/drei";
import * as THREE from "three";

export type RaptorState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING';

interface OrbProps {
  state: RaptorState;
}

function RaptorOrb({ state }: OrbProps) {
  const mesh = useRef<THREE.Mesh>(null!);
  
  // Dynamic parameters based on state
  const getParams = () => {
    switch (state) {
      case 'LISTENING':
        return { color: "#3b82f6", speed: 4, distort: 0.6, scale: 1.1, rotSpeed: 0.5 };
      case 'PROCESSING':
        return { color: "#eab308", speed: 8, distort: 0.8, scale: 0.9, rotSpeed: 2.0 };
      case 'SPEAKING':
        return { color: "#22c55e", speed: 6, distort: 0.7, scale: 1.2, rotSpeed: 1.0 };
      case 'IDLE':
      default:
        return { color: "#00f2ff", speed: 2, distort: 0.3, scale: 1.0, rotSpeed: 0.2 };
    }
  };

  const params = getParams();

  useFrame((rootState) => {
    if (!mesh.current) return;
    const t = rootState.clock.getElapsedTime();
    
    // Rotate
    mesh.current.rotation.x = t * params.rotSpeed;
    mesh.current.rotation.y = t * params.rotSpeed * 1.5;
    
    // Smoothly interpolate scale
    const targetScale = params.scale + (state === 'LISTENING' ? Math.sin(t * 5) * 0.05 : 0);
    mesh.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
  });

  return (
    <Float speed={state === 'PROCESSING' ? 4 : 2} rotationIntensity={1} floatIntensity={1.5}>
      <Sphere ref={mesh} args={[1, 64, 64]}>
        <MeshDistortMaterial
          color={params.color}
          speed={params.speed}
          distort={params.distort}
          radius={1}
          emissive={params.color}
          emissiveIntensity={1.5}
          metalness={0.8}
          roughness={0.2}
        />
      </Sphere>
    </Float>
  );
}

interface VisualizerProps {
  state: RaptorState;
}

export default function RaptorVisualizer({ state }: VisualizerProps) {
  return (
    <div className="w-full h-full min-h-[400px] relative pointer-events-none">
      <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={2} color="#ffffff" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#ffffff" />
        
        <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={state === 'PROCESSING'? 3 : 1} />
        
        <RaptorOrb state={state} />
        
        {/* Decorative rings */}
        <mesh rotation-x={Math.PI / 2}>
           <torusGeometry args={[2.5, 0.01, 16, 100]} />
           <meshBasicMaterial color="#ffffff" transparent opacity={0.1} />
        </mesh>
        
        {/* Inner Waveform ring for LISTENING */}
        {state === 'LISTENING' && (
           <mesh rotation-x={Math.PI / 2} position={[0, 0, 0]}>
             <torusGeometry args={[1.5, 0.02, 16, 100]} />
             <meshBasicMaterial color="#3b82f6" transparent opacity={0.5} />
           </mesh>
        )}
      </Canvas>
    </div>
  );
}
