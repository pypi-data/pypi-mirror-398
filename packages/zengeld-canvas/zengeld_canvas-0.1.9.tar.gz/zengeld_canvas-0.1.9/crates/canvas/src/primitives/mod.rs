//! Drawing Primitives
//!
//! Headless rendering system for chart drawing primitives.
//!
//! This module provides primitive types for chart drawings
//! that can be rendered across platforms (egui native, WASM Canvas2D, SVG, etc.).
//!
//! # Architecture
//!
//! ```text
//! primitives/
//! ├── mod.rs              # Main exports (this file)
//! ├── core/               # Core types and traits
//! │   ├── traits.rs       # Primitive trait, PrimitiveData, PrimitiveKind
//! │   ├── types.rs        # PrimitiveColor, LineStyle, ControlPoint, etc.
//! │   ├── render.rs       # RenderContext, RenderOp, rendering utilities
//! │   └── config.rs       # Configurable trait, property system
//! ├── registry.rs         # PrimitiveRegistry (factory)
//! ├── signals/            # Strategy signals system
//! │   ├── types.rs        # SignalType, SystemSignal, StrategySignalConfig
//! │   └── manager.rs      # SignalManager
//! ├── trades/             # Trade visualization
//! │   └── types.rs        # Trade, TradeDirection, TradeManager
//! ├── utils/              # Utility functions
//! │   └── point_labels.rs # get_point_labels
//! └── catalog/            # All 80+ primitives by category
//!     ├── lines/          # TrendLine, HorizontalLine, Ray, etc.
//!     ├── channels/       # ParallelChannel, RegressionTrend, etc.
//!     ├── shapes/         # Rectangle, Circle, Ellipse, etc.
//!     ├── fibonacci/      # FibRetracement, FibExtension, etc.
//!     ├── pitchforks/     # Pitchfork, SchiffPitchfork, etc.
//!     ├── gann/           # GannBox, GannFan, etc.
//!     ├── arrows/         # ArrowMarker, ArrowLine, etc.
//!     ├── annotations/    # Text, Note, Callout, etc.
//!     ├── patterns/       # XabcdPattern, HeadShoulders, etc.
//!     ├── elliott/        # ElliottImpulse, ElliottCorrection, etc.
//!     ├── cycles/         # CycleLines, TimeCycles, SineWave
//!     ├── projection/     # LongPosition, ShortPosition, Forecast
//!     ├── volume/         # AnchoredVwap, VolumeProfile
//!     ├── measurement/    # PriceRange, DateRange
//!     ├── brushes/        # Brush, Highlighter
//!     ├── icons/          # Emoji, Image
//!     └── events/         # Crossover, Breakdown, Divergence, etc.
//! ```

// =============================================================================
// Core module - traits, types, rendering, configuration
// =============================================================================

pub mod catalog;
pub mod core;
mod registry;
pub mod signals;
pub mod trades;
pub mod utils;

// =============================================================================
// Re-exports from core
// =============================================================================

pub use core::{
    // Control points (data types)
    ControlPoint,
    ControlPointType,
    ExtendMode,
    LineStyle,
    // Core trait
    Primitive as PrimitiveTrait,
    // Styling
    PrimitiveColor,
    PrimitiveData,
    PrimitiveKind,
    PrimitiveText,
    // Sync mode
    SyncMode,
    TextAlign,
    TextAnchor,
    // Text rotation helper
    normalize_text_rotation,
    // Geometry helpers
    point_to_line_distance,
};

// Rendering exports
pub use core::render::{
    EllipseParams, RenderContext, RenderOp, RenderOps, TextBaseline, crisp as render_crisp,
    crisp_rect as render_crisp_rect, execute_ops, render_primitive_text,
    render_primitive_text_rotated, render_text_with_background,
};

// Configuration exports
pub use core::config::{
    ConfigProperty, Configurable, FibLevelConfig, PrimitiveFullConfig, PropertyCategory,
    PropertyType, PropertyValue, SelectOption, SettingsTemplate, TemplateStyle,
    TimeframeVisibilityConfig,
};

// =============================================================================
// Registry exports
// =============================================================================

pub use registry::{PrimitiveFactory, PrimitiveMetadata, PrimitiveRegistry};

// =============================================================================
// Signals exports
// =============================================================================

pub use signals::{SignalManager, SignalType, StrategySignalConfig, SystemSignal};

// =============================================================================
// Trades exports
// =============================================================================

pub use trades::{Trade, TradeDirection, TradeManager};

// =============================================================================
// Utils exports
// =============================================================================

pub use utils::get_point_labels;

// =============================================================================
// Primitive catalog re-exports (all 70+ primitives)
// =============================================================================

// Lines
pub use catalog::lines::{
    CrossLine, ExtendedLine, HorizontalLine, HorizontalRay, InfoLine, Ray, TrendAngle, TrendLine,
    VerticalLine,
};

// Channels
pub use catalog::channels::{DisjointChannel, FlatTopBottom, ParallelChannel, RegressionTrend};

// Shapes
pub use catalog::shapes::{
    Arc, Circle, Curve, DoubleCurve, Ellipse, Path, Polyline, Rectangle, RotatedRectangle, Triangle,
};

// Fibonacci
pub use catalog::fibonacci::{
    FibArcs, FibChannel, FibCircles, FibFan, FibRetracement, FibSpeedResistance, FibSpiral,
    FibTimeZones, FibTrendExtension, FibTrendTime, FibWedge,
};

// Pitchforks
pub use catalog::pitchforks::{InsidePitchfork, ModifiedSchiff, Pitchfork, SchiffPitchfork};

// Gann
pub use catalog::gann::{GannBox, GannFan, GannSquare, GannSquareFixed};

// Arrows
pub use catalog::arrows::{ArrowDown, ArrowLine, ArrowMarker, ArrowUp};

// Annotations
pub use catalog::annotations::{
    AnchoredText, Callout, Comment, Flag, Note, PriceLabel, PriceNote, Sign, Signpost, Table, Text,
};

// Patterns
pub use catalog::patterns::{
    AbcdPattern, CypherPattern, HeadShoulders, ThreeDrives, TrianglePattern, XabcdPattern,
};

// Elliott
pub use catalog::elliott::{
    ElliottCorrection, ElliottDoubleCombo, ElliottImpulse, ElliottTriangle, ElliottTripleCombo,
};

// Cycles
pub use catalog::cycles::{CycleLines, SineWave, TimeCycles};

// Projection
pub use catalog::projection::{
    BarsPattern, Forecast, LongPosition, PriceProjection, Projection, ShortPosition,
};

// Volume
pub use catalog::volume::{AnchoredVolumeProfile, AnchoredVwap, FixedVolumeProfile};

// Measurement
pub use catalog::measurement::{DateRange, PriceDateRange, PriceRange};

// Brushes
pub use catalog::brushes::{Brush, Highlighter};

// Icons
pub use catalog::icons::{Emoji, EmojiType, Image};

// Events (strategy event primitives)
pub use catalog::events::{
    Breakdown, BreakdownType, Crossover, CrossoverDirection, CrossoverType, CustomEvent,
    CustomEventStyle, Divergence, DivergenceType, MomentumEvent, MomentumEventType, PatternMatch,
    PatternType, TrendEvent, TrendEventType, VolumeEvent, VolumeEventType, ZoneAction, ZoneEvent,
    ZoneType,
};
