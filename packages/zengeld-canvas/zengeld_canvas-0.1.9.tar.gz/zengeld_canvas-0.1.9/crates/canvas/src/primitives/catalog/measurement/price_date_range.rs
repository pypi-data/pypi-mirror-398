//! Price Date Range - combined price and time measurement

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceDateRange {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1: f64,
    pub bar2: f64,
    pub price2: f64,
    #[serde(default = "default_true")]
    pub show_percentage: bool,
    #[serde(default = "default_true")]
    pub show_bars: bool,
    #[serde(default = "default_true")]
    pub show_pips: bool,
}
fn default_true() -> bool {
    true
}

impl PriceDateRange {
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "price_date_range".to_string(),
                display_name: "Price/Date Range".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            show_percentage: true,
            show_bars: true,
            show_pips: true,
        }
    }
}

impl Primitive for PriceDateRange {
    fn type_id(&self) -> &'static str {
        "price_date_range"
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
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = pts.get(1) {
            self.bar2 = b;
            self.price2 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price1 += pd;
        self.price2 += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let min_x = x1.min(x2);
        let min_y = y1.min(y2);
        let w = (x2 - x1).abs();
        let h = (y2 - y1).abs();

        // Draw filled rectangle
        ctx.set_fill_color(&format!("{}40", &self.data.color.stroke));
        ctx.fill_rect(crisp(min_x, dpr), crisp(min_y, dpr), w, h);

        // Draw rectangle border
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_line_style(LineStyle::Solid);
        ctx.set_stroke_width(self.data.width);
        ctx.stroke_rect(crisp(min_x, dpr), crisp(min_y, dpr), w, h);

        // Calculate metrics
        let price_diff = (self.price2 - self.price1).abs();
        let percentage = if self.price1 != 0.0 {
            (price_diff / self.price1.abs()) * 100.0
        } else {
            0.0
        };
        let bar_count = (self.bar2 - self.bar1).abs();

        // Draw labels
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_font("12px sans-serif");

        let center_x = crisp(min_x + w / 2.0, dpr);
        let center_y = crisp(min_y + h / 2.0, dpr);

        // Price label
        let mut y_offset = center_y - 15.0;
        if self.show_pips {
            let price_label = if self.show_percentage {
                format!("{:.2} ({:.2}%)", price_diff, percentage)
            } else {
                format!("{:.2}", price_diff)
            };
            ctx.fill_text(&price_label, center_x, y_offset);
            y_offset += 15.0;
        }

        // Bar count label
        if self.show_bars {
            let bar_label = format!("{:.0} bars", bar_count);
            ctx.fill_text(&bar_label, center_x, y_offset);
        }
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
        type_id: "price_date_range",
        display_name: "Price/Date Range",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 20.0, p1 + 10.0));
            Box::new(PriceDateRange::new(b1, p1, b2, p2, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
