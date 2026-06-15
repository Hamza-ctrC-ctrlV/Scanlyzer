/**
 * URL validation helper
 * Returns error message or null if valid
 */
export function validateUrl(url) {
  if (!url.trim())
    return "Please enter a URL.";
  if (!url.startsWith("http://") && !url.startsWith("https://"))
    return "URL must start with http:// or https://";
  try {
    const p = new URL(url);
    const hostname = p.hostname?.toLowerCase() || "";
    const blockedHosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"];
    const isLocalhost = blockedHosts.some((l) => hostname === l || hostname.startsWith(`${l}:`));

    if (!hostname)
      return "Invalid domain — e.g. https://example.com";
    if (isLocalhost)
      return "Scanning localhost or loopback addresses is not allowed.";
    if (!hostname.includes("."))
      return "Invalid domain — e.g. https://example.com";
  } catch {
    return "Invalid URL — check the format.";
  }
  return null;
}
