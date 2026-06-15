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
    const isLocalhost = ["localhost","127.0.0.1","0.0.0.0","::1"].some(l => p.hostname.startsWith(l));
    if (!p.hostname)
      return "Invalid domain — e.g. https://example.com";
    if (!isLocalhost && !p.hostname.includes("."))
      return "Invalid domain — e.g. https://example.com";
  } catch {
    return "Invalid URL — check the format.";
  }
  return null;
}
