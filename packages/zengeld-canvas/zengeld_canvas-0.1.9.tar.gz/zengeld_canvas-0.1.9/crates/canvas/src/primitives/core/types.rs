//! Shared types for primitives
//!
//! These types are used by all primitives and the drawing system.

use serde::{Deserialize, Serialize};

// Re-export LineStyle from annotations
pub use crate::model::annotations::price_line::LineStyle;

// =============================================================================
// Color Configuration
// =============================================================================

/// Color configuration for primitives
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimitiveColor {
    /// Stroke/border color (hex)
    pub stroke: String,
    /// Fill color (hex with alpha, optional)
    pub fill: Option<String>,
}

impl Default for PrimitiveColor {
    fn default() -> Self {
        Self {
            stroke: "#2196F3".to_string(),
            fill: None,
        }
    }
}

impl PrimitiveColor {
    /// Create with stroke color only
    pub fn new(stroke: &str) -> Self {
        Self {
            stroke: stroke.to_string(),
            fill: None,
        }
    }

    /// Create with stroke and fill colors
    pub fn with_fill(stroke: &str, fill: &str) -> Self {
        Self {
            stroke: stroke.to_string(),
            fill: Some(fill.to_string()),
        }
    }

    /// Create semi-transparent fill from stroke color
    pub fn with_alpha_fill(stroke: &str, alpha: u8) -> Self {
        let fill = format!("{}{:02x}", stroke, alpha);
        Self {
            stroke: stroke.to_string(),
            fill: Some(fill),
        }
    }
}

// =============================================================================
// Text Configuration
// =============================================================================

/// Text alignment options
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum TextAlign {
    #[default]
    Start, // Left / Top
    Center,
    End, // Right / Bottom
}

impl TextAlign {
    pub fn as_str(&self) -> &'static str {
        match self {
            TextAlign::Start => "start",
            TextAlign::Center => "center",
            TextAlign::End => "end",
        }
    }
}

/// Text configuration for primitives
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct PrimitiveText {
    /// Text content
    pub content: String,
    /// Font size in pixels
    pub font_size: f64,
    /// Text color (defaults to stroke color if None)
    pub color: Option<String>,
    /// Bold text
    pub bold: bool,
    /// Italic text
    pub italic: bool,
    /// Vertical alignment
    pub v_align: TextAlign,
    /// Horizontal alignment
    pub h_align: TextAlign,
}

impl PrimitiveText {
    pub fn new(content: &str) -> Self {
        Self {
            content: content.to_string(),
            font_size: 14.0,
            color: None,
            bold: false,
            italic: false,
            v_align: TextAlign::Start,
            h_align: TextAlign::Center,
        }
    }

    pub fn with_size(content: &str, font_size: f64) -> Self {
        Self {
            content: content.to_string(),
            font_size,
            ..Default::default()
        }
    }
}

// =============================================================================
// Text Anchor (for centralized text rendering)
// =============================================================================

/// Text anchor point for centralized rendering
///
/// Primitives return this to indicate where their text should be drawn.
/// The actual rendering is done centrally after primitive.render().
#[derive(Clone, Debug)]
pub struct TextAnchor {
    /// X position in screen coordinates
    pub x: f64,
    /// Y position in screen coordinates
    pub y: f64,
    /// Fallback color if text.color is None
    pub fallback_color: String,
    /// Optional background color for text
    pub background: Option<String>,
    /// Padding around text (used with background)
    pub padding: f64,
    /// Rotation angle in radians (for text along angled lines)
    pub rotation: f64,
}

impl TextAnchor {
    /// Create a simple text anchor
    pub fn new(x: f64, y: f64, fallback_color: &str) -> Self {
        Self {
            x,
            y,
            fallback_color: fallback_color.to_string(),
            background: None,
            padding: 0.0,
            rotation: 0.0,
        }
    }

    /// Create text anchor with rotation (for angled lines)
    pub fn with_rotation(x: f64, y: f64, fallback_color: &str, rotation: f64) -> Self {
        Self {
            x,
            y,
            fallback_color: fallback_color.to_string(),
            background: None,
            padding: 0.0,
            rotation,
        }
    }

    /// Create text anchor with background
    pub fn with_background(
        x: f64,
        y: f64,
        fallback_color: &str,
        bg_color: &str,
        padding: f64,
    ) -> Self {
        Self {
            x,
            y,
            fallback_color: fallback_color.to_string(),
            background: Some(bg_color.to_string()),
            padding,
            rotation: 0.0,
        }
    }
}

