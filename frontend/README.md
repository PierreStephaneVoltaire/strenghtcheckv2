# Enhanced Powerlifting Analytics Frontend

Modern React TypeScript application for analyzing powerlifting performance with percentile rankings.

## Features

- **Real-time percentile calculator** for squat, bench, deadlift, and total
- **Advanced filtering system** with equipment, age division, and tested status
- **Responsive design** optimized for mobile and desktop
- **Dynamic weight class calculation** based on bodyweight
- **Progressive loading states** with error handling
- **Fallback data** for development without backend

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Modern browser with ES6+ support

### Quick Start
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:5173 (or alternative port if in use)
```

### Data Loading Strategy

The application uses a flexible data loading approach:

1. **Production**: Loads JSON data from the same CloudFront distribution
2. **Development**: Loads from `/public/data/` directory 
3. **Fallback**: Uses embedded sample data if JSON loading fails

#### Data Files Location
```
public/
├── data/
│   ├── percentiles.json    # Percentile data for all filter combinations
│   └── metadata.json       # Filter options and data metadata
```

#### Data Service Features
- Environment-aware data loading (dev vs production)
- Automatic fallback to sample data in development
- Comprehensive error handling and logging
- TypeScript interfaces for data validation

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

The build output in `dist/` can be deployed to any static hosting service.

### Architecture

```
src/
├── components/
│   └── LiftCalculator.tsx     # Main calculator component
├── services/
│   └── dataService.ts         # Data loading and fallback logic
├── types/
│   └── index.ts              # TypeScript interfaces
├── utils/
│   └── percentiles.ts        # Percentile calculation utilities
└── App.tsx                   # Root application component
```

### Key Dependencies

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type safety and developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Heroicons** - Beautiful SVG icons
- **Vite** - Fast build tool and dev server

### Data Integration

The frontend expects JSON data in this format:

**percentiles.json**:
```json
{
  "M_Raw_83_Open_Tested": {
    "percentiles": {
      "squat": [100, 101, 102, ...],    // 99 percentile values
      "bench": [60, 61, 62, ...],       // 99 percentile values  
      "deadlift": [120, 121, 122, ...], // 99 percentile values
      "total": [280, 281, 282, ...]     // 99 percentile values
    },
    "sample_size": 1000,
    "filters": { ... }
  }
}
```

**metadata.json**:
```json
{
  "equipment_types": ["Raw", "Wraps", "Single-ply", "Multi-ply"],
  "weight_classes": {
    "M": ["59", "66", "74", "83", "93", "105", "120", "120+"],
    "F": ["47", "52", "57", "63", "72", "84", "84+"]
  },
  "age_divisions": ["Open", "Junior", "Masters 1", ...],
  "tested_statuses": ["Tested", "Untested"],
  "total_records": 500000,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

### Development Features

- **Hot Module Replacement** - Instant updates during development
- **TypeScript checking** - Compile-time error detection  
- **ESLint integration** - Code quality enforcement
- **Fallback data** - Works without backend during development
- **Console logging** - Data loading status and debugging info

### Deployment

The application is designed to be deployed alongside the data files:

1. **Same-origin deployment**: JSON files served from same domain/CDN
2. **CORS-free**: No cross-origin requests needed
3. **CDN-optimized**: Static files with aggressive caching
4. **Progressive enhancement**: Graceful fallback if data unavailable

For AWS deployment, the frontend and data files are served from the same CloudFront distribution, ensuring fast loading and no CORS issues.