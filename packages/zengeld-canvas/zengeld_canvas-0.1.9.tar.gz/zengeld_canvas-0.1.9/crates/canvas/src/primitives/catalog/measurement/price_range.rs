//! Price Range - vertical price measurement

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceRange {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price1: f64,
    pub price2: f64,
    #[serde(default = "default_true")]
    pub show_percentage: bool,
    #[serde(default = "default_true")]
    pub show_pips: bool,
}
fn default_true() -> bool {
    true
}

impl PriceRange {
    pub fn new(bar: f64, price1: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "price_range".to_string(),
                display_name: "Price Range".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price1,
            price2,
            show_percentage: true,
            show_pips: true,
        }
    }
}

impl Primitive for PriceRange {
    fn type_id(&self) -> &'static str {
        "price_range"
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
        vec![(self.bar, self.price1), (self.bar, self.price2)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar = b;
            self.price1 = p;
        }
        if let Some(&(_, p)) = pts.get(1) {
            self.price2 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.price1 += pd;
        self.price2 += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y1 = ctx.price_to_y(self.price1);
        let y2 = ctx.price_to_y(self.price2);

        let min_y = y1.min(y2);
        let max_y = y1.max(y2);
        let h = max_y - min_y;

        // Draw filled area between the two horizontal lines
        ctx.set_fill_color(&format!("{}40", &self.data.color.stroke));
        ctx.fill_rect(0.0, crisp(min_y, dpr), ctx.width() as f64, h);

        // Draw the two horizontal lines
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_line_style(LineStyle::Solid);
        ctx.set_stroke_width(self.data.width);

        ctx.begin_path();
        ctx.move_to(0.0, crisp(y1, dpr));
        ctx.line_to(ctx.width() as f64, crisp(y1, dpr));
        ctx.stroke();

        ctx.begin_path();
        ctx.move_to(0.0, crisp(y2, dpr));
        ctx.line_to(ctx.width() as f64, crisp(y2, dpr));
        ctx.stroke();

        // Draw price difference label
        let price_diff = (self.price2 - self.price1).abs();
        let percentage = if self.price1 != 0.0 {
            (price_diff / self.price1.abs()) * 100.0
        } else {
            0.0
        };

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_font("12px sans-serif");

        let label = if self.show_percentage && self.show_pips {
            format!("{:.2} ({:.2}%)", price_diff, percentage)
        } else if self.show_percentage {
            format!("{:.2}%", percentage)
        } else {
            // show_pips only, or neither (default to pips)
            format!("{:.2}", price_diff)
        };

        ctx.fill_text(&label, crisp(x + 10.0, dpr), crisp(min_y + h / 2.0, dpr));
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
        type_id: "price_range",
        display_name: "Price Range",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b, p1) = points.first().copied().unwrap_or((0.0, 100.0));
            let (_, p2) = points.get(1).copied().unwrap_or((b, p1 + 10.0));
            Box::new(PriceRange::new(b, p1, p2, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
