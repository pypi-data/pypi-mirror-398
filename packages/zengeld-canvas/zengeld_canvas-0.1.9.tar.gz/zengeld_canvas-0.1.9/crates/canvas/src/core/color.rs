//! Platform-independent color utilities
//!
//! Provides CSS color parsing that returns raw RGBA tuples,
//! allowing platform-specific code to convert to their native color types.

/// Parse CSS color string to RGBA tuple
///
/// Supports:
/// - Hex formats: `#RGB`, `#RRGGBB`, `#RRGGBBAA`
/// - RGB function: `rgb(r, g, b)`
/// - RGBA function: `rgba(r, g, b, a)`
/// - Keyword: `transparent`
///
/// Returns (r, g, b, a) where each component is 0-255.
/// Returns (255, 255, 255, 255) (white) for unrecognized formats.
///
/// # Examples
///
/// ```
/// use zengeld_canvas::parse_css_color;
///
/// assert_eq!(parse_css_color("#FF0000"), (255, 0, 0, 255));
/// assert_eq!(parse_css_color("#00FF0080"), (0, 255, 0, 128));
/// assert_eq!(parse_css_color("rgb(100, 150, 200)"), (100, 150, 200, 255));
/// assert_eq!(parse_css_color("rgba(100, 150, 200, 0.5)"), (100, 150, 200, 127));
/// assert_eq!(parse_css_color("transparent"), (0, 0, 0, 0));
/// ```
pub fn parse_css_color(color: &str) -> (u8, u8, u8, u8) {
    // Handle "transparent" keyword
    if color == "transparent" {
        return (0, 0, 0, 0);
    }

    if let Some(hex) = color.strip_prefix('#') {
        match hex.len() {
            // #RGB -> #RRGGBB
            3 => {
                let r = u8::from_str_radix(&hex[0..1], 16).unwrap_or(15);
                let g = u8::from_str_radix(&hex[1..2], 16).unwrap_or(15);
                let b = u8::from_str_radix(&hex[2..3], 16).unwrap_or(15);
                // Expand: F -> FF (multiply by 17)
                return (r * 17, g * 17, b * 17, 255);
            }
            // #RRGGBB
            6 => {
                let r = u8::from_str_radix(&hex[0..2], 16).unwrap_or(255);
                let g = u8::from_str_radix(&hex[2..4], 16).unwrap_or(255);
                let b = u8::from_str_radix(&hex[4..6], 16).unwrap_or(255);
                return (r, g, b, 255);
            }
            // #RRGGBBAA
            8 => {
                let r = u8::from_str_radix(&hex[0..2], 16).unwrap_or(255);
                let g = u8::from_str_radix(&hex[2..4], 16).unwrap_or(255);
                let b = u8::from_str_radix(&hex[4..6], 16).unwrap_or(255);
                let a = u8::from_str_radix(&hex[6..8], 16).unwrap_or(255);
                return (r, g, b, a);
            }
            _ => {}
        }
    } else if color.starts_with("rgba(") && color.ends_with(')') {
        let inner = &color[5..color.len() - 1];
        let parts: Vec<&str> = inner.split(',').map(|s| s.trim()).collect();
        if parts.len() == 4 {
            let r = parts[0].parse::<u8>().unwrap_or(255);
            let g = parts[1].parse::<u8>().unwrap_or(255);
            let b = parts[2].parse::<u8>().unwrap_or(255);
            let a = (parts[3].parse::<f32>().unwrap_or(1.0) * 255.0) as u8;
            return (r, g, b, a);
        }
    } else if color.starts_with("rgb(") && color.ends_with(')') {
        let inner = &color[4..color.len() - 1];
        let parts: Vec<&str> = inner.split(',').map(|s| s.trim()).collect();
        if parts.len() == 3 {
            let r = parts[0].parse::<u8>().unwrap_or(255);
            let g = parts[1].parse::<u8>().unwrap_or(255);
            let b = parts[2].parse::<u8>().unwrap_or(255);
            return (r, g, b, 255);
        }
    }

    // Default: white
    (255, 255, 255, 255)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hex_6() {
        assert_eq!(parse_css_color("#FF0000"), (255, 0, 0, 255));
        assert_eq!(parse_css_color("#00FF00"), (0, 255, 0, 255));
        assert_eq!(parse_css_color("#0000FF"), (0, 0, 255, 255));
        assert_eq!(parse_css_color("#FFFFFF"), (255, 255, 255, 255));
        assert_eq!(parse_css_color("#000000"), (0, 0, 0, 255));
    }

    #[test]
    fn test_hex_8() {
        assert_eq!(parse_css_color("#FF000080"), (255, 0, 0, 128));
        assert_eq!(parse_css_color("#00FF00FF"), (0, 255, 0, 255));
        assert_eq!(parse_css_color("#0000FF00"), (0, 0, 255, 0));
    }

    #[test]
    fn test_hex_3() {
        assert_eq!(parse_css_color("#F00"), (255, 0, 0, 255));
        assert_eq!(parse_css_color("#0F0"), (0, 255, 0, 255));
        assert_eq!(parse_css_color("#00F"), (0, 0, 255, 255));
        assert_eq!(parse_css_color("#FFF"), (255, 255, 255, 255));
        assert_eq!(parse_css_color("#000"), (0, 0, 0, 255));
    }

    #[test]
    fn test_rgb() {
        assert_eq!(parse_css_color("rgb(255, 0, 0)"), (255, 0, 0, 255));
        assert_eq!(parse_css_color("rgb(100, 150, 200)"), (100, 150, 200, 255));
        assert_eq!(parse_css_color("rgb(0,0,0)"), (0, 0, 0, 255));
    }

    #[test]
    fn test_rgba() {
        assert_eq!(parse_css_color("rgba(255, 0, 0, 1.0)"), (255, 0, 0, 255));
        assert_eq!(parse_css_color("rgba(255, 0, 0, 0.5)"), (255, 0, 0, 127));
        assert_eq!(
            parse_css_color("rgba(100, 150, 200, 0)"),
            (100, 150, 200, 0)
        );
    }

    #[test]
    fn test_transparent() {
        assert_eq!(parse_css_color("transparent"), (0, 0, 0, 0));
    }

    #[test]
    fn test_invalid_returns_white() {
        assert_eq!(parse_css_color("invalid"), (255, 255, 255, 255));
        assert_eq!(parse_css_color(""), (255, 255, 255, 255));
        assert_eq!(parse_css_color("#GGG"), (255, 255, 255, 255));
    }

    #[test]
    fn test_lowercase_hex() {
        assert_eq!(parse_css_color("#ff0000"), (255, 0, 0, 255));
        assert_eq!(parse_css_color("#aabbcc"), (170, 187, 204, 255));
    }
}
