import { useState, useEffect, useMemo } from 'react';
import { BookOpen, Play, Square, ExternalLink, Copy, MessageSquare, ChevronRight } from 'lucide-react';
import { GenerationResponse } from '../services/api';

interface StorySegment {
  id: number;
  type: 'narrative' | 'dialogue';
  speaker?: string;
  text: string;
  choices?: Array<{ text: string; nextId: number }>;
}

interface StoryGamePreviewProps {
  result: GenerationResponse | null;
}

export default function StoryGamePreview({ result }: StoryGamePreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showRobloxInstructions, setShowRobloxInstructions] = useState(false);
  const [showHowToPlay, setShowHowToPlay] = useState(true); // Show instructions on first load
  
  // Generate story segments from the game result
  const generateStorySegments = (): StorySegment[] => {
    if (!result) return defaultStory;

    const narrative = result.narrative || '';
    const title = result.title || 'Story Game';
    
    // ALWAYS use the default story structure - it has complete, tested branching
    // Just customize the first segment's text if we have narrative
    const segments: StorySegment[] = defaultStory.map((segment, index) => {
      if (index === 0 && narrative && narrative.length > 20) {
        // Update first segment with custom welcome text, but keep all choices the same
        return {
          ...segment,
          text: `Welcome to ${title}! ${narrative}`
        };
      }
      // Return segment as-is for all other segments
      return segment;
    });
    
    // Validate all segments exist and fix any broken references
    const segmentIds = new Set(segments.map(s => s.id));
    segments.forEach(segment => {
      if (segment.choices) {
        segment.choices = segment.choices.filter(choice => {
          const exists = segmentIds.has(choice.nextId);
          if (!exists) {
            console.warn(`Choice "${choice.text}" references non-existent segment ${choice.nextId}`);
          }
          return exists;
        });
      }
    });
    
    // Log to verify structure
    console.log('📖 Story segments generated:', {
      count: segments.length,
      ids: segments.map(s => s.id),
      firstSegmentText: segments[0]?.text?.substring(0, 50)
    });
    
    return segments;
  };

  // Use useMemo to regenerate segments when result changes
  const storySegments = useMemo(() => {
    return generateStorySegments();
  }, [result]);
  
  // Initialize currentSegment to first segment's ID - update when segments change
  const [currentSegment, setCurrentSegment] = useState<number>(0);
  const [storyHistory, setStoryHistory] = useState<number[]>([0]);
  
  // Reset to first segment when storySegments change
  useEffect(() => {
    if (storySegments.length > 0) {
      const firstSegment = storySegments[0];
      setCurrentSegment(firstSegment.id);
      setStoryHistory([firstSegment.id]);
    }
  }, [storySegments]);
  
  // Use state for currentStory to ensure it updates reactively
  const [currentStory, setCurrentStory] = useState<StorySegment | null>(null);
  
  // Update currentStory whenever currentSegment or storySegments change
  useEffect(() => {
    if (storySegments.length > 0) {
      const found = storySegments.find(s => s.id === currentSegment) || storySegments[0];
      if (found) {
        setCurrentStory(found);
        console.log('🔄 Updated currentStory:', {
          segmentId: currentSegment,
          storyId: found?.id,
          text: found?.text?.substring(0, 50),
          hasText: !!found?.text,
          textLength: found?.text?.length || 0
        });
      } else {
        console.error('❌ Could not find story segment:', { currentSegment, availableIds: storySegments.map(s => s.id) });
        // Fallback to first segment
        const firstSegment = storySegments[0];
        if (firstSegment) {
          setCurrentStory(firstSegment);
          setCurrentSegment(firstSegment.id);
        }
      }
    } else {
      setCurrentStory(null);
    }
  }, [currentSegment, storySegments]);
  
  // Log currentStory whenever it changes
  useEffect(() => {
    if (isPlaying && currentStory) {
      console.log('📖 Current Story:', {
        id: currentStory.id,
        text: currentStory.text?.substring(0, 100),
        hasText: !!currentStory.text,
        textLength: currentStory.text?.length || 0
      });
    } else if (isPlaying && !currentStory) {
      console.error('❌ Current Story is NULL!', { currentSegment, segmentIds: storySegments.map(s => s.id) });
    }
  }, [currentStory, isPlaying, currentSegment, storySegments]);
  
  // Debug logging - always log to help diagnose
  useEffect(() => {
    if (isPlaying) {
      console.log('Story Debug:', {
        currentSegment,
        currentStoryExists: !!currentStory,
        currentStoryId: currentStory?.id,
        currentStoryText: currentStory?.text?.substring(0, 100),
        currentStoryHasText: !!currentStory?.text,
        currentStoryChoices: currentStory?.choices?.length || 0,
        storySegmentsCount: storySegments.length,
        storySegmentIds: storySegments.map(s => s.id),
        storyHistory: storyHistory
      });
    }
  }, [currentSegment, currentStory, isPlaying, storySegments, storyHistory]);
  
  // Sync currentSegment if it doesn't match any segment - fix invalid segments
  useEffect(() => {
    if (storySegments.length === 0) return;
    
    const foundStory = storySegments.find(s => s.id === currentSegment);
    if (!foundStory) {
      // Current segment doesn't exist, reset to first segment
      const firstSegment = storySegments[0];
      if (firstSegment) {
        console.log(`Segment ${currentSegment} not found, resetting to segment ${firstSegment.id}`);
        setCurrentSegment(firstSegment.id);
        setStoryHistory([firstSegment.id]);
      }
    }
  }, [currentSegment, storySegments]);

  const handleChoice = (nextId: number) => {
    // Validate that the next segment exists
    const nextSegment = storySegments.find(s => s.id === nextId);
    if (nextSegment) {
      console.log('✅ Navigating to segment:', { 
        id: nextId, 
        text: nextSegment.text?.substring(0, 50),
        hasText: !!nextSegment.text,
        choicesCount: nextSegment.choices?.length || 0
      });
      setStoryHistory(prev => [...prev, nextId]);
      setCurrentSegment(nextId);
    } else {
      // If segment doesn't exist, restart the story
      console.error(`❌ Story segment ${nextId} not found. Available IDs:`, storySegments.map(s => s.id));
      alert(`Segment ${nextId} not found. Available segments: ${storySegments.map(s => s.id).join(', ')}`);
      handleRestart();
    }
  };

  const handleGoBack = () => {
    if (storyHistory.length > 1) {
      const newHistory = [...storyHistory];
      newHistory.pop();
      const previousSegment = newHistory[newHistory.length - 1];
      setStoryHistory(newHistory);
      setCurrentSegment(previousSegment);
    }
  };

  const handleRestart = () => {
    const firstSegment = storySegments[0];
    if (firstSegment) {
      setCurrentSegment(firstSegment.id);
      setStoryHistory([firstSegment.id]);
    }
  };

  const handleCopyToRoblox = () => {
    if (result?.lua_script) {
      navigator.clipboard.writeText(result.lua_script);
      setShowRobloxInstructions(true);
      setTimeout(() => setShowRobloxInstructions(false), 5000);
    }
  };

  const gameTitle = result?.title || 'Story Game';
  
  // Check if story is finished (current segment has no choices)
  const storyToShow = currentStory || storySegments.find(s => s.id === currentSegment) || storySegments[0];
  const isStoryFinished = storyToShow && (!storyToShow.choices || storyToShow.choices.length === 0);

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
          <button
            onClick={() => setShowHowToPlay(true)}
            className="px-4 py-2 border border-robotic-cyan/30 text-robotic-cyan rounded-md text-sm font-semibold hover:bg-robotic-cyan/10 transition-all flex items-center gap-2"
            title="How to Play"
          >
            <BookOpen className="w-4 h-4" />
            How to Play
          </button>
          {(() => {
            // Show "Finish" if story is finished
            if (isStoryFinished && isPlaying) {
              return (
                <button
                  disabled
                  className="px-4 py-2 bg-robotic-cyan/30 text-robotic-cyan rounded-md text-sm font-semibold cursor-not-allowed flex items-center gap-2 opacity-70"
                >
                  <Square className="w-4 h-4" />
                  Finish
                </button>
              );
            }
            
            // Show "Continue" when paused
            if (!isPlaying) {
              return (
                <button
                  onClick={() => {
                    setShowHowToPlay(false);
                    // Ensure we have a current story before continuing
                    if (storySegments.length > 0 && !currentStory) {
                      const firstSegment = storySegments[0];
                      setCurrentSegment(firstSegment.id);
                      setStoryHistory([firstSegment.id]);
                      setCurrentStory(firstSegment);
                    }
                    setIsPlaying(true);
                  }}
                  className="px-4 py-2 bg-robotic-green text-robotic-bg rounded-md text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Continue
                </button>
              );
            }
            
            // Show "Pause" when playing
            return (
              <button
                onClick={() => setIsPlaying(false)}
                className="px-4 py-2 bg-robotic-magenta text-white rounded-md text-sm font-semibold hover:bg-robotic-magenta/90 transition-all flex items-center gap-2"
              >
                <Square className="w-4 h-4" />
                Pause
              </button>
            );
          })()}
          <button
            onClick={handleCopyToRoblox}
            className="px-4 py-2 border border-robotic-cyan/30 text-robotic-cyan rounded-md text-sm font-semibold hover:bg-robotic-cyan/10 transition-all flex items-center gap-2"
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
        </div>
      </div>

      {/* Story Game Area */}
      <div className="flex-1 flex flex-col gap-4 p-4 min-h-0">
        {/* Visual Scene Area - How to Play Instructions */}
        <div 
          className="flex-1 bg-robotic-darker rounded-lg border border-robotic-cyan/20 relative overflow-hidden"
          style={{
            background: '#0a0f1a',
            minHeight: '200px',
            position: 'relative'
          }}
        >
          {/* Top border line */}
          <div className="absolute top-0 left-0 right-0 h-px bg-robotic-cyan/30" />

          {/* Story progress dots (only when playing) */}
          {isPlaying && storyHistory.length > 0 && (
            <div className="absolute top-4 left-4 flex gap-2">
              {Array.from({ length: storyHistory.length }).map((_, i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-robotic-cyan/60 border border-robotic-cyan"
                />
              ))}
            </div>
          )}

          {/* How to Play Instructions Overlay */}
          {showHowToPlay && (
            <div className="absolute inset-0 flex items-center justify-center bg-robotic-dark/90 backdrop-blur-sm z-20">
              <div className="w-full max-w-2xl mx-4 p-6 border-2 border-robotic-cyan rounded-lg bg-robotic-dark/95">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-heading font-bold text-robotic-cyan neon-glow flex items-center gap-2">
                    <BookOpen className="w-6 h-6" />
                    How to Play Story Game
                  </h3>
                  <button
                    onClick={() => setShowHowToPlay(false)}
                    className="text-robotic-cyan/60 hover:text-robotic-cyan transition-colors text-xl"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-3 text-left">
                  <div className="flex items-start gap-3 p-3 bg-robotic-darker/50 rounded-lg border border-robotic-cyan/20">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-robotic-cyan/20 border-2 border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">1</div>
                    <div className="flex-1">
                      <h4 className="text-robotic-cyan font-semibold mb-1 text-sm">Click Play to Start</h4>
                      <p className="text-robotic-cyan/70 text-xs">Press the green "Play" button in the header to begin your story adventure.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-robotic-darker/50 rounded-lg border border-robotic-cyan/20">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-robotic-cyan/20 border-2 border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">2</div>
                    <div className="flex-1">
                      <h4 className="text-robotic-cyan font-semibold mb-1 text-sm">Read the Story</h4>
                      <p className="text-robotic-cyan/70 text-xs">Read each story segment carefully. The text appears in the panel below the scene area.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-robotic-darker/50 rounded-lg border border-robotic-cyan/20">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-robotic-cyan/20 border-2 border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">3</div>
                    <div className="flex-1">
                      <h4 className="text-robotic-cyan font-semibold mb-1 text-sm">Make Choices</h4>
                      <p className="text-robotic-cyan/70 text-xs">When you see choice buttons, click one to continue. Each choice affects the story direction.</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-robotic-darker/50 rounded-lg border border-robotic-cyan/20">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-robotic-cyan/20 border-2 border-robotic-cyan flex items-center justify-center text-robotic-cyan font-bold text-xs">4</div>
                    <div className="flex-1">
                      <h4 className="text-robotic-cyan font-semibold mb-1 text-sm">Navigate Your Story</h4>
                      <p className="text-robotic-cyan/70 text-xs">Use "Back" to revisit previous segments or "Restart Story" to explore different paths.</p>
                    </div>
                  </div>
                </div>

                <div className="mt-5 flex gap-3">
                  <button
                    onClick={() => {
                      setShowHowToPlay(false);
                      // Ensure we have a current story before starting
                      if (storySegments.length > 0 && !currentStory) {
                        const firstSegment = storySegments[0];
                        setCurrentSegment(firstSegment.id);
                        setStoryHistory([firstSegment.id]);
                        setCurrentStory(firstSegment);
                      }
                      setIsPlaying(true);
                    }}
                    className="flex-1 px-5 py-2.5 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Start Playing
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

          {/* Pause overlay */}
          {!isPlaying && !showHowToPlay && !isStoryFinished && (
            <div className="absolute inset-0 flex items-center justify-center bg-robotic-dark/70 backdrop-blur-sm z-10">
              <div className="text-center p-6 border-2 border-robotic-cyan rounded-lg bg-robotic-dark/95">
                <Square className="w-12 h-12 text-robotic-cyan mx-auto mb-4" />
                <p className="text-robotic-cyan font-semibold text-lg mb-2">Story Paused</p>
                <p className="text-robotic-cyan/70 text-sm mb-4">Click Continue to resume your adventure from where you left off</p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={() => {
                      // Ensure we have a current story before continuing
                      if (storySegments.length > 0 && !currentStory) {
                        const firstSegment = storySegments[0];
                        setCurrentSegment(firstSegment.id);
                        setStoryHistory([firstSegment.id]);
                        setCurrentStory(firstSegment);
                      }
                      setIsPlaying(true);
                    }}
                    className="px-5 py-2.5 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Continue
                  </button>
                  <button
                    onClick={() => setShowHowToPlay(true)}
                    className="px-5 py-2.5 border-2 border-robotic-cyan text-robotic-cyan rounded-lg text-sm font-semibold hover:bg-robotic-cyan/10 transition-all flex items-center gap-2"
                  >
                    <BookOpen className="w-4 h-4" />
                    How to Play
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Finish overlay - when story ends */}
          {isStoryFinished && isPlaying && (
            <div className="absolute inset-0 flex items-center justify-center bg-robotic-dark/80 backdrop-blur-sm z-10">
              <div className="text-center p-6 border-2 border-robotic-green rounded-lg bg-robotic-dark/95">
                <div className="w-16 h-16 rounded-full bg-robotic-green/20 border-2 border-robotic-green flex items-center justify-center mx-auto mb-4">
                  <span className="text-robotic-green text-2xl font-bold">✓</span>
                </div>
                <p className="text-robotic-green font-semibold text-xl mb-2">Story Complete!</p>
                <p className="text-robotic-cyan/70 text-sm mb-4">You've reached the end of this story path. Restart to explore different choices.</p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={handleRestart}
                    className="px-5 py-2.5 bg-robotic-green text-robotic-bg rounded-lg text-sm font-semibold hover:bg-robotic-green/90 transition-all flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Restart Story
                  </button>
                  <button
                    onClick={() => setIsPlaying(false)}
                    className="px-5 py-2.5 border-2 border-robotic-cyan text-robotic-cyan rounded-lg text-sm font-semibold hover:bg-robotic-cyan/10 transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Scene elements - Show story text in top area when playing or when we have segments */}
          {!showHowToPlay && (() => {
            const storyToShow = currentStory || storySegments.find(s => s.id === currentSegment) || storySegments[0];
            
            // Show story text in top area if playing or if we have segments
            if ((isPlaying || storySegments.length > 0) && storyToShow && storyToShow.text) {
              return (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-8 overflow-y-auto">
                  <div className="w-full max-w-3xl">
                    {/* Speaker name (if dialogue) */}
                    {storyToShow.type === 'dialogue' && storyToShow.speaker && (
                      <div className="flex items-center justify-center gap-2 mb-4">
                        <MessageSquare className="w-5 h-5 text-robotic-cyan" />
                        <span className="text-robotic-cyan font-semibold text-sm">{storyToShow.speaker}</span>
                      </div>
                    )}

                    {/* Story text displayed in top area */}
                    <div 
                      key={`story-text-top-${currentSegment}-${storyToShow.id}`}
                      className="text-lg leading-relaxed mb-6 min-h-[120px] whitespace-pre-wrap font-mono text-center" 
                      style={{ 
                        color: '#0ff0ff',
                        opacity: 1,
                        display: 'block',
                        visibility: 'visible',
                        fontSize: '18px',
                        lineHeight: '1.8',
                        fontWeight: 'normal',
                        padding: '20px'
                      }}
                    >
                      {storyToShow.text}
                    </div>
                  </div>
                </div>
              );
            }
            
            // Fallback if no story
            return (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <BookOpen className="w-16 h-16 text-robotic-cyan/20 mx-auto mb-4" />
                  <div className="text-robotic-cyan/30 text-xs font-mono">
                    {isPlaying ? `Scene ${currentSegment + 1}` : 'Story Scene'}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>

        {/* Choices and Navigation Panel - Bottom area when playing */}
        {isPlaying && !showHowToPlay && (
          <div className="bg-robotic-dark/70 rounded-lg border-2 border-robotic-cyan/30 p-6 backdrop-blur-sm" style={{ display: 'block', visibility: 'visible' }}>
            {(() => {
              // Get the current story - use currentStory if available, otherwise find it
              const storyToShow = currentStory || storySegments.find(s => s.id === currentSegment) || storySegments[0];
              
              if (storyToShow) {
                // Check if story is finished
                const isFinished = !storyToShow.choices || storyToShow.choices.length === 0;
                
                return (
                  <>
                    {/* Finish message when story ends */}
                    {isFinished ? (
                      <div className="text-center py-6">
                        <div className="w-12 h-12 rounded-full bg-robotic-green/20 border-2 border-robotic-green flex items-center justify-center mx-auto mb-4">
                          <span className="text-robotic-green text-xl font-bold">✓</span>
                        </div>
                        <p className="text-robotic-green font-semibold text-lg mb-2">Story Complete!</p>
                        <p className="text-robotic-cyan/70 text-sm mb-6">You've reached the end of this story path.</p>
                      </div>
                    ) : (
                      /* Choices */
                      storyToShow.choices && storyToShow.choices.length > 0 && (
                        <div className="space-y-3">
                          <div className="text-xs text-robotic-cyan/60 mb-2 font-semibold">Choose your path:</div>
                          <div className="grid grid-cols-1 gap-3">
                            {storyToShow.choices.map((choice, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleChoice(choice.nextId)}
                                className="w-full p-4 bg-robotic-dark/50 border-2 border-robotic-cyan/30 rounded-lg hover:border-robotic-cyan hover:bg-robotic-cyan/10 transition-all text-left flex items-center justify-between group"
                              >
                                <span className="text-robotic-cyan/90 text-sm">{choice.text}</span>
                                <ChevronRight className="w-4 h-4 text-robotic-cyan/50 group-hover:text-robotic-cyan group-hover:translate-x-1 transition-all" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )
                    )}

                    {/* Navigation buttons */}
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-robotic-cyan/20">
                      <button
                        onClick={handleGoBack}
                        disabled={storyHistory.length <= 1}
                        className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all disabled:opacity-50 disabled:cursor-not-allowed text-robotic-cyan"
                      >
                        ← Back
                      </button>
                      <button
                        onClick={handleRestart}
                        className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all text-robotic-cyan"
                      >
                        Restart Story
                      </button>
                    </div>
                  </>
                );
              } else {
                // Fallback: show first segment choices
                const firstSegment = storySegments[0];
                return (
                  <>
                    {firstSegment?.choices && firstSegment.choices.length > 0 && (
                      <div className="space-y-3">
                        <div className="text-xs text-robotic-cyan/60 mb-2 font-semibold">Choose your path:</div>
                        <div className="grid grid-cols-1 gap-3">
                          {firstSegment.choices.map((choice, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleChoice(choice.nextId)}
                              className="w-full p-4 bg-robotic-dark/50 border-2 border-robotic-cyan/30 rounded-lg hover:border-robotic-cyan hover:bg-robotic-cyan/10 transition-all text-left flex items-center justify-between group"
                            >
                              <span className="text-robotic-cyan/90 text-sm">{choice.text}</span>
                              <ChevronRight className="w-4 h-4 text-robotic-cyan/50 group-hover:text-robotic-cyan group-hover:translate-x-1 transition-all" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-robotic-cyan/20">
                      <button
                        onClick={handleRestart}
                        className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all text-robotic-cyan"
                      >
                        Restart Story
                      </button>
                    </div>
                  </>
                );
              }
            })()}
          </div>
        )}
        
        {/* Fallback: Show choices panel when not playing if we have segments */}
        {!isPlaying && !showHowToPlay && storySegments.length > 0 && (
          <div className="bg-robotic-dark/70 rounded-lg border-2 border-robotic-cyan/30 p-6 backdrop-blur-sm">
            {storySegments[0]?.choices && storySegments[0].choices.length > 0 && (
              <div className="space-y-3">
                <div className="text-xs text-robotic-cyan/60 mb-2 font-semibold">Choose your path:</div>
                <div className="grid grid-cols-1 gap-3">
                  {storySegments[0].choices.map((choice, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setShowHowToPlay(false);
                        setIsPlaying(true);
                        handleChoice(choice.nextId);
                      }}
                      className="w-full p-4 bg-robotic-dark/50 border-2 border-robotic-cyan/30 rounded-lg hover:border-robotic-cyan hover:bg-robotic-cyan/10 transition-all text-left flex items-center justify-between group"
                    >
                      <span className="text-robotic-cyan/90 text-sm">{choice.text}</span>
                      <ChevronRight className="w-4 h-4 text-robotic-cyan/50 group-hover:text-robotic-cyan group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
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
          className="h-full bg-gradient-to-r from-robotic-cyan to-robotic-green transition-all duration-500"
          style={{ 
            width: `${Math.min(100, ((currentSegment + 1) / storySegments.length) * 100)}%`,
            boxShadow: '0 0 10px rgba(15, 245, 255, 0.5)'
          }}
        />
      </div>
    </div>
  );
}

// Default story for when narrative is too short
const defaultStory: StorySegment[] = [
  {
    id: 0,
    type: 'narrative',
    text: 'You find yourself at the beginning of an adventure. The path ahead is unclear, but your journey begins now.',
    choices: [
      { text: 'Take the left path into the forest', nextId: 1 },
      { text: 'Take the right path toward the mountains', nextId: 2 },
      { text: 'Stay where you are and observe', nextId: 3 }
    ]
  },
  {
    id: 1,
    type: 'narrative',
    text: 'You enter the mysterious forest. Sunlight filters through the canopy above, creating dappled patterns on the forest floor. You hear strange sounds in the distance.',
    choices: [
      { text: 'Investigate the sounds', nextId: 4 },
      { text: 'Continue deeper into the forest', nextId: 5 },
      { text: 'Turn back', nextId: 0 }
    ]
  },
  {
    id: 2,
    type: 'narrative',
    text: 'You begin climbing toward the mountains. The air grows thinner, and you see ancient ruins in the distance. Something glimmers on the path ahead.',
    choices: [
      { text: 'Examine the glimmering object', nextId: 6 },
      { text: 'Head toward the ruins', nextId: 7 },
      { text: 'Turn back', nextId: 0 }
    ]
  },
  {
    id: 3,
    type: 'dialogue',
    speaker: 'Mysterious Voice',
    text: 'Patience is a virtue, but sometimes action is required. What will you choose?',
    choices: [
      { text: 'I\'ll take the left path', nextId: 1 },
      { text: 'I\'ll take the right path', nextId: 2 }
    ]
  },
  {
    id: 4,
    type: 'dialogue',
    speaker: 'Forest Guardian',
    text: 'You discover a friendly forest guardian who offers to help you on your quest. Will you accept their assistance?',
    choices: [
      { text: 'Accept the help gratefully', nextId: 8 },
      { text: 'Politely decline and continue alone', nextId: 5 }
    ]
  },
  {
    id: 5,
    type: 'narrative',
    text: 'You venture deeper into the forest and discover a hidden clearing with ancient symbols. Your adventure continues...',
  },
  {
    id: 6,
    type: 'narrative',
    text: 'You find a magical artifact! It pulses with energy and seems to respond to your touch. Your journey takes an interesting turn.',
  },
  {
    id: 7,
    type: 'narrative',
    text: 'You reach the ruins and find ancient writings that tell of great adventures and legendary heroes. Your story is just beginning...',
  },
  {
    id: 8,
    type: 'dialogue',
    speaker: 'Forest Guardian',
    text: 'Thank you for trusting me. Together, we shall face whatever challenges lie ahead. Your adventure is truly beginning now!',
  }
];

