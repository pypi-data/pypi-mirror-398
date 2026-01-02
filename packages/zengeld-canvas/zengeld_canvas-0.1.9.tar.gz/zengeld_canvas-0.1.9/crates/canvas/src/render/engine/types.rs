//! Core rendering types
//!
//! Minimal, zero-copy types optimized for high-frequency rendering.
//! All types are `Copy` where possible to avoid allocation.

use serde::{Deserialize, Serialize};

// =============================================================================
// Geometry Types (all Copy for zero-cost passing)
// =============================================================================

/// RGBA color with 8-bit components
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

impl Color {
    pub const TRANSPARENT: Color = Color {
        r: 0,
        g: 0,
        b: 0,
        a: 0,
    };
    pub const BLACK: Color = Color {
        r: 0,
        g: 0,
        b: 0,
        a: 255,
    };
    pub const WHITE: Color = Color {
        r: 255,
        g: 255,
        b: 255,
        a: 255,
    };

    #[inline]
    pub const fn rgb(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b, a: 255 }
    }

    #[inline]
    pub const fn rgba(r: u8, g: u8, b: u8, a: u8) -> Self {
        Self { r, g, b, a }
    }

    /// Create from hex string (#RGB, #RRGGBB, #RRGGBBAA)
    pub fn from_hex(hex: &str) -> Option<Self> {
        let hex = hex.trim_start_matches('#');
        match hex.len() {
            3 => {
                let r = u8::from_str_radix(&hex[0..1], 16).ok()? * 17;
                let g = u8::from_str_radix(&hex[1..2], 16).ok()? * 17;
                let b = u8::from_str_radix(&hex[2..3], 16).ok()? * 17;
                Some(Self::rgb(r, g, b))
            }
            6 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
                Some(Self::rgb(r, g, b))
            }
            8 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
                let a = u8::from_str_radix(&hex[6..8], 16).ok()?;
                Some(Self::rgba(r, g, b, a))
            }
            _ => None,
        }
    }

    /// Parse CSS color string (hex, rgb(), rgba())
    pub fn from_css(css: &str) -> Option<Self> {
        let css = css.trim();

        if css.starts_with('#') {
            return Self::from_hex(css);
        }

        if css.starts_with("rgba(") && css.ends_with(')') {
            let inner = &css[5..css.len() - 1];
            let parts: Vec<&str> = inner.split(',').map(|s| s.trim()).collect();
            if parts.len() == 4 {
                let r = parts[0].parse().ok()?;
                let g = parts[1].parse().ok()?;
                let b = parts[2].parse().ok()?;
                let a = (parts[3].parse::<f64>().ok()? * 255.0) as u8;
                return Some(Self::rgba(r, g, b, a));
            }
        }

        if css.starts_with("rgb(") && css.ends_with(')') {
            let inner = &css[4..css.len() - 1];
            let parts: Vec<&str> = inner.split(',').map(|s| s.trim()).collect();
            if parts.len() == 3 {
                let r = parts[0].parse().ok()?;
                let g = parts[1].parse().ok()?;
                let b = parts[2].parse().ok()?;
                return Some(Self::rgb(r, g, b));
            }
        }

        None
    }

    /// Convert to CSS string
    #[inline]
    pub fn to_css(&self) -> String {
        if self.a == 255 {
            format!("#{:02x}{:02x}{:02x}", self.r, self.g, self.b)
        } else {
            format!(
                "rgba({},{},{},{:.3})",
                self.r,
                self.g,
                self.b,
                self.a as f64 / 255.0
            )
        }
    }

    /// Apply alpha multiplication
    #[inline]
    pub fn with_alpha(self, alpha: f64) -> Self {
        Self {
            r: self.r,
            g: self.g,
            b: self.b,
            a: (self.a as f64 * alpha.clamp(0.0, 1.0)) as u8,
        }
    }
}

/// 2D point (f64 for precision in coordinate transforms)
#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
#[repr(C)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub const ZERO: Point = Point { x: 0.0, y: 0.0 };

    #[inline]
    pub const fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    #[inline]
    pub fn distance_to(self, other: Point) -> f64 {
        let dx = other.x - self.x;
        let dy = other.y - self.y;
        (dx * dx + dy * dy).sqrt()
    }

    #[inline]
    pub fn lerp(self, other: Point, t: f64) -> Point {
        Point {
            x: self.x + (other.x - self.x) * t,
            y: self.y + (other.y - self.y) * t,
        }
    }
}

