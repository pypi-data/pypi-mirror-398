//! Path construction and manipulation
//!
//! Immutable paths that can be reused for multiple draw operations.
//! Optimized for minimal allocations in hot rendering paths.

use super::types::{Point, Rect};
use serde::{Deserialize, Serialize};

/// Path command (subpath segment)
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum PathCommand {
    /// Move to point (start new subpath)
    MoveTo(Point),
    /// Line to point
    LineTo(Point),
    /// Quadratic bezier curve
    QuadTo { control: Point, end: Point },
    /// Cubic bezier curve
    CubicTo { c1: Point, c2: Point, end: Point },
    /// Arc segment (center, radius, start_angle, end_angle, counterclockwise)
    Arc {
        center: Point,
        radius: f64,
        start: f64,
        end: f64,
        ccw: bool,
    },
    /// Ellipse (center, rx, ry, rotation, start_angle, end_angle, ccw)
    Ellipse {
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        start: f64,
        end: f64,
        ccw: bool,
    },
    /// Close current subpath
    Close,
}

/// Immutable path (can be stored and reused)
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Path {
    commands: Vec<PathCommand>,
    bounds: Rect,
}

impl Path {
    /// Create empty path
    pub fn new() -> Self {
        Self::default()
    }

    /// Create path builder
    pub fn builder() -> PathBuilder {
        PathBuilder::new()
    }

    /// Get path commands
    #[inline]
    pub fn commands(&self) -> &[PathCommand] {
        &self.commands
    }

    /// Get bounding box
    #[inline]
    pub fn bounds(&self) -> Rect {
        self.bounds
    }

    /// Check if path is empty
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.commands.is_empty()
    }

    // =========================================================================
    // Factory methods for common shapes
    // =========================================================================

    /// Create rectangle path
    pub fn rect(r: Rect) -> Self {
        let mut builder = PathBuilder::new();
        builder.move_to(Point::new(r.x, r.y));
        builder.line_to(Point::new(r.right(), r.y));
        builder.line_to(Point::new(r.right(), r.bottom()));
        builder.line_to(Point::new(r.x, r.bottom()));
        builder.close();
        builder.build()
    }

    /// Create rounded rectangle path
    pub fn rounded_rect(r: Rect, radius: f64) -> Self {
        let mut builder = PathBuilder::new();
        let radius = radius.min(r.width / 2.0).min(r.height / 2.0);

        // Top edge
        builder.move_to(Point::new(r.x + radius, r.y));
        builder.line_to(Point::new(r.right() - radius, r.y));

        // Top-right corner
        builder.arc_to(Point::new(r.right(), r.y + radius), radius);

        // Right edge
        builder.line_to(Point::new(r.right(), r.bottom() - radius));

        // Bottom-right corner
        builder.arc_to(Point::new(r.right() - radius, r.bottom()), radius);

        // Bottom edge
        builder.line_to(Point::new(r.x + radius, r.bottom()));

        // Bottom-left corner
        builder.arc_to(Point::new(r.x, r.bottom() - radius), radius);

        // Left edge
        builder.line_to(Point::new(r.x, r.y + radius));

        // Top-left corner
        builder.arc_to(Point::new(r.x + radius, r.y), radius);

        builder.close();
        builder.build()
    }

    /// Create circle path
    pub fn circle(center: Point, radius: f64) -> Self {
        let mut builder = PathBuilder::new();
        builder.arc(center, radius, 0.0, std::f64::consts::TAU);
        builder.build()
    }

    /// Create ellipse path
    pub fn ellipse(center: Point, rx: f64, ry: f64, rotation: f64, start: f64, end: f64) -> Self {
        let mut builder = PathBuilder::new();
        builder.ellipse(center, rx, ry, rotation, start, end);
        builder.build()
    }

    /// Create arc path (circle segment)
    pub fn arc(center: Point, radius: f64, start: f64, end: f64) -> Self {
        let mut builder = PathBuilder::new();
        builder.arc(center, radius, start, end);
        builder.build()
    }

    /// Create line path
    pub fn line(from: Point, to: Point) -> Self {
        let mut builder = PathBuilder::new();
        builder.move_to(from);
        builder.line_to(to);
        builder.build()
    }

    /// Create polyline path (connected line segments)
    pub fn polyline(points: &[Point]) -> Self {
        if points.is_empty() {
            return Self::new();
        }
        let mut builder = PathBuilder::new();
        builder.move_to(points[0]);
        for p in &points[1..] {
            builder.line_to(*p);
        }
        builder.build()
    }

    /// Create polygon path (closed polyline)
    pub fn polygon(points: &[Point]) -> Self {
        if points.is_empty() {
            return Self::new();
        }
        let mut builder = PathBuilder::new();
        builder.move_to(points[0]);
        for p in &points[1..] {
            builder.line_to(*p);
        }
        builder.close();
        builder.build()
    }
}

