import { GenerationResponse } from '../services/api';

export interface GameMechanics {
  gameType: string;
  hasTeams: boolean;
  teams: string[];
  hasFlags: boolean;
  flagColors: string[];
  hasWeapons: boolean;
  hasHealthPacks: boolean;
  hasSpawnPoints: boolean;
  hasCheckpoints: boolean;
  hasPlatforms: boolean;
  hasObstacles: boolean;
  hasPowerUps: boolean;
  hasLeaderboard: boolean;
  hasScoring: boolean;
  interactionMethod: 'touch' | 'click' | 'proximity' | 'auto';
  objectives: string[];
  mechanics: string[];
}

export function analyzeScript(result: GenerationResponse): GameMechanics {
  const script = result.lua_script.toLowerCase();
  const title = result.title.toLowerCase();
  const narrative = result.narrative.toLowerCase();
  
  // Detect game type
  let gameType = 'default';
  if (script.includes('capture') || script.includes('flag') || title.includes('capture') || title.includes('flag') || narrative.includes('capture the flag')) {
    gameType = 'fps';
  } else if (script.includes('obby') || script.includes('obstacle') || script.includes('platform') || title.includes('obby') || title.includes('obstacle')) {
    gameType = 'obby';
  } else if (script.includes('tycoon') || script.includes('money') || script.includes('upgrade') || title.includes('tycoon')) {
    gameType = 'tycoon';
  } else if (script.includes('race') || script.includes('lap') || script.includes('checkpoint') || title.includes('racing') || title.includes('race')) {
    gameType = 'racing';
  } else if (script.includes('simulator') || title.includes('simulator')) {
    gameType = 'simulator';
  } else if (script.includes('story') || script.includes('narrative') || script.includes('dialogue') || script.includes('choice') || title.includes('story') || narrative.includes('story')) {
    gameType = 'story';
  }

  // Detect teams
  const hasTeams = script.includes('team') || script.includes('teams');
  const teams: string[] = [];
  if (script.includes('red team') || script.includes('redteam') || script.includes('team.red')) {
    teams.push('Red');
  }
  if (script.includes('blue team') || script.includes('blueteam') || script.includes('team.blue')) {
    teams.push('Blue');
  }
  if (script.includes('green team') || script.includes('greenteam')) {
    teams.push('Green');
  }
  if (script.includes('yellow team') || script.includes('yellowteam')) {
    teams.push('Yellow');
  }

  // Detect flags
  const hasFlags = script.includes('flag') || script.includes('redflag') || script.includes('blueflag');
  const flagColors: string[] = [];
  if (script.includes('red flag') || script.includes('redflag') || script.includes('flag.red')) {
    flagColors.push('Red');
  }
  if (script.includes('blue flag') || script.includes('blueflag') || script.includes('flag.blue')) {
    flagColors.push('Blue');
  }

  // Detect game elements
  const hasWeapons = script.includes('weapon') || script.includes('gun') || script.includes('rifle') || script.includes('sword');
  const hasHealthPacks = script.includes('health') || script.includes('heal') || script.includes('medkit');
  const hasSpawnPoints = script.includes('spawn') || script.includes('respawn');
  const hasCheckpoints = script.includes('checkpoint') || script.includes('check point');
  const hasPlatforms = script.includes('platform') || script.includes('part.new') || script.includes('instance.new(\'part\')');
  const hasObstacles = script.includes('obstacle') || script.includes('barrier') || script.includes('wall');
  const hasPowerUps = script.includes('powerup') || script.includes('power-up') || script.includes('boost');
  const hasLeaderboard = script.includes('leaderboard') || script.includes('leaderstats') || script.includes('leader board');
  const hasScoring = script.includes('score') || script.includes('point') || script.includes('win');

  // Detect interaction method
  let interactionMethod: 'touch' | 'click' | 'proximity' | 'auto' = 'touch';
  if (script.includes('touched') || script.includes('touch')) {
    interactionMethod = 'touch';
  } else if (script.includes('clicked') || script.includes('mouseclick') || script.includes('click')) {
    interactionMethod = 'click';
  } else if (script.includes('proximity') || script.includes('magnitude') || script.includes('distance')) {
    interactionMethod = 'proximity';
  } else if (script.includes('automatic') || script.includes('auto')) {
    interactionMethod = 'auto';
  }

  // Extract objectives
  const objectives: string[] = [];
  if (hasFlags && hasTeams) {
    objectives.push('Capture the enemy flag');
    objectives.push('Return flag to your base');
    objectives.push('Defend your flag');
  }
  if (hasCheckpoints) {
    objectives.push('Reach checkpoints');
  }
  if (hasPlatforms && gameType === 'obby') {
    objectives.push('Jump on platforms');
    objectives.push('Avoid obstacles');
    objectives.push('Reach the finish');
  }
  if (hasScoring) {
    objectives.push('Score points');
  }

  // Extract mechanics
  const mechanics: string[] = [];
  if (hasTeams) {
    mechanics.push('Team-based gameplay');
  }
  if (hasWeapons) {
    mechanics.push('Weapon system');
  }
  if (hasHealthPacks) {
    mechanics.push('Health system');
  }
  if (hasSpawnPoints) {
    mechanics.push('Respawn system');
  }
  if (hasPowerUps) {
    mechanics.push('Power-up collection');
  }
  if (hasLeaderboard) {
    mechanics.push('Leaderboard tracking');
  }

  return {
    gameType,
    hasTeams,
    teams: teams.length > 0 ? teams : (hasTeams ? ['Red', 'Blue'] : []),
    hasFlags,
    flagColors: flagColors.length > 0 ? flagColors : (hasFlags ? ['Red', 'Blue'] : []),
    hasWeapons,
    hasHealthPacks,
    hasSpawnPoints,
    hasCheckpoints,
    hasPlatforms,
    hasObstacles,
    hasPowerUps,
    hasLeaderboard,
    hasScoring,
    interactionMethod,
    objectives,
    mechanics
  };
}

