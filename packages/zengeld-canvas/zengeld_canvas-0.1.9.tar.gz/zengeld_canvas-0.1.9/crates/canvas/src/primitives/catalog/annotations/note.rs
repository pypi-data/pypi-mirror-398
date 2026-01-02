//! Note primitive - expandable note with content
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Note {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy fields for backwards compatibility
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub content: String,
    #[serde(default)]
    pub expanded: bool,
}

impl Note {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "note".to_string(),
            display_name: "Note".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Note"));

        Self {
            data,
            bar,
            price,
            title: String::new(),
            content: String::new(),
            expanded: false,
        }
    }
}

impl Primitive for Note {
    fn type_id(&self) -> &'static str {
        "note"
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
        let size = 24.0;

        // Draw note icon (document shape)
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        ctx.begin_path();
        ctx.move_to(crisp(x - size / 3.0, dpr), crisp(y - size / 2.0, dpr));
        ctx.line_to(crisp(x + size / 4.0, dpr), crisp(y - size / 2.0, dpr));
        ctx.line_to(crisp(x + size / 3.0, dpr), crisp(y - size / 3.0, dpr));
        ctx.line_to(crisp(x + size / 3.0, dpr), crisp(y + size / 2.0, dpr));
        ctx.line_to(crisp(x - size / 3.0, dpr), crisp(y + size / 2.0, dpr));
        ctx.close_path();
        ctx.fill();
        ctx.stroke();

        // Fold corner
        ctx.begin_path();
        ctx.move_to(crisp(x + size / 4.0, dpr), crisp(y - size / 2.0, dpr));
        ctx.line_to(crisp(x + size / 4.0, dpr), crisp(y - size / 3.0, dpr));
        ctx.line_to(crisp(x + size / 3.0, dpr), crisp(y - size / 3.0, dpr));
        ctx.stroke();

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Note renders text when expanded - show text below the icon
        if self.data.text.is_none() || !self.expanded {
            return None;
        }
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        Some(TextAnchor::new(x, y + 20.0, &self.data.color.stroke))
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
        type_id: "note",
        display_name: "Note",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Note::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
