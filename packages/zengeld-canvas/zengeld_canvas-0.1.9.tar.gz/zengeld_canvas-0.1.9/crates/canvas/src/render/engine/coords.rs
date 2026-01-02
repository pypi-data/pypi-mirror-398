//! Coordinate system utilities
//!
//! Provides coordinate conversion between:
//! - Data coordinates (price, time/bar index)
//! - Pixel coordinates (screen space)
//! - Logical coordinates (before DPR scaling)

use super::types::{Point, Rect};

/// Viewport configuration for coordinate transforms
///
/// Maps data space (price/time) to pixel space.
#[derive(Clone, Copy, Debug)]
pub struct CoordSystem {
    /// Visible data range on X axis (bar index or timestamp)
    pub data_x_min: f64,
    pub data_x_max: f64,

    /// Visible data range on Y axis (price)
    pub data_y_min: f64,
    pub data_y_max: f64,

    /// Pixel bounds of the chart area
    pub pixel_rect: Rect,

    /// Device pixel ratio
    pub dpr: f64,

    /// Whether Y axis is inverted (screen Y increases downward)
    pub y_inverted: bool,
}

impl Default for CoordSystem {
    fn default() -> Self {
        Self {
            data_x_min: 0.0,
            data_x_max: 100.0,
            data_y_min: 0.0,
            data_y_max: 100.0,
            pixel_rect: Rect::new(0.0, 0.0, 800.0, 600.0),
            dpr: 1.0,
            y_inverted: true,
        }
    }
}

impl CoordSystem {
    /// Create a new coordinate system
    pub fn new(
        data_x_range: (f64, f64),
        data_y_range: (f64, f64),
        pixel_rect: Rect,
        dpr: f64,
    ) -> Self {
        Self {
            data_x_min: data_x_range.0,
            data_x_max: data_x_range.1,
            data_y_min: data_y_range.0,
            data_y_max: data_y_range.1,
            pixel_rect,
            dpr,
            y_inverted: true,
        }
    }

    // =========================================================================
    // Data -> Pixel conversions
    // =========================================================================

    /// Convert data X to pixel X
    #[inline]
    pub fn x_to_pixel(&self, data_x: f64) -> f64 {
        let range = self.data_x_max - self.data_x_min;
        if range.abs() < 1e-12 {
            return self.pixel_rect.x + self.pixel_rect.width / 2.0;
        }
        let t = (data_x - self.data_x_min) / range;
        self.pixel_rect.x + t * self.pixel_rect.width
    }

    /// Convert data Y (price) to pixel Y
    #[inline]
    pub fn y_to_pixel(&self, data_y: f64) -> f64 {
        let range = self.data_y_max - self.data_y_min;
        if range.abs() < 1e-12 {
            return self.pixel_rect.y + self.pixel_rect.height / 2.0;
        }
        let t = (data_y - self.data_y_min) / range;
        if self.y_inverted {
            // Screen Y increases downward, but price increases upward
            self.pixel_rect.y + (1.0 - t) * self.pixel_rect.height
        } else {
            self.pixel_rect.y + t * self.pixel_rect.height
        }
    }

    /// Convert data point to pixel point
    #[inline]
    pub fn to_pixel(&self, data: Point) -> Point {
        Point::new(self.x_to_pixel(data.x), self.y_to_pixel(data.y))
    }

    /// Convert bar index to pixel X (centered on bar)
    #[inline]
    pub fn bar_to_pixel(&self, bar_index: f64, bar_spacing: f64) -> f64 {
        self.x_to_pixel(bar_index) + bar_spacing / 2.0
    }

    // =========================================================================
    // Pixel -> Data conversions
    // =========================================================================

    /// Convert pixel X to data X
    #[inline]
    pub fn pixel_to_x(&self, pixel_x: f64) -> f64 {
        let t = (pixel_x - self.pixel_rect.x) / self.pixel_rect.width;
        self.data_x_min + t * (self.data_x_max - self.data_x_min)
    }

    /// Convert pixel Y to data Y (price)
    #[inline]
    pub fn pixel_to_y(&self, pixel_y: f64) -> f64 {
        let t = (pixel_y - self.pixel_rect.y) / self.pixel_rect.height;
        if self.y_inverted {
            self.data_y_min + (1.0 - t) * (self.data_y_max - self.data_y_min)
        } else {
            self.data_y_min + t * (self.data_y_max - self.data_y_min)
        }
    }

    /// Convert pixel point to data point
    #[inline]
    pub fn to_data(&self, pixel: Point) -> Point {
        Point::new(self.pixel_to_x(pixel.x), self.pixel_to_y(pixel.y))
    }

    // =========================================================================
    // Scale factors
    // =========================================================================

    /// Get pixels per data unit on X axis
    #[inline]
    pub fn x_scale(&self) -> f64 {
        let range = self.data_x_max - self.data_x_min;
        if range.abs() < 1e-12 {
            1.0
        } else {
            self.pixel_rect.width / range
        }
    }

    /// Get pixels per data unit on Y axis
    #[inline]
    pub fn y_scale(&self) -> f64 {
        let range = self.data_y_max - self.data_y_min;
        if range.abs() < 1e-12 {
            1.0
        } else {
            self.pixel_rect.height / range
        }
    }