/// Mutable path builder
pub struct PathBuilder {
    commands: Vec<PathCommand>,
    current: Point,
    start: Point,
    min: Point,
    max: Point,
}

impl PathBuilder {
    /// Create new path builder
    pub fn new() -> Self {
        Self::with_capacity(16)
    }

    /// Create with pre-allocated capacity
    pub fn with_capacity(cap: usize) -> Self {
        Self {
            commands: Vec::with_capacity(cap),
            current: Point::ZERO,
            start: Point::ZERO,
            min: Point::new(f64::INFINITY, f64::INFINITY),
            max: Point::new(f64::NEG_INFINITY, f64::NEG_INFINITY),
        }
    }

    /// Build immutable path
    pub fn build(self) -> Path {
        let bounds = if self.min.x.is_finite() {
            Rect::new(
                self.min.x,
                self.min.y,
                self.max.x - self.min.x,
                self.max.y - self.min.y,
            )
        } else {
            Rect::ZERO
        };
        Path {
            commands: self.commands,
            bounds,
        }
    }

    /// Clear and reuse builder
    pub fn clear(&mut self) {
        self.commands.clear();
        self.current = Point::ZERO;
        self.start = Point::ZERO;
        self.min = Point::new(f64::INFINITY, f64::INFINITY);
        self.max = Point::new(f64::NEG_INFINITY, f64::NEG_INFINITY);
    }

    // =========================================================================
    // Path commands
    // =========================================================================

    #[inline]
    fn update_bounds(&mut self, p: Point) {
        self.min.x = self.min.x.min(p.x);
        self.min.y = self.min.y.min(p.y);
        self.max.x = self.max.x.max(p.x);
        self.max.y = self.max.y.max(p.y);
    }

    /// Move to point (start new subpath)
    pub fn move_to(&mut self, p: Point) -> &mut Self {
        self.commands.push(PathCommand::MoveTo(p));
        self.current = p;
        self.start = p;
        self.update_bounds(p);
        self
    }

    /// Line to point
    pub fn line_to(&mut self, p: Point) -> &mut Self {
        self.commands.push(PathCommand::LineTo(p));
        self.current = p;
        self.update_bounds(p);
        self
    }

    /// Quadratic bezier curve
    pub fn quad_to(&mut self, control: Point, end: Point) -> &mut Self {
        self.commands.push(PathCommand::QuadTo { control, end });
        self.current = end;
        self.update_bounds(control);
        self.update_bounds(end);
        self
    }

    /// Cubic bezier curve
    pub fn cubic_to(&mut self, c1: Point, c2: Point, end: Point) -> &mut Self {
        self.commands.push(PathCommand::CubicTo { c1, c2, end });
        self.current = end;
        self.update_bounds(c1);
        self.update_bounds(c2);
        self.update_bounds(end);
        self
    }

    /// Arc (circle segment)
    pub fn arc(&mut self, center: Point, radius: f64, start: f64, end: f64) -> &mut Self {
        self.commands.push(PathCommand::Arc {
            center,
            radius,
            start,
            end,
            ccw: false,
        });
        // Update bounds (approximate with bounding box of full circle)
        self.update_bounds(Point::new(center.x - radius, center.y - radius));
        self.update_bounds(Point::new(center.x + radius, center.y + radius));
        // Update current position
        self.current = Point::new(center.x + radius * end.cos(), center.y + radius * end.sin());
        self
    }

