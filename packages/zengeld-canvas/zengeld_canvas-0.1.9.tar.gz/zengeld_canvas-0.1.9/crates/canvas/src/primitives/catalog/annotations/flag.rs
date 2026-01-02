//! Flag primitive - flag marker with label
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Flag {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default = "default_flag_color")]
    pub flag_color: String,
}
fn default_flag_color() -> String {
    "#F44336".to_string()
}

impl Flag {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "flag".to_string(),
            display_name: "Flag".to_string(),
            color: PrimitiveColor::new(color),
            width: 2.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Flag"));

        Self {
            data,
            bar,
            price,
            text: String::new(),
            flag_color: "#F44336".to_string(),
        }
    }

    fn get_text(&self) -> &str {
        if let Some(ref text) = self.data.text {
            &text.content
        } else if !self.text.is_empty() {
            &self.text
        } else {
            ""
        }
    }
}

impl Primitive for Flag {
    fn type_id(&self) -> &'static str {
        "flag"
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

        // Draw pole
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp(y, dpr));
        ctx.line_to(crisp(x, dpr), crisp(y - 30.0, dpr));
        ctx.stroke();

        // Draw flag
        ctx.set_fill_color(&self.flag_color);
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp(y - 30.0, dpr));
        ctx.line_to(crisp(x + 25.0, dpr), crisp(y - 22.0, dpr));
        ctx.line_to(crisp(x, dpr), crisp(y - 14.0, dpr));
        ctx.close_path();
        ctx.fill();

        // Text rendering is now centralized via text_anchor()

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text_content = self.get_text();
        if text_content.is_empty() || self.data.text.is_none() {
            return None;
        }
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        Some(TextAnchor::new(x - 10.0, y + 12.0, &self.data.color.stroke))
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
        type_id: "flag",
        display_name: "Flag",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Flag::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
