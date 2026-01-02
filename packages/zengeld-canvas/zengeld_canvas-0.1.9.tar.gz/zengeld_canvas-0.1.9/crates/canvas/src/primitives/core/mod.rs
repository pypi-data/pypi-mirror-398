//! Core types and traits for primitives
//!
//! This module contains the foundational types used by all primitives:
//! - `Primitive` trait - the core contract all primitives implement
//! - `PrimitiveData` - common data shared by all primitives
//! - `RenderContext` - abstraction for rendering backends
//! - `Configurable` - trait for primitive configuration UI

pub mod config;
pub mod render;
mod traits;
mod types;

// Re-export core trait and types
pub use config::{
    ConfigProperty, Configurable, FibLevelConfig, Language, PrimitiveFullConfig, PropertyCategory,
    PropertyType, PropertyValue, SelectOption, SettingsTemplate, TemplateStyle,
    TimeframeVisibilityConfig,
};
pub use render::{
    RenderContext, RenderOp, RenderOps, TextAlign as RenderTextAlign, TextBaseline, crisp,
    crisp_rect, execute_ops, measure_primitive_text, render_primitive_text,
    render_primitive_text_rotated, render_text_with_background,
};
pub use traits::{Primitive, PrimitiveData, PrimitiveKind, SyncMode};
pub use types::{
    ControlPoint, ControlPointType, ExtendMode, LineStyle, PrimitiveColor, PrimitiveText,
    TextAlign, TextAnchor, normalize_text_rotation, point_to_line_distance,
};
