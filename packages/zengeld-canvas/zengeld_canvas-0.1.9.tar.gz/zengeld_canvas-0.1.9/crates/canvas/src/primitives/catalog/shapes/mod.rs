//! Shape-based primitives
//!
//! This module contains geometric shape drawing tools:
//! - Rectangle: box defined by two corners
//! - Rotated Rectangle: rectangle that can be rotated
//! - Circle: perfect circle
//! - Ellipse: oval shape
//! - Triangle: three-point shape
//! - Arc: curved line segment
//! - Path: free-form connected points
//! - Polyline: connected straight lines
//! - Curve: Bezier curve
//! - Double Curve: S-curve with two control points

pub mod arc;
pub mod circle;
pub mod curve;
pub mod double_curve;
pub mod ellipse;
pub mod path;
pub mod polyline;
pub mod rectangle;
pub mod rotated_rectangle;
pub mod triangle;

// Re-export primitive types
pub use arc::Arc;
pub use circle::Circle;
pub use curve::Curve;
pub use double_curve::DoubleCurve;
pub use ellipse::Ellipse;
pub use path::Path;
pub use polyline::Polyline;
pub use rectangle::Rectangle;
pub use rotated_rectangle::RotatedRectangle;
pub use triangle::Triangle;
