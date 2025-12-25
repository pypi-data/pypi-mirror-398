/**
 * Smart Labeler Automation Script
 * 
 * Analyzes title and description to automatically suggest labels.
 */

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface Context {
  workItem: {
    id: string;
    title: string;
    description?: string;
    type: string;
    state: string;
    priority?: string;
    labels: string[];
    assignees: string[];
    properties: Record<string, unknown>;
  };
  trigger: {
    type: string;
    timestamp: string;
  };
  config: Record<string, unknown>;
}

type Action =
  | { set: Record<string, unknown> }
  | { add_label: string | string[] }
  | { comment: string };

// =============================================================================
// KEYWORD MAPPINGS
// =============================================================================

const LABEL_KEYWORDS: Record<string, string[]> = {
  // Tech areas
  "frontend": ["ui", "ux", "css", "html", "react", "vue", "angular", "button", "form", "modal", "page", "layout", "style", "design"],
  "backend": ["api", "server", "database", "sql", "endpoint", "rest", "graphql", "query", "migration", "model"],
  "mobile": ["ios", "android", "app", "mobile", "phone", "tablet", "native"],
  "devops": ["deploy", "ci", "cd", "pipeline", "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform"],
  
  // Issue types
  "bug": ["bug", "error", "crash", "broken", "not working", "fails", "issue", "problem", "fix"],
  "feature": ["feature", "add", "new", "implement", "create", "build", "enhance"],
  "documentation": ["docs", "documentation", "readme", "guide", "tutorial", "help"],
  "performance": ["slow", "performance", "optimize", "speed", "fast", "memory", "cpu", "lag"],
  "security": ["security", "vulnerability", "auth", "permission", "access", "password", "token", "xss", "injection"],
  
  // Priority indicators
  "urgent": ["urgent", "asap", "critical", "emergency", "immediately", "blocker", "production down"],
};

// =============================================================================
// AUTOMATION LOGIC
// =============================================================================

export default function run(ctx: Context): Action[] {
  const { workItem } = ctx;
  
  // Skip if already has many labels (probably manually labeled)
  if (workItem.labels.length >= 3) {
    return [];
  }
  
  // Combine title and description for analysis
  const text = `${workItem.title} ${workItem.description || ""}`.toLowerCase();
  
  // Find matching labels
  const suggestedLabels: string[] = [];
  const matchedKeywords: Record<string, string[]> = {};
  
  for (const [label, keywords] of Object.entries(LABEL_KEYWORDS)) {
    // Skip if already has this label
    if (workItem.labels.includes(label)) {
      continue;
    }
    
    const matches = keywords.filter(kw => text.includes(kw.toLowerCase()));
    if (matches.length > 0) {
      suggestedLabels.push(label);
      matchedKeywords[label] = matches;
    }
  }
  
  // Limit to top 3 suggestions
  const labelsToAdd = suggestedLabels.slice(0, 3);
  
  if (labelsToAdd.length === 0) {
    return [];
  }
  
  // Build actions
  const actions: Action[] = [
    { add_label: labelsToAdd }
  ];
  
  // Add explanatory comment
  const explanations = labelsToAdd.map(label => {
    const keywords = matchedKeywords[label];
    return `- **${label}**: matched "${keywords.slice(0, 3).join('", "')}"`;
  });
  
  actions.push({
    comment: `🏷️ **Auto-labeled** based on content analysis:\n\n${explanations.join("\n")}`
  });
  
  // If urgent indicators found, also set priority
  if (labelsToAdd.includes("urgent") && workItem.priority !== "urgent") {
    actions.push({ set: { priority: "urgent" } });
  }
  
  return actions;
}

