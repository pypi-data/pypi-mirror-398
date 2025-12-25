#[derive(Debug, Clone)]
pub enum Severity {
    Warning,
    Error,
}

// TODO: Expand RuleType to include more types of DRC rules as needed
#[derive(Debug, Clone)]
pub enum RuleType {
    MinSpacing(u32),
    MinWidth(u32),
}

#[derive(Clone)]
#[expect(dead_code)]
pub struct DRCRule {
    /// Minimum spacing required between shapes on this layer and shapes on the other layer
    rule: RuleType,
    description: String, // A brief description of the rule which can be used for reporting to user
    severity: Severity,
}
