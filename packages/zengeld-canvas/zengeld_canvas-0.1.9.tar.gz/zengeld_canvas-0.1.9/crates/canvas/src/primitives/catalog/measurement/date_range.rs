//! Date Range - horizontal time measurement

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DateRange {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub bar2: f64,
    pub price: f64,
    #[serde(default = "default_true")]
    pub show_bars: bool,
    #[serde(default = "default_true")]
    pub show_time: bool,
}
fn default_true() -> bool {
    true
}

impl DateRange {
    pub fn new(bar1: f64, bar2: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "date_range".to_string(),
                display_name: "Date Range".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            bar2,
            price,
            show_bars: true,
            show_time: true,
        }
    }
}

impl Primitive for DateRange {
    fn type_id(&self) -> &'static str {
        "date_range"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Measurement
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, self.price), (self.bar2, self.price)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar1 = b;
            self.price = p;
        }
        if let Some(&(b, _)) = pts.get(1) {
            self.bar2 = b;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y = ctx.price_to_y(self.price);

        let min_x = x1.min(x2);
        let max_x = x1.max(x2);
        let w = max_x - min_x;

        // Draw filled area between the two vertical lines
        ctx.set_fill_color(&format!("{}40", &self.data.color.stroke));
        ctx.fill_rect(crisp(min_x, dpr), 0.0, w, ctx.height() as f64);

        // Draw the two vertical lines
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_line_style(LineStyle::Solid);
        ctx.set_stroke_width(self.data.width);

        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), 0.0);
        ctx.line_to(crisp(x1, dpr), ctx.height() as f64);
        ctx.stroke();

        ctx.begin_path();
        ctx.move_to(crisp(x2, dpr), 0.0);
        ctx.line_to(crisp(x2, dpr), ctx.height() as f64);
        ctx.stroke();

        // Draw bar count label
        let bar_count = (self.bar2 - self.bar1).abs();

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_font("12px sans-serif");

        let label = if self.show_bars {
            format!("{:.0} bars", bar_count)
        } else {
            format!("{:.0}", bar_count)
        };

        ctx.fill_text(&label, crisp(min_x + w / 2.0, dpr), crisp(y - 10.0, dpr));
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "date_range",
        display_name: "Date Range",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b1, p) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, _) = points.get(1).copied().unwrap_or((b1 + 20.0, p));
            Box::new(DateRange::new(b1, b2, p, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
