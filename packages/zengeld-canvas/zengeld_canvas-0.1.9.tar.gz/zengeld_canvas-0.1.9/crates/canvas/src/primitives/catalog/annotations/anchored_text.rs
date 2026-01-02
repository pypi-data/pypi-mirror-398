//! Anchored Text primitive - text anchored to price/time with optional background
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AnchoredText {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy fields for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default = "default_font_size")]
    pub font_size: f64,
    #[serde(default = "default_background")]
    pub background: bool,
}
fn default_font_size() -> f64 {
    14.0
}
fn default_background() -> bool {
    true
}

impl AnchoredText {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "anchored_text".to_string(),
            display_name: "Anchored Text".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Anchored Text"));

        Self {
            data,
            bar,
            price,
            text: String::new(),
            font_size: 14.0,
            background: true,
        }
    }
}

impl Primitive for AnchoredText {
    fn type_id(&self) -> &'static str {
        "anchored_text"
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
        if self.background {
            let bg_color = format!("{}40", &self.data.color.stroke);
            Some(TextAnchor::with_background(
                x,
                y,
                &self.data.color.stroke,
                &bg_color,
                4.0,
            ))
        } else {
            Some(TextAnchor::new(x, y, &self.data.color.stroke))
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
        type_id: "anchored_text",
        display_name: "Anchored Text",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(AnchoredText::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