impl std::ops::Add for Point {
    type Output = Point;
    #[inline]
    fn add(self, rhs: Point) -> Point {
        Point {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
        }
    }
}

impl std::ops::Sub for Point {
    type Output = Point;
    #[inline]
    fn sub(self, rhs: Point) -> Point {
        Point {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
        }
    }
}

impl std::ops::Mul<f64> for Point {
    type Output = Point;
    #[inline]
    fn mul(self, rhs: f64) -> Point {
        Point {
            x: self.x * rhs,
            y: self.y * rhs,
        }
    }
}

/// Axis-aligned rectangle
#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
#[repr(C)]
pub struct Rect {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}

impl Rect {
    pub const ZERO: Rect = Rect {
        x: 0.0,
        y: 0.0,
        width: 0.0,
        height: 0.0,
    };

    #[inline]
    pub const fn new(x: f64, y: f64, width: f64, height: f64) -> Self {
        Self {
            x,
            y,
            width,
            height,
        }
    }

    #[inline]
    pub fn from_points(p1: Point, p2: Point) -> Self {
        let x = p1.x.min(p2.x);
        let y = p1.y.min(p2.y);
        let width = (p2.x - p1.x).abs();
        let height = (p2.y - p1.y).abs();
        Self {
            x,
            y,
            width,
            height,
        }
    }

    #[inline]
    pub fn right(&self) -> f64 {
        self.x + self.width
    }

    #[inline]
    pub fn bottom(&self) -> f64 {
        self.y + self.height
    }

    #[inline]
    pub fn center(&self) -> Point {
        Point::new(self.x + self.width / 2.0, self.y + self.height / 2.0)
    }

    #[inline]
    pub fn contains(&self, p: Point) -> bool {
        p.x >= self.x && p.x <= self.right() && p.y >= self.y && p.y <= self.bottom()
    }

    #[inline]
    pub fn intersects(&self, other: &Rect) -> bool {
        self.x < other.right()
            && self.right() > other.x
            && self.y < other.bottom()
            && self.bottom() > other.y
    }

    #[inline]
    pub fn union(&self, other: &Rect) -> Rect {
        let x = self.x.min(other.x);
        let y = self.y.min(other.y);
        let right = self.right().max(other.right());
        let bottom = self.bottom().max(other.bottom());
        Rect::new(x, y, right - x, bottom - y)
    }

    #[inline]
    pub fn expand(&self, amount: f64) -> Rect {
        Rect::new(
            self.x - amount,
            self.y - amount,
            self.width + amount * 2.0,
            self.height + amount * 2.0,
        )
    }
}

/// 2D affine transform matrix
#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[repr(C)]
pub struct Transform2D {
    pub a: f64,
    pub b: f64, // scale_x, skew_y
    pub c: f64,
    pub d: f64, // skew_x, scale_y
    pub e: f64,
    pub f: f64, // translate_x, translate_y
}

impl Default for Transform2D {
    fn default() -> Self {
        Self::IDENTITY
    }
}

impl Transform2D {
    pub const IDENTITY: Transform2D = Transform2D {
        a: 1.0,
        b: 0.0,
        c: 0.0,
        d: 1.0,
        e: 0.0,
        f: 0.0,
    };

    #[inline]
    pub fn translate(tx: f64, ty: f64) -> Self {
        Self {
            a: 1.0,
            b: 0.0,
            c: 0.0,
            d: 1.0,
            e: tx,
            f: ty,
        }
    }

    #[inline]
    pub fn scale(sx: f64, sy: f64) -> Self {
        Self {
            a: sx,
            b: 0.0,
            c: 0.0,
            d: sy,
            e: 0.0,
            f: 0.0,
        }
    }

    #[inline]
    pub fn rotate(angle: f64) -> Self {
        let cos = angle.cos();
        let sin = angle.sin();
        Self {
            a: cos,
            b: sin,
            c: -sin,
            d: cos,
            e: 0.0,
            f: 0.0,
        }
    }

    /// Rotate around a center point
    #[inline]
    pub fn rotation(angle: f64, cx: f64, cy: f64) -> Self {
        // Translate to origin, rotate, translate back
        let cos = angle.cos();
        let sin = angle.sin();
        Self {
            a: cos,
            b: sin,
            c: -sin,
            d: cos,
            e: cx - cos * cx + sin * cy,
            f: cy - sin * cx - cos * cy,
        }
    }

