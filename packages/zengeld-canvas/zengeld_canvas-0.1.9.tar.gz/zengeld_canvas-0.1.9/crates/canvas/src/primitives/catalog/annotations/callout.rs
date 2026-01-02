//! Callout primitive - speech bubble style annotation
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Callout {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1: f64, // Anchor point
    pub bar2: f64,
    pub price2: f64, // Bubble position
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default = "default_width")]
    pub bubble_width: f64,
    #[serde(default = "default_height")]
    pub bubble_height: f64,
}
fn default_width() -> f64 {
    100.0
}
fn default_height() -> f64 {
    50.0
}

impl Callout {
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "callout".to_string(),
            display_name: "Callout".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Callout"));

        Self {
            data,
            bar1,
            price1,
            bar2,
            price2,
            text: String::new(),
            bubble_width: 100.0,
            bubble_height: 50.0,
        }
    }
}

impl Primitive for Callout {
    fn type_id(&self) -> &'static str {
        "callout"
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
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = points.get(1) {
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
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Draw connector line from anchor to bubble
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Draw bubble background
        let half_w = self.bubble_width / 2.0;
        let half_h = self.bubble_height / 2.0;
        ctx.set_fill_color(&format!("{}CC", &self.data.color.stroke));
        ctx.fill_rect(
            crisp(x2 - half_w, dpr),
            crisp(y2 - half_h, dpr),
            self.bubble_width,
            self.bubble_height,
        );
        ctx.stroke_rect(
            crisp(x2 - half_w, dpr),
            crisp(y2 - half_h, dpr),
            self.bubble_width,
            self.bubble_height,
        );

        // Text rendering is now centralized via text_anchor()

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        self.data.text.as_ref()?;
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let half_w = self.bubble_width / 2.0;
        Some(TextAnchor::new(x2 - half_w + 5.0, y2, "#FFFFFF"))
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
        type_id: "callout",
        display_name: "Callout",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 0.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 5.0, p1 + 10.0));
            Box::new(Callout::new(b1, p1, b2, p2, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
