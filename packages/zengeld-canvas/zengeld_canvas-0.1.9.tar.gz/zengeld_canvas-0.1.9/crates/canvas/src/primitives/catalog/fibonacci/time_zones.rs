//! Fibonacci Time Zones primitive
//!
//! Vertical lines at Fibonacci intervals from a starting point.
//! Shows time-based projections: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89 bars...

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

/// Fibonacci sequence for time zones
pub const FIB_SEQUENCE: &[i32] = &[1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233];

/// Fibonacci Time Zones - vertical lines at Fib intervals
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibTimeZones {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Starting bar index
    pub start_bar: f64,
    /// Starting price (for anchor display)
    pub start_price: f64,
    /// Number of zones to show
    #[serde(default = "default_zone_count")]
    pub zone_count: usize,
    /// Show zone labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
}

fn default_true() -> bool {
    true
}
fn default_zone_count() -> usize {
    12
}

impl FibTimeZones {
    /// Create new Fibonacci time zones
    pub fn new(start_bar: f64, start_price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_time_zones".to_string(),
                display_name: "Fib Time Zones".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            start_bar,
            start_price,
            zone_count: 12,
            show_labels: true,
        }
    }

    /// Get bar positions for all zones
    pub fn zone_bars(&self) -> Vec<f64> {
        FIB_SEQUENCE
            .iter()
            .take(self.zone_count)
            .map(|&n| self.start_bar + n as f64)
            .collect()
    }
}

impl Primitive for FibTimeZones {
    fn type_id(&self) -> &'static str {
        "fib_time_zones"
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
        vec![(self.start_bar, self.start_price)]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.start_bar = bar;
            self.start_price = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.start_bar += bar_delta;
        self.start_price += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let start_x = ctx.bar_to_x(self.start_bar);
        let chart_height = ctx.chart_height();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw starting vertical line
        ctx.begin_path();
        ctx.move_to(crisp(start_x, dpr), 0.0);
        ctx.line_to(crisp(start_x, dpr), chart_height);
        ctx.stroke();

        // Draw vertical lines at each Fibonacci zone
        for zone_bar in self.zone_bars() {
            let zone_x = ctx.bar_to_x(zone_bar);
            ctx.begin_path();
            ctx.move_to(crisp(zone_x, dpr), 0.0);
            ctx.line_to(crisp(zone_x, dpr), chart_height);
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
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

fn create_fib_time_zones(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar, price) = points.first().copied().unwrap_or((0.0, 0.0));
    Box::new(FibTimeZones::new(bar, price, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_time_zones",
        display_name: "Fib Time Zones",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_time_zones,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
