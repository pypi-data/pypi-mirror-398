//! Pixel-perfect (crisp) rendering utilities
//!
//! These functions align coordinates to device pixel boundaries to ensure
//! sharp 1px lines without anti-aliasing blur on high-DPI displays.
//!
//! # Strategy
//!
//! For a 1px line to appear crisp:
//! - The coordinate must be at a half-pixel boundary (e.g., 10.5, not 10.0)
//! - This centers the 1px stroke on the pixel boundary
//!
//! For a filled rectangle:
//! - Coordinates should be at exact pixel boundaries
//! - Width/height should be whole pixel counts

use super::types::{Point, Rect};

/// Align a coordinate to device pixel boundary for crisp 1px lines
///
/// The +0.5 offset centers a 1px stroke on the pixel boundary.
///
/// # Arguments
/// * `coord` - The coordinate to align
/// * `dpr` - Device pixel ratio (1.0 for standard, 2.0 for retina)
///
/// # Example
/// ```
/// use zengeld_canvas::render::crisp_coord;
///
/// // On a retina display (dpr=2.0), pixel 10.3 becomes 10.25
/// let crisp = crisp_coord(10.3, 2.0);
/// ```
#[inline]
pub fn crisp_coord(coord: f64, dpr: f64) -> f64 {
    (coord * dpr).floor() / dpr + 0.5 / dpr
}

/// Align both coordinates for a crisp horizontal or vertical line
#[inline]
pub fn crisp_line_coords(x1: f64, y1: f64, x2: f64, y2: f64, dpr: f64) -> (f64, f64, f64, f64) {
    // For horizontal lines, align Y; for vertical lines, align X
    let is_horizontal = (y2 - y1).abs() < 0.001;
    let is_vertical = (x2 - x1).abs() < 0.001;

    if is_horizontal {
        let y = crisp_coord(y1, dpr);
        ((x1 * dpr).floor() / dpr, y, (x2 * dpr).ceil() / dpr, y)
    } else if is_vertical {
        let x = crisp_coord(x1, dpr);
        (x, (y1 * dpr).floor() / dpr, x, (y2 * dpr).ceil() / dpr)
    } else {
        // Diagonal line - align start point
        (
            crisp_coord(x1, dpr),
            crisp_coord(y1, dpr),
            crisp_coord(x2, dpr),
            crisp_coord(y2, dpr),
        )
    }
}

/// Align a rectangle to device pixel boundaries for crisp edges
///
/// Ensures the rectangle has whole-pixel dimensions and aligns to pixel grid.
///
/// # Arguments
/// * `x`, `y` - Top-left corner
/// * `width`, `height` - Dimensions
/// * `dpr` - Device pixel ratio
///
/// # Returns
/// Tuple of (x, y, width, height) aligned to pixels
#[inline]
pub fn crisp_rect(x: f64, y: f64, width: f64, height: f64, dpr: f64) -> (f64, f64, f64, f64) {
    let x1 = (x * dpr).floor() / dpr;
    let y1 = (y * dpr).floor() / dpr;
    let x2 = ((x + width) * dpr).floor() / dpr;
    let y2 = ((y + height) * dpr).floor() / dpr;

    // Ensure minimum 1 device pixel size
    let w = (x2 - x1).max(1.0 / dpr);
    let h = (y2 - y1).max(1.0 / dpr);

    (x1, y1, w, h)
}

/// Align a Rect struct to device pixel boundaries
#[inline]
pub fn crisp_rect_struct(rect: Rect, dpr: f64) -> Rect {
    let (x, y, w, h) = crisp_rect(rect.x, rect.y, rect.width, rect.height, dpr);
    Rect::new(x, y, w, h)
}

/// Align a point for crisp rendering (useful for control points)
#[inline]
pub fn crisp_point(p: Point, dpr: f64) -> Point {
    Point::new(crisp_coord(p.x, dpr), crisp_coord(p.y, dpr))
}

/// Calculate dynamic bar/column width that snaps to device pixels
///
/// Used for candlesticks, histogram bars, etc.
///
/// # Arguments
/// * `base_width` - Desired width based on bar_spacing
/// * `dpr` - Device pixel ratio
///
/// # Returns
/// Width that is a whole number of device pixels (minimum 1 device pixel)
#[inline]
pub fn crisp_bar_width(base_width: f64, dpr: f64) -> f64 {
    let pixels = (base_width * dpr).round();
    (pixels / dpr).max(1.0 / dpr)
}

/// Calculate crisp stroke offset for centered lines
///
/// When drawing a stroked rectangle or line, the stroke is centered on the path.
/// For a 1px stroke to be crisp, we need to offset by 0.5 device pixels.
#[inline]
pub fn stroke_offset(stroke_width: f64, dpr: f64) -> f64 {
    if stroke_width <= 1.0 / dpr {
        0.5 / dpr
    } else {
        0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_crisp_coord_standard() {
        // Standard display (dpr = 1.0)
        assert_eq!(crisp_coord(10.0, 1.0), 10.5);
        assert_eq!(crisp_coord(10.3, 1.0), 10.5);
        assert_eq!(crisp_coord(10.7, 1.0), 10.5);
    }

    #[test]
    fn test_crisp_coord_retina() {
        // Retina display (dpr = 2.0)
        let dpr = 2.0;
        let c = crisp_coord(10.3, dpr);
        // 10.3 * 2 = 20.6, floor = 20, /2 = 10.0, +0.25 = 10.25
        assert!((c - 10.25).abs() < 0.001);
    }

    #[test]
    fn test_crisp_rect() {
        let (x, y, w, h) = crisp_rect(10.3, 20.7, 50.5, 30.2, 1.0);
        assert_eq!(x, 10.0);
        assert_eq!(y, 20.0);
        assert_eq!(w, 50.0);
        assert_eq!(h, 30.0);
    }

    #[test]
    fn test_crisp_rect_minimum_size() {
        // Very small rectangle should still have 1 pixel size
        let (_, _, w, h) = crisp_rect(10.0, 10.0, 0.1, 0.1, 1.0);
        assert_eq!(w, 1.0);
        assert_eq!(h, 1.0);
    }

    #[test]
    fn test_crisp_bar_width() {
        assert_eq!(crisp_bar_width(5.3, 1.0), 5.0);
        assert_eq!(crisp_bar_width(5.7, 1.0), 6.0);
        assert_eq!(crisp_bar_width(0.3, 1.0), 1.0); // Minimum
    }
}
