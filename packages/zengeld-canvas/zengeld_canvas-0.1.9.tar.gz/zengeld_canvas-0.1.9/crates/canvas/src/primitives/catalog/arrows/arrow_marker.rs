//! Arrow Marker primitive - a simple arrow pointing in a specified direction

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Default)]
pub enum ArrowDirection {
    #[default]
    Up,
    Down,
    Left,
    Right,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ArrowMarker {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub direction: ArrowDirection,
    pub size: f64,
}

impl ArrowMarker {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "arrow_marker".to_string(),
                display_name: "Arrow Marker".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            direction: ArrowDirection::Up,
            size: 20.0,
        }
    }
}

impl Primitive for ArrowMarker {
    fn type_id(&self) -> &'static str {
        "arrow_marker"
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
        if let Some(&(bar, price)) = points.first() {
            self.bar = bar;
            self.price = price;
        }
    }
    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar += bar_delta;
        self.price += price_delta;
    }
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let s = self.size;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        ctx.begin_path();
        match self.direction {
            ArrowDirection::Up => {
                ctx.move_to(crisp(x, dpr), crisp(y - s / 2.0, dpr));
                ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y + s / 2.0, dpr));
            }
            ArrowDirection::Down => {
                ctx.move_to(crisp(x, dpr), crisp(y + s / 2.0, dpr));
                ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y - s / 2.0, dpr));
                ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y - s / 2.0, dpr));
            }
            ArrowDirection::Left => {
                ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y - s / 3.0, dpr));
                ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y + s / 3.0, dpr));
            }
            ArrowDirection::Right => {
                ctx.move_to(crisp(x + s / 2.0, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x - s / 2.0, dpr), crisp(y - s / 3.0, dpr));
                ctx.line_to(crisp(x - s / 2.0, dpr), crisp(y + s / 3.0, dpr));
            }
        }
        ctx.close_path();
        ctx.fill();
        ctx.stroke();

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);

        let offset = 20.0 + text.font_size / 2.0;
        let y_offset = match text.v_align {
            TextAlign::Start => -offset, // above
            TextAlign::Center => 0.0,
            TextAlign::End => offset, // below
        };

        Some(TextAnchor::new(x, y + y_offset, &self.data.color.stroke))
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
        type_id: "arrow_marker",
        display_name: "Arrow Marker",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (bar, price) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(ArrowMarker::new(bar, price, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