/// Normalize rotation angle for readable text.
///
/// When text is rotated along a line, angles beyond ±90° would make text upside-down.
/// This function flips such angles by ±180° to keep text readable.
///
/// # Arguments
/// * `raw_angle` - The raw angle in radians (typically from `dy.atan2(dx)`)
///
/// # Returns
/// * `(normalized_angle, was_flipped)` - The normalized angle and whether it was flipped
///
/// # Example
/// ```
/// use zengeld_canvas::primitives::normalize_text_rotation;
///
/// // Angle pointing right (0°) - no change
/// let (angle, flipped) = normalize_text_rotation(0.0);
/// assert!(!flipped);
///
/// // Angle pointing left (180°) - flipped to 0°
/// let (angle, flipped) = normalize_text_rotation(std::f64::consts::PI);
/// assert!(flipped);
/// ```
pub fn normalize_text_rotation(raw_angle: f64) -> (f64, bool) {
    use std::f64::consts::{FRAC_PI_2, PI};

    let was_flipped = !(-FRAC_PI_2..=FRAC_PI_2).contains(&raw_angle);
    let normalized = if raw_angle > FRAC_PI_2 {
        raw_angle - PI
    } else if raw_angle < -FRAC_PI_2 {
        raw_angle + PI
    } else {
        raw_angle
    };
    (normalized, was_flipped)
}

// =============================================================================
// Line Extension Mode
// =============================================================================

/// Line extension mode for trend lines
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExtendMode {
    /// No extension (default for TrendLine)
    #[default]
    None,
    /// Extend to the right only (Ray)
    Right,
    /// Extend to the left only
    Left,
    /// Extend both directions (ExtendedLine)
    Both,
}

// =============================================================================
// Control Points (Handles)
// =============================================================================

/// Type of control point for editing primitives
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ControlPointType {
    /// Move the entire primitive
    Move,
    /// Endpoint 1 (start point)
    Point1,
    /// Endpoint 2 (end point)
    Point2,
    /// Endpoint 3 (for 3-point primitives)
    Point3,
    /// Endpoint 4 (for 4-point primitives like disjoint channel)
    Point4,
    /// Corner handle (for rectangles) - index 0=TL, 1=TR, 2=BR, 3=BL
    Corner(u8),
    /// Edge midpoint handle (for rectangles) - index 0=Top, 1=Right, 2=Bottom, 3=Left
    Edge(u8),
    /// Level handle (for Fibonacci) - index is level number
    Level(u8),
    /// Generic indexed point (for polylines, patterns)
    Index(u8),
}

/// A control point (handle) for editing a primitive
#[derive(Clone, Debug)]
pub struct ControlPoint {
    /// Type of control point
    pub point_type: ControlPointType,
    /// X position in screen coordinates
    pub x: f64,
    /// Y position in screen coordinates
    pub y: f64,
}

impl ControlPoint {
    pub fn new(point_type: ControlPointType, x: f64, y: f64) -> Self {
        Self { point_type, x, y }
    }

    /// Create a control point with default Move cursor
    pub fn with_type(point_type: ControlPointType, x: f64, y: f64) -> Self {
        Self::new(point_type, x, y)
    }

    pub fn move_point(x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Move, x, y)
    }

    pub fn point1(x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Point1, x, y)
    }

    pub fn point2(x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Point2, x, y)
    }

    pub fn point3(x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Point3, x, y)
    }

    pub fn point4(x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Point4, x, y)
    }

    pub fn index(i: u8, x: f64, y: f64) -> Self {
        Self::new(ControlPointType::Index(i), x, y)
    }
}

// =============================================================================
// Constants
// =============================================================================

// =============================================================================
// Geometry Utilities
// =============================================================================

/// Calculate distance from point to line segment
pub fn point_to_line_distance(px: f64, py: f64, x1: f64, y1: f64, x2: f64, y2: f64) -> f64 {
    let dx = x2 - x1;
    let dy = y2 - y1;
    let len_sq = dx * dx + dy * dy;

    if len_sq < 0.0001 {
        // Line is a point
        let ddx = px - x1;
        let ddy = py - y1;
        return (ddx * ddx + ddy * ddy).sqrt();
    }

    // Project point onto line, clamping to segment
    let t = ((px - x1) * dx + (py - y1) * dy) / len_sq;
    let t = t.clamp(0.0, 1.0);

    let proj_x = x1 + t * dx;
    let proj_y = y1 + t * dy;

    let ddx = px - proj_x;
    let ddy = py - proj_y;
    (ddx * ddx + ddy * ddy).sqrt()
}
