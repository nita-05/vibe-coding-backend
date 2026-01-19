import { useState, useEffect, useRef } from 'react';
import { Star, BarChart3, ExternalLink, Play, Square } from 'lucide-react';
import { GenerationResponse } from '../services/api';

interface Upgrade {
  id: string;
  name: string;
  description: string;
  cost: number;
  level: number;
  multiplier: number;
  effect: string;
  icon: string;
  type: 'click' | 'auto' | 'multiplier' | 'rebirth';
}

interface SimulatorGamePreviewProps {
  result: GenerationResponse | null;
}

export default function SimulatorGamePreview({ result }: SimulatorGamePreviewProps) {
  const [money, setMoney] = useState(0);
  const [totalEarned, setTotalEarned] = useState(0);
  const [clickPower, setClickPower] = useState(1);
  const [autoClickPower, setAutoClickPower] = useState(0);
  const [moneyPerSecond, setMoneyPerSecond] = useState(0);
  const [multiplier, setMultiplier] = useState(1);
  const [level, setLevel] = useState(1);
  const [rebirthCount, setRebirthCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showRobloxInstructions, setShowRobloxInstructions] = useState(false);
  const [clickEffects, setClickEffects] = useState<Array<{id: number, x: number, y: number, amount: number}>>([]);
  const clickEffectId = useRef(0);
  const gameAreaRef = useRef<HTMLDivElement>(null);
  const autoClickerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [upgrades, setUpgrades] = useState<Upgrade[]>([
    {
      id: 'click_power',
      name: 'Click Power',
      description: 'Increases money per click',
      cost: 10,
      level: 0,
      multiplier: 1.5,
      effect: '+1 per click',
      icon: '⚡',
      type: 'click'
    },
    {
      id: 'auto_clicker',
      name: 'Auto Clicker',
      description: 'Automatically clicks for you',
      cost: 50,
      level: 0,
      multiplier: 1.2,
      effect: '+1 auto click/sec',
      icon: '🤖',
      type: 'auto'
    },
    {
      id: 'click_multiplier',
      name: 'Click Multiplier',
      description: 'Doubles all click earnings',
      cost: 200,
      level: 0,
      multiplier: 2,
      effect: '2x clicks',
      icon: '⭐',
      type: 'multiplier'
    },
    {
      id: 'money_generator',
      name: 'Money Generator',
      description: 'Generates passive income',
      cost: 100,
      level: 0,
      multiplier: 1.5,
      effect: '+2/sec',
      icon: '💰',
      type: 'auto'
    },
    {
      id: 'super_clicker',
      name: 'Super Clicker',
      description: 'Massive click power boost',
      cost: 500,
      level: 0,
      multiplier: 2,
      effect: '+10 per click',
      icon: '🚀',
      type: 'click'
    },
    {
      id: 'rebirth',
      name: 'Rebirth',
      description: 'Reset for permanent bonuses',
      cost: 10000,
      level: 0,
      multiplier: 1.1,
      effect: '+10% to all',
      icon: '✨',
      type: 'rebirth'
    }
  ]);

  // Calculate level based on total earned - only when playing
  useEffect(() => {
    if (!isPlaying) return;
    
    const newLevel = Math.floor(totalEarned / 1000) + 1;
    if (newLevel > level) {
      setLevel(newLevel);
    }
  }, [totalEarned, level, isPlaying]);

  // Auto-clicker effect (clicks automatically when enabled) - ONLY when playing
  useEffect(() => {
    // Clear interval immediately if not playing
    if (!isPlaying) {
      if (autoClickerRef.current) {
        clearInterval(autoClickerRef.current);
        autoClickerRef.current = null;
      }
      return;
    }

    // Only start if playing AND has auto click power
    if (autoClickPower <= 0) {
      return;
    }

    autoClickerRef.current = setInterval(() => {
      // Double check isPlaying inside interval
      if (!isPlaying) {
        if (autoClickerRef.current) {
          clearInterval(autoClickerRef.current);
          autoClickerRef.current = null;
        }
        return;
      }

      const earned = autoClickPower * multiplier;
      setMoney(prev => prev + earned);
      setTotalEarned(prev => prev + earned);
      
      // Add visual effect for auto-click
      if (gameAreaRef.current) {
        const rect = gameAreaRef.current.getBoundingClientRect();
        const x = rect.width / 2 + (Math.random() - 0.5) * 100;
        const y = rect.height / 2 + (Math.random() - 0.5) * 100;
        
        const newEffect = {
          id: clickEffectId.current++,
          x,
          y,
          amount: earned
        };
        setClickEffects(prev => [...prev, newEffect]);
        
        setTimeout(() => {
          setClickEffects(prev => prev.filter(e => e.id !== newEffect.id));
        }, 1000);
      }
    }, 1000);

    return () => {
      if (autoClickerRef.current) {
        clearInterval(autoClickerRef.current);
        autoClickerRef.current = null;
      }
    };
  }, [autoClickPower, multiplier, isPlaying]);

  // Passive money generation - ONLY when playing
  useEffect(() => {
    // Stop immediately if not playing
    if (!isPlaying) {
      return;
    }

    // Only start if playing AND has money per second
    if (moneyPerSecond <= 0) {
      return;
    }

    const interval = setInterval(() => {
      // Double check isPlaying inside interval
      if (!isPlaying) {
        return;
      }

      const earned = moneyPerSecond * multiplier;
      setMoney(prev => prev + earned);
      setTotalEarned(prev => prev + earned);
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [moneyPerSecond, multiplier, isPlaying]);

  // Handle main click - ONLY works when playing
  const handleMainClick = (event: React.MouseEvent) => {
    // Block all clicks when not playing
    if (!isPlaying) {
      return;
    }
    
    const rect = gameAreaRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const earned = clickPower * multiplier;
    setMoney(prev => prev + earned);
    setTotalEarned(prev => prev + earned);

    // Add click effect
    const newEffect = {
      id: clickEffectId.current++,
      x,
      y,
      amount: earned
    };
    setClickEffects(prev => [...prev, newEffect]);

    setTimeout(() => {
      setClickEffects(prev => prev.filter(e => e.id !== newEffect.id));
    }, 1000);
  };

  // Handle upgrade purchase
  const handleUpgrade = (upgrade: Upgrade) => {
    if (money < upgrade.cost || !isPlaying) return;

    setMoney(prev => prev - upgrade.cost);

    const updatedUpgrades = upgrades.map(u => {
      if (u.id === upgrade.id) {
        const newLevel = u.level + 1;
        const newCost = Math.floor(u.cost * u.multiplier);
        
        if (u.type === 'click') {
          setClickPower(prev => prev + Math.floor(upgrade.cost / 10));
        } else if (u.type === 'auto' && u.id === 'auto_clicker') {
          setAutoClickPower(prev => prev + 1);
        } else if (u.type === 'auto' && u.id === 'money_generator') {
          setMoneyPerSecond(prev => prev + 2);
        } else if (u.type === 'multiplier') {
          setMultiplier(prev => prev * upgrade.multiplier);
        } else if (u.type === 'rebirth') {
          // Rebirth mechanic - reset with permanent bonus
          handleRebirth();
          return u;
        }
        
        return {
          ...u,
          level: newLevel,
          cost: newCost
        };
      }
      return u;
    });

    setUpgrades(updatedUpgrades);
  };

  const handleRebirth = () => {
    const bonus = 1 + (rebirthCount * 0.1);
    setRebirthCount(prev => prev + 1);
    setMoney(0);
    setTotalEarned(0);
    setClickPower(Math.floor(1 * bonus));
    setAutoClickPower(Math.floor(autoClickPower * bonus));
    setMoneyPerSecond(Math.floor(moneyPerSecond * bonus));
    setMultiplier(prev => prev * 1.1);
    setLevel(1);
    
    // Reset upgrade costs
    setUpgrades(prev => prev.map(u => ({
      ...u,
      cost: Math.floor(u.cost * 0.5)
    })));
  };

  // Removed unused handleCopyToRoblox function

  const formatNumber = (num: number): string => {
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return Math.floor(num).toString();
  };

  const gameTitle = result?.title || 'Simulator Game';

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
          {rebirthCount > 0 && (
            <div className="px-3 py-1 bg-robotic-green/20 border border-robotic-green rounded text-xs text-robotic-green flex items-center gap-1">
              <Star className="w-3 h-3" />
              Rebirth {rebirthCount}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          {!isPlaying ? (
            <button
              onClick={() => setIsPlaying(true)}
              className="px-4 py-2 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Play
            </button>
          ) : (
            <button
              onClick={() => setIsPlaying(false)}
              className="px-4 py-2 bg-robotic-magenta text-white rounded-lg text-sm font-semibold hover:bg-robotic-magenta/90 transition-all flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Pause
            </button>
          )}
          <button
            onClick={() => setShowRobloxInstructions(true)}
            className="px-4 py-2 border border-robotic-cyan/30 rounded-lg text-sm hover:neon-border transition-all flex items-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Play in Roblox
          </button>
        </div>
      </div>

      {/* Main Game Area - Incremental Simulator Style */}
      <div className="flex-1 flex flex-col gap-4 p-4 min-h-0 overflow-hidden">
        {/* Top Stats Bar - Minimalist Number Focus */}
        <div className="flex items-center justify-between bg-robotic-dark/50 rounded-lg border border-robotic-cyan/20 p-4">
          <div className="flex items-center gap-6">
            <div>
              <div className="text-xs text-robotic-cyan/50 mb-1">Total Money</div>
              <div className="text-3xl font-bold text-robotic-cyan font-mono">
                {formatNumber(money)}
              </div>
            </div>
            <div className="h-12 w-px bg-robotic-cyan/20" />
            <div>
              <div className="text-xs text-robotic-green/50 mb-1">Per Second</div>
              <div className="text-2xl font-bold text-robotic-green font-mono">
                {formatNumber((autoClickPower + moneyPerSecond) * multiplier)}/s
              </div>
            </div>
            <div className="h-12 w-px bg-robotic-cyan/20" />
            <div>
              <div className="text-xs text-robotic-magenta/50 mb-1">Multiplier</div>
              <div className="text-2xl font-bold text-robotic-magenta font-mono">
                {multiplier.toFixed(1)}x
              </div>
            </div>
            <div className="h-12 w-px bg-robotic-cyan/20" />
            <div>
              <div className="text-xs text-robotic-cyan/50 mb-1">Level</div>
              <div className="text-2xl font-bold text-robotic-cyan font-mono">
                {level}
              </div>
            </div>
          </div>
          {rebirthCount > 0 && (
            <div className="px-4 py-2 bg-gradient-to-r from-robotic-green/20 to-robotic-cyan/20 border border-robotic-green/50 rounded-lg">
              <div className="text-xs text-robotic-green/70 mb-1">Rebirth</div>
              <div className="text-xl font-bold text-robotic-green font-mono flex items-center gap-2">
                <Star className="w-5 h-5" />
                {rebirthCount}
              </div>
            </div>
          )}
        </div>

        {/* Main Click Area - Big Central Object Style */}
        <div className="flex-1 flex gap-4 min-h-0">
          {/* Central Click Object */}
          <div className="flex-1 flex items-center justify-center relative">
            <div
              ref={gameAreaRef}
              onClick={handleMainClick}
              className={`relative cursor-pointer transition-all duration-100 ${
                isPlaying ? 'hover:scale-105 active:scale-95' : ''
              }`}
            >
              {/* Big Central Object - Glowing Orb/Crystal */}
              <div
                className="relative"
                style={{
                  width: isPlaying ? '280px' : '200px',
                  height: isPlaying ? '280px' : '200px',
                  transition: 'all 0.3s ease'
                }}
              >
                {/* Outer glow rings */}
                {isPlaying && (
                  <>
                    <div className="absolute inset-0 rounded-full bg-robotic-cyan/20 animate-ping" style={{ animationDuration: '2s' }} />
                    <div className="absolute inset-0 rounded-full bg-robotic-green/20 animate-ping" style={{ animationDuration: '2.5s', animationDelay: '0.5s' }} />
                  </>
                )}
                
                {/* Main orb */}
                <div
                  className="absolute inset-0 rounded-full border-4"
                  style={{
                    background: isPlaying 
                      ? 'radial-gradient(circle at 30% 30%, rgba(15, 245, 255, 0.8), rgba(15, 245, 255, 0.3), rgba(0, 255, 150, 0.5))'
                      : 'radial-gradient(circle at 30% 30%, rgba(15, 245, 255, 0.4), rgba(15, 245, 255, 0.1))',
                    borderColor: isPlaying ? '#0ff0ff' : '#0ff0ff40',
                    boxShadow: isPlaying 
                      ? '0 0 60px rgba(15, 245, 255, 0.6), 0 0 120px rgba(15, 245, 255, 0.3), inset 0 0 40px rgba(15, 245, 255, 0.2)'
                      : '0 0 30px rgba(15, 245, 255, 0.3)',
                    transition: 'all 0.3s ease'
                  }}
                />
                
                {/* Inner core */}
                <div
                  className="absolute inset-8 rounded-full"
                  style={{
                    background: 'radial-gradient(circle, rgba(15, 245, 255, 0.9), rgba(0, 255, 150, 0.7))',
                    boxShadow: 'inset 0 0 20px rgba(15, 245, 255, 0.5)'
                  }}
                />
                
                {/* Center sparkle */}
                <div
                  className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full"
                  style={{
                    background: 'radial-gradient(circle, #ffffff, rgba(15, 245, 255, 0.8))',
                    boxShadow: '0 0 20px rgba(255, 255, 255, 0.8)'
                  }}
                />
              </div>

              {/* Click prompt overlay */}
              {!isPlaying && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center mt-64">
                    <p className="text-robotic-cyan text-xl font-semibold mb-2">Click Play to Start!</p>
                    <p className="text-robotic-cyan/60 text-sm">Then click the orb to earn</p>
                  </div>
                </div>
              )}

              {/* Click effects - floating numbers */}
              {clickEffects.map(effect => (
                <div
                  key={effect.id}
                  className="absolute pointer-events-none font-bold z-20"
                  style={{
                    left: `${effect.x}px`,
                    top: `${effect.y}px`,
                    transform: 'translate(-50%, -50%)',
                    fontSize: '24px',
                    color: '#0ff0ff',
                    textShadow: '0 0 10px rgba(15, 245, 255, 1), 0 0 20px rgba(0, 255, 150, 0.8)',
                    animation: 'floatUp 1.5s ease-out forwards',
                    fontWeight: 700
                  }}
                >
                  +{formatNumber(effect.amount)}
                </div>
              ))}

              {/* Click instruction */}
              {isPlaying && (
                <div className="absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-center">
                  <div className="text-robotic-cyan/80 text-sm font-semibold bg-robotic-dark/90 px-4 py-2 rounded-lg border border-robotic-cyan/30">
                    Click to Earn {formatNumber(clickPower * multiplier)}!
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Side - Upgrades Panel */}
          <div className="w-96 bg-robotic-dark/50 rounded-lg border border-robotic-cyan/20 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-heading font-semibold text-robotic-cyan flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Upgrades
              </h3>
              <div className="text-xs text-robotic-cyan/50 font-mono">
                {upgrades.filter(u => u.level > 0).length}/{upgrades.length} Owned
              </div>
            </div>
            <div className="space-y-3">
              {upgrades.map(upgrade => {
                const canAfford = money >= upgrade.cost && isPlaying;
                return (
                  <button
                    key={upgrade.id}
                    onClick={() => handleUpgrade(upgrade)}
                    disabled={!canAfford}
                    className={`w-full p-4 rounded-lg border-2 transition-all text-left relative overflow-hidden ${
                      canAfford
                        ? 'border-robotic-cyan/50 hover:border-robotic-cyan hover:bg-robotic-cyan/10 cursor-pointer hover:scale-[1.02]'
                        : 'border-robotic-cyan/20 opacity-50 cursor-not-allowed'
                    }`}
                  >
                    {/* Upgrade glow effect when affordable */}
                    {canAfford && (
                      <div className="absolute inset-0 bg-gradient-to-r from-robotic-cyan/5 to-transparent pointer-events-none" />
                    )}
                    
                    <div className="flex items-start justify-between relative z-10">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-3xl">{upgrade.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <div className="text-sm font-bold text-robotic-cyan">{upgrade.name}</div>
                            {upgrade.level > 0 && (
                              <div className="px-2 py-0.5 bg-robotic-green/20 border border-robotic-green/50 rounded text-xs text-robotic-green font-mono">
                                Lv.{upgrade.level}
                              </div>
                            )}
                          </div>
                          <div className="text-xs text-robotic-cyan/60 mb-2">{upgrade.description}</div>
                          <div className="text-xs text-robotic-cyan/70 font-mono">
                            {upgrade.effect}
                          </div>
                        </div>
                      </div>
                      <div className={`text-right ml-3 ${
                        canAfford ? 'text-robotic-green' : 'text-robotic-cyan/50'
                      }`}>
                        <div className="text-lg font-bold font-mono">
                          {formatNumber(upgrade.cost)}
                        </div>
                        {upgrade.type === 'rebirth' && (
                          <div className="text-xs text-robotic-magenta/70 mt-1">Prestige</div>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Roblox Instructions Toast */}
      {showRobloxInstructions && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50">
          <div className="bg-robotic-dark border-2 border-robotic-cyan rounded-lg p-6 max-w-md mx-4 shadow-2xl">
            <div className="flex items-start gap-4">
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
        </div>
      )}

      {/* Add CSS animation for floating effects */}
      <style>{`
        @keyframes floatUp {
          0% {
            opacity: 1;
            transform: translate(-50%, -50%) translateY(0);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) translateY(-100px);
          }
        }
      `}</style>
    </div>
  );
}

