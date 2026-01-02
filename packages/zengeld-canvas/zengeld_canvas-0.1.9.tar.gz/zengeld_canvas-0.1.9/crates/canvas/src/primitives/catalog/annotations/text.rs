//! Text primitive - simple text annotation
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Text {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy fields for backwards compatibility - will migrate to data.text
    #[serde(default)]
    pub text: String,
    #[serde(default = "default_font_size")]
    pub font_size: f64,
    #[serde(default)]
    pub bold: bool,
    #[serde(default)]
    pub italic: bool,
}
fn default_font_size() -> f64 {
    14.0
}

impl Text {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "text".to_string(),
            display_name: "Text".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Text"));

        Self {
            data,
            bar,
            price,
            text: String::new(), // Legacy, use data.text instead
            font_size: 14.0,
            bold: false,
            italic: false,
        }
    }
}

impl Primitive for Text {
    fn type_id(&self) -> &'static str {
        "text"
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
    fn render(&self, _ctx: &mut dyn RenderContext, _is_selected: bool) {
        // Text rendering is centralized via text_anchor()
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        self.data.text.as_ref()?;
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        Some(TextAnchor::new(x, y, &self.data.color.stroke))
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
        type_id: "text",
        display_name: "Text",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Text::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
