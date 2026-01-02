//! Layout System
//!
//! Chart layout and organization:
//! - `pane` - Sub-pane system for indicator panels
//! - `multichart` - Multichart grid layouts (2x2, 1+3, etc.)

pub mod multichart;
pub mod pane;

// Re-exports - Pane system
pub use pane::{MAIN_PANE, Pane, PaneGeometry, PaneId, PaneManager, SubPane, coordinate_utils};

// Re-exports - Multichart
pub use multichart::{CellBounds, CellId, LayoutCell, MultichartLayout};
