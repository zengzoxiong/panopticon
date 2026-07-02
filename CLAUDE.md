# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Panopticon is a web-based military simulation platform compatible with OpenAI Gym. The project consists of two main components:

- **client/**: React + TypeScript frontend with Vite build system
- **gym/**: Python package (BLADE) for reinforcement learning environment

## Development Commands

### Client (Frontend)

```bash
cd client

# Install dependencies
npm install

# Start development server (port 3000)
npm run start
# or
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Format code
npm run format

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test suites
npm run test:game      # Game logic tests
npm run test:units     # Unit tests
npm run test:utils     # Utility tests
```

### Gym (Python Backend)

```bash
cd gym

# Create and activate virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install in editable mode
pip install -e .

# Install with gym dependencies
pip install -e .[gym]

# Run demo script
python scripts/simple_demo/demo.py
```

## Architecture

### Client Architecture

The client is a React application using TypeScript and Vite:

**Core Game Logic** (`src/game/`):
- `Game.ts`: Main game controller managing simulation state, time compression, and unit interactions
- `Scenario.ts`: Scenario configuration and unit management
- `Side.ts`: Represents military factions/sides in simulation
- `Doctrine.ts`: Military doctrine and rules of engagement
- `Relationships.ts`: Diplomatic relationships between sides

**Unit Types** (`src/game/units/`):
- `Aircraft.ts`: Aircraft units with flight dynamics
- `Ship.ts`: Naval vessels
- `Airbase.ts`: Military airbases
- `Facility.ts`: Ground facilities
- `Weapon.ts`: Weapon systems
- `ReferencePoint.ts`: Geographic reference points

**Mission System** (`src/game/mission/`):
- `PatrolMission.ts`: Patrol route management
- `StrikeMission.ts`: Strike mission coordination

**Combat Engine** (`src/game/engine/`):
- `weaponEngagement.ts`: Weapon engagement logic, threat detection, and targeting

**GUI Layer** (`src/gui/`):
- `map/`: OpenLayers-based map visualization
- `mapLayers/`: Map layer management (base maps, features, styles)

**Database** (`src/game/db/`):
- `UnitDb.ts`: Unit database and lookups
- `models/`: Data models for different unit types

### Gym Architecture

The gym package provides an OpenAI Gym-compatible environment:

**Core Components** (`blade/`):
- `Game.py`: Python implementation of game logic
- `Scenario.py`: Scenario management
- `Side.py`: Military side representation
- `envs/blade.py`: Gymnasium environment wrapper (`BLADE` class)

**Key Features**:
- Observation and action spaces using Gymnasium's Text space
- Configurable reward, observation, and termination filters
- Integration with stable-baselines3 for RL training

### Data Flow

1. Scenarios are defined in JSON format (see `client/src/scenarios/`)
2. `Scenario.ts` loads and parses scenario data
3. `Game.ts` manages simulation loop and unit updates
4. `weaponEngagement.ts` handles combat calculations
5. GUI components render state on OpenLayers map

## Testing

Tests use Vitest with jsdom environment:

- Test files: `*.spec.ts` colocated with source files
- Setup: `src/testing/setup.ts`
- Helpers: `src/testing/helpers.ts`

## Code Style

- TypeScript strict mode enabled
- ESLint + Prettier for formatting
- Path aliases: `@/` maps to `src/`

## Key Dependencies

**Client**:
- React 18 with TypeScript
- OpenLayers (ol) for map visualization
- MUI (Material-UI) for UI components
- Auth0 for authentication
- Vite for build tooling

**Gym**:
- Python 3.12.3
- Gymnasium 0.29.1
- stable-baselines3 2.4.1
- Shapely for geometric operations
