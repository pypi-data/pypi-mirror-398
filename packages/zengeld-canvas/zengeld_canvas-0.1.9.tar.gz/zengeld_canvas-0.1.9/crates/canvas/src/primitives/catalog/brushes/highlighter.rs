//! Highlighter - semi-transparent highlight

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Highlighter {
    pub data: PrimitiveData,
    pub points: Vec<(f64, f64)>,
    #[serde(default = "default_size")]
    pub brush_size: f64,
    #[serde(default = "default_opacity")]
    pub opacity: f64,
}
fn default_size() -> f64 {
    20.0
}
fn default_opacity() -> f64 {
    0.4
}

impl Highlighter {
    pub fn new(points: Vec<(f64, f64)>, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "highlighter".to_string(),
                display_name: "Highlighter".to_string(),
                color: PrimitiveColor::new(color),
                width: 20.0,
                ..Default::default()
            },
            points,
            brush_size: 20.0,
            opacity: 0.4,
        }
    }
}

impl Primitive for Highlighter {
    fn type_id(&self) -> &'static str {
        "highlighter"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Annotation
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        self.points.clone()
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        self.points = pts.to_vec();
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        for p in &mut self.points {
            p.0 += bd;
            p.1 += pd;
        }
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        if self.points.is_empty() {
            return;
        }

        let _dpr = ctx.dpr();

        // Parse the color and apply opacity
        let color_with_opacity = apply_opacity(&self.data.color.stroke, self.opacity);

        ctx.set_stroke_color(&color_with_opacity);
        ctx.set_stroke_width(self.data.width);
        ctx.set_line_cap("round");
        ctx.set_line_join("round");

        // Convert to screen coordinates
        let screen_pts: Vec<(f64, f64)> = self
            .points
            .iter()
            .map(|&(bar, price)| (ctx.bar_to_x(bar), ctx.price_to_y(price)))
            .collect();

        // Draw smooth curve using quadratic bezier interpolation
        ctx.begin_path();
        if screen_pts.len() == 1 {
            // Single point - just draw a dot
            let (x, y) = screen_pts[0];
            ctx.arc(x, y, self.data.width / 2.0, 0.0, std::f64::consts::TAU);
            ctx.fill();
            return;
        } else if screen_pts.len() == 2 {
            // Two points - draw a line
            ctx.move_to(screen_pts[0].0, screen_pts[0].1);
            ctx.line_to(screen_pts[1].0, screen_pts[1].1);
        } else {
            // 3+ points - use quadratic bezier through midpoints for smooth curves
            ctx.move_to(screen_pts[0].0, screen_pts[0].1);

            // First segment: line to midpoint of first two points
            let mid_x = (screen_pts[0].0 + screen_pts[1].0) / 2.0;
            let mid_y = (screen_pts[0].1 + screen_pts[1].1) / 2.0;
            ctx.line_to(mid_x, mid_y);

            // Middle segments: quadratic curves through points, ending at midpoints
            for i in 1..screen_pts.len() - 1 {
                let next_mid_x = (screen_pts[i].0 + screen_pts[i + 1].0) / 2.0;
                let next_mid_y = (screen_pts[i].1 + screen_pts[i + 1].1) / 2.0;
                ctx.quadratic_curve_to(screen_pts[i].0, screen_pts[i].1, next_mid_x, next_mid_y);
            }

            // Last segment: line to final point
            let last = screen_pts.last().unwrap();
            ctx.line_to(last.0, last.1);
        }
        ctx.stroke();
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

fn apply_opacity(color: &str, opacity: f64) -> String {
    // Handle hex colors (#RGB or #RRGGBB)
    if let Some(hex) = color.strip_prefix('#') {
        let (r, g, b) = if hex.len() == 3 {
            // #RGB format
            let r = u8::from_str_radix(&hex[0..1], 16).unwrap_or(0) * 17;
            let g = u8::from_str_radix(&hex[1..2], 16).unwrap_or(0) * 17;
            let b = u8::from_str_radix(&hex[2..3], 16).unwrap_or(0) * 17;
            (r, g, b)
        } else if hex.len() == 6 {
            // #RRGGBB format
            let r = u8::from_str_radix(&hex[0..2], 16).unwrap_or(0);
            let g = u8::from_str_radix(&hex[2..4], 16).unwrap_or(0);
            let b = u8::from_str_radix(&hex[4..6], 16).unwrap_or(0);
            (r, g, b)
        } else {
            return color.to_string();
        };
        return format!("rgba({}, {}, {}, {})", r, g, b, opacity);
    }

    // If already rgba, replace alpha
    if color.starts_with("rgba(") {
        if let Some(close_paren) = color.rfind(')') {
            if let Some(last_comma) = color[..close_paren].rfind(',') {
                return format!("{}, {})", &color[..last_comma], opacity);
            }
        }
    }

    // If rgb, convert to rgba
    if let Some(rgb_inner) = color.strip_prefix("rgb(") {
        if let Some(rgb_inner) = rgb_inner.strip_suffix(')') {
            return format!("rgba({}, {})", rgb_inner, opacity);
        }
    }

    // Default: return original color
    color.to_string()
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "highlighter",
        display_name: "Highlighter",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| Box::new(Highlighter::new(points.to_vec(), color)),
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
