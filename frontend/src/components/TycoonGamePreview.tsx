import { useState, useEffect, useRef } from 'react';
import { Coins, TrendingUp, Building2, Zap, ChevronRight, ExternalLink, Copy, Play, Square } from 'lucide-react';
import { GenerationResponse } from '../services/api';

interface Upgrade {
  id: string;
  name: string;
  description: string;
  cost: number;
  level: number;
  effect: string;
  icon: string;
}

interface TycoonGamePreviewProps {
  result: GenerationResponse | null;
}

export default function TycoonGamePreview({ result }: TycoonGamePreviewProps) {
  const [money, setMoney] = useState(100);
  const [moneyPerSecond, setMoneyPerSecond] = useState(0);
  const [clickPower, setClickPower] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false); // Game only runs when actively playing
  const [upgrades, setUpgrades] = useState<Upgrade[]>([
    {
      id: 'generator',
      name: 'Money Generator',
      description: 'Increases money per second',
      cost: 50,
      level: 0,
      effect: '+1/sec',
      icon: '💰'
    },
    {
      id: 'click',
      name: 'Click Power',
      description: 'Doubles money from clicks',
      cost: 100,
      level: 0,
      effect: '2x clicks',
      icon: '⚡'
    },
    {
      id: 'base',
      name: 'Base Expansion',
      description: 'Expands your tycoon base',
      cost: 200,
      level: 0,
      effect: '+1 building',
      icon: '🏢'
    },
    {
      id: 'factory',
      name: 'Factory',
      description: 'Massive income boost',
      cost: 500,
      level: 0,
      effect: '+5/sec',
      icon: '🏭'
    }
  ]);
  const [buildings, setBuildings] = useState(1);
  const [clickEffects, setClickEffects] = useState<Array<{id: number, x: number, y: number}>>([]);
  const clickEffectId = useRef(0);
  const gameAreaRef = useRef<HTMLDivElement>(null);

  // Automatic money generation - ONLY when playing
  useEffect(() => {
    if (!isPlaying || moneyPerSecond <= 0) return;
    
    const interval = setInterval(() => {
      setMoney(prev => prev + moneyPerSecond);
    }, 1000);

    return () => clearInterval(interval);
  }, [moneyPerSecond, isPlaying]);

  // Handle generator clicks
  const handleGeneratorClick = (event: React.MouseEvent) => {
    const rect = gameAreaRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Add click effect
    const newEffect = {
      id: clickEffectId.current++,
      x,
      y
    };
    setClickEffects(prev => [...prev, newEffect]);

    // Remove effect after animation
    setTimeout(() => {
      setClickEffects(prev => prev.filter(e => e.id !== newEffect.id));
    }, 1000);

    // Add money
    setMoney(prev => prev + clickPower);

    // Visual feedback
    if (gameAreaRef.current) {
      gameAreaRef.current.style.transform = 'scale(0.98)';
      setTimeout(() => {
        if (gameAreaRef.current) {
          gameAreaRef.current.style.transform = 'scale(1)';
        }
      }, 100);
    }
  };

  // Buy upgrade
  const buyUpgrade = (upgradeId: string) => {
    const upgrade = upgrades.find(u => u.id === upgradeId);
    if (!upgrade || money < upgrade.cost) return;

    setMoney(prev => prev - upgrade.cost);

    const updatedUpgrades = upgrades.map(u => {
      if (u.id === upgradeId) {
        const newLevel = u.level + 1;
        let newCost = Math.floor(u.cost * 1.5);
        let newEffect = u.effect;

        // Apply upgrade effects
        if (u.id === 'generator') {
          setMoneyPerSecond(prev => prev + 1);
          newEffect = `+${newLevel + 1}/sec`;
        } else if (u.id === 'click') {
          setClickPower(prev => prev * 2);
          newEffect = `${Math.pow(2, newLevel + 1)}x clicks`;
        } else if (u.id === 'base') {
          setBuildings(prev => prev + 1);
          newEffect = `${newLevel + 1} buildings`;
        } else if (u.id === 'factory') {
          setMoneyPerSecond(prev => prev + 5);
          newEffect = `+${(newLevel + 1) * 5}/sec`;
        }

        return {
          ...u,
          level: newLevel,
          cost: newCost,
          effect: newEffect
        };
      }
      return u;
    });

    setUpgrades(updatedUpgrades);
  };

  const gameTitle = result?.title || 'Tycoon Game';
  const [showRobloxInstructions, setShowRobloxInstructions] = useState(false);

  const handleCopyToRoblox = () => {
    if (result?.lua_script) {
      navigator.clipboard.writeText(result.lua_script);
      setShowRobloxInstructions(true);
      setTimeout(() => setShowRobloxInstructions(false), 5000);
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-robotic-darker rounded-lg overflow-hidden" style={{
      background: 'linear-gradient(135deg, #0a0f1a 0%, #0f172a 100%)'
    }}>
      {/* Game Header */}
      <div className="flex items-center justify-between p-4 border-b border-robotic-cyan/30 bg-robotic-darker">
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 border border-robotic-cyan rounded-lg bg-robotic-dark/30 shadow-lg" style={{
            boxShadow: '0 0 10px rgba(15, 245, 255, 0.3), inset 0 0 10px rgba(15, 245, 255, 0.1)'
          }}>
            <span className="text-robotic-cyan font-mono text-sm font-semibold tracking-wide">{gameTitle}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Play/Pause Button */}
          {!isPlaying ? (
            <button
              onClick={() => setIsPlaying(true)}
              className="px-4 py-2 bg-robotic-green text-robotic-bg rounded-md text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
              title="Start playing the game"
            >
              <Play className="w-4 h-4" />
              Play
            </button>
          ) : (
            <button
              onClick={() => setIsPlaying(false)}
              className="px-4 py-2 bg-robotic-magenta text-white rounded-md text-sm font-semibold hover:bg-robotic-magenta/90 transition-all flex items-center gap-2"
              title="Pause the game"
            >
              <Square className="w-4 h-4" />
              Pause
            </button>
          )}
          <button
            onClick={handleCopyToRoblox}
            className="px-4 py-2 border border-robotic-cyan/30 text-robotic-cyan rounded-md text-sm font-semibold hover:bg-robotic-cyan/10 transition-all flex items-center gap-2"
            title="Copy code and open Roblox Studio"
          >
            {showRobloxInstructions ? (
              <>
                <Copy className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <ExternalLink className="w-4 h-4" />
                Play in Roblox
              </>
            )}
          </button>
          <div className="flex items-center gap-2 px-3 py-1.5 border border-robotic-cyan/30 rounded-md bg-robotic-dark/30">
            <Coins className="w-4 h-4 text-robotic-green" />
            <span className="text-robotic-cyan font-mono font-bold text-lg">{money.toLocaleString()}</span>
          </div>
          {moneyPerSecond > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 border border-robotic-green/30 rounded-md bg-robotic-dark/30">
              <TrendingUp className="w-4 h-4 text-robotic-green" />
              <span className="text-robotic-green font-mono text-sm">+{moneyPerSecond}/sec</span>
            </div>
          )}
        </div>
      </div>

      {/* Game Area */}
      <div className="flex-1 flex gap-4 p-4 min-h-0">
        {/* Main Game View - Roblox Style 3D Environment */}
        <div 
          ref={gameAreaRef}
          className="flex-1 bg-robotic-dark/30 rounded-lg border-2 border-robotic-cyan/30 relative overflow-hidden cursor-pointer transition-transform duration-100"
          onClick={isPlaying ? handleGeneratorClick : undefined}
          style={{ 
            background: 'linear-gradient(to bottom, #87CEEB 0%, #98D8E8 50%, #B0E0E6 100%)',
            boxShadow: 'inset 0 0 20px rgba(15, 245, 255, 0.1)',
            position: 'relative',
            perspective: '1000px'
          }}
        >
          {/* Grid Floor (Roblox style) */}
          <div 
            className="absolute inset-0"
            style={{
              backgroundImage: `
                linear-gradient(to right, rgba(200, 200, 200, 0.3) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(200, 200, 200, 0.3) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px',
              transform: 'rotateX(60deg) translateY(50%)',
              transformOrigin: 'center',
              transformStyle: 'preserve-3d'
            }}
          />

          {/* Base Platform (Red base) */}
          <div 
            className="absolute"
            style={{
              bottom: '30%',
              left: '50%',
              transform: 'translateX(-50%) rotateX(60deg)',
              width: '200px',
              height: '150px',
              background: '#dc2626',
              border: '2px solid #991b1b',
              borderRadius: '4px',
              boxShadow: '0 10px 20px rgba(0,0,0,0.3)'
            }}
          >
            {/* Character (simple block) */}
            <div
              className="absolute"
              style={{
                top: '-30px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '20px',
                height: '30px',
                background: '#404040',
                borderRadius: '2px'
              }}
            />

            {/* Yellow Glowing Cube (Money Generator) */}
            <div
              className="absolute"
              style={{
                top: '-25px',
                left: '60%',
                transform: 'translateX(-50%)',
                width: '30px',
                height: '30px',
                background: '#fbbf24',
                borderRadius: '4px',
                boxShadow: '0 0 20px #fbbf24, 0 0 40px #fbbf24',
                animation: 'glow 1s ease-in-out infinite alternate'
              }}
            />

            {/* Blue Block */}
            <div
              className="absolute"
              style={{
                top: '-25px',
                left: '35%',
                transform: 'translateX(-50%)',
                width: '25px',
                height: '25px',
                background: '#3b82f6',
                borderRadius: '4px'
              }}
            />
          </div>

          {/* Green Path Blocks */}
          <div className="absolute" style={{ bottom: '20%', left: '50%', transform: 'translateX(-50%) rotateX(60deg)' }}>
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: `${i * 70}px`,
                  top: '0',
                  width: '50px',
                  height: '40px',
                  background: '#22c55e',
                  border: '2px solid #16a34a',
                  borderRadius: '4px',
                  boxShadow: '0 5px 10px rgba(0,0,0,0.2)',
                  backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.3) 2px, transparent 2px)',
                  backgroundSize: '10px 10px'
                }}
              />
            ))}
          </div>

          {/* Buildings Visualization (when expanded) */}
          {buildings > 1 && (
            <div className="absolute" style={{ bottom: '25%', left: '50%', transform: 'translateX(-50%) rotateX(60deg)' }}>
              {Array.from({ length: buildings - 1 }).map((_, i) => (
                <div
                  key={i}
                  className="bg-robotic-cyan/30 border-2 border-robotic-cyan rounded transition-all duration-500"
                  style={{
                    position: 'absolute',
                    left: `${(i - (buildings - 2) / 2) * 80}px`,
                    width: `${40 + i * 15}px`,
                    height: `${60 + i * 25}px`,
                    animation: isPlaying ? 'glow 2s ease-in-out infinite alternate' : 'none',
                    animationDelay: `${i * 0.2}s`,
                    boxShadow: '0 10px 20px rgba(0,0,0,0.3)'
                  }}
                >
                  <div className="h-full flex items-center justify-center">
                    <Building2 className="w-4 h-4 text-robotic-cyan" style={{ opacity: 0.8 + i * 0.1 }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Click Effects */}
          {clickEffects.map(effect => (
            <div
              key={effect.id}
              className="absolute pointer-events-none text-robotic-green font-bold text-xl"
              style={{
                left: `${effect.x}px`,
                top: `${effect.y - 20}px`,
                transform: 'translate(-50%, -50%)',
                textShadow: '0 0 10px rgba(94, 243, 140, 0.8)',
                animation: 'floatUp 1s ease-out forwards'
              }}
            >
              +{clickPower}
            </div>
          ))}

          {/* Generator Indicators - Animated Progress Bars (only when playing) */}
          {isPlaying && moneyPerSecond > 0 && (
            <div className="absolute top-4 left-4 right-4 flex gap-2">
              {Array.from({ length: Math.min(moneyPerSecond, 10) }).map((_, i) => (
                <div
                  key={i}
                  className="flex-1 h-1.5 bg-robotic-green/30 rounded-full overflow-hidden border border-robotic-green/20"
                >
                  <div 
                    className="h-full bg-gradient-to-r from-robotic-green to-robotic-cyan rounded-full"
                    style={{
                      animation: 'progress 1s linear infinite',
                      animationDelay: `${i * 0.15}s`,
                      boxShadow: '0 0 5px rgba(94, 243, 140, 0.5)'
                    }}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Instructions Overlay - Show when not playing */}
          {!isPlaying && (
            <div className="absolute inset-0 flex items-center justify-center bg-robotic-dark/70 backdrop-blur-sm z-10">
              <div className="text-center p-6 border-2 border-robotic-cyan rounded-lg bg-robotic-dark/95">
                <Play className="w-12 h-12 text-robotic-cyan mx-auto mb-4" />
                <p className="text-robotic-cyan font-semibold text-lg mb-2">Click Play to Start!</p>
                <p className="text-robotic-cyan/70 text-sm mb-4">The game will pause when you're not playing</p>
                <button
                  onClick={() => setIsPlaying(true)}
                  className="px-6 py-3 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2 mx-auto"
                >
                  <Play className="w-4 h-4" />
                  Start Playing
                </button>
              </div>
            </div>
          )}

          {/* Click Hint (only when playing) */}
          {isPlaying && (
            <div className="absolute bottom-4 left-4 right-4 text-center z-10">
              <p className="text-white/80 bg-black/50 px-3 py-1.5 rounded text-xs font-mono backdrop-blur-sm">
                Click generators to collect • {clickPower}x per click
              </p>
            </div>
          )}
        </div>

        {/* Upgrades Panel */}
        <div className="w-80 bg-robotic-dark/50 rounded-lg border border-robotic-cyan/20 p-4 overflow-y-auto">
          <h3 className="text-robotic-cyan font-heading font-bold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Upgrades
          </h3>
          <div className="space-y-3">
            {upgrades.map(upgrade => {
              const canAfford = money >= upgrade.cost;
              const isMaxed = upgrade.level >= 5; // Cap at level 5 for balance

              return (
                <button
                  key={upgrade.id}
                  onClick={() => buyUpgrade(upgrade.id)}
                  disabled={!canAfford || isMaxed}
                  className={`w-full p-3 rounded-lg border-2 transition-all duration-200 text-left ${
                    canAfford && !isMaxed
                      ? 'border-robotic-cyan/50 hover:border-robotic-cyan hover:bg-robotic-cyan/10 cursor-pointer'
                      : 'border-robotic-cyan/10 bg-robotic-dark/30 cursor-not-allowed opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{upgrade.icon}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-robotic-cyan font-semibold text-sm">{upgrade.name}</span>
                          {upgrade.level > 0 && (
                            <span className="px-1.5 py-0.5 bg-robotic-green/20 border border-robotic-green/30 rounded text-xs text-robotic-green">
                              Lv.{upgrade.level}
                            </span>
                          )}
                        </div>
                        <p className="text-robotic-cyan/60 text-xs mt-0.5">{upgrade.description}</p>
                      </div>
                    </div>
                    {!isMaxed && (
                      <ChevronRight className={`w-4 h-4 flex-shrink-0 ${canAfford ? 'text-robotic-cyan' : 'text-robotic-cyan/30'}`} />
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-robotic-cyan/10">
                    <span className={`text-xs font-mono ${canAfford ? 'text-robotic-green' : 'text-robotic-cyan/40'}`}>
                      {isMaxed ? 'MAX LEVEL' : upgrade.effect}
                    </span>
                    <span className={`font-mono font-bold ${canAfford ? 'text-robotic-cyan' : 'text-robotic-cyan/40'}`}>
                      {isMaxed ? '---' : `${upgrade.cost.toLocaleString()} $`}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Stats */}
          <div className="mt-6 pt-4 border-t border-robotic-cyan/20">
            <h4 className="text-robotic-cyan/80 font-semibold text-sm mb-3">Stats</h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-robotic-cyan/70">
                <span>Buildings:</span>
                <span className="font-mono font-semibold text-robotic-cyan">{buildings}</span>
              </div>
              <div className="flex justify-between text-robotic-cyan/70">
                <span>Income/sec:</span>
                <span className="font-mono font-semibold text-robotic-green">{moneyPerSecond}</span>
              </div>
              <div className="flex justify-between text-robotic-cyan/70">
                <span>Click Power:</span>
                <span className="font-mono font-semibold text-robotic-cyan">{clickPower}x</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Roblox Instructions Toast */}
      {showRobloxInstructions && (
        <div className="absolute bottom-4 right-4 bg-robotic-dark/95 border-2 border-robotic-cyan rounded-lg p-4 max-w-sm z-50 shadow-xl">
          <div className="flex items-start gap-3">
            <ExternalLink className="w-5 h-5 text-robotic-cyan flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-robotic-cyan font-semibold mb-2">Code Copied!</h4>
              <ol className="text-xs text-robotic-cyan/80 space-y-1.5 list-decimal list-inside">
                <li>Open <a href="https://www.roblox.com/create" target="_blank" rel="noopener noreferrer" className="text-robotic-green hover:underline">Roblox Studio</a></li>
                <li>Create new place → Baseplate</li>
                <li>Right-click ServerScriptService → Insert → Script</li>
                <li>Paste code (Ctrl+V) and click Play!</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      <div className="h-1 bg-robotic-dark/50">
        <div 
          className="h-full bg-gradient-to-r from-robotic-cyan to-robotic-green transition-all duration-1000"
          style={{ 
            width: `${Math.min(100, (money / 1000) * 100)}%`,
            boxShadow: '0 0 10px rgba(15, 245, 255, 0.5)'
          }}
        />
      </div>

      <style>{`
        @keyframes progress {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes floatUp {
          0% { 
            opacity: 1; 
            transform: translate(-50%, -50%) translateY(0);
          }
          100% { 
            opacity: 0; 
            transform: translate(-50%, -50%) translateY(-60px);
          }
        }
      `}</style>
    </div>
  );
}