export function generateGuideSteps(mechanics: GameMechanics, result: GenerationResponse): Array<{
  id: number;
  title: string;
  instruction: string;
  action?: string;
  completed: boolean;
}> {
  const steps: Array<{
    id: number;
    title: string;
    instruction: string;
    action?: string;
    completed: boolean;
  }> = [];

  let stepId = 1;

  // Welcome step
  steps.push({
    id: stepId++,
    title: `Welcome to ${result.title}!`,
    instruction: result.narrative || `Your goal is to play and enjoy this ${mechanics.gameType} game.`,
    action: 'Look around the game world',
    completed: false
  });

  // Team assignment (if applicable)
  if (mechanics.hasTeams && mechanics.teams.length > 0) {
    const teamName = mechanics.teams[0]; // Default to first team
    steps.push({
      id: stepId++,
      title: `You're on the ${teamName} Team`,
      instruction: `You have been assigned to the ${teamName} team. Your team color is ${teamName.toLowerCase()}. Work with your team to achieve victory!`,
      action: `Check your team color - you should see ${teamName} indicators`,
      completed: false
    });
  }

  // Find base/starting point
  if (mechanics.hasFlags || mechanics.hasSpawnPoints) {
    if (mechanics.hasFlags && mechanics.flagColors.length > 0) {
      const playerTeam = mechanics.teams[0] || 'Blue';
      const playerFlag = mechanics.flagColors.find(c => c === playerTeam) || mechanics.flagColors[0];
      steps.push({
        id: stepId++,
        title: `Find Your ${playerFlag} Base`,
        instruction: `Look for the ${playerFlag} flag - that's your team's base. This is where you spawn and where you need to return captured items.`,
        action: `Walk to the ${playerFlag} flag location`,
        completed: false
      });
    } else if (mechanics.hasSpawnPoints) {
      steps.push({
        id: stepId++,
        title: 'Find Your Spawn Point',
        instruction: 'Your spawn point is where you appear when the game starts or after respawning. Remember this location!',
        action: 'Locate your spawn point',
        completed: false
      });
    }
  }

  // Locate enemy/objective
  if (mechanics.hasFlags && mechanics.flagColors.length > 1) {
    const enemyFlag = mechanics.flagColors.find(c => c !== mechanics.teams[0]) || mechanics.flagColors[1];
    steps.push({
      id: stepId++,
      title: `Locate the ${enemyFlag} Flag`,
      instruction: `Find the ${enemyFlag} flag - that's the enemy team's flag you need to capture. It should be at their base.`,
      action: `Walk to the ${enemyFlag} flag`,
      completed: false
    });
  }

  // Collect items
  if (mechanics.hasWeapons) {
    steps.push({
      id: stepId++,
      title: 'Collect Weapons',
      instruction: `Weapons are scattered around the map. ${mechanics.interactionMethod === 'touch' ? 'Walk over them' : mechanics.interactionMethod === 'click' ? 'Click on them' : 'Find and collect them'} to arm yourself.`,
      action: 'Find and collect a weapon',
      completed: false
    });
  }

  if (mechanics.hasHealthPacks) {
    steps.push({
      id: stepId++,
      title: 'Find Health Packs',
      instruction: `Health packs restore your health. ${mechanics.interactionMethod === 'touch' ? 'Walk over them' : mechanics.interactionMethod === 'click' ? 'Click on them' : 'Collect them'} when your health is low.`,
      action: 'Locate a health pack',
      completed: false
    });
  }

  if (mechanics.hasPowerUps) {
    steps.push({
      id: stepId++,
      title: 'Collect Power-ups',
      instruction: `Power-ups give you special abilities like speed boosts or shields. ${mechanics.interactionMethod === 'touch' ? 'Walk over them' : 'Collect them'} to gain advantages.`,
      action: 'Collect a power-up',
      completed: false
    });
  }

  // Main objective
  if (mechanics.hasFlags && mechanics.objectives.includes('Capture the enemy flag')) {
    const enemyFlag = mechanics.flagColors.find(c => c !== mechanics.teams[0]) || mechanics.flagColors[1];
    steps.push({
      id: stepId++,
      title: `Capture the ${enemyFlag} Flag`,
      instruction: `${mechanics.interactionMethod === 'touch' ? 'Walk directly into' : mechanics.interactionMethod === 'click' ? 'Click on' : 'Interact with'} the ${enemyFlag} flag to capture it. The flag will attach to you or follow you.`,
      action: `${mechanics.interactionMethod === 'touch' ? 'Touch' : mechanics.interactionMethod === 'click' ? 'Click' : 'Capture'} the ${enemyFlag} flag`,
      completed: false
    });
  }

  if (mechanics.hasCheckpoints && mechanics.gameType === 'obby') {
    steps.push({
      id: stepId++,
      title: 'Reach Checkpoints',
      instruction: 'Touch checkpoints to save your progress. If you fall, you\'ll respawn at the last checkpoint you reached.',
      action: 'Touch a checkpoint',
      completed: false
    });
  }

  if (mechanics.hasPlatforms && mechanics.gameType === 'obby') {
    steps.push({
      id: stepId++,
      title: 'Navigate Platforms',
      instruction: 'Use W, A, S, D to move and Space to jump. Jump onto platforms and avoid falling. Time your jumps carefully!',
      action: 'Jump onto the platforms',
      completed: false
    });
  }

  // Return/Score
  if (mechanics.hasFlags && mechanics.objectives.includes('Return flag to your base')) {
    const playerTeam = mechanics.teams[0] || 'Blue';
    steps.push({
      id: stepId++,
      title: `Return to Your ${playerTeam} Base`,
      instruction: `Now run back to your ${playerTeam} base with the captured flag. ${mechanics.hasObstacles ? 'Avoid obstacles and enemies!' : 'Get there as fast as you can!'}`,
      action: `Walk back to ${playerTeam} base`,
      completed: false
    });

    steps.push({
      id: stepId++,
      title: 'Score a Point!',
      instruction: `${mechanics.interactionMethod === 'touch' ? 'Touch' : mechanics.interactionMethod === 'click' ? 'Click on' : 'Return to'} your base to return the flag and score a point for your team!`,
      action: `${mechanics.interactionMethod === 'touch' ? 'Touch' : 'Return to'} your base to score`,
      completed: false
    });
  }

  if (mechanics.hasCheckpoints && mechanics.gameType === 'obby') {
    steps.push({
      id: stepId++,
      title: 'Finish the Course!',
      instruction: 'Keep going until you reach the finish line at the end of the course. Complete all checkpoints!',
      action: 'Reach the finish line',
      completed: false
    });
  }

  // Final step
  steps.push({
    id: stepId++,
    title: 'Have Fun Playing!',
    instruction: 'You now know how to play! Practice and improve your skills. Good luck!',
    action: 'Continue playing and exploring',
    completed: false
  });

  return steps;
}

