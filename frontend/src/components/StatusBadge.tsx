export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  let cls = "badge-neutral";
  if (["completed", "success", "active", "ok"].includes(normalized)) cls = "badge-ok";
  if (["failed", "error", "invalid_response"].includes(normalized)) cls = "badge-bad";
  if (["running", "pending", "degraded"].includes(normalized)) cls = "badge-warn";
  return <span className={`badge ${cls}`}>{status}</span>;
}