    /// Arc to point with radius (for rounded corners)
    /// Uses quadratic bezier as approximation - control point at corner vertex
    pub fn arc_to(&mut self, to: Point, radius: f64) -> &mut Self {
        // For rounded corners: current -> corner -> to
        // The control point is offset from the corner by radius along both edges
        let from = self.current;

        // Calculate direction vectors
        let dx = to.x - from.x;
        let dy = to.y - from.y;
        let len = (dx * dx + dy * dy).sqrt();

        if len < 1e-9 || radius < 1e-9 {
            // Degenerate case: just line to target
            return self.line_to(to);
        }

        // Clamp radius to half the distance
        let r = radius.min(len / 2.0);

        // Control point is the "corner" - offset from both endpoints
        let t = r / len;
        let control = Point::new(from.x + dx * 0.5, from.y + dy * 0.5);

        // Start point on arc (offset from current by radius towards control)
        let start = Point::new(
            from.x + (control.x - from.x) * t * 2.0,
            from.y + (control.y - from.y) * t * 2.0,
        );

        // Line to arc start if needed
        if (start.x - from.x).abs() > 1e-9 || (start.y - from.y).abs() > 1e-9 {
            self.commands.push(PathCommand::LineTo(start));
        }

        // Quadratic bezier for the arc
        self.commands.push(PathCommand::QuadTo { control, end: to });
        self.current = to;
        self.update_bounds(control);
        self.update_bounds(to);
        self
    }

    /// Ellipse
    pub fn ellipse(
        &mut self,
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        start: f64,
        end: f64,
    ) -> &mut Self {
        self.commands.push(PathCommand::Ellipse {
            center,
            rx,
            ry,
            rotation,
            start,
            end,
            ccw: false,
        });
        // Update bounds (approximate)
        let max_r = rx.max(ry);
        self.update_bounds(Point::new(center.x - max_r, center.y - max_r));
        self.update_bounds(Point::new(center.x + max_r, center.y + max_r));
        self
    }

    /// Close current subpath
    pub fn close(&mut self) -> &mut Self {
        self.commands.push(PathCommand::Close);
        self.current = self.start;
        self
    }

    // =========================================================================
    // Convenience methods
    // =========================================================================

    /// Add horizontal line
    pub fn h_line_to(&mut self, x: f64) -> &mut Self {
        self.line_to(Point::new(x, self.current.y))
    }

    /// Add vertical line
    pub fn v_line_to(&mut self, y: f64) -> &mut Self {
        self.line_to(Point::new(self.current.x, y))
    }

    /// Add relative line
    pub fn rel_line_to(&mut self, dx: f64, dy: f64) -> &mut Self {
        self.line_to(Point::new(self.current.x + dx, self.current.y + dy))
    }

    /// Add rectangle to path
    pub fn rect(&mut self, r: Rect) -> &mut Self {
        self.move_to(Point::new(r.x, r.y))
            .line_to(Point::new(r.right(), r.y))
            .line_to(Point::new(r.right(), r.bottom()))
            .line_to(Point::new(r.x, r.bottom()))
            .close()
    }
}

impl Default for PathBuilder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_path_rect() {
        let path = Path::rect(Rect::new(10.0, 20.0, 100.0, 50.0));
        assert_eq!(path.commands().len(), 5); // move, 3 lines, close
        assert_eq!(path.bounds(), Rect::new(10.0, 20.0, 100.0, 50.0));
    }

    #[test]
    fn test_path_circle() {
        let path = Path::circle(Point::new(50.0, 50.0), 25.0);
        assert!(!path.is_empty());
        assert_eq!(path.bounds(), Rect::new(25.0, 25.0, 50.0, 50.0));
    }

    #[test]
    fn test_path_polyline() {
        let points = vec![
            Point::new(0.0, 0.0),
            Point::new(100.0, 0.0),
            Point::new(100.0, 100.0),
        ];
        let path = Path::polyline(&points);
        assert_eq!(path.commands().len(), 3); // move, 2 lines
    }

    #[test]
    fn test_builder_reuse() {
        let mut builder = PathBuilder::new();
        builder
            .move_to(Point::new(0.0, 0.0))
            .line_to(Point::new(10.0, 10.0));
        let _path1 = builder.build();

        let mut builder = PathBuilder::new();
        builder
            .move_to(Point::new(5.0, 5.0))
            .line_to(Point::new(15.0, 15.0));
        let path2 = builder.build();
        assert_eq!(path2.bounds(), Rect::new(5.0, 5.0, 10.0, 10.0));
    }
}
