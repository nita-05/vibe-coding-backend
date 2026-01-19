import { useState, useEffect, useRef } from 'react';
import { Play, Square, Flag, Zap, Clock, Target, ExternalLink, Gauge, Award, BookOpen } from 'lucide-react';
import { GenerationResponse } from '../services/api';

interface Checkpoint {
  id: number;
  x: number;
  y: number;
  passed: boolean;
}

interface RacingGamePreviewProps {
  result: GenerationResponse | null;
}

export default function RacingGamePreview({ result }: RacingGamePreviewProps) {
  const [speed, setSpeed] = useState(0);
  const maxSpeed = 150;
  const [lap, setLap] = useState(1);
  const totalLaps = 3;
  const [raceTime, setRaceTime] = useState(0);
  const [bestTime, setBestTime] = useState<number | null>(null);
  const [position, setPosition] = useState({ x: 50, y: 50 });
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [showRobloxInstructions, setShowRobloxInstructions] = useState(false);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([
    { id: 1, x: 75, y: 20, passed: false },
    { id: 2, x: 90, y: 50, passed: false },
    { id: 3, x: 75, y: 80, passed: false },
    { id: 4, x: 50, y: 80, passed: false },
    { id: 5, x: 25, y: 80, passed: false },
    { id: 6, x: 10, y: 50, passed: false },
    { id: 7, x: 25, y: 20, passed: false }
  ]);
  const [nextCheckpoint, setNextCheckpoint] = useState(0);
  const [boost, setBoost] = useState(0);
  const [keysPressed, setKeysPressed] = useState<Set<string>>(new Set());
  const [showHowToPlay, setShowHowToPlay] = useState(true); // Show instructions on first load
  const raceAreaRef = useRef<HTMLDivElement>(null);
  const gameLoopRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Store keys in ref for immediate access in game loop
  const keysPressedRef = useRef<Set<string>>(new Set());

  // Handle keyboard controls - works when game area is focused
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const keyMap: Record<string, string> = {
        'arrowup': 'arrowup',
        'arrowdown': 'arrowdown',
        'arrowleft': 'arrowleft',
        'arrowright': 'arrowright',
        'w': 'w',
        'a': 'a',
        's': 's',
        'd': 'd'
      };

      if (keyMap[key] || key === 'arrowup' || key === 'arrowdown' || key === 'arrowleft' || key === 'arrowright') {
        e.preventDefault();
        keysPressedRef.current.add(key);
        setKeysPressed(new Set(keysPressedRef.current));
      }
      
      if (e.key === ' ' || e.key === 'Space') {
        e.preventDefault();
        if (isPlaying && boost > 0) {
          activateBoost();
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const keyMap: Record<string, string> = {
        'arrowup': 'arrowup',
        'arrowdown': 'arrowdown',
        'arrowleft': 'arrowleft',
        'arrowright': 'arrowright',
        'w': 'w',
        'a': 'a',
        's': 's',
        'd': 'd'
      };

      if (keyMap[key] || key === 'arrowup' || key === 'arrowdown' || key === 'arrowleft' || key === 'arrowright') {
        keysPressedRef.current.delete(key);
        setKeysPressed(new Set(keysPressedRef.current));
      }
    };

    // Always listen, but only respond when playing
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      keysPressedRef.current.clear();
      setKeysPressed(new Set());
    };
  }, [isPlaying, boost]);

  // Game loop - ONLY when playing
  useEffect(() => {
    if (!isPlaying || isFinished) {
      if (gameLoopRef.current) {
        clearInterval(gameLoopRef.current);
        gameLoopRef.current = null;
      }
      return;
    }

    gameLoopRef.current = setInterval(() => {
      // Use ref for immediate key state access
      const currentKeys = keysPressedRef.current;
      
      // Calculate speed based on keys
      let newSpeed = speed;
      const hasAcceleration = currentKeys.has('arrowup') || currentKeys.has('w');
      const hasDeceleration = currentKeys.has('arrowdown') || currentKeys.has('s');

      if (hasAcceleration && !hasDeceleration) {
        newSpeed = Math.min(speed + 2, maxSpeed);
      } else if (hasDeceleration && !hasAcceleration) {
        newSpeed = Math.max(speed - 3, 0);
      } else {
        // Natural deceleration
        newSpeed = Math.max(speed - 0.5, 0);
      }

      // Apply boost if active
      if (boost > 0) {
        newSpeed = Math.min(newSpeed + 30, maxSpeed + 50);
        setBoost(prev => Math.max(0, prev - 0.1));
      }

      setSpeed(newSpeed);

      // Update position based on speed and direction
      if (newSpeed > 0) {
        const moveX = (currentKeys.has('arrowright') || currentKeys.has('d') ? 1 : 0) - 
                      (currentKeys.has('arrowleft') || currentKeys.has('a') ? 1 : 0);
        const moveY = (hasAcceleration ? -1 : 0) - (hasDeceleration ? 1 : 0);

        setPosition(prev => ({
          x: Math.max(5, Math.min(95, prev.x + moveX * (newSpeed / 50))),
          y: Math.max(5, Math.min(95, prev.y + moveY * (newSpeed / 50)))
        }));
      }

      // Check checkpoints
      checkCheckpoints();
    }, 16); // ~60 FPS

    return () => {
      if (gameLoopRef.current) {
        clearInterval(gameLoopRef.current);
        gameLoopRef.current = null;
      }
    };
  }, [isPlaying, isFinished, speed, keysPressed, boost, maxSpeed, position]);

  // Race timer - ONLY when playing
  useEffect(() => {
    if (!isPlaying || isFinished) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    timerRef.current = setInterval(() => {
      setRaceTime(prev => prev + 0.1);
    }, 100);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPlaying, isFinished]);

  const checkCheckpoints = () => {
    const currentCheckpoint = checkpoints[nextCheckpoint];
    if (!currentCheckpoint) return;

    // Simple distance check (in practice, would be more precise)
    const distance = Math.sqrt(
      Math.pow((position.x - currentCheckpoint.x), 2) + 
      Math.pow((position.y - currentCheckpoint.y), 2)
    );

    if (distance < 8 && !currentCheckpoint.passed) {
      const updatedCheckpoints = checkpoints.map((cp, idx) => 
        idx === nextCheckpoint ? { ...cp, passed: true } : cp
      );
      setCheckpoints(updatedCheckpoints);
      
      // Award boost when passing checkpoint
      setBoost(prev => Math.min(prev + 20, 100));
      
      if (nextCheckpoint === checkpoints.length - 1) {
        // Completed a lap
        if (lap >= totalLaps) {
          finishRace();
        } else {
          setLap(prev => prev + 1);
          // Reset checkpoints for new lap
          setCheckpoints(checkpoints.map(cp => ({ ...cp, passed: false })));
          setNextCheckpoint(0);
        }
      } else {
        setNextCheckpoint(prev => prev + 1);
      }
    }
  };

  const finishRace = () => {
    setIsFinished(true);
    setIsPlaying(false);
    if (!bestTime || raceTime < bestTime) {
      setBestTime(raceTime);
    }
  };

  const activateBoost = () => {
    if (boost > 0) {
      setBoost(prev => Math.max(0, prev - 30));
    }
  };

  const handleStartRace = () => {
    setIsPlaying(true);
    setIsFinished(false);
    setRaceTime(0);
    setLap(1);
    setSpeed(0);
    setPosition({ x: 50, y: 50 });
    setCheckpoints(checkpoints.map(cp => ({ ...cp, passed: false })));
    setNextCheckpoint(0);
    setBoost(0);
    // Clear any stuck keys
    keysPressedRef.current.clear();
    setKeysPressed(new Set());
  };

  const handleReset = () => {
    setIsPlaying(false);
    setIsFinished(false);
    setRaceTime(0);
    setLap(1);
    setSpeed(0);
    setPosition({ x: 50, y: 50 });
    setCheckpoints(checkpoints.map(cp => ({ ...cp, passed: false })));
    setNextCheckpoint(0);
    setBoost(0);
    setKeysPressed(new Set());
  };

  // Removed unused handleCopyToRoblox function

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  const gameTitle = result?.title || 'Racing Game';

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
          {bestTime && (
            <div className="px-3 py-1 bg-robotic-green/20 border border-robotic-green rounded text-xs text-robotic-green flex items-center gap-1">
              <Award className="w-3 h-3" />
              Best: {formatTime(bestTime)}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHowToPlay(true)}
            className="px-4 py-2 border border-robotic-cyan/30 rounded-lg text-sm hover:neon-border transition-all flex items-center gap-2"
            title="How to Play"
          >
            <BookOpen className="w-4 h-4" />
            How to Play
          </button>
          {!isPlaying && !isFinished ? (
            <button
              onClick={handleStartRace}
              className="px-4 py-2 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Start Race
            </button>
          ) : isPlaying ? (
            <button
              onClick={() => setIsPlaying(false)}
              className="px-4 py-2 bg-robotic-magenta text-white rounded-lg text-sm font-semibold hover:bg-robotic-magenta/90 transition-all flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Pause
            </button>
          ) : (
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-robotic-cyan text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-cyan/90 transition-all flex items-center gap-2"
            >
              Reset
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

      {/* Main Game Area */}
      <div className="flex-1 flex flex-col gap-4 p-4 min-h-0">
        {/* Race Stats Bar */}
        <div className="grid grid-cols-5 gap-3">
          <div className="bg-robotic-dark/70 rounded-lg border border-robotic-cyan/30 p-3">
            <div className="text-xs text-robotic-cyan/60 mb-1">Race Time</div>
            <div className="text-lg font-bold text-robotic-cyan font-mono flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatTime(raceTime)}
            </div>
          </div>
          <div className="bg-robotic-dark/70 rounded-lg border border-robotic-cyan/30 p-3">
            <div className="text-xs text-robotic-cyan/60 mb-1">Speed</div>
            <div className="text-lg font-bold text-robotic-green font-mono flex items-center gap-1">
              <Gauge className="w-4 h-4" />
              {Math.floor(speed)} km/h
            </div>
          </div>
          <div className="bg-robotic-dark/70 rounded-lg border border-robotic-cyan/30 p-3">
            <div className="text-xs text-robotic-cyan/60 mb-1">Lap</div>
            <div className="text-lg font-bold text-robotic-cyan font-mono flex items-center gap-1">
              <Flag className="w-4 h-4" />
              {lap}/{totalLaps}
            </div>
          </div>
          <div className="bg-robotic-dark/70 rounded-lg border border-robotic-cyan/30 p-3">
            <div className="text-xs text-robotic-cyan/60 mb-1">Checkpoints</div>
            <div className="text-lg font-bold text-robotic-cyan font-mono flex items-center gap-1">
              <Target className="w-4 h-4" />
              {nextCheckpoint}/{checkpoints.length}
            </div>
          </div>
          <div className="bg-robotic-dark/70 rounded-lg border border-robotic-cyan/30 p-3">
            <div className="text-xs text-robotic-cyan/60 mb-1">Boost</div>
            <div className="text-lg font-bold text-robotic-magenta font-mono flex items-center gap-1">
              <Zap className="w-4 h-4" />
              {Math.floor(boost)}%
            </div>
          </div>
        </div>

        {/* Race Track */}
        <div className="flex-1 flex gap-4 min-h-0">
          <div className="flex-1 relative bg-robotic-dark/50 rounded-lg border-2 border-robotic-cyan/30 overflow-hidden">
            <div
              ref={raceAreaRef}
              className="w-full h-full relative"
              style={{
                background: 'linear-gradient(135deg, #1a3a2e 0%, #0d2818 100%)',
                backgroundImage: `
                  repeating-linear-gradient(90deg, transparent, transparent 50px, rgba(15, 245, 255, 0.1) 50px, rgba(15, 245, 255, 0.1) 52px),
                  repeating-linear-gradient(0deg, transparent, transparent 50px, rgba(15, 245, 255, 0.1) 50px, rgba(15, 245, 255, 0.1) 52px)
                `
              }}
            >
              {/* Track outline */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <path
                  d="M 10,50 Q 50,10 90,50 T 90,90 Q 50,90 10,90 Q 10,70 10,50"
                  fill="none"
                  stroke="rgba(200, 200, 200, 0.3)"
                  strokeWidth="60"
                  strokeLinecap="round"
                />
                <path
                  d="M 10,50 Q 50,10 90,50 T 90,90 Q 50,90 10,90 Q 10,70 10,50"
                  fill="none"
                  stroke="rgba(15, 245, 255, 0.5)"
                  strokeWidth="3"
                  strokeDasharray="10,5"
                />
              </svg>

              {/* Checkpoints */}
              {checkpoints.map((checkpoint) => (
                <div
                  key={checkpoint.id}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2"
                  style={{
                    left: `${checkpoint.x}%`,
                    top: `${checkpoint.y}%`,
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    border: `3px solid ${checkpoint.passed ? '#0ff0ff' : '#0ff0ff40'}`,
                    background: checkpoint.passed 
                      ? 'radial-gradient(circle, #0ff0ff, #00ff96)'
                      : 'radial-gradient(circle, rgba(15, 245, 255, 0.3), transparent)',
                    boxShadow: checkpoint.passed 
                      ? '0 0 20px rgba(15, 245, 255, 0.8)' 
                      : '0 0 10px rgba(15, 245, 255, 0.3)',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {checkpoint.passed && (
                    <div className="absolute inset-0 rounded-full bg-robotic-green animate-ping opacity-75" />
                  )}
                </div>
              ))}

              {/* Player Car */}
              <div
                className="absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-100"
                style={{
                  left: `${position.x}%`,
                  top: `${position.y}%`,
                  width: '24px',
                  height: '32px',
                  background: 'linear-gradient(135deg, #ff4444, #cc0000)',
                  borderRadius: '4px',
                  border: '2px solid #ffffff',
                  boxShadow: '0 0 15px rgba(255, 68, 68, 0.8), 0 4px 8px rgba(0,0,0,0.5)',
                  transform: `translate(-50%, -50%) rotate(${speed > 0 ? Math.atan2(
                    (keysPressedRef.current.has('arrowright') || keysPressedRef.current.has('d') ? 1 : keysPressedRef.current.has('arrowleft') || keysPressedRef.current.has('a') ? -1 : 0),
                    (keysPressedRef.current.has('arrowup') || keysPressedRef.current.has('w') ? -1 : keysPressedRef.current.has('arrowdown') || keysPressedRef.current.has('s') ? 1 : 0)
                  ) * 180 / Math.PI : 0}deg)`
                }}
              >
                {/* Car windows */}
                <div className="absolute top-1 left-1 right-1 h-2 bg-blue-400/50 rounded-sm" />
              </div>

              {/* Finish line */}
              {lap > totalLaps && nextCheckpoint === checkpoints.length && (
                <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                  <div className="text-4xl font-bold text-robotic-green mb-2 animate-bounce">FINISH!</div>
                  <div className="text-robotic-cyan text-lg">Time: {formatTime(raceTime)}</div>
                </div>
              )}

              {/* Start overlay - only show if how to play is closed */}
              {!isPlaying && !isFinished && !showHowToPlay && (
                <div className="absolute inset-0 flex items-center justify-center bg-robotic-dark/80 backdrop-blur-sm z-10">
                  <div className="text-center">
                    <Flag className="w-16 h-16 text-robotic-cyan/50 mx-auto mb-4" />
                    <p className="text-robotic-cyan text-lg font-semibold mb-2">Ready to Race!</p>
                    <p className="text-robotic-cyan/60 text-sm mb-4">Click "Start Race" to begin</p>
                    <p className="text-robotic-cyan/60 text-xs">Use Arrow Keys or WASD to drive</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Controls Panel */}
          <div className="w-64 bg-robotic-dark/50 rounded-lg border border-robotic-cyan/20 p-4">
            <h3 className="text-sm font-semibold text-robotic-cyan mb-3">Controls</h3>
            <div className="space-y-2 text-xs text-robotic-cyan/70">
              <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                <span>↑ / W</span>
                <span>Accelerate</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                <span>↓ / S</span>
                <span>Brake</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                <span>← → / A D</span>
                <span>Steer</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                <span>Space</span>
                <span>Boost</span>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-robotic-cyan/20">
              <div className="text-xs text-robotic-cyan/60 mb-2">Race Info</div>
              <div className="text-xs text-robotic-cyan/70 space-y-1">
                <div>Total Laps: {totalLaps}</div>
                <div>Checkpoints per lap: {checkpoints.length}</div>
                <div>Pass checkpoints to get boost!</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How to Play Overlay */}
      {showHowToPlay && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm z-50">
          <div className="bg-robotic-dark border-2 border-robotic-cyan rounded-lg p-6 max-w-2xl mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-heading font-bold text-robotic-cyan neon-glow flex items-center gap-2">
                <BookOpen className="w-6 h-6" />
                How to Play Racing Game
              </h3>
              <button
                onClick={() => setShowHowToPlay(false)}
                className="text-robotic-cyan/60 hover:text-robotic-cyan transition-colors text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4 text-left">
              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Start the Race
                </h4>
                <p className="text-robotic-cyan/80 text-sm">Click "Start Race" button to begin. The race timer starts immediately!</p>
              </div>

              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Controls
                </h4>
                <div className="grid grid-cols-2 gap-3 text-sm text-robotic-cyan/80">
                  <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                    <span className="font-mono">↑ or W</span>
                    <span>Accelerate</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                    <span className="font-mono">↓ or S</span>
                    <span>Brake</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                    <span className="font-mono">← → or A D</span>
                    <span>Steer Left/Right</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-robotic-dark/50 rounded">
                    <span className="font-mono">Spacebar</span>
                    <span>Activate Boost</span>
                  </div>
                </div>
              </div>

              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  Checkpoints
                </h4>
                <p className="text-robotic-cyan/80 text-sm">Drive through the glowing checkpoints around the track. Each checkpoint you pass gives you boost power! You must pass all checkpoints to complete a lap.</p>
              </div>

              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Flag className="w-4 h-4" />
                  Complete Laps
                </h4>
                <p className="text-robotic-cyan/80 text-sm">You need to complete {totalLaps} laps to finish the race. Watch your lap counter in the stats bar at the top!</p>
              </div>

              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Gauge className="w-4 h-4" />
                  Boost System
                </h4>
                <p className="text-robotic-cyan/80 text-sm">When you have boost power (gained from checkpoints), press Spacebar to activate a temporary speed boost. Use it wisely on straightaways!</p>
              </div>

              <div className="bg-robotic-dark/50 rounded-lg p-4 border border-robotic-cyan/20">
                <h4 className="text-robotic-cyan font-semibold mb-2 flex items-center gap-2">
                  <Award className="w-4 h-4" />
                  Best Time
                </h4>
                <p className="text-robotic-cyan/80 text-sm">Try to beat your best time! Your fastest race time will be saved and displayed at the top.</p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => {
                  setShowHowToPlay(false);
                  handleStartRace();
                }}
                className="flex-1 px-5 py-2.5 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4" />
                Start Racing!
              </button>
              <button
                onClick={() => setShowHowToPlay(false)}
                className="px-5 py-2.5 border-2 border-robotic-cyan text-robotic-cyan rounded-lg text-sm font-semibold hover:bg-robotic-cyan/10 transition-all"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}

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
    </div>
  );
}

