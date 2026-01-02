//! SVG Render Backend
//!
//! Generates SVG output for headless chart rendering.
//! Produces high-quality vector graphics suitable for print and scaling.

use super::backend::{ImageInfo, RenderBackend, TextMetrics};
use super::path::{Path, PathCommand};
use super::types::{
    Color, FillStyle, LineStyle, Point, Rect, TextAlign, TextBaseline, TextStyle, Transform2D,
};
use std::fmt::Write;

/// SVG render backend
///
/// Accumulates SVG elements and produces a complete SVG document.
pub struct SvgBackend {
    /// SVG content buffer
    content: String,
    /// Current width
    width: f64,
    /// Current height
    height: f64,
    /// Device pixel ratio
    dpr: f64,
    /// State stack (for save/restore)
    state_stack: Vec<SvgState>,
    /// Current state
    state: SvgState,
    /// Gradient definitions
    defs: String,
    /// Next gradient ID
    next_gradient_id: u32,
}

#[derive(Clone, Debug, Default)]
struct SvgState {
    transform: Option<Transform2D>,
    clip_path: Option<String>,
    alpha: f64,
}

impl SvgBackend {
    /// Create a new SVG backend
    pub fn new(width: u32, height: u32, dpr: f64) -> Self {
        Self {
            content: String::with_capacity(65536),
            width: width as f64,
            height: height as f64,
            dpr,
            state_stack: Vec::new(),
            state: SvgState {
                alpha: 1.0,
                ..Default::default()
            },
            defs: String::new(),
            next_gradient_id: 0,
        }
    }

    /// Get the SVG document as a string
    pub fn to_svg(&self) -> String {
        let mut svg = String::with_capacity(self.content.len() + 512);

        writeln!(
            svg,
            r#"<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{}" height="{}" viewBox="0 0 {} {}">
<defs>
{}
</defs>
{}</svg>"#,
            self.width, self.height, self.width, self.height, self.defs, self.content
        )
        .unwrap();

        svg
    }

    /// Convert color to CSS string
    fn color_to_css(color: Color) -> String {
        if color.a < 255 {
            format!(
                "rgba({},{},{},{})",
                color.r,
                color.g,
                color.b,
                color.a as f64 / 255.0
            )
        } else {
            format!("#{:02x}{:02x}{:02x}", color.r, color.g, color.b)
        }
    }

    /// Convert path to SVG path data
    fn path_to_d(path: &Path) -> String {
        let mut d = String::new();

        for cmd in path.commands() {
            match cmd {
                PathCommand::MoveTo(p) => {
                    write!(d, "M{:.2} {:.2} ", p.x, p.y).unwrap();
                }
                PathCommand::LineTo(p) => {
                    write!(d, "L{:.2} {:.2} ", p.x, p.y).unwrap();
                }
                PathCommand::QuadTo { control, end } => {
                    write!(
                        d,
                        "Q{:.2} {:.2} {:.2} {:.2} ",
                        control.x, control.y, end.x, end.y
                    )
                    .unwrap();
                }
                PathCommand::CubicTo { c1, c2, end } => {
                    write!(
                        d,
                        "C{:.2} {:.2} {:.2} {:.2} {:.2} {:.2} ",
                        c1.x, c1.y, c2.x, c2.y, end.x, end.y
                    )
                    .unwrap();
                }
                PathCommand::Arc {
                    center,
                    radius,
                    start,
                    end,
                    ccw,
                } => {
                    // Convert arc to SVG arc
                    let start_x = center.x + radius * start.cos();
                    let start_y = center.y + radius * start.sin();
                    let end_x = center.x + radius * end.cos();
                    let end_y = center.y + radius * end.sin();
                    let large_arc = if (end - start).abs() > std::f64::consts::PI {
                        1
                    } else {
                        0
                    };
                    let sweep = if *ccw { 0 } else { 1 };
                    write!(
                        d,
                        "M{:.2} {:.2} A{:.2} {:.2} 0 {} {} {:.2} {:.2} ",
                        start_x, start_y, radius, radius, large_arc, sweep, end_x, end_y
                    )
                    .unwrap();
                }
                PathCommand::Ellipse {
                    center,
                    rx,
                    ry,
                    rotation,
                    start,
                    end,
                    ccw,
                } => {
                    // Simplified ellipse to arc conversion
                    let cos_r = rotation.cos();
                    let sin_r = rotation.sin();
                    let start_x = center.x + rx * start.cos() * cos_r - ry * start.sin() * sin_r;
                    let start_y = center.y + rx * start.cos() * sin_r + ry * start.sin() * cos_r;
                    let end_x = center.x + rx * end.cos() * cos_r - ry * end.sin() * sin_r;
                    let end_y = center.y + rx * end.cos() * sin_r + ry * end.sin() * cos_r;
                    let large_arc = if (end - start).abs() > std::f64::consts::PI {
                        1
                    } else {
                        0
                    };
                    let sweep = if *ccw { 0 } else { 1 };
                    write!(
                        d,
                        "M{:.2} {:.2} A{:.2} {:.2} {:.2} {} {} {:.2} {:.2} ",
                        start_x,
                        start_y,
                        rx,
                        ry,
                        rotation.to_degrees(),
                        large_arc,
                        sweep,
                        end_x,
                        end_y
                    )
                    .unwrap();
                }
                PathCommand::Close => {
                    d.push_str("Z ");
                }
            }
        }

        d.trim_end().to_string()
    }

