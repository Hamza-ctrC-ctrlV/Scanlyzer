/**
 * URL validation helper
 * Returns error message or null if valid
 */
export function validateUrl(url) {
  if (!url.trim())
    return "Veuillez entrer une URL.";
  if (!url.startsWith("http://") && !url.startsWith("https://"))
    return "L'URL doit commencer par http:// ou https://";
  try {
    const p = new URL(url);
    const isLocalhost = ["localhost","127.0.0.1","0.0.0.0","::1"].some(l => p.hostname.startsWith(l));
    if (!p.hostname)
      return "Domaine invalide — exemple : https://mon-site.com";
    if (!isLocalhost && !p.hostname.includes("."))
      return "Domaine invalide — exemple : https://mon-site.com";
  } catch {
    return "URL invalide — vérifiez le format.";
  }
  return null;
}
