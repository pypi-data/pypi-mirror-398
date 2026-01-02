//! Rendering Engine Core
//!
//! Low-level rendering infrastructure: types, commands, batching, backends.
//! This is the "how we draw" layer - platform-agnostic primitives.
//!
//! # Modules
//!
//! - `types` - Core types: Color, Point, Rect, LineStyle, FillStyle, TextStyle
//! - `path` - Path construction and manipulation
//! - `commands` - Atomic render commands (RenderCommand enum)
//! - `batch` - Command batching with O(1) bounds tracking
//! - `backend` - RenderBackend trait for platform abstraction
//! - `crisp` - Pixel-perfect rendering utilities
//! - `coords` - Coordinate system conversion

pub mod backend;
pub mod batch;
pub mod commands;
pub mod coords;
pub mod crisp;
pub mod path;
pub mod svg_backend;
pub mod types;

// Re-exports - Core types
pub use types::{Color, Point, Rect, Transform2D};
pub use types::{
    FillStyle, FontWeight, LineCap, LineJoin, LineStyle, TextAlign, TextBaseline, TextStyle,
};

// Re-exports - Path
pub use path::{Path, PathBuilder, PathCommand};

// Re-exports - Commands
pub use commands::RenderCommand;

// Re-exports - Batch
pub use batch::{RenderBatch, RenderQueue, layers};

// Re-exports - Backend
pub use backend::{ImageInfo, NullBackend, RenderBackend, RenderError, RenderResult, TextMetrics};

// Re-exports - Crisp rendering
pub use crisp::{
    crisp_bar_width, crisp_coord, crisp_line_coords, crisp_point, crisp_rect, crisp_rect_struct,
    stroke_offset,
};

// Re-exports - Coordinate conversion
pub use coords::{CoordSystem, snap_point_to_pixel, snap_rect_to_pixel, snap_to_pixel};

// Re-exports - SVG backend
pub use svg_backend::SvgBackend;