    #[inline]
    pub fn transform_point(&self, p: Point) -> Point {
        Point {
            x: self.a * p.x + self.c * p.y + self.e,
            y: self.b * p.x + self.d * p.y + self.f,
        }
    }

    #[inline]
    pub fn then(&self, other: &Transform2D) -> Transform2D {
        Transform2D {
            a: self.a * other.a + self.b * other.c,
            b: self.a * other.b + self.b * other.d,
            c: self.c * other.a + self.d * other.c,
            d: self.c * other.b + self.d * other.d,
            e: self.e * other.a + self.f * other.c + other.e,
            f: self.e * other.b + self.f * other.d + other.f,
        }
    }
}

// =============================================================================
// Style Types
// =============================================================================

/// Line cap style
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum LineCap {
    #[default]
    Butt,
    Round,
    Square,
}

/// Line join style
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum LineJoin {
    #[default]
    Miter,
    Round,
    Bevel,
}

/// Line style configuration
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct LineStyle {
    pub color: Color,
    pub width: f64,
    pub dash: Option<Vec<f64>>,
    pub cap: LineCap,
    pub join: LineJoin,
}

impl Default for LineStyle {
    fn default() -> Self {
        Self {
            color: Color::WHITE,
            width: 1.0,
            dash: None,
            cap: LineCap::Butt,
            join: LineJoin::Miter,
        }
    }
}

impl LineStyle {
    #[inline]
    pub fn solid(color: Color, width: f64) -> Self {
        Self {
            color,
            width,
            ..Default::default()
        }
    }

    #[inline]
    pub fn dashed(color: Color, width: f64, dash_len: f64, gap_len: f64) -> Self {
        Self {
            color,
            width,
            dash: Some(vec![dash_len, gap_len]),
            ..Default::default()
        }
    }

    #[inline]
    pub fn dotted(color: Color, width: f64) -> Self {
        Self::dashed(color, width, 2.0, 2.0)
    }

    /// Large dashed style [12, 6]
    #[inline]
    pub fn large_dashed(color: Color, width: f64) -> Self {
        Self::dashed(color, width, 12.0, 6.0)
    }

    /// Sparse dotted style [2, 8]
    #[inline]
    pub fn sparse_dotted(color: Color, width: f64) -> Self {
        Self::dashed(color, width, 2.0, 8.0)
    }

    /// With custom cap style
    #[inline]
    pub fn with_cap(mut self, cap: LineCap) -> Self {
        self.cap = cap;
        self
    }

    /// With custom join style
    #[inline]
    pub fn with_join(mut self, join: LineJoin) -> Self {
        self.join = join;
        self
    }
}

/// Fill style
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum FillStyle {
    Solid(Color),
    LinearGradient {
        start: Point,
        end: Point,
        stops: Vec<(f64, Color)>,
    },
    RadialGradient {
        center: Point,
        radius: f64,
        stops: Vec<(f64, Color)>,
    },
}

impl Default for FillStyle {
    fn default() -> Self {
        FillStyle::Solid(Color::WHITE)
    }
}

impl FillStyle {
    #[inline]
    pub fn solid(color: Color) -> Self {
        FillStyle::Solid(color)
    }

    /// Create a simple vertical linear gradient (top to bottom)
    #[inline]
    pub fn linear_vertical(
        y_start: f64,
        y_end: f64,
        top_color: Color,
        bottom_color: Color,
    ) -> Self {
        FillStyle::LinearGradient {
            start: Point::new(0.0, y_start),
            end: Point::new(0.0, y_end),
            stops: vec![(0.0, top_color), (1.0, bottom_color)],
        }
    }

    /// Create a simple horizontal linear gradient (left to right)
    #[inline]
    pub fn linear_horizontal(
        x_start: f64,
        x_end: f64,
        left_color: Color,
        right_color: Color,
    ) -> Self {
        FillStyle::LinearGradient {
            start: Point::new(x_start, 0.0),
            end: Point::new(x_end, 0.0),
            stops: vec![(0.0, left_color), (1.0, right_color)],
        }
    }

    /// Create a linear gradient with custom stops
    #[inline]
    pub fn linear_gradient(start: Point, end: Point, stops: Vec<(f64, Color)>) -> Self {
        FillStyle::LinearGradient { start, end, stops }
    }

    /// Create a radial gradient
    #[inline]
    pub fn radial_gradient(center: Point, radius: f64, stops: Vec<(f64, Color)>) -> Self {
        FillStyle::RadialGradient {
            center,
            radius,
            stops,
        }
    }

