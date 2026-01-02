//! zen-canvas Rendering Engine
//!
//! High-performance, pixel-perfect rendering engine for financial charts.
//! Designed for minimal allocations, maximum throughput, and cross-platform export.
//!
//! # Architecture
//!
//! ```text
//! ┌─────────────────────────────────────────────────────────────┐
//! │  render/                                                     │
//! ├─────────────────────────────────────────────────────────────┤
//! │  engine/           │  chart/                                 │
//! │  ─────────────     │  ───────────────────────────────        │
//! │  types.rs          │  series.rs (candlestick, line, area)    │
//! │  path.rs           │  overlays.rs (grid, legend, watermark)  │
//! │  commands.rs       │  annotations.rs (markers, price lines)  │
//! │  batch.rs          │                                         │
//! │  backend.rs        │                                         │
//! │  crisp.rs          │                                         │
//! │  coords.rs         │                                         │
//! ├────────────────────┴─────────────────────────────────────────┤
//! │  "How we draw"      "What we draw"                           │
//! └─────────────────────────────────────────────────────────────┘
//! ```
//!
//! # Performance Design
//!
//! - **Zero-copy coordinates**: Inline functions for bar_to_x/price_to_y
//! - **Visible range culling**: Only render what's on screen
//! - **Crisp rendering**: Pixel-perfect alignment for 1px lines
//! - **Path reuse**: Immutable paths can be drawn multiple times
//! - **Batch grouping**: Commands grouped by style to minimize state changes
//! - **Arena-style allocation**: Pre-allocated buffers for hot paths

// Engine - Low-level rendering infrastructure
pub mod engine;

// Chart - High-level chart element rendering
pub mod chart;

// =============================================================================
// Re-exports from engine (for backwards compatibility and convenience)
// =============================================================================

// Core types
pub use engine::{Color, Point, Rect, Transform2D};
pub use engine::{
    FillStyle, FontWeight, LineCap, LineJoin, LineStyle, TextAlign, TextBaseline, TextStyle,
};

// Path
pub use engine::{Path, PathBuilder, PathCommand};

// Commands
pub use engine::RenderCommand;

// Batch
pub use engine::{RenderBatch, RenderQueue, layers};

// Backend
pub use engine::{
    ImageInfo, NullBackend, RenderBackend, RenderError, RenderResult, SvgBackend, TextMetrics,
};

// Crisp rendering
pub use engine::{
    crisp_bar_width, crisp_coord, crisp_line_coords, crisp_point, crisp_rect, crisp_rect_struct,
    stroke_offset,
};

// Coordinate conversion
pub use engine::{CoordSystem, snap_point_to_pixel, snap_rect_to_pixel, snap_to_pixel};

// =============================================================================
// Re-exports from chart
// =============================================================================

// Series rendering
pub use chart::{
    render_area, render_bars, render_baseline, render_candlesticks, render_histogram, render_line,
};

// Overlay rendering
pub use chart::{render_grid, render_legend, render_watermark};

// Annotation rendering
pub use chart::{render_markers, render_price_lines};

// Indicator and signal rendering
pub use chart::{render_indicator, render_signals, render_strategy};
