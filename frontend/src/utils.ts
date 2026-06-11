// Shared display helpers.

/**
 * The PDF parser sometimes pulls junk metadata (e.g. "Contact") as the
 * document title. Fall back to a sensible label when the title is empty
 * or a known-bad value.
 */
export function displayTitle(raw: string | null | undefined): string {
  const title = (raw ?? "").trim();
  if (title === "" || title.toLowerCase() === "contact") {
    return "Translation ready for Human Review";
  }
  return title;
}
