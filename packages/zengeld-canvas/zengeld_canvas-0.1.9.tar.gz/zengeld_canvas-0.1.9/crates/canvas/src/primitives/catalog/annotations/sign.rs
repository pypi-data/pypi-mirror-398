//! Sign primitive - icon-based marker

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Default)]
pub enum SignType {
    #[default]
    Circle,
    Square,
    Diamond,
    Triangle,
    Star,
    Cross,
    Check,
    X,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Sign {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub sign_type: SignType,
    #[serde(default = "default_size")]
    pub size: f64,
}
fn default_size() -> f64 {
    20.0
}

impl Sign {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "sign".to_string(),
                display_name: "Sign".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            sign_type: SignType::Circle,
            size: 20.0,
        }
    }
}

impl Primitive for Sign {
    fn type_id(&self) -> &'static str {
        "sign"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Signal
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
        let s = self.size / 2.0;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        ctx.begin_path();
        match self.sign_type {
            SignType::Circle => {
                ctx.arc(x, y, s, 0.0, std::f64::consts::TAU);
                ctx.fill();
            }
            SignType::Square => {
                ctx.fill_rect(crisp(x - s, dpr), crisp(y - s, dpr), self.size, self.size);
            }
            SignType::Diamond => {
                ctx.move_to(crisp(x, dpr), crisp(y - s, dpr));
                ctx.line_to(crisp(x + s, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + s, dpr));
                ctx.line_to(crisp(x - s, dpr), crisp(y, dpr));
                ctx.close_path();
                ctx.fill();
            }
            SignType::Triangle => {
                ctx.move_to(crisp(x, dpr), crisp(y - s, dpr));
                ctx.line_to(crisp(x + s, dpr), crisp(y + s, dpr));
                ctx.line_to(crisp(x - s, dpr), crisp(y + s, dpr));
                ctx.close_path();
                ctx.fill();
            }
            SignType::Star => {
                for i in 0..5 {
                    let angle = (i as f64 * 72.0 - 90.0) * std::f64::consts::PI / 180.0;
                    let px = x + s * angle.cos();
                    let py = y + s * angle.sin();
                    if i == 0 {
                        ctx.move_to(crisp(px, dpr), crisp(py, dpr));
                    } else {
                        ctx.line_to(crisp(px, dpr), crisp(py, dpr));
                    }
                }
                ctx.close_path();
                ctx.fill();
            }
            SignType::Cross => {
                ctx.move_to(crisp(x - s, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x + s, dpr), crisp(y, dpr));
                ctx.stroke();
                ctx.begin_path();
                ctx.move_to(crisp(x, dpr), crisp(y - s, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + s, dpr));
                ctx.stroke();
            }
            SignType::Check => {
                ctx.move_to(crisp(x - s, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.line_to(crisp(x + s, dpr), crisp(y - s / 2.0, dpr));
                ctx.stroke();
            }
            SignType::X => {
                ctx.move_to(crisp(x - s, dpr), crisp(y - s, dpr));
                ctx.line_to(crisp(x + s, dpr), crisp(y + s, dpr));
                ctx.stroke();
                ctx.begin_path();
                ctx.move_to(crisp(x + s, dpr), crisp(y - s, dpr));
                ctx.line_to(crisp(x - s, dpr), crisp(y + s, dpr));
                ctx.stroke();
            }
        }

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);

        let offset = 15.0 + text.font_size / 2.0;
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
        type_id: "sign",
        display_name: "Sign",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Sign::new(b, p, color))
        },
        supports_text: false,
        has_levels: false,
        has_points_config: false,
    }
}
