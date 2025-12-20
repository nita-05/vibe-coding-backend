import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Volume2, VolumeX, X, Check, ArrowRight } from 'lucide-react';
import { GenerationResponse } from '../services/api';
import { analyzeScript, generateGuideSteps } from '../utils/scriptAnalyzer';

interface GuideStep {
  id: number;
  title: string;
  instruction: string;
  action?: string;
  completed: boolean;
}

interface InteractiveGuideProps {
  gameType: string;
  isActive: boolean;
  onClose: () => void;
  gameResult?: GenerationResponse | null;
}

export default function InteractiveGuide({ gameType, isActive, onClose, gameResult }: InteractiveGuideProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [steps, setSteps] = useState<GuideStep[]>([]);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    synthRef.current = window.speechSynthesis;
    loadGuideSteps();
  }, [gameType, gameResult]);

  const loadGuideSteps = () => {
    // If we have the actual game result, analyze the script and generate dynamic guide
    if (gameResult && gameResult.lua_script) {
      const mechanics = analyzeScript(gameResult);
      const dynamicSteps = generateGuideSteps(mechanics, gameResult);
      setSteps(dynamicSteps);
      return;
    }

    // Fallback to static guides if no script available
    const guideSteps: Record<string, GuideStep[]> = {
      'fps': [
        {
          id: 1,
          title: 'Welcome to Capture the Flag!',
          instruction: 'You are on the Blue team. Your goal is to capture the Red team flag and return it to your base.',
          action: 'Look around to see the game map',
          completed: false
        },
        {
          id: 2,
          title: 'Find Your Base',
          instruction: 'Look for the Blue flag - that\'s your team\'s base. This is where you need to return the enemy flag.',
          action: 'Walk to the Blue flag location',
          completed: false
        },
        {
          id: 3,
          title: 'Locate Enemy Flag',
          instruction: 'Now find the Red flag - that\'s the enemy team\'s flag you need to capture.',
          action: 'Walk to the Red flag',
          completed: false
        },
        {
          id: 4,
          title: 'Capture the Flag',
          instruction: 'Walk directly into the Red flag to capture it. The flag will attach to you.',
          action: 'Touch the Red flag to capture',
          completed: false
        },
        {
          id: 5,
          title: 'Return to Base',
          instruction: 'Now run back to your Blue base with the captured flag. Avoid obstacles!',
          action: 'Walk back to Blue flag location',
          completed: false
        },
        {
          id: 6,
          title: 'Score a Point!',
          instruction: 'Touch your Blue base to return the flag and score a point for your team!',
          action: 'Touch your base to score',
          completed: false
        }
      ],
      'obby': [
        {
          id: 1,
          title: 'Welcome to the Obby!',
          instruction: 'Your goal is to reach the finish line by jumping on platforms and avoiding obstacles.',
          action: 'Start moving forward',
          completed: false
        },
        {
          id: 2,
          title: 'Jump on Platforms',
          instruction: 'Use W, A, S, D to move and Space to jump. Jump onto the platforms ahead.',
          action: 'Jump onto the first platform',
          completed: false
        },
        {
          id: 3,
          title: 'Avoid Obstacles',
          instruction: 'Watch out for moving obstacles and gaps. Time your jumps carefully.',
          action: 'Navigate past obstacles',
          completed: false
        },
        {
          id: 4,
          title: 'Reach Checkpoints',
          instruction: 'Touch checkpoints to save your progress. If you fall, you\'ll respawn at the last checkpoint.',
          action: 'Touch the checkpoint',
          completed: false
        },
        {
          id: 5,
          title: 'Finish the Course',
          instruction: 'Keep going until you reach the finish line at the end of the course!',
          action: 'Reach the finish line',
          completed: false
        }
      ],
      'tycoon': [
        {
          id: 1,
          title: 'Welcome to Your Tycoon!',
          instruction: 'Your goal is to build and expand your business to earn money and unlock upgrades.',
          action: 'Look around your tycoon base',
          completed: false
        },
        {
          id: 2,
          title: 'Collect Money',
          instruction: 'Walk over money generators to collect coins. Your money will automatically increase over time.',
          action: 'Walk to money generators',
          completed: false
        },
        {
          id: 3,
          title: 'Buy Upgrades',
          instruction: 'Click on upgrade stations to purchase improvements. Each upgrade makes your tycoon more profitable.',
          action: 'Click upgrade buttons',
          completed: false
        },
        {
          id: 4,
          title: 'Expand Your Base',
          instruction: 'Use your earnings to build new structures and expand your tycoon empire!',
          action: 'Build new structures',
          completed: false
        }
      ],
      'racing': [
        {
          id: 1,
          title: 'Welcome to the Race!',
          instruction: 'Click "Start Race" to begin! Your goal is to complete all laps around the track as fast as possible.',
          action: 'Click the Start Race button',
          completed: false
        },
        {
          id: 2,
          title: 'Learn the Controls',
          instruction: 'Use Arrow Keys or WASD to drive. ↑ or W to accelerate, ↓ or S to brake, ← → or A D to steer left and right.',
          action: 'Try moving your car with the keys',
          completed: false
        },
        {
          id: 3,
          title: 'Pass Checkpoints',
          instruction: 'Drive through the glowing checkpoints around the track. Each checkpoint you pass gives you boost power!',
          action: 'Drive through a checkpoint',
          completed: false
        },
        {
          id: 4,
          title: 'Use Boost',
          instruction: 'Press Spacebar to activate your boost when you have enough boost power. This gives you a temporary speed boost!',
          action: 'Press Spacebar to use boost',
          completed: false
        },
        {
          id: 5,
          title: 'Complete Laps',
          instruction: 'Pass all checkpoints to complete a lap. You need to complete multiple laps to finish the race. Watch your lap counter!',
          action: 'Complete your first lap',
          completed: false
        },
        {
          id: 6,
          title: 'Finish the Race!',
          instruction: 'Complete all laps and beat your best time! Try to improve your record with each race.',
          action: 'Finish the race',
          completed: false
        }
      ],
      'story': [
        {
          id: 1,
          title: 'Welcome to Your Story!',
          instruction: 'You are about to embark on an interactive narrative adventure. Read each story segment carefully and make choices that shape your journey.',
          action: 'Click Play to begin',
          completed: false
        },
        {
          id: 2,
          title: 'Read the Story',
          instruction: 'Each scene contains narrative text or dialogue. Take your time to read and understand what is happening in the story.',
          action: 'Read the current story segment',
          completed: false
        },
        {
          id: 3,
          title: 'Make Choices',
          instruction: 'When you see choice buttons, click on one to continue. Each choice affects the direction of your story.',
          action: 'Select a choice to progress',
          completed: false
        },
        {
          id: 4,
          title: 'Explore Different Paths',
          instruction: 'You can go back to previous segments or restart the story to explore different narrative paths and endings.',
          action: 'Try different choices to see different outcomes',
          completed: false
        }
      ],
      'simulator': [
        {
          id: 1,
          title: 'Welcome to the Simulator!',
          instruction: 'This is an incremental simulator game. Your goal is to earn money, buy upgrades, and progress through levels. The more you play, the more you earn!',
          action: 'Click Play to start',
          completed: false
        },
        {
          id: 2,
          title: 'Click to Earn',
          instruction: 'Click anywhere on the main game area to earn money. Each click gives you coins that you can use to buy upgrades.',
          action: 'Click on the blue game area',
          completed: false
        },
        {
          id: 3,
          title: 'Buy Upgrades',
          instruction: 'Use your earned money to purchase upgrades from the right panel. Start with Click Power to earn more per click, then buy Auto Clickers for passive income.',
          action: 'Purchase your first upgrade',
          completed: false
        },
        {
          id: 4,
          title: 'Auto Income',
          instruction: 'Auto Clickers and Money Generators provide passive income that earns money automatically over time. Upgrade these to maximize your earnings!',
          action: 'Buy an Auto Clicker or Generator',
          completed: false
        },
        {
          id: 5,
          title: 'Level Up',
          instruction: 'As you earn more money, you level up automatically. Higher levels unlock better opportunities and bonuses.',
          action: 'Earn money to level up',
          completed: false
        },
        {
          id: 6,
          title: 'Rebirth System',
          instruction: 'Once you have enough money, you can Rebirth to reset your progress but gain permanent bonuses. This allows you to progress faster each time!',
          action: 'Save up for a Rebirth upgrade',
          completed: false
        }
      ],
      'default': [
        {
          id: 1,
          title: 'Game Started!',
          instruction: 'Follow the on-screen instructions to play the game. Complete each step to progress.',
          action: 'Follow the instructions',
          completed: false
        }
      ]
    };

    const gameSteps = guideSteps[gameType.toLowerCase()] || guideSteps['default'];
    setSteps(gameSteps);
  };

  const speak = (text: string) => {
    if (!voiceEnabled || !synthRef.current) return;
    
    // Cancel any ongoing speech
    synthRef.current.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    // Try to use a friendly voice
    const voices = synthRef.current.getVoices();
    const preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Microsoft')) || voices[0];
    if (preferredVoice) utterance.voice = preferredVoice;
    
    synthRef.current.speak(utterance);
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      const newStep = currentStep + 1;
      setCurrentStep(newStep);
      markStepComplete(currentStep);
      
      if (voiceEnabled && steps[newStep]) {
        speak(`${steps[newStep].title}. ${steps[newStep].instruction}`);
      }
    } else {
      // All steps complete
      if (voiceEnabled) {
        speak('Congratulations! You\'ve completed the guide. Have fun playing!');
      }
      onClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const markStepComplete = (stepIndex: number) => {
    setSteps(prev => prev.map((step, idx) => 
      idx === stepIndex ? { ...step, completed: true } : step
    ));
  };

  const togglePlayPause = () => {
    if (isPlaying) {
      synthRef.current?.pause();
    } else {
      synthRef.current?.resume();
      if (steps[currentStep]) {
        speak(`${steps[currentStep].title}. ${steps[currentStep].instruction}`);
      }
    }
    setIsPlaying(!isPlaying);
  };

  const toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
    if (voiceEnabled) {
      synthRef.current?.cancel();
    } else if (steps[currentStep]) {
      speak(`${steps[currentStep].title}. ${steps[currentStep].instruction}`);
    }
  };

  useEffect(() => {
    if (isActive && steps.length > 0 && voiceEnabled) {
      speak(`${steps[currentStep].title}. ${steps[currentStep].instruction}`);
    }
    
    return () => {
      synthRef.current?.cancel();
    };
  }, [isActive, currentStep, steps, voiceEnabled]);

  if (!isActive || steps.length === 0) return null;

  const currentStepData = steps[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto" onClick={onClose} />
      
      {/* Guide Card */}
      <div className="relative w-full max-w-2xl mx-4 bg-robotic-dark/95 border-2 border-robotic-cyan rounded-lg p-6 pointer-events-auto neon-glow">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-robotic-cyan/20 border-2 border-robotic-cyan flex items-center justify-center">
              <span className="text-robotic-cyan font-bold">{currentStep + 1}</span>
            </div>
            <div>
              <h3 className="text-xl font-heading font-bold text-robotic-cyan neon-glow">
                Interactive Guide
              </h3>
              <p className="text-sm text-robotic-cyan/60">
                Step {currentStep + 1} of {steps.length}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleVoice}
              className="p-2 rounded border border-robotic-cyan/30 hover:neon-border transition-all"
              title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
            >
              {voiceEnabled ? (
                <Volume2 className="w-5 h-5 text-robotic-cyan" />
              ) : (
                <VolumeX className="w-5 h-5 text-robotic-cyan/50" />
              )}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded border border-robotic-cyan/30 hover:neon-border transition-all"
            >
              <X className="w-5 h-5 text-robotic-cyan" />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex gap-2 mb-2">
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className={`flex-1 h-2 rounded ${
                  idx < currentStep
                    ? 'bg-robotic-green'
                    : idx === currentStep
                    ? 'bg-robotic-cyan'
                    : 'bg-robotic-cyan/20'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Current Step Content */}
        <div className="mb-6">
          <h4 className="text-2xl font-heading font-bold text-robotic-cyan mb-3 neon-glow">
            {currentStepData.title}
          </h4>
          <p className="text-lg text-robotic-cyan/90 mb-4 leading-relaxed">
            {currentStepData.instruction}
          </p>
          {currentStepData.action && (
            <div className="p-4 bg-robotic-darker/50 rounded border border-robotic-green/30">
              <p className="text-sm font-semibold text-robotic-green mb-1 flex items-center gap-2">
                <ArrowRight className="w-4 h-4" />
                Your Action:
              </p>
              <p className="text-robotic-cyan/80">{currentStepData.action}</p>
            </div>
          )}
        </div>

        {/* Step List */}
        <div className="mb-6 max-h-32 overflow-y-auto">
          <div className="space-y-2">
            {steps.map((step, idx) => (
              <div
                key={step.id}
                className={`flex items-center gap-3 p-2 rounded ${
                  idx === currentStep
                    ? 'bg-robotic-cyan/20 border border-robotic-cyan'
                    : idx < currentStep
                    ? 'bg-robotic-green/10 border border-robotic-green/30'
                    : 'bg-robotic-dark/50 border border-robotic-cyan/10'
                }`}
              >
                {idx < currentStep ? (
                  <Check className="w-5 h-5 text-robotic-green flex-shrink-0" />
                ) : (
                  <div className={`w-5 h-5 rounded-full border-2 flex-shrink-0 ${
                    idx === currentStep
                      ? 'border-robotic-cyan bg-robotic-cyan/20'
                      : 'border-robotic-cyan/30'
                  }`} />
                )}
                <span className={`text-sm ${
                  idx === currentStep
                    ? 'text-robotic-cyan font-semibold'
                    : idx < currentStep
                    ? 'text-robotic-green'
                    : 'text-robotic-cyan/60'
                }`}>
                  {step.title}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="px-4 py-2 border border-robotic-cyan/30 rounded text-sm hover:neon-border transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          <div className="flex items-center gap-2">
            <button
              onClick={togglePlayPause}
              className="p-2 rounded border border-robotic-cyan/30 hover:neon-border transition-all"
            >
              {isPlaying ? (
                <Pause className="w-5 h-5 text-robotic-cyan" />
              ) : (
                <Play className="w-5 h-5 text-robotic-cyan" />
              )}
            </button>
          </div>

          <button
            onClick={handleNext}
            className="px-6 py-2 bg-robotic-cyan text-robotic-bg rounded text-sm font-heading font-semibold hover:bg-robotic-cyan/90 transition-all flex items-center gap-2 neon-glow"
          >
            {currentStep < steps.length - 1 ? 'Next Step' : 'Finish Guide'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

