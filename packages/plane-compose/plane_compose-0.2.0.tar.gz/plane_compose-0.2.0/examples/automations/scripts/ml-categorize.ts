/**
 * Automation: ml-categorize
 * 
 * Receives context with work item data, returns actions to execute.
 */
export default function run(ctx: Context): Action[] {
  const { workItem } = ctx;
  
  // Your logic here
  if (workItem.labels.includes("critical")) {
    return [
      { set: { priority: "urgent" } },
      { comment: "Auto-escalated due to critical label" }
    ];
  }
  
  return [];
}

// =============================================================================
// TYPE DEFINITIONS (for reference)
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
    properties: Record<string, any>;
  };
  trigger: {
    type: string;
    timestamp: string;
    changes?: Record<string, { from: any; to: any }>;
  };
  config: Record<string, any>;
}

type Action =
  | { set: Record<string, any> }
  | { assign: string | string[] }
  | { unassign: string | string[] }
  | { add_label: string | string[] }
  | { remove_label: string | string[] }
  | { comment: string }
  | { notify: { channel?: string; to?: string; message: string } };
