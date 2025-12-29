# Sparkback Roadmap: Real-time Monitoring Features

This roadmap outlines the path to adding btop-style real-time monitoring capabilities to sparkback.

## Current State

- ✅ Single-line sparklines (default, block, ascii, numeric, braille, arrows)
- ✅ Multi-line vertical bar charts (10 lines tall)
- ✅ Static output (print once and exit)
- ✅ Basic statistics computation

## Phase 1: Enhanced Graph Rendering

**Goal**: Better line graph visualization with connected points

- [x] Add `LineGraphStyle` class that connects data points with lines
  - Use Unicode box-drawing characters (─│╱╲●)
  - Support diagonal connections (╱╲)
  - Configurable graph height (default: 10 lines)
  - Full type hints and comprehensive test coverage
- [ ] Add `SmoothLineGraphStyle` using Braille patterns for sub-character resolution
- [ ] Support multiple line styles: stepped, linear interpolation, bezier curves
- [ ] Add grid rendering (optional background grid)
- [ ] Add corner characters (┌┐└┘) for better line joining

**Deliverable**: `spark --ticks line 1 5 3 8 2 9 4` renders a connected line graph

## Phase 2: Dynamic Data Handling

**Goal**: Handle streaming data with fixed-width windows

- [ ] Create `DataWindow` class for managing fixed-width sliding buffers
  - Configure window size (e.g., last 60 data points)
  - Auto-scroll as new data arrives
- [ ] Add `TimeSeriesData` class with timestamps
- [ ] Support data aggregation (min/max/avg over time buckets)
- [ ] Add data sampling strategies for downsampling large datasets

**Deliverable**: API to push data points and maintain a rolling window

## Phase 3: Real-time Terminal Updates

**Goal**: Refresh graphs in-place instead of scrolling output

- [ ] Add terminal control library (choose: blessed, rich, or curses)
- [ ] Implement `LiveGraph` class for in-place updates
  - Clear and redraw at fixed intervals
  - Handle terminal resize events
- [ ] Add frame rate control (e.g., 1 FPS, 10 FPS)
- [ ] Support color gradients (low/medium/high thresholds)
- [ ] Add keyboard controls (pause/resume, zoom, quit)

**Deliverable**: `spark --live --source <command>` updates graph in real-time

## Phase 4: Layout and Composition

**Goal**: Display multiple graphs simultaneously

- [ ] Create `Panel` class for rectangular graph containers
- [ ] Implement `GridLayout` for arranging multiple panels
  - Support rows and columns
  - Automatic sizing or fixed dimensions
- [ ] Add `Dashboard` class to compose multiple graphs
- [ ] Support horizontal and vertical stacking
- [ ] Add borders, titles, and padding

**Deliverable**: Show 4 graphs in 2x2 grid layout

## Phase 5: Axes, Labels, and Formatting

**Goal**: Professional graph annotations

- [ ] Add Y-axis with value labels
  - Auto-scaling (0-100%, dynamic ranges)
  - Custom units (%, MB, GB, req/s)
- [ ] Add X-axis with time labels
  - Relative time (1m, 5m, 30m ago)
  - Absolute timestamps
- [ ] Add graph titles and legends
- [ ] Support custom color themes
- [ ] Add status bar with current/min/max/avg values

**Deliverable**: Fully labeled graphs with axes and legends

## Phase 6: System Monitoring Integration

**Goal**: Built-in data sources for common monitoring tasks

- [ ] Create `DataSource` plugin architecture
- [ ] Implement system metric collectors:
  - CPU usage (per-core and total)
  - Memory usage (used/free/cached)
  - Disk I/O (read/write rates)
  - Network I/O (rx/tx rates)
  - Process monitoring (top processes)
- [ ] Add example monitoring applications:
  - `spark-monitor-cpu` - CPU dashboard
  - `spark-monitor-net` - Network traffic
  - `spark-monitor-sys` - Full system overview
- [ ] Cross-platform support (Linux, macOS, Windows)
- [ ] Optional: Docker container metrics

**Deliverable**: `spark-monitor` command launches a btop-style interface

## Phase 7: Advanced Features (Future)

- [ ] Export graphs as images (PNG, SVG)
- [ ] Save/load data sessions
- [ ] Remote monitoring (TCP/HTTP data sources)
- [ ] Alerting/thresholds
- [ ] Log file tailing and visualization
- [ ] Plugin system for custom data sources
- [ ] Web-based dashboard (optional)

## Dependencies to Add

- **Terminal UI**: `rich` or `blessed` (Phase 3)
- **System metrics**: `psutil` (Phase 6)
- **Async I/O**: `asyncio` (Phase 3+)
- **Colors**: Already have ANSI support, may enhance

## Architecture Principles

1. **Layered design**: Separate rendering, data handling, and data sources
2. **Plugin architecture**: Easy to add new graph styles and data sources
3. **API-first**: Library remains usable programmatically, CLI built on top
4. **Backward compatible**: Existing sparkline features continue working
5. **Optional dependencies**: Heavy features (psutil, rich) are extras

## Non-Goals

- Not trying to replace btop/htop completely
- Not adding process management (kill, nice, etc.)
- Keeping the library lightweight for embedded use cases

## Getting Started

Begin with Phase 1 to enhance the existing `MultiLineGraphStyle` into a proper line graph renderer. Each phase builds on the previous, allowing incremental development and testing.