    /// Create a simple radial gradient (center to edge)
    #[inline]
    pub fn radial_simple(
        center: Point,
        radius: f64,
        center_color: Color,
        edge_color: Color,
    ) -> Self {
        FillStyle::RadialGradient {
            center,
            radius,
            stops: vec![(0.0, center_color), (1.0, edge_color)],
        }
    }

    /// Get color at position (for solid fills, always returns the color)
    pub fn color_at(&self, t: f64) -> Color {
        match self {
            FillStyle::Solid(c) => *c,
            FillStyle::LinearGradient { stops, .. } | FillStyle::RadialGradient { stops, .. } => {
                if stops.is_empty() {
                    return Color::TRANSPARENT;
                }
                if stops.len() == 1 {
                    return stops[0].1;
                }
                let t = t.clamp(0.0, 1.0);
                // Find surrounding stops
                for i in 0..stops.len() - 1 {
                    let (t0, c0) = stops[i];
                    let (t1, c1) = stops[i + 1];
                    if t >= t0 && t <= t1 {
                        let local_t = if (t1 - t0).abs() < 1e-9 {
                            0.0
                        } else {
                            (t - t0) / (t1 - t0)
                        };
                        return Color::rgba(
                            (c0.r as f64 + (c1.r as f64 - c0.r as f64) * local_t) as u8,
                            (c0.g as f64 + (c1.g as f64 - c0.g as f64) * local_t) as u8,
                            (c0.b as f64 + (c1.b as f64 - c0.b as f64) * local_t) as u8,
                            (c0.a as f64 + (c1.a as f64 - c0.a as f64) * local_t) as u8,
                        );
                    }
                }
                stops.last().map(|(_, c)| *c).unwrap_or(Color::TRANSPARENT)
            }
        }
    }
}

/// Font weight
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum FontWeight {
    #[default]
    Normal,
    Bold,
    Light,
}

/// Text horizontal alignment
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum TextAlign {
    #[default]
    Left,
    Center,
    Right,
}

/// Text vertical baseline
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum TextBaseline {
    Top,
    #[default]
    Middle,
    Bottom,
    Alphabetic,
}

/// Text style configuration
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TextStyle {
    pub font_family: String,
    pub font_size: f64,
    pub font_weight: FontWeight,
    pub color: Color,
    pub align: TextAlign,
    pub baseline: TextBaseline,
}

impl Default for TextStyle {
    fn default() -> Self {
        Self {
            font_family: "sans-serif".to_string(),
            font_size: 12.0,
            font_weight: FontWeight::Normal,
            color: Color::WHITE,
            align: TextAlign::Left,
            baseline: TextBaseline::Middle,
        }
    }
}

impl TextStyle {
    /// Convert to CSS font string
    pub fn to_css_font(&self) -> String {
        let weight = match self.font_weight {
            FontWeight::Normal => "",
            FontWeight::Bold => "bold ",
            FontWeight::Light => "300 ",
        };
        format!("{}{}px {}", weight, self.font_size as i32, self.font_family)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_from_hex() {
        assert_eq!(Color::from_hex("#fff"), Some(Color::rgb(255, 255, 255)));
        assert_eq!(Color::from_hex("#000000"), Some(Color::rgb(0, 0, 0)));
        assert_eq!(
            Color::from_hex("#ff000080"),
            Some(Color::rgba(255, 0, 0, 128))
        );
    }

    #[test]
    fn test_color_from_css() {
        assert_eq!(
            Color::from_css("rgb(255, 0, 0)"),
            Some(Color::rgb(255, 0, 0))
        );
        assert_eq!(
            Color::from_css("rgba(0, 255, 0, 0.5)"),
            Some(Color::rgba(0, 255, 0, 127))
        );
    }

    #[test]
    fn test_rect_operations() {
        let r1 = Rect::new(0.0, 0.0, 100.0, 100.0);
        let r2 = Rect::new(50.0, 50.0, 100.0, 100.0);

        assert!(r1.intersects(&r2));
        assert!(r1.contains(Point::new(50.0, 50.0)));

        let union = r1.union(&r2);
        assert_eq!(union, Rect::new(0.0, 0.0, 150.0, 150.0));
    }

    #[test]
    fn test_transform() {
        let t = Transform2D::translate(10.0, 20.0);
        let p = t.transform_point(Point::new(5.0, 5.0));
        assert_eq!(p, Point::new(15.0, 25.0));
    }
}
