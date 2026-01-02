//! Comment primitive - comment marker with popup
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Comment {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub author: String,
    #[serde(default)]
    pub timestamp: i64,
}

impl Comment {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "comment".to_string(),
            display_name: "Comment".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Comment"));

        Self {
            data,
            bar,
            price,
            text: String::new(),
            author: String::new(),
            timestamp: 0,
        }
    }
}

impl Primitive for Comment {
    fn type_id(&self) -> &'static str {
        "comment"
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
        let size = 20.0;

        // Draw speech bubble icon
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Main bubble
        ctx.begin_path();
        ctx.arc(x, y, size / 2.0, 0.0, std::f64::consts::TAU);
        ctx.fill();

        // Tail
        ctx.begin_path();
        ctx.move_to(crisp(x - 3.0, dpr), crisp(y + size / 2.0 - 2.0, dpr));
        ctx.line_to(crisp(x - 8.0, dpr), crisp(y + size / 2.0 + 6.0, dpr));
        ctx.line_to(crisp(x + 2.0, dpr), crisp(y + size / 2.0 - 2.0, dpr));
        ctx.close_path();
        ctx.fill();

        // Draw text indicator (three lines)
        ctx.set_stroke_color("#000000");
        ctx.set_stroke_width(1.0);
        for i in 0..3 {
            let ly = y - 3.0 + (i as f64 * 3.0);
            ctx.begin_path();
            ctx.move_to(crisp(x - 5.0, dpr), crisp(ly, dpr));
            ctx.line_to(crisp(x + 5.0, dpr), crisp(ly, dpr));
            ctx.stroke();
        }

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Comment shows text as tooltip/popup - render below the bubble icon
        self.data.text.as_ref()?;
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
        type_id: "comment",
        display_name: "Comment",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Comment::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
