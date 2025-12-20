import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import PromptWorkbench from '../components/PromptWorkbench';
import CodePreview from '../components/CodePreview';
import GamePreview from '../components/GamePreview';
import { 
  generateScript, 
  saveDraft, 
  getBlueprints,
  GenerationRequest,
  GenerationResponse,
  BlueprintInfo 
} from '../services/api';
import { Zap, Code2, Gamepad2 } from 'lucide-react';

export default function Home() {
  const [result, setResult] = useState<GenerationResponse | null>(null);
  const [blueprints, setBlueprints] = useState<BlueprintInfo[]>([]);
  const [generationKey, setGenerationKey] = useState(0); // Force re-render key

  // Fetch blueprints on mount
  const { data: blueprintsData } = useQuery({
    queryKey: ['blueprints'],
    queryFn: getBlueprints,
  });

  useEffect(() => {
    if (blueprintsData) {
      setBlueprints(blueprintsData);
    }
  }, [blueprintsData]);

  // Generate script mutation
  const generateMutation = useMutation({
    mutationFn: (request: GenerationRequest) => generateScript(request),
    onMutate: () => {
      // Clear previous result immediately when mutation starts
      setResult(null);
    },
    onSuccess: (data) => {
      // Only set result when new data arrives
      setResult(data);
      // Auto-save to localStorage (optional - can remove if you don't want persistence)
      localStorage.setItem('lastGeneration', JSON.stringify(data));
    },
    onError: (error: any) => {
      console.error('Generation error:', error);
      // Clear result on error to show fresh state
      setResult(null);
      alert(`Failed to generate script: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Save draft mutation
  const saveDraftMutation = useMutation({
    mutationFn: saveDraft,
    onSuccess: () => {
      alert('Draft saved successfully!');
    },
    onError: (error: any) => {
      console.error('Save error:', error);
      alert(`Failed to save draft: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleGenerate = (prompt: string, blueprintId?: string, settings?: any) => {
    // Clear previous result immediately when generating new script
    // This happens BEFORE the mutation starts
    setResult(null);
    
    // Increment generation key to force complete re-render of child components
    setGenerationKey(prev => prev + 1);
    
    // Store prompt for draft saving
    localStorage.setItem('lastPrompt', prompt);
    
    // Generate new script - onMutate will also clear result as backup
    generateMutation.mutate({
      prompt,
      blueprint_id: blueprintId,
      settings,
    });
  };

  const handleSaveDraft = () => {
    if (!result) return;
    
    // Get last prompt from localStorage or use default
    const lastPrompt = localStorage.getItem('lastPrompt') || 'Generated script';
    
    saveDraftMutation.mutate({
      prompt: lastPrompt,
      result,
    });
  };

  // DON'T load from localStorage on mount - start fresh every time
  // This ensures new generations always show fresh results
  // Commented out to prevent old data from showing
  // useEffect(() => {
  //   const lastGen = localStorage.getItem('lastGeneration');
  //   if (lastGen && !result) {
  //     try {
  //       const parsed = JSON.parse(lastGen);
  //       setResult(parsed);
  //     } catch (e) {
  //       console.error('Failed to load last generation:', e);
  //       localStorage.removeItem('lastGeneration');
  //     }
  //   }
  // }, []);

  return (
    <div className="min-h-screen bg-robotic-bg grid-bg overflow-x-hidden">
      {/* Header */}
      <header className="border-b border-robotic-cyan/20 bg-robotic-dark/30 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 border-2 border-robotic-cyan rounded flex items-center justify-center neon-glow">
                <Zap className="w-6 h-6 text-robotic-cyan" />
              </div>
              <div>
                <h1 className="text-2xl font-heading font-bold neon-glow">Vibe Coding</h1>
                <p className="text-xs text-robotic-cyan/60">Create Roblox Games from Text</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#create" className="text-sm text-robotic-cyan/70 hover:text-robotic-cyan transition-colors flex items-center gap-2">
                <Code2 className="w-4 h-4" />
                Create
              </a>
              <a href="#preview" className="text-sm text-robotic-cyan/70 hover:text-robotic-cyan transition-colors flex items-center gap-2">
                <Gamepad2 className="w-4 h-4" />
                Preview
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Left Column: Prompt Workbench */}
          <div className="space-y-6 flex flex-col">
            <PromptWorkbench
              onGenerate={handleGenerate}
              blueprints={blueprints}
              isLoading={generateMutation.isPending}
            />
            
            {/* Code Preview */}
            <div className="flex-1 min-h-[400px]">
              <CodePreview
                key={`code-${generationKey}-${result?.title || 'empty'}`} // Force complete re-render on new generation
                result={result}
                onSaveDraft={handleSaveDraft}
              />
            </div>
          </div>

          {/* Right Column: Game Preview */}
          <div className="flex flex-col min-h-[400px]">
            <GamePreview
              key={`game-${generationKey}-${result?.title || 'empty'}`} // Force complete re-render on new generation
              result={result}
              gameUrl={undefined} // Will be set when Roblox integration is added
            />
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 pt-8 border-t border-robotic-cyan/20 pb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-heading font-bold text-robotic-cyan mb-2">AI-Powered</div>
              <p className="text-xs md:text-sm text-robotic-cyan/60 px-2">
                Advanced AI translates your ideas into production-ready Roblox Lua scripts
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-heading font-bold text-robotic-cyan mb-2">Instant Preview</div>
              <p className="text-xs md:text-sm text-robotic-cyan/60 px-2">
                See your games come to life with real-time preview and testing
              </p>
            </div>
            <div className="text-center">
              <div className="text-2xl md:text-3xl font-heading font-bold text-robotic-cyan mb-2">Export Ready</div>
              <p className="text-xs md:text-sm text-robotic-cyan/60 px-2">
                Export scripts directly to Roblox Studio for immediate use
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