    /// Convert a data width to pixel width
    #[inline]
    pub fn width_to_pixel(&self, data_width: f64) -> f64 {
        data_width * self.x_scale()
    }

    /// Convert a data height to pixel height
    #[inline]
    pub fn height_to_pixel(&self, data_height: f64) -> f64 {
        data_height * self.y_scale()
    }

    // =========================================================================
    // Bounds checking
    // =========================================================================

    /// Check if data point is within visible range
    #[inline]
    pub fn is_visible_data(&self, data: Point) -> bool {
        data.x >= self.data_x_min
            && data.x <= self.data_x_max
            && data.y >= self.data_y_min
            && data.y <= self.data_y_max
    }

    /// Check if pixel point is within chart bounds
    #[inline]
    pub fn is_visible_pixel(&self, pixel: Point) -> bool {
        self.pixel_rect.contains(pixel)
    }

    /// Clamp data point to visible range
    #[inline]
    pub fn clamp_data(&self, data: Point) -> Point {
        Point::new(
            data.x.clamp(self.data_x_min, self.data_x_max),
            data.y.clamp(self.data_y_min, self.data_y_max),
        )
    }

    /// Clamp pixel point to chart bounds
    #[inline]
    pub fn clamp_pixel(&self, pixel: Point) -> Point {
        Point::new(
            pixel.x.clamp(self.pixel_rect.x, self.pixel_rect.right()),
            pixel.y.clamp(self.pixel_rect.y, self.pixel_rect.bottom()),
        )
    }

    // =========================================================================
    // Visible range helpers
    // =========================================================================

    /// Get visible data range on X axis
    #[inline]
    pub fn visible_x_range(&self) -> (f64, f64) {
        (self.data_x_min, self.data_x_max)
    }

    /// Get visible data range on Y axis
    #[inline]
    pub fn visible_y_range(&self) -> (f64, f64) {
        (self.data_y_min, self.data_y_max)
    }

    /// Get first visible bar index (floor)
    #[inline]
    pub fn first_visible_bar(&self) -> i64 {
        self.data_x_min.floor() as i64
    }

    /// Get last visible bar index (ceil)
    #[inline]
    pub fn last_visible_bar(&self) -> i64 {
        self.data_x_max.ceil() as i64
    }
}

/// Snap a coordinate to the nearest pixel boundary
#[inline]
pub fn snap_to_pixel(coord: f64, dpr: f64) -> f64 {
    (coord * dpr).round() / dpr
}

/// Snap a point to pixel boundaries
#[inline]
pub fn snap_point_to_pixel(p: Point, dpr: f64) -> Point {
    Point::new(snap_to_pixel(p.x, dpr), snap_to_pixel(p.y, dpr))
}

/// Snap a rect to pixel boundaries (preserving size)
#[inline]
pub fn snap_rect_to_pixel(r: Rect, dpr: f64) -> Rect {
    let x = snap_to_pixel(r.x, dpr);
    let y = snap_to_pixel(r.y, dpr);
    let w = snap_to_pixel(r.width, dpr);
    let h = snap_to_pixel(r.height, dpr);
    Rect::new(x, y, w, h)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coord_system_basic() {
        let cs = CoordSystem::new(
            (0.0, 100.0),
            (0.0, 100.0),
            Rect::new(0.0, 0.0, 800.0, 600.0),
            1.0,
        );

        // Center should map to center
        assert!((cs.x_to_pixel(50.0) - 400.0).abs() < 0.01);

        // Y is inverted by default
        assert!((cs.y_to_pixel(100.0) - 0.0).abs() < 0.01); // Top price at top
        assert!((cs.y_to_pixel(0.0) - 600.0).abs() < 0.01); // Low price at bottom
    }

    #[test]
    fn test_round_trip() {
        let cs = CoordSystem::new(
            (10.0, 110.0),
            (100.0, 200.0),
            Rect::new(50.0, 50.0, 700.0, 500.0),
            1.0,
        );

        let original = Point::new(60.0, 150.0);
        let pixel = cs.to_pixel(original);
        let back = cs.to_data(pixel);

        assert!((back.x - original.x).abs() < 0.001);
        assert!((back.y - original.y).abs() < 0.001);
    }

    #[test]
    fn test_scale_factors() {
        let cs = CoordSystem::new(
            (0.0, 100.0),
            (0.0, 50.0),
            Rect::new(0.0, 0.0, 200.0, 100.0),
            1.0,
        );

        assert!((cs.x_scale() - 2.0).abs() < 0.001); // 200px / 100 units = 2 px/unit
        assert!((cs.y_scale() - 2.0).abs() < 0.001); // 100px / 50 units = 2 px/unit
    }

    #[test]
    fn test_snap_to_pixel() {
        assert!((snap_to_pixel(10.3, 1.0) - 10.0).abs() < 0.001);
        assert!((snap_to_pixel(10.7, 1.0) - 11.0).abs() < 0.001);
        assert!((snap_to_pixel(10.3, 2.0) - 10.5).abs() < 0.001);
    }
}
