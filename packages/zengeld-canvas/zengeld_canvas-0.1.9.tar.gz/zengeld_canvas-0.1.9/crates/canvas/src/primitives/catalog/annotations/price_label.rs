//! Price Label primitive - label showing price value
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceLabel {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub custom_text: Option<String>,
    #[serde(default = "default_true")]
    pub show_line: bool,
}
fn default_true() -> bool {
    true
}

impl PriceLabel {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "price_label".to_string(),
            display_name: "Price Label".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system - empty means show price
        data.text = Some(PrimitiveText::new(""));

        Self {
            data,
            bar,
            price,
            custom_text: None,
            show_line: true,
        }
    }

    fn get_custom_text(&self) -> Option<&str> {
        if let Some(ref text) = self.data.text {
            if !text.content.is_empty() {
                return Some(&text.content);
            }
        }
        self.custom_text.as_deref()
    }

    fn get_font_size(&self) -> f64 {
        if let Some(ref text) = self.data.text {
            text.font_size
        } else {
            12.0
        }
    }
}

impl Primitive for PriceLabel {
    fn type_id(&self) -> &'static str {
        "price_label"
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

        // Use centralized text system
        let default_text = format!("{:.2}", self.price);
        let label_text = self.get_custom_text().unwrap_or(&default_text);
        let font_size = self.get_font_size();
        let char_width = font_size * 0.65;
        let text_width = label_text.len() as f64 * char_width;

        // Draw horizontal dashed line if enabled
        if self.show_line {
            ctx.set_stroke_color(&self.data.color.stroke);
            ctx.set_stroke_width(self.data.width);
            ctx.set_line_dash(&[4.0, 4.0]);
            ctx.begin_path();
            ctx.move_to(crisp(0.0, dpr), crisp(y, dpr));
            ctx.line_to(crisp(x - 5.0, dpr), crisp(y, dpr));
            ctx.stroke();
            ctx.set_line_dash(&[]);
        }

        // Draw label background
        let label_height = font_size * 1.4;
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.fill_rect(
            crisp(x - text_width / 2.0, dpr),
            crisp(y - label_height / 2.0, dpr),
            text_width,
            label_height,
        );

        // Draw text
        ctx.set_fill_color("#000000");
        ctx.set_font(&format!("{}px sans-serif", font_size as i32));
        ctx.fill_text(label_text, x - text_width / 2.0 + 4.0, y + font_size * 0.3);

        let _ = is_selected;
    }

    fn text_anchor(&self, _ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Price Label renders its own text inline, so no additional text anchor needed
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
        type_id: "price_label",
        display_name: "Price Label",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(PriceLabel::new(b, p, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
