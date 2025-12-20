import { useState } from 'react';
import { Play, Square, Maximize2, ExternalLink, Copy, BookOpen } from 'lucide-react';
import { GenerationResponse } from '../services/api';
import InteractiveGuide from './InteractiveGuide';
import TycoonGamePreview from './TycoonGamePreview';
import StoryGamePreview from './StoryGamePreview';
import SimulatorGamePreview from './SimulatorGamePreview';
import RacingGamePreview from './RacingGamePreview';
import { analyzeScript } from '../utils/scriptAnalyzer';

interface GamePreviewProps {
  result: GenerationResponse | null;
  gameUrl?: string;
}

export default function GamePreview({ result, gameUrl }: GamePreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showGuide, setShowGuide] = useState(false);

  // Auto-show guide when game is generated (optional - can be disabled)
  // useEffect(() => {
  //   if (result && !showGuide) {
  //     // Auto-start guide after 2 seconds
  //     const timer = setTimeout(() => {
  //       setShowGuide(true);
  //     }, 2000);
  //     return () => clearTimeout(timer);
  //   }
  // }, [result]);

  if (!result) {
    return (
      <div className="neon-border rounded-lg p-6 bg-robotic-dark/50 backdrop-blur-sm h-full flex items-center justify-center">
        <p className="text-robotic-cyan/50 text-center">
          Game preview will appear here after generation...
        </p>
      </div>
    );
  }

  // Detect game types
  const mechanics = analyzeScript(result);
  const isTycoonGame = mechanics.gameType === 'tycoon' || 
                       result.title.toLowerCase().includes('tycoon') ||
                       result.narrative.toLowerCase().includes('tycoon') ||
                       result.lua_script.toLowerCase().includes('tycoon');
  const isStoryGame = mechanics.gameType === 'story' ||
                     result.title.toLowerCase().includes('story') ||
                     result.narrative.toLowerCase().includes('story') ||
                     result.lua_script.toLowerCase().includes('story') ||
                     result.lua_script.toLowerCase().includes('narrative') ||
                     result.lua_script.toLowerCase().includes('dialogue');
  const isSimulatorGame = mechanics.gameType === 'simulator' ||
                          result.title.toLowerCase().includes('simulator') ||
                          result.narrative.toLowerCase().includes('simulator') ||
                          result.lua_script.toLowerCase().includes('simulator');
  const isRacingGame = mechanics.gameType === 'racing' ||
                       result.title.toLowerCase().includes('racing') ||
                       result.title.toLowerCase().includes('race') ||
                       result.narrative.toLowerCase().includes('racing') ||
                       result.narrative.toLowerCase().includes('race') ||
                       result.lua_script.toLowerCase().includes('racing') ||
                       result.lua_script.toLowerCase().includes('race') ||
                       result.lua_script.toLowerCase().includes('lap') ||
                       result.lua_script.toLowerCase().includes('checkpoint');

  // For MVP: If no game URL, show placeholder with instructions
  // Later: Embed Roblox Web Player here
  const handlePlay = () => {
    setIsPlaying(true);
    // TODO: Integrate Roblox Web Player or game rendering
  };

  const handleStop = () => {
    setIsPlaying(false);
  };

  // For tycoon games, render the interactive game directly without wrapper
  if (isTycoonGame) {
    return (
      <>
        <InteractiveGuide
          gameType="tycoon"
          isActive={showGuide}
          onClose={() => setShowGuide(false)}
          gameResult={result}
        />
        <div className="neon-border rounded-lg bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
          <TycoonGamePreview result={result} />
        </div>
      </>
    );
  }

  // For story games, render the interactive story game
  if (isStoryGame) {
    return (
      <>
        <InteractiveGuide
          gameType="story"
          isActive={showGuide}
          onClose={() => setShowGuide(false)}
          gameResult={result}
        />
        <div className="neon-border rounded-lg bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
          <StoryGamePreview result={result} />
        </div>
      </>
    );
  }

  // For simulator games, render the interactive simulator game
  if (isSimulatorGame) {
    return (
      <>
        <InteractiveGuide
          gameType="simulator"
          isActive={showGuide}
          onClose={() => setShowGuide(false)}
          gameResult={result}
        />
        <div className="neon-border rounded-lg bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
          <SimulatorGamePreview result={result} />
        </div>
      </>
    );
  }

  // For racing games, render the interactive racing game
  if (isRacingGame) {
    return (
      <>
        <InteractiveGuide
          gameType="racing"
          isActive={showGuide}
          onClose={() => setShowGuide(false)}
          gameResult={result}
        />
        <div className="neon-border rounded-lg bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
          <RacingGamePreview result={result} />
        </div>
      </>
    );
  }

  return (
    <div className="neon-border rounded-lg p-6 bg-robotic-dark/50 backdrop-blur-sm h-full flex flex-col min-h-[400px]">
      <div className="flex items-center justify-between mb-4 flex-shrink-0 flex-wrap gap-2">
        <h3 className="text-lg font-heading font-semibold neon-glow">Game Preview</h3>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setShowGuide(true)}
            className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all flex items-center gap-2"
            title="Start Interactive Guide"
          >
            <BookOpen className="w-4 h-4" />
            Guide
          </button>
          {!isPlaying ? (
            <button
              onClick={handlePlay}
              className="px-4 py-2 bg-robotic-green text-robotic-bg rounded text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Play
            </button>
          ) : (
            <button
              onClick={handleStop}
              className="px-4 py-2 bg-robotic-magenta text-white rounded text-sm font-semibold hover:bg-robotic-magenta/90 transition-all flex items-center gap-2"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          )}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all flex items-center gap-2"
          >
            <Maximize2 className="w-4 h-4" />
            Fullscreen
          </button>
        </div>
      </div>

      {/* Interactive Guide */}
      {showGuide && (
        <InteractiveGuide
          gameType={
            result?.title.toLowerCase().includes('fps') || 
            result?.title.toLowerCase().includes('capture') || 
            result?.title.toLowerCase().includes('flag') ||
            result?.narrative.toLowerCase().includes('capture the flag')
              ? 'fps' 
              : result?.title.toLowerCase().includes('obby') || 
                result?.title.toLowerCase().includes('obstacle') ||
                result?.narrative.toLowerCase().includes('obstacle')
              ? 'obby'
              : 'default'
          }
          isActive={showGuide}
          onClose={() => setShowGuide(false)}
          gameResult={result}
        />
      )}

      {/* Game Embed Area */}
      <div className="flex-1 min-h-[300px] bg-robotic-darker rounded border border-robotic-cyan/20 relative overflow-hidden">
        {gameUrl ? (
          <iframe
            src={gameUrl}
            className="w-full h-full border-0"
            allow="fullscreen"
            title={`${result.title} - Roblox Game`}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center overflow-y-auto">
            <div className="mb-6 text-robotic-cyan/50">
              <Play className="w-20 h-20 mx-auto mb-4 opacity-50" />
              <p className="text-xl font-heading mb-3 neon-glow">Roblox Game Preview</p>
              <p className="text-sm text-robotic-cyan/60 max-w-lg mb-6">
                To play this game, follow the steps below to open Roblox Studio, paste the code, and run it!
              </p>
            </div>
            
            <div className="w-full max-w-lg p-6 bg-robotic-dark/70 rounded-lg border-2 border-robotic-cyan/30 text-left mb-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-base font-heading font-semibold text-robotic-cyan neon-glow flex items-center gap-2">
                  <span className="text-robotic-green">▶</span> Quick Start Guide
                </h4>
                <button
                  onClick={() => setShowGuide(true)}
                  className="px-3 py-1.5 bg-robotic-cyan text-robotic-bg rounded text-xs font-semibold hover:bg-robotic-cyan/90 transition-all flex items-center gap-1.5"
                  title="Start Interactive Voice Guide"
                >
                  <BookOpen className="w-3 h-3" />
                  Voice Guide
                </button>
              </div>
              <ol className="space-y-3 text-sm text-robotic-cyan/80">
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-cyan/20 border border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">1</span>
                  <span className="pt-0.5">Copy the generated Lua script from the code editor above</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-cyan/20 border border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">2</span>
                  <span className="pt-0.5">Open Roblox Studio (download from roblox.com/create if not installed, then launch it)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-cyan/20 border border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">3</span>
                  <span className="pt-0.5">Create a new place or open an existing one</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-cyan/20 border border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">4</span>
                  <span className="pt-0.5">In the Explorer, right-click <span className="font-mono text-robotic-green">ServerScriptService</span> → Insert Object → Script</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-cyan/20 border border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">5</span>
                  <span className="pt-0.5">Double-click the Script, delete default code, and <span className="font-semibold text-robotic-green">paste your copied code</span></span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-robotic-green/20 border border-robotic-green flex items-center justify-center text-robotic-green font-bold text-xs">6</span>
                  <span className="pt-0.5"><span className="font-semibold text-robotic-green">Click the Play button</span> in Roblox Studio to test your game!</span>
                </li>
              </ol>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 w-full max-w-lg">
              <a
                href="https://www.roblox.com/create"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 px-6 py-3 bg-robotic-cyan text-robotic-bg rounded-lg text-sm font-heading font-semibold hover:bg-robotic-cyan/90 transition-all flex items-center justify-center gap-2 neon-glow"
              >
                <ExternalLink className="w-5 h-5" />
                Download Roblox Studio
              </a>
              <button
                onClick={() => {
                  if (result?.lua_script) {
                    navigator.clipboard.writeText(result.lua_script);
                    alert('Code copied to clipboard! Now paste it in Roblox Studio.');
                  }
                }}
                className="flex-1 px-6 py-3 border-2 border-robotic-green text-robotic-green rounded-lg text-sm font-heading font-semibold hover:bg-robotic-green/10 transition-all flex items-center justify-center gap-2"
              >
                <Copy className="w-5 h-5" />
                Copy Code
              </button>
            </div>

            <p className="mt-4 text-xs text-robotic-cyan/50 max-w-lg">
              💡 Tip: Make sure to save your place in Roblox Studio before testing!
            </p>
          </div>
        )}
      </div>

      {/* Game Info */}
      {result.assets_needed && result.assets_needed.length > 0 && (
        <div className="mt-4 pt-4 border-t border-robotic-cyan/20 flex-shrink-0">
          <h4 className="text-xs md:text-sm font-semibold mb-2">Required Assets</h4>
          <div className="flex flex-wrap gap-2">
            {result.assets_needed.map((asset, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-robotic-dark border border-robotic-cyan/20 rounded text-xs text-robotic-cyan/70 break-words"
              >
                {asset}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

