export interface WritingCard {
	id: string // unique, stable identifier
	title: string // human-readable title
	content: string // text content (ideally a paragraph)
	tags: string[] // for grouping (e.g., ["scene", "chapter1"])
	status: CardStatus // "draft" | "edited" | "reviewed" | "final"
	history: VersionEntry[] // full versioning history
	position: CardPosition // for visual layout in corkboard
	metadata: {
		wordCount: number
		createdAt: Date
		updatedAt: Date
		chunkId?: string // reference to logical chunk
		color?: string // card color for visual organization
		priority?: number // for ordering/importance
	}
}

export interface VersionEntry {
	timestamp: Date
	content: string
	author?: string // human or AI assistant
	changeType: "create" | "edit" | "merge" | "split"
}

export interface ContentChunk {
	id: string
	name: string
	cardIds: string[] // ordered list of cards in this chunk
	purpose: string // e.g., "context-window", "chapter", "scene"
	layout: ChunkLayout // visual layout configuration
}

export interface CardPosition {
	x: number
	y: number
	width: number
	height: number
	zIndex?: number
}

export interface ChunkLayout {
	type: "grid" | "freeform" | "linear"
	columns?: number // for grid layout
	spacing?: number // gap between cards
	autoArrange?: boolean // auto-arrange cards
}

export type CardStatus = "draft" | "edited" | "reviewed" | "final"

export interface CardboardView {
	id: string
	name: string
	description?: string
	chunkIds: string[] // chunks visible in this view
	viewSettings: {
		zoom: number
		centerPoint: { x: number; y: number }
		showMetadata: boolean
		showConnections: boolean
		groupBy?: "status" | "tags" | "chunk" | "none"
	}
}
