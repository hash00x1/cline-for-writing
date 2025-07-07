import { randomUUID } from "crypto"

export function generateCardId(): string {
	return randomUUID()
}

export function extractTitle(content: string): string {
	// Extract first line or first sentence as title
	const lines = content.trim().split("\n")
	const firstLine = lines[0].trim()

	if (firstLine.length > 0) {
		// If first line is short, use it as title
		if (firstLine.length <= 50) {
			return firstLine
		}

		// Otherwise, take first sentence or truncate
		const sentences = firstLine.split(/[.!?]+/)
		const firstSentence = sentences[0].trim()

		if (firstSentence.length <= 50) {
			return firstSentence
		}

		// Truncate and add ellipsis
		return firstSentence.substring(0, 47) + "..."
	}

	return "Untitled Card"
}

export function countWords(content: string): number {
	if (!content || content.trim().length === 0) {
		return 0
	}

	// Remove extra whitespace and split by whitespace
	const words = content.trim().split(/\s+/)
	return words.length
}

export function detectParagraphs(text: string): string[] {
	// Split by double newlines to detect paragraphs
	return text
		.split(/\n\s*\n/)
		.map((p) => p.trim())
		.filter((p) => p.length > 0)
}

export function sanitizeFilename(filename: string): string {
	// Remove or replace invalid characters for filenames
	return filename
		.replace(/[<>:"/\\|?*]/g, "-")
		.replace(/\s+/g, "_")
		.toLowerCase()
}

export function formatDate(date: Date): string {
	return date.toISOString().split("T")[0]
}

export function formatTime(date: Date): string {
	return date.toLocaleTimeString()
}

export function truncateText(text: string, maxLength: number = 100): string {
	if (text.length <= maxLength) {
		return text
	}

	return text.substring(0, maxLength - 3) + "..."
}