    /// Convert line style to SVG attributes
    fn line_style_attrs(style: &LineStyle) -> String {
        let mut attrs = format!(
            r#"stroke="{}" stroke-width="{:.2}""#,
            Self::color_to_css(style.color),
            style.width
        );

        if let Some(ref dash) = style.dash {
            if !dash.is_empty() {
                let dash_str: Vec<String> = dash.iter().map(|d| format!("{:.2}", d)).collect();
                write!(attrs, r#" stroke-dasharray="{}""#, dash_str.join(",")).unwrap();
            }
        }

        match style.cap {
            super::types::LineCap::Butt => {}
            super::types::LineCap::Round => {
                attrs.push_str(r#" stroke-linecap="round""#);
            }
            super::types::LineCap::Square => {
                attrs.push_str(r#" stroke-linecap="square""#);
            }
        }

        match style.join {
            super::types::LineJoin::Miter => {}
            super::types::LineJoin::Round => {
                attrs.push_str(r#" stroke-linejoin="round""#);
            }
            super::types::LineJoin::Bevel => {
                attrs.push_str(r#" stroke-linejoin="bevel""#);
            }
        }

        attrs
    }

    /// Get fill attribute for FillStyle
    fn fill_attr(&mut self, style: &FillStyle) -> String {
        match style {
            FillStyle::Solid(color) => {
                format!(r#"fill="{}""#, Self::color_to_css(*color))
            }
            FillStyle::LinearGradient { start, end, stops } => {
                let id = self.next_gradient_id;
                self.next_gradient_id += 1;

                let mut gradient = format!(
                    r#"<linearGradient id="grad{}" x1="{:.2}%" y1="{:.2}%" x2="{:.2}%" y2="{:.2}%">"#,
                    id,
                    start.x * 100.0,
                    start.y * 100.0,
                    end.x * 100.0,
                    end.y * 100.0
                );

                for (offset, color) in stops {
                    write!(
                        gradient,
                        r#"<stop offset="{:.0}%" stop-color="{}"/>"#,
                        offset * 100.0,
                        Self::color_to_css(*color)
                    )
                    .unwrap();
                }

                gradient.push_str("</linearGradient>\n");
                self.defs.push_str(&gradient);

                format!(r#"fill="url(#grad{})""#, id)
            }
            FillStyle::RadialGradient {
                center,
                radius,
                stops,
            } => {
                let id = self.next_gradient_id;
                self.next_gradient_id += 1;

                let mut gradient = format!(
                    r#"<radialGradient id="grad{}" cx="{:.2}%" cy="{:.2}%" r="{:.2}%">"#,
                    id,
                    center.x * 100.0,
                    center.y * 100.0,
                    radius * 100.0
                );

                for (offset, color) in stops {
                    write!(
                        gradient,
                        r#"<stop offset="{:.0}%" stop-color="{}"/>"#,
                        offset * 100.0,
                        Self::color_to_css(*color)
                    )
                    .unwrap();
                }

                gradient.push_str("</radialGradient>\n");
                self.defs.push_str(&gradient);

                format!(r#"fill="url(#grad{})""#, id)
            }
        }
    }

    /// Get current transform string
    fn transform_attr(&self) -> String {
        if let Some(ref t) = self.state.transform {
            format!(
                r#" transform="matrix({:.4},{:.4},{:.4},{:.4},{:.2},{:.2})""#,
                t.a, t.b, t.c, t.d, t.e, t.f
            )
        } else {
            String::new()
        }
    }

    /// Get opacity attribute
    fn opacity_attr(&self) -> String {
        if self.state.alpha < 1.0 {
            format!(r#" opacity="{:.2}""#, self.state.alpha)
        } else {
            String::new()
        }
    }
}

impl RenderBackend for SvgBackend {
    fn begin_frame(&mut self, width: f64, height: f64, dpr: f64) {
        self.width = width;
        self.height = height;
        self.dpr = dpr;
        self.content.clear();
        self.defs.clear();
        self.state_stack.clear();
        self.state = SvgState {
            alpha: 1.0,
            ..Default::default()
        };
        self.next_gradient_id = 0;
    }

    fn end_frame(&mut self) {
        // Nothing to do - content is ready
    }

    fn dpr(&self) -> f64 {
        self.dpr
    }

    fn size(&self) -> (f64, f64) {
        (self.width, self.height)
    }

    fn clear(&mut self, color: Color) {
        writeln!(
            self.content,
            r#"<rect x="0" y="0" width="{}" height="{}" fill="{}"/>"#,
            self.width,
            self.height,
            Self::color_to_css(color)
        )
        .unwrap();
    }

    fn clear_rect(&mut self, rect: Rect) {
        // SVG doesn't have clear_rect, but we can draw a rect with background
        writeln!(
            self.content,
            r#"<rect x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}" fill="none"/>"#,
            rect.x, rect.y, rect.width, rect.height
        )
        .unwrap();
    }

    fn fill_path(&mut self, path: &Path, style: &FillStyle) {
        let d = Self::path_to_d(path);
        let fill = self.fill_attr(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<path d="{}" {} stroke="none"{}{}/>""#,
            d, fill, transform, opacity
        )
        .unwrap();
    }

    fn stroke_path(&mut self, path: &Path, style: &LineStyle) {
        let d = Self::path_to_d(path);
        let stroke = Self::line_style_attrs(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<path d="{}" {} fill="none"{}{}/>""#,
            d, stroke, transform, opacity
        )
        .unwrap();
    }

    fn fill_rect(&mut self, rect: Rect, color: Color) {
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<rect x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}" fill="{}"{}{}/>""#,
            rect.x,
            rect.y,
            rect.width,
            rect.height,
            Self::color_to_css(color),
            transform,
            opacity
        )
        .unwrap();
    }

    fn stroke_rect(&mut self, rect: Rect, style: &LineStyle) {
        let stroke = Self::line_style_attrs(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<rect x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}" {} fill="none"{}{}/>""#,
            rect.x, rect.y, rect.width, rect.height, stroke, transform, opacity
        )
        .unwrap();
    }

    fn line(&mut self, from: Point, to: Point, style: &LineStyle) {
        let stroke = Self::line_style_attrs(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<line x1="{:.2}" y1="{:.2}" x2="{:.2}" y2="{:.2}" {}{}{}/>""#,
            from.x, from.y, to.x, to.y, stroke, transform, opacity
        )
        .unwrap();
    }

    fn polyline(&mut self, points: &[Point], style: &LineStyle) {
        if points.len() < 2 {
            return;
        }

        let pts: Vec<String> = points
            .iter()
            .map(|p| format!("{:.2},{:.2}", p.x, p.y))
            .collect();

        let stroke = Self::line_style_attrs(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<polyline points="{}" {} fill="none"{}{}/>""#,
            pts.join(" "),
            stroke,
            transform,
            opacity
        )
        .unwrap();
    }

    fn fill_circle(&mut self, center: Point, radius: f64, color: Color) {
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<circle cx="{:.2}" cy="{:.2}" r="{:.2}" fill="{}" stroke="none"{}{}/>""#,
            center.x,
            center.y,
            radius,
            Self::color_to_css(color),
            transform,
            opacity
        )
        .unwrap();
    }

    fn stroke_circle(&mut self, center: Point, radius: f64, style: &LineStyle) {
        let stroke = Self::line_style_attrs(style);
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<circle cx="{:.2}" cy="{:.2}" r="{:.2}" {} fill="none"{}{}/>""#,
            center.x, center.y, radius, stroke, transform, opacity
        )
        .unwrap();
    }

    fn fill_ellipse(&mut self, center: Point, rx: f64, ry: f64, rotation: f64, color: Color) {
        let mut transform = self.transform_attr();
        if rotation != 0.0 {
            write!(
                transform,
                r#" transform="rotate({:.2},{:.2},{:.2})""#,
                rotation.to_degrees(),
                center.x,
                center.y
            )
            .unwrap();
        }
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<ellipse cx="{:.2}" cy="{:.2}" rx="{:.2}" ry="{:.2}" fill="{}" stroke="none"{}{}/>""#,
            center.x, center.y, rx, ry, Self::color_to_css(color), transform, opacity
        ).unwrap();
    }

    fn stroke_ellipse(
        &mut self,
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        style: &LineStyle,
    ) {
        let stroke = Self::line_style_attrs(style);
        let mut transform = self.transform_attr();
        if rotation != 0.0 {
            write!(
                transform,
                r#" transform="rotate({:.2},{:.2},{:.2})""#,
                rotation.to_degrees(),
                center.x,
                center.y
            )
            .unwrap();
        }
        let opacity = self.opacity_attr();

        writeln!(
            self.content,
            r#"<ellipse cx="{:.2}" cy="{:.2}" rx="{:.2}" ry="{:.2}" {} fill="none"{}{}/>""#,
            center.x, center.y, rx, ry, stroke, transform, opacity
        )
        .unwrap();
    }

    fn text(&mut self, text: &str, pos: Point, style: &TextStyle) {
        let anchor = match style.align {
            TextAlign::Left => "start",
            TextAlign::Center => "middle",
            TextAlign::Right => "end",
        };

        let baseline = match style.baseline {
            TextBaseline::Top => "hanging",
            TextBaseline::Middle => "central",
            TextBaseline::Bottom => "text-after-edge",
            TextBaseline::Alphabetic => "alphabetic",
        };

        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        let font_weight = match style.font_weight {
            super::types::FontWeight::Bold => r#" font-weight="bold""#,
            super::types::FontWeight::Light => r#" font-weight="lighter""#,
            super::types::FontWeight::Normal => "",
        };

        // Escape XML special characters
        let escaped = text
            .replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
            .replace('"', "&quot;");

        writeln!(
            self.content,
            r#"<text x="{:.2}" y="{:.2}" fill="{}" font-family="{}" font-size="{:.1}" text-anchor="{}" dominant-baseline="{}"{}{}{}>{}</text>"#,
            pos.x, pos.y,
            Self::color_to_css(style.color),
            style.font_family,
            style.font_size,
            anchor,
            baseline,
            font_weight,
            transform,
            opacity,
            escaped
        ).unwrap();
    }

    fn measure_text(&self, text: &str, style: &TextStyle) -> TextMetrics {
        // Approximate text measurement (SVG is typically rendered client-side)
        let char_width = style.font_size * 0.6;
        let width = text.len() as f64 * char_width;

        TextMetrics {
            width,
            height: style.font_size,
            ascent: style.font_size * 0.8,
            descent: style.font_size * 0.2,
        }
    }

    fn image(&mut self, id: &str, src: Option<Rect>, dst: Rect) {
        // SVG xlink:href for images
        let transform = self.transform_attr();
        let opacity = self.opacity_attr();

        if let Some(_src_rect) = src {
            // Clip to source rectangle (would need clipPath)
            writeln!(
                self.content,
                r#"<image x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}" href="{}"{}{}/>""#,
                dst.x, dst.y, dst.width, dst.height, id, transform, opacity
            )
            .unwrap();
        } else {
            writeln!(
                self.content,
                r#"<image x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}" href="{}"{}{}/>""#,
                dst.x, dst.y, dst.width, dst.height, id, transform, opacity
            )
            .unwrap();
        }
    }

    fn image_info(&self, _id: &str) -> Option<ImageInfo> {
        // SVG backend doesn't track image info
        None
    }

    fn preload_image(&mut self, _id: &str, _url: &str) {
        // No-op for SVG
    }

    fn push_clip(&mut self, rect: Rect) {
        let clip_id = format!("clip{}", self.next_gradient_id);
        self.next_gradient_id += 1;

        writeln!(
            self.defs,
            r#"<clipPath id="{}"><rect x="{:.2}" y="{:.2}" width="{:.2}" height="{:.2}"/></clipPath>"#,
            clip_id, rect.x, rect.y, rect.width, rect.height
        ).unwrap();

        writeln!(self.content, r#"<g clip-path="url(#{})">"#, clip_id).unwrap();
        self.state.clip_path = Some(clip_id);
    }

    fn pop_clip(&mut self) {
        writeln!(self.content, "</g>").unwrap();
        self.state.clip_path = None;
    }

    fn push_transform(&mut self, transform: Transform2D) {
        writeln!(
            self.content,
            r#"<g transform="matrix({:.4},{:.4},{:.4},{:.4},{:.2},{:.2})">"#,
            transform.a, transform.b, transform.c, transform.d, transform.e, transform.f
        )
        .unwrap();
        self.state.transform = Some(transform);
    }

    fn pop_transform(&mut self) {
        writeln!(self.content, "</g>").unwrap();
        self.state.transform = None;
    }

    fn push_layer(&mut self, opacity: f64) {
        writeln!(self.content, r#"<g opacity="{:.2}">"#, opacity).unwrap();
    }

    fn pop_layer(&mut self) {
        writeln!(self.content, "</g>").unwrap();
    }

    fn set_alpha(&mut self, alpha: f64) {
        self.state.alpha = alpha;
    }

    fn save(&mut self) {
        self.state_stack.push(self.state.clone());
        writeln!(self.content, "<g>").unwrap();
    }

    fn restore(&mut self) {
        if let Some(state) = self.state_stack.pop() {
            self.state = state;
        }
        writeln!(self.content, "</g>").unwrap();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_svg_basic() {
        let mut backend = SvgBackend::new(800, 600, 1.0);
        backend.begin_frame(800.0, 600.0, 1.0);
        backend.clear(Color::rgb(19, 23, 34));
        backend.fill_rect(Rect::new(10.0, 10.0, 100.0, 50.0), Color::rgb(255, 0, 0));
        backend.end_frame();

        let svg = backend.to_svg();
        assert!(svg.contains("<svg"));
        assert!(svg.contains("rect"));
        assert!(svg.contains("#ff0000"));
    }

    #[test]
    fn test_svg_line() {
        let mut backend = SvgBackend::new(400, 300, 1.0);
        backend.begin_frame(400.0, 300.0, 1.0);
        backend.line(
            Point::new(0.0, 0.0),
            Point::new(100.0, 100.0),
            &LineStyle::solid(Color::rgb(0, 255, 0), 2.0),
        );
        backend.end_frame();

        let svg = backend.to_svg();
        assert!(svg.contains("<line"));
        assert!(svg.contains("stroke="));
    }
}
