//! Signpost primitive - directional sign marker
//!
//! Uses centralized PrimitiveText system for text configuration.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, PrimitiveText,
    RenderContext, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Signpost {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    // Legacy field for backwards compatibility
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub direction: SignpostDirection,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Default)]
pub enum SignpostDirection {
    #[default]
    Right,
    Left,
    Up,
    Down,
}

impl Signpost {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        let mut data = PrimitiveData {
            type_id: "signpost".to_string(),
            display_name: "Signpost".to_string(),
            color: PrimitiveColor::new(color),
            width: 1.0,
            ..Default::default()
        };
        // Initialize centralized text system
        data.text = Some(PrimitiveText::new("Signpost"));

        Self {
            data,
            bar,
            price,
            text: String::new(),
            direction: SignpostDirection::Right,
        }
    }
}

impl Primitive for Signpost {
    fn type_id(&self) -> &'static str {
        "signpost"
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
        let size = 30.0;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Draw signpost shape based on direction
        ctx.begin_path();
        match self.direction {
            SignpostDirection::Right => {
                ctx.move_to(crisp(x, dpr), crisp(y - 10.0, dpr));
                ctx.line_to(crisp(x + size, dpr), crisp(y - 10.0, dpr));
                ctx.line_to(crisp(x + size + 10.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x + size, dpr), crisp(y + 10.0, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + 10.0, dpr));
            }
            SignpostDirection::Left => {
                ctx.move_to(crisp(x, dpr), crisp(y - 10.0, dpr));
                ctx.line_to(crisp(x - size, dpr), crisp(y - 10.0, dpr));
                ctx.line_to(crisp(x - size - 10.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x - size, dpr), crisp(y + 10.0, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + 10.0, dpr));
            }
            SignpostDirection::Up => {
                ctx.move_to(crisp(x - 10.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x - 10.0, dpr), crisp(y - size, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y - size - 10.0, dpr));
                ctx.line_to(crisp(x + 10.0, dpr), crisp(y - size, dpr));
                ctx.line_to(crisp(x + 10.0, dpr), crisp(y, dpr));
            }
            SignpostDirection::Down => {
                ctx.move_to(crisp(x - 10.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x - 10.0, dpr), crisp(y + size, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + size + 10.0, dpr));
                ctx.line_to(crisp(x + 10.0, dpr), crisp(y + size, dpr));
                ctx.line_to(crisp(x + 10.0, dpr), crisp(y, dpr));
            }
        }
        ctx.close_path();
        ctx.fill();
        ctx.stroke();

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        self.data.text.as_ref()?;
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        // Text position depends on direction
        let (tx, ty) = match self.direction {
            SignpostDirection::Right => (x + 45.0, y),
            SignpostDirection::Left => (x - 45.0, y),
            SignpostDirection::Up => (x, y - 45.0),
            SignpostDirection::Down => (x, y + 45.0),
        };
        Some(TextAnchor::new(tx, ty, &self.data.color.stroke))
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
        type_id: "signpost",
        display_name: "Signpost",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Signpost::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
