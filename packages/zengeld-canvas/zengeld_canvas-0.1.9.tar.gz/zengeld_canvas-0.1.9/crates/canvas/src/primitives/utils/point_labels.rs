//! Point label generation for drawing primitives
//!
//! This module provides logic for generating point labels for multi-point
//! drawing primitives like harmonic patterns, Elliott waves, and pitchforks.

use crate::primitives::core::config::Language;

/// Get point labels for multi-point primitives (with language support)
///
/// Returns appropriate labels based on the primitive type:
/// - XABCD patterns: ["X", "A", "B", "C", "D"]
/// - ABCD patterns: ["A", "B", "C", "D"]
/// - Head and shoulders: ["L Shoulder", "Head", "R Shoulder", "Low 1", "Low 2"]
/// - Three drives: ["1", "2", "3", "4", "5", "6"]
/// - Triangle patterns: ["A", "B", "C"]
/// - Elliott waves: ["1", "2", "3", ...] (numeric)
/// - Default: ["Point", "Point", ...] (generic point label)
///
/// # Arguments
///
/// * `primitive_type` - The type identifier of the primitive (e.g., "xabcd_pattern", "elliott_impulse")
/// * `count` - The number of point labels to generate
/// * `lang` - The language for localized labels
///
/// # Returns
///
/// A vector of label strings, with length equal to `count`
///
/// # Examples
///
/// ```
/// use zengeld_canvas::primitives::utils::{get_point_labels, Language};
///
/// // XABCD pattern
/// let labels = get_point_labels("xabcd_pattern", 5, Language::English);
/// assert_eq!(labels, vec!["X", "A", "B", "C", "D"]);
///
/// // Elliott wave
/// let labels = get_point_labels("elliott_impulse", 3, Language::English);
/// assert_eq!(labels, vec!["1", "2", "3"]);
///
/// // Generic primitive
/// let labels = get_point_labels("unknown_type", 2, Language::English);
/// assert_eq!(labels, vec!["Point", "Point"]);
/// ```
pub fn get_point_labels(primitive_type: &str, count: usize, lang: Language) -> Vec<String> {
    match primitive_type {
        // Harmonic patterns use XABCD naming
        "xabcd_pattern" | "cypher_pattern" => vec!["X", "A", "B", "C", "D"]
            .into_iter()
            .take(count)
            .map(String::from)
            .collect(),
        // ABCD patterns
        "abcd_pattern" => vec!["A", "B", "C", "D"]
            .into_iter()
            .take(count)
            .map(String::from)
            .collect(),
        // Head and shoulders
        "head_shoulders" => {
            let labels = match lang {
                Language::Russian => vec!["L плечо", "Голова", "R плечо", "Низ 1", "Низ 2"],
                Language::English => vec!["L Shoulder", "Head", "R Shoulder", "Low 1", "Low 2"],
            };
            labels.into_iter().take(count).map(String::from).collect()
        }
        // Three drives
        "three_drives" => vec!["1", "2", "3", "4", "5", "6"]
            .into_iter()
            .take(count)
            .map(String::from)
            .collect(),
        // Triangle pattern
        "triangle_pattern" => vec!["A", "B", "C"]
            .into_iter()
            .take(count)
            .map(String::from)
            .collect(),
        // Elliott wave patterns use wave numbers
        s if s.starts_with("elliott") => (1..=count).map(|i| i.to_string()).collect(),
        // Default: generic point labels
        _ => {
            let point = match lang {
                Language::Russian => "Точка",
                Language::English => "Point",
            };
            (1..=count).map(|_| point.to_string()).collect()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xabcd_pattern() {
        let labels = get_point_labels("xabcd_pattern", 5, Language::English);
        assert_eq!(labels, vec!["X", "A", "B", "C", "D"]);
    }

    #[test]
    fn test_xabcd_pattern_partial() {
        let labels = get_point_labels("xabcd_pattern", 3, Language::English);
        assert_eq!(labels, vec!["X", "A", "B"]);
    }

    #[test]
    fn test_cypher_pattern() {
        let labels = get_point_labels("cypher_pattern", 5, Language::English);
        assert_eq!(labels, vec!["X", "A", "B", "C", "D"]);
    }

    #[test]
    fn test_abcd_pattern() {
        let labels = get_point_labels("abcd_pattern", 4, Language::English);
        assert_eq!(labels, vec!["A", "B", "C", "D"]);
    }

    #[test]
    fn test_head_shoulders_english() {
        let labels = get_point_labels("head_shoulders", 5, Language::English);
        assert_eq!(
            labels,
            vec!["L Shoulder", "Head", "R Shoulder", "Low 1", "Low 2"]
        );
    }

    #[test]
    fn test_head_shoulders_russian() {
        let labels = get_point_labels("head_shoulders", 5, Language::Russian);
        assert_eq!(
            labels,
            vec!["L плечо", "Голова", "R плечо", "Низ 1", "Низ 2"]
        );
    }

    #[test]
    fn test_three_drives() {
        let labels = get_point_labels("three_drives", 6, Language::English);
        assert_eq!(labels, vec!["1", "2", "3", "4", "5", "6"]);
    }

    #[test]
    fn test_triangle_pattern() {
        let labels = get_point_labels("triangle_pattern", 3, Language::English);
        assert_eq!(labels, vec!["A", "B", "C"]);
    }

    #[test]
    fn test_elliott_impulse() {
        let labels = get_point_labels("elliott_impulse", 5, Language::English);
        assert_eq!(labels, vec!["1", "2", "3", "4", "5"]);
    }

    #[test]
    fn test_elliott_correction() {
        let labels = get_point_labels("elliott_correction", 3, Language::English);
        assert_eq!(labels, vec!["1", "2", "3"]);
    }

    #[test]
    fn test_default_labels_english() {
        let labels = get_point_labels("unknown_type", 3, Language::English);
        assert_eq!(labels, vec!["Point", "Point", "Point"]);
    }

    #[test]
    fn test_default_labels_russian() {
        let labels = get_point_labels("unknown_type", 3, Language::Russian);
        assert_eq!(labels, vec!["Точка", "Точка", "Точка"]);
    }

    #[test]
    fn test_zero_count() {
        let labels = get_point_labels("xabcd_pattern", 0, Language::English);
        assert!(labels.is_empty());
    }
}
