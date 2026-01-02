//! Fibonacci Wedge primitive
//!
//! A wedge/triangle shape with Fibonacci levels inside.
//! Three points define the wedge, levels are drawn between the sides.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Default wedge levels
pub const DEFAULT_WEDGE_LEVELS: &[f64] = &[0.236, 0.382, 0.5, 0.618, 0.786];

/// Fibonacci Wedge
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibWedge {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Apex bar (point 1 - the tip)
    pub bar1: f64,
    /// Apex price
    pub price1: f64,
    /// Upper corner bar (point 2)
    pub bar2: f64,
    /// Upper corner price
    pub price2: f64,
    /// Lower corner bar (point 3)
    pub bar3: f64,
    /// Lower corner price
    pub price3: f64,
    /// Fibonacci levels
    #[serde(default = "default_wedge_levels")]
    pub levels: Vec<f64>,
    /// Show labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
    /// Fill the wedge
    #[serde(default)]
    pub fill: bool,
    /// Fill opacity
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
}

fn default_true() -> bool {
    true
}
fn default_wedge_levels() -> Vec<f64> {
    DEFAULT_WEDGE_LEVELS.to_vec()
}
fn default_fill_opacity() -> f64 {
    0.1
}

impl FibWedge {
    /// Create a new Fibonacci wedge
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_wedge".to_string(),
                display_name: "Fib Wedge".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            bar3,
            price3,
            levels: DEFAULT_WEDGE_LEVELS.to_vec(),
            show_labels: true,
            fill: false,
            fill_opacity: 0.1,
        }
    }

    /// Get a point on the upper edge at parameter t (0=apex, 1=corner)
    fn upper_edge_point(&self, t: f64) -> (f64, f64) {
        (
            self.bar1 + t * (self.bar2 - self.bar1),
            self.price1 + t * (self.price2 - self.price1),
        )
    }

    /// Get a point on the lower edge at parameter t (0=apex, 1=corner)
    fn lower_edge_point(&self, t: f64) -> (f64, f64) {
        (
            self.bar1 + t * (self.bar3 - self.bar1),
            self.price1 + t * (self.price3 - self.price1),
        )
    }
}

impl Primitive for FibWedge {
    fn type_id(&self) -> &'static str {
        "fib_wedge"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Fibonacci
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar3, self.price3),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.bar1 = bar;
            self.price1 = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.bar2 = bar;
            self.price2 = price;
        }
        if let Some(&(bar, price)) = points.get(2) {
            self.bar3 = bar;
            self.price3 = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.bar3 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        self.price3 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);

        // Fill if enabled
        if self.fill {
            let opacity_hex = format!("{:02X}", (self.fill_opacity * 255.0) as u8);
            let fill_color = format!("{}{}", &self.data.color.stroke, opacity_hex);
            ctx.set_fill_color(&fill_color);
            ctx.begin_path();
            ctx.move_to(x1, y1);
            ctx.line_to(x2, y2);
            ctx.line_to(x3, y3);
            ctx.close_path();
            ctx.fill();
        }

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw wedge outline
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.line_to(crisp(x3, dpr), crisp(y3, dpr));
        ctx.close_path();
        ctx.stroke();

        // Draw Fibonacci level lines inside wedge
        for &level in &self.levels {
            let (u_bar, u_price) = self.upper_edge_point(level);
            let (l_bar, l_price) = self.lower_edge_point(level);

            let ux = ctx.bar_to_x(u_bar);
            let uy = ctx.price_to_y(u_price);
            let lx = ctx.bar_to_x(l_bar);
            let ly = ctx.price_to_y(l_price);

            ctx.begin_path();
            ctx.move_to(crisp(ux, dpr), crisp(uy, dpr));
            ctx.line_to(crisp(lx, dpr), crisp(ly, dpr));
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> {
        Some(
            self.levels
                .iter()
                .map(|&level| FibLevelConfig::new(level))
                .collect(),
        )
    }

    fn set_level_configs(&mut self, configs: Vec<FibLevelConfig>) -> bool {
        self.levels = configs.iter().map(|c| c.level).collect();
        true
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

// =============================================================================
// Factory Registration
// =============================================================================

fn create_fib_wedge(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 + 10.0));
    let (bar3, price3) = points
        .get(2)
        .copied()
        .unwrap_or((bar1 + 20.0, price1 - 10.0));
    Box::new(FibWedge::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_wedge",
        display_name: "Fib Wedge",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_wedge,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
