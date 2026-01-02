//! Primitive catalog - all 70+ drawing primitives organized by category
//!
//! # Categories
//!
//! - **lines** - Trend lines, rays, horizontal/vertical lines
//! - **channels** - Parallel channels, regression trends
//! - **shapes** - Rectangle, circle, ellipse, triangle, polyline
//! - **fibonacci** - Retracement, extension, fans, arcs, spirals
//! - **pitchforks** - Pitchfork, Schiff, modified Schiff
//! - **gann** - Gann fan, box, square
//! - **arrows** - Arrow markers, arrow lines
//! - **annotations** - Text, notes, callouts, labels, flags
//! - **patterns** - XABCD, ABCD, head & shoulders, triangles
//! - **elliott** - Elliott wave patterns
//! - **cycles** - Cycle lines, time cycles, sine waves
//! - **projection** - Long/short positions, forecasts
//! - **volume** - VWAP, volume profiles
//! - **measurement** - Price/date ranges
//! - **brushes** - Brush, highlighter
//! - **icons** - Emoji markers, images
//! - **events** - Strategy events (crossover, breakdown, divergence, etc.)

pub mod annotations;
pub mod arrows;
pub mod brushes;
pub mod channels;
pub mod cycles;
pub mod elliott;
pub mod events;
pub mod fibonacci;
pub mod gann;
pub mod icons;
pub mod lines;
pub mod measurement;
pub mod patterns;
pub mod pitchforks;
pub mod projection;
pub mod shapes;
pub mod volume;

// Re-export all primitives for convenience
pub use annotations::*;
pub use arrows::*;
pub use brushes::*;
pub use channels::*;
pub use cycles::*;
pub use elliott::*;
pub use events::*;
pub use fibonacci::*;
pub use gann::*;
pub use icons::*;
pub use lines::*;
pub use measurement::*;
pub use patterns::*;
pub use pitchforks::*;
pub use projection::*;
pub use shapes::*;
pub use volume::*;

// Re-export core types for primitives to use via super::super
// This maintains backward compatibility with existing primitive imports
pub use super::core::{
    ControlPoint, ControlPointType, ExtendMode, LineStyle, Primitive, PrimitiveColor,
    PrimitiveData, PrimitiveKind, PrimitiveText, SyncMode, TextAlign, TextAnchor,
    normalize_text_rotation, point_to_line_distance,
};

// Re-export render module and its types (for super::super::render::X usage)
pub use super::core::render;
pub use super::core::render::{
    EllipseParams, RenderContext, RenderOp, RenderOps, TextBaseline, crisp, crisp_rect,
    execute_ops, render_primitive_text, render_primitive_text_rotated, render_text_with_background,
};

// Re-export config module and its types (for super::super::config::X usage)
pub use super::core::config;
pub use super::core::config::{
    ConfigProperty, Configurable, FibLevelConfig, PrimitiveFullConfig, PropertyCategory,
    PropertyType, PropertyValue, SelectOption, SettingsTemplate, TemplateStyle,
    TimeframeVisibilityConfig,
};

pub use super::registry::PrimitiveMetadata;
