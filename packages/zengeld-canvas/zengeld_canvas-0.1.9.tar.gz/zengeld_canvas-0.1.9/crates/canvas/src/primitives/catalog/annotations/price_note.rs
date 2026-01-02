//! Price Note primitive - note attached to a price level
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceNote {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default = "default_true")]
    pub show_price: bool,
}
fn default_true() -> bool {
    true
}

impl PriceNote {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "price_note".to_string(),
            display_name: "Price Note".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Price Note"));

        Self {
            data,
            bar,
            price,
            text: String::new(),
            show_price: true,
        }
    }

    fn get_text(&self) -> &str {
        if let Some(ref text) = self.data.text {
            &text.content
        } else if !self.text.is_empty() {
            &self.text
        } else {
            "Price Note"
        }
    }

    fn get_font_size(&self) -> f64 {
        if let Some(ref text) = self.data.text {
            text.font_size
        } else {
            12.0
        }
    }
}

impl Primitive for PriceNote {
    fn type_id(&self) -> &'static str {
        "price_note"
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
        vec![(self.bar, self.price)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar = b;
            self.price = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.price += pd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);

        // Draw horizontal line from anchor point
        let chart_width = ctx.chart_width();
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        ctx.set_line_dash(&[4.0, 4.0]);
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp(y, dpr));
        ctx.line_to(crisp(chart_width, dpr), crisp(y, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);

        // Draw price label background - use centralized text system
        let text_content = self.get_text();
        let font_size = self.get_font_size();
        let label_text = if self.show_price {
            format!("{:.2} - {}", self.price, text_content)
        } else {
            text_content.to_string()
        };
        let char_width = font_size * 0.6;
        let text_width = label_text.len() as f64 * char_width;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.fill_rect(
            crisp(chart_width - text_width - 8.0, dpr),
            crisp(y - font_size * 0.7, dpr),
            text_width + 8.0,
            font_size * 1.4,
        );

        ctx.set_fill_color("#000000");
        ctx.set_font(&format!("{}px sans-serif", font_size as i32));
        ctx.fill_text(
            &label_text,
            chart_width - text_width - 4.0,
            y + font_size * 0.3,
        );

        let _ = is_selected;
    }

    fn text_anchor(&self, _ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Price Note renders its own text inline, so no additional text anchor needed
        None
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
        type_id: "price_note",
        display_name: "Price Note",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(PriceNote::new(b, p, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
