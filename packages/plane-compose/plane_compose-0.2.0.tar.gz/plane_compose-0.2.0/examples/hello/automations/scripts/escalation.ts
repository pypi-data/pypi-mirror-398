/**
 * Escalation Automation Script
 * 
 * Escalates items based on:
 * - Customer tier (enterprise, business, free)
 * - Time since creation
 * - Priority level
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
    createdAt?: string;
    updatedAt?: string;
  };
  trigger: {
    type: string;
    timestamp: string;
    changes?: Record<string, { from: unknown; to: unknown }>;
  };
  config: Record<string, unknown>;
}

type Action =
  | { set: Record<string, unknown> }
  | { assign: string | string[] }
  | { add_label: string | string[] }
  | { remove_label: string | string[] }
  | { comment: string }
  | { notify: { channel?: string; to?: string; message: string } };

// =============================================================================
// CONFIGURATION
// =============================================================================

const SLA_THRESHOLDS: Record<string, Record<string, number>> = {
  enterprise: { urgent: 1, high: 4, medium: 24, low: 48 },
  business: { urgent: 4, high: 12, medium: 48, low: 96 },
  free: { urgent: 24, high: 48, medium: 168, low: 336 },
};

const ESCALATION_CONTACTS: Record<string, string> = {
  enterprise: "enterprise-support@example.com",
  business: "support-manager@example.com",
  free: "support-team@example.com",
};

// =============================================================================
// AUTOMATION LOGIC
// =============================================================================

export default function run(ctx: Context): Action[] {
  const { workItem } = ctx;
  
  // Skip if already escalated
  if (workItem.labels.includes("escalated")) {
    return [];
  }
  
  // Get customer tier (default to 'free')
  // Note: Properties are converted to camelCase, so customer_tier becomes customerTier
  const customerTier = (workItem.properties.customerTier as string) || "free";
  const priority = workItem.priority || "medium";
  
  // Calculate hours since creation
  const createdAt = workItem.createdAt;
  if (!createdAt) {
    return [];
  }
  
  const hoursSinceCreation = getHoursSince(createdAt);
  
  // Get threshold for this tier and priority
  const tierThresholds = SLA_THRESHOLDS[customerTier] || SLA_THRESHOLDS.free;
  const threshold = tierThresholds[priority] || tierThresholds.medium;
  
  // Check if SLA is breached
  if (hoursSinceCreation > threshold) {
    const escalationContact = ESCALATION_CONTACTS[customerTier] || ESCALATION_CONTACTS.free;
    
    return [
      { add_label: "escalated" },
      { add_label: "sla-breach" },
      { set: { priority: "urgent" } },
      { assign: escalationContact },
      { 
        comment: `⚠️ **SLA BREACH**\n\n` +
          `This ${customerTier} tier item has exceeded the ${threshold}h SLA.\n` +
          `- Created: ${Math.round(hoursSinceCreation)}h ago\n` +
          `- Original priority: ${priority}\n` +
          `- Escalated to: ${escalationContact}`
      },
      { 
        notify: {
          channel: "#escalations",
          message: `🚨 SLA Breach: "${workItem.title}" (${customerTier} tier, ${Math.round(hoursSinceCreation)}h old)`
        }
      }
    ];
  }
  
  // Check if approaching SLA (80% of threshold)
  if (hoursSinceCreation > threshold * 0.8) {
    return [
      { add_label: "sla-warning" },
      { 
        comment: `⏰ **SLA Warning**\n\n` +
          `This item is approaching its SLA deadline.\n` +
          `- ${Math.round(threshold - hoursSinceCreation)}h remaining`
      }
    ];
  }
  
  return [];
}

// =============================================================================
// HELPERS
// =============================================================================

function getHoursSince(dateString: string): number {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  return diffMs / (1000 * 60 * 60);
}

