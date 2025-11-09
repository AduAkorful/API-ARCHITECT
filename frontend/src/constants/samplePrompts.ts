export interface SamplePrompt {
  label: string;
  description: string;
  prompt: string;
}

export const SAMPLE_PROMPTS: SamplePrompt[] = [
  {
    label: "Contact Form API",
    description: "Collects name, email, and message via POST.",
    prompt: "Create a POST endpoint at /contact that accepts name, email, and message fields. Validate email format and store submissions.",
  },
  {
    label: "Webhook Relay",
    description: "Receives JSON payload and forwards to another URL.",
    prompt: "Build a POST /webhook-relay endpoint that validates a topic and payload field, then queues the payload for delivery to an external webhook URL.",
  },
  {
    label: "Support Ticket Lookup",
    description: "Returns ticket details by ticket_id.",
    prompt: "Generate a GET /tickets/{ticket_id} endpoint that looks up a ticket by ID and returns subject, status, assignee, and last_updated fields.",
  },
  {
    label: "Inventory Updater",
    description: "Updates product quantity and price.",
    prompt: "Create a PUT /inventory/{sku} endpoint that accepts quantity, price, and is_active fields to update an inventory record.",
  },
];

